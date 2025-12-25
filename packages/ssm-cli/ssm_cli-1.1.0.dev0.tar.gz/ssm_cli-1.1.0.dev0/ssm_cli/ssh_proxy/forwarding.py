r"""
This module is split into 2 parts, the proxy side and the manager side.

The proxy side is the code that runs in the main process along side the ssh server, it is responsible for handling all the requests for port forwarding and starting the manager process.

The manager side is the code that runs in a separate process and is responsible for starting and stopping the session-manager-plugin processes, including the clean up if things end unexpectedly.

[ssh server] <--> [PortForwardingSession] <--> [PortForwardingSessionProcess] <--> [session-manager-plugin]
    [ssh server] --> [PortForwardingSession] will send commands to us across many threads
    [PortForwardingSession] --> [manager] is a pipe for ipc
    [proxy] --> [session-manager-plugin] is a local socket on internal_port
    [manager] <-/-> [session-manager-plugin] doesnt connect to session-manager-plugin, it just starts and stops them
    [manager] --> [proxy] monitors the pipe and the process to see if cleanup is needed

"""

import io
import socket
from typing import Dict, Any, List
import time
import subprocess
import multiprocessing
import threading
from multiprocessing.connection import Connection

from ssm_cli.aws import aws_client, setup_aws, get_profile
from ssm_cli.instances import Instance, SessionManagerPluginError, SessionManagerPluginPortError
from ssm_cli.config import CONFIG
from confclasses import load, save

import logging

logger = logging.getLogger(__name__)

#######
# Proxy Side
# Names should reflect both sides
#######

class PortForwardingSession():
    """
    This is the object that the user will interact with
    """
    def __init__(self, manager: "PortForwarding", session_id: str, internal_port: int):
        self.manager = manager
        self.session_id = session_id
        self.internal_port = internal_port

    def is_open(self):
        return self.manager.is_open(self)
    
    def close(self):
        self.manager.close_session(self)

class PortForwarding():
    """
    Starts the manager process and creates the session objects.
    """
    session_cache: Dict[tuple, PortForwardingSession] # (host, port) -> session
    instance: Instance
    proxy_pipe: Connection
    pipe_lock: threading.Lock
    manager_process: multiprocessing.Process

    def __init__(self, instance):
        self.session_cache = {}
        self.instance = instance
    
    def start(self):
        logger.debug("starting manager process")
        self.proxy_pipe, manager_pipe = multiprocessing.Pipe()
        self.manager_process = PortForwardingManagerProcess(manager_pipe, self.instance)
        self.manager_process.start()

        logger.debug("waiting for manager process to start")
        self.pipe_lock = threading.Lock()
        ready = self.recv()
        if ready != "ready":
            logger.error(f"manager process failed to start: 'ready' != '{ready}'")
            self.manager_process.terminate()
            self.proxy_pipe.close()
            raise Exception("Manager process failed to start")

    def open_session(self, host: str, remote_port: int) -> PortForwardingSession:
        session = self.session_cache.get((host, remote_port))
        if session is not None:
            if self.is_open(session):
                logger.debug(f"{session.session_id} still running, reusing")
                return session
            else:
                logger.debug(f"{session.session_id} closed, opening new one")
                del self.session_cache[(host, remote_port)]

        session_id, internal_port = self.send_recv(("open_session", (host, remote_port)))
        session = PortForwardingSession(self, session_id, internal_port)
        self.session_cache[(host, remote_port)] = session
        return session
    
    def close_session(self, session: PortForwardingSession):
        self.proxy_pipe.send(("close_session", session.session_id))
        del self.session_cache[(session.host, session.remote_port)]

    def is_open(self, session: PortForwardingSession):
        return self.send_recv(("is_open", session.session_id))

    def is_alive(self):
        return self.manager_process.is_alive()
    
    def send(self, obj: Any):
        if not self.is_alive():
            raise Exception("Manager process has ended")
        with self.pipe_lock:
            logger.debug(f"sending {obj} to manager")
            self.proxy_pipe.send(obj)
    
    def recv(self) -> Any:
        if not self.is_alive():
            raise Exception("Manager process has ended")
        with self.pipe_lock:
            result = self.proxy_pipe.recv()
            logger.debug(f"received {result} from manager")
            return result
        
    def send_recv(self, obj: Any) -> Any:
        if not self.is_alive():
            raise Exception("Manager process has ended")
        with self.pipe_lock:
            logger.debug(f"sending {obj} to manager")
            self.proxy_pipe.send(obj)
            result = self.proxy_pipe.recv()
            logger.debug(f"received {result} from manager")
            return result

#######
# Manager Side
# class suffix should be Process
#######

