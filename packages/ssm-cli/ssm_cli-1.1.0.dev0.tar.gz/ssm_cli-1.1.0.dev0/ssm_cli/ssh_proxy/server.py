import threading
import paramiko
import socket
import time
import select

from ssm_cli.ssh_proxy.socket import StdIoSocket
from ssm_cli.ssh_proxy.shell import ShellThread
from ssm_cli.ssh_proxy.channels import Channels
from ssm_cli.ssh_proxy.forwarding import PortForwarding, PortForwardingSession
from ssm_cli.xdg import get_ssh_hostkey
from ssm_cli.instances import Instance

import logging
logger = logging.getLogger(__name__)

class SshServer(paramiko.ServerInterface):
    """
    Creates ssh server using StdIoSocket
    """
    event: threading.Event
    instance: Instance
    channels: Channels
    transport: paramiko.Transport
    port_forwarding_manager: PortForwarding
    
    def __init__(self, instance: Instance):
        logger.debug("creating server")
        self.event = threading.Event()
        self.instance = instance
        self.port_forwarding_manager = PortForwarding(instance)

    def start(self):
        logger.info("starting server")

        sock = StdIoSocket()
        self.transport = paramiko.Transport(sock)
        self.channels = Channels(self.transport)

        key_path = get_ssh_hostkey()
        host_key = paramiko.RSAKey(filename=key_path)
        logger.info("Loaded existing host key")
        self.transport.add_server_key(host_key)

        self.port_forwarding_manager.start()
        self.transport.start_server(server=self)

        self.event.wait()

    # Auth handlers, just allow anything. The only use of this code is ProxyCommand and auth is not needed
    def get_allowed_auths(self, username):
        logger.info(f"allowing all auths: username={username}")
        return "password,publickey,none"
    def check_auth_none(self, username):
        logger.info(f"accepting auth none: username={username}")
        return paramiko.AUTH_SUCCESSFUL
    def check_auth_password(self, username, password):
        logger.info(f"accepting auth password: username={username}")
        return paramiko.AUTH_SUCCESSFUL
    def check_auth_publickey(self, username, key):
        logger.info(f"accepting auth public key: username={username}")
        return paramiko.AUTH_SUCCESSFUL
    
    # Allow sessions
    def check_channel_request(self, kind, chanid):
        logger.info(f"received channel request: kind={kind} chanid={chanid}")
        if kind == 'session':
            return paramiko.OPEN_SUCCEEDED
        logger.error(f"we only accept session")
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY
    
    # Just accept the PTY request
    def check_channel_pty_request(self, channel, term, width, height, pixelwidth, pixelheight, modes):
        return True
    # Start a echo shell if requested
    def check_channel_shell_request(self, channel):
        logger.info(f"shell request: {channel.get_id()}")
        t = ShellThread(channel, self.channels)
        t.start()
        return True

    # Handle direct-tcpip requests when they come in, this will only be triggered when a connection is made.
    def check_channel_direct_tcpip_request(self, chanid, origin, destination):
        logger.info(f"direct TCP/IP request: chan={chanid} origin={origin} destination={destination}")
        host = destination[0]
        remote_port = destination[1]
        
        try:
            session = self.port_forwarding_manager.open_session(host, remote_port)
        except Exception as e:
            logger.error(f"failed to connect: {e}")
            return paramiko.OPEN_FAILED_CONNECT_FAILED
        
        logger.debug(f"connecting to session manager plugin on 127.0.0.1:{session.internal_port}")
        # Even though we wait for the process to say its connected, we STILL need to wait for it
        for attempt in range(10):
            try:
                sock = socket.create_connection(('127.0.0.1', session.internal_port))
                logger.info(f"connected to 127.0.0.1:{session.internal_port}")
                break
            except Exception as e:
                logger.warning(f"connection attempt {attempt} failed: {e}")
                time.sleep(0.1)
                if not session.is_open():
                    logger.error(f"session is closed")
                    return paramiko.OPEN_FAILED_CONNECT_FAILED
        else:
            logger.error("max retries reached, giving up")
            return paramiko.OPEN_FAILED_CONNECT_FAILED
        

        chunk_size = 1024

        # Start thread to open the channel and forward data
        def forwarding_thread():
            logger.info(f"starting forward thread chan={chanid}")

            chan = self.channels.get_channel(chanid)
            while True:
                r, _, _ = select.select([chan, sock], [], [])
                if sock in r:
                    data = sock.recv(chunk_size)
                    if len(data) == 0:
                        break
                    chan.send(data)

                if chan in r:
                    data = chan.recv(chunk_size)
                    if len(data) == 0:
                        break
                    sock.send(data)
   
            session.close()
            logger.info(f"forward thread chan={chanid} exiting")
        
        t = threading.Thread(target=forwarding_thread)
        t.start()

        logger.debug("started forwarding thread")
        return paramiko.OPEN_SUCCEEDED
    
    def get_banner(self):
        return ("SSM CLI - SSH server\r\n", "en-US")