class PortForwardingSessionProcess():
    """
    Exposes open/close methods for the sessions, this will send messages to the manager process to do the actual work.
    """
    _open: bool = False
    host: str
    remote_port: int
    internal_port: int
    session_id: str
    proc: subprocess.Popen
    instance: Instance

    def __init__(self, host: str, remote_port: int, instance: Instance):
        self.host = host
        self.remote_port = remote_port
        self.instance = instance

    def open(self):
        # Retry because of rare race condition from get_free_port
        for attempt in range(3):
            try:
                self.internal_port = get_free_port()
                logger.debug(f"getting session for localhost:{self.internal_port} to {self.host}:{self.remote_port} over {self.instance.id} from aws")
                session_id, proc = self.instance.start_port_forwarding_session_to_remote_host(self.host, self.remote_port, self.internal_port)
                self.session_id = session_id
                self.proc = proc
                self._open = True
                logger.info(f"{self.session_id} opened to {self.host}:{self.remote_port} on 127.0.0.1:{self.internal_port}, pid {self.proc.pid}")
                return
            except SessionManagerPluginPortError as e:
                logger.warning(f"session-manager-plugin attempt {attempt} failed due to port clash, retrying: {e}")
                time.sleep(0.1)

        logger.error(f"session-manager-plugin failed to open session to {self.host}:{self.remote_port} after {attempt} attempts")
        raise SessionManagerPluginError("Max retries hit") from e
    
    def close(self):
        logger.info(f"{self.session_id} closing")
        self._open = False
        try:
            logger.debug(f"{self.session_id} killing process {self.proc.pid}")
            self.proc.terminate()
            self.proc.wait()
        except Exception as e:
            logger.error(f"{self.session_id} failed to kill process: {e}")

        try:
            logger.debug(f"{self.session_id} terminating session")
            with aws_client('ssm') as client:
                client.terminate_session(SessionId=self.session_id)
        except Exception as e:
            logger.error(f"{self.session_id} to terminate session: {e}")

    def is_open(self):
        if self.proc.poll() is not None:
            logger.debug(f"process for {self.host}:{self.remote_port} has exited, restarting")
            self._open = False
        # the process ends when aws terminates the session, no need to check that
        return self._open


class PortForwardingManagerProcess(multiprocessing.Process):
    """
    This is the process that will run the manager code, it is responsible for starting and stopping the session-manager-plugin processes.
    As well as monitoring the proxy side and cleaning up.

    This runs in a single thread, no need for all the locking and threading like the other class.
    """

    sessions: List[PortForwardingSessionProcess]
    def __init__(self, pipe: Connection, instance: Instance):
        self.pipe = pipe
        self.instance = instance

        with io.StringIO() as f:
            save(CONFIG, f)
        
        self.config_yaml = f.getvalue()
        super().__init__()
    
    def run(self):
        # Rebuild some global state that ssm_cli.cli normally deals with, the manager process is a clean slate,
        # We can be selective about what we rebuild
        # when config/args are refactored, this should be taken into account.
        from ssm_cli.logging import setup_logging, set_log_level
        setup_logging("manager")
        set_log_level(CONFIG.log.level)
        for logger_name, level in CONFIG.log.loggers.items():
            set_log_level(level, name=logger_name)
        
        with io.StringIO(self.config_yaml) as f:
            load(CONFIG, f)
        self.sessions = []
        self.pipe.send("ready")
        while True:
            try:
                msg, data = self.pipe.recv()
                logger.debug(f"received {msg} {data} from proxy")
                reply = None
                if msg == "open_session":
                    reply = self.open_session(*data)
                elif msg == "close_session":
                    self.close_session(data)
                elif msg == "is_open":
                    reply = self.is_open(data)
                
                if reply is not None:
                    logger.debug(f"sending {reply} to proxy")
                    self.pipe.send(reply)
            except EOFError:
                break

    def open_session(self, host: str, remote_port: int):
        session = None
        for s in self.sessions:
            if s.host == host and s.remote_port == remote_port:
                logger.debug(f"{s.session_id} in cache for {host}:{remote_port}")
                if s.is_open():
                    logger.debug(f"{s.session_id} still running, reusing")
                    return s
                else:
                    logger.debug(f"{s.session_id} closed, removing from cache")
                    self.sessions.remove(s)

        session = PortForwardingSessionProcess(host, remote_port, self.instance)
        session.open()
        self.sessions.append(session)
        return session.session_id, session.internal_port
    
    def close_session(self, session_id: str):
        for session in self.sessions:
            if session.session_id == session_id:
                session.close()
                self.sessions.remove(session)

    def is_open(self, session_id: str) -> bool:
        for session in self.sessions:
            if session.session_id == session_id:
                if session.is_open():
                    return True
                else:
                    self.sessions.remove(session)
                    break
        return False

def get_free_port(bind_host="127.0.0.1"):
    """
    Ask OS for an ephemeral free port. Returns the port number, however it is not guaranteed that the port will remain free. A retry should be used.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((bind_host, 0))
    port = s.getsockname()[1]
    s.close()
    return port