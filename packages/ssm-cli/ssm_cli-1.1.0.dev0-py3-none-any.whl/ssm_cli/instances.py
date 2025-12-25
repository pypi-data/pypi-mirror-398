from functools import cache
import json
import re
import signal
import subprocess
import sys
from typing import List, Tuple

from ssm_cli.selectors import SELECTORS
from ssm_cli.aws import aws_client, aws_session
from ssm_cli.config import CONFIG

import logging
logger = logging.getLogger(__name__)

class SessionManagerPluginError(Exception):
    """ A generic exception for any AWS errors """
    stdout = []
    returncode = 0
    def __init__(self, message, stdout = None, returncode = None):
        super().__init__(message)
        self.stdout = stdout
        self.returncode = returncode
    
    def __str__(self):
        return f"{super().__str__()} (returncode={self.returncode}, stdout={self.stdout})"

class SessionManagerPluginPortError(SessionManagerPluginError):
    """ A specific exception for a timeout error """
    pass

class Instance:
    """
    Contains information about an EC2 instance and methods to handle sessions with them.
    """
    id: str
    name: str = None
    ip: str = None
    ping: str = None

    def __str__(self):
        return f"{self.id} {self.ip:<15} {self.ping:<7} {self.name}"
    
    def start_session(self):
        logger.debug(f"start session instance={self.id}")

        with aws_session() as session, aws_client('ssm') as client:
            parameters = dict(
                Target=self.id
            )
            
            logger.info("calling out to ssm:StartSession")
            response = client.start_session(**parameters)
            logger.info(f"starting session: {response['SessionId']}")
            result = _session_manager_plugin([
                json.dumps({
                    "SessionId": response["SessionId"],
                    "TokenValue": response["TokenValue"],
                    "StreamUrl": response["StreamUrl"]
                }),
                session.region_name,
                "StartSession",
                session.profile_name if hasattr(session, "profile_name") else "",
                json.dumps(parameters),
                f"https://ssm.{session.region_name}.amazonaws.com"
            ])
            if result != 0:
                logger.error(f"Failed to connect to session: {result.stderr.decode()}")
                raise RuntimeError(f"Failed to connect to session: {result.stderr.decode()}")
        
    def start_port_forwarding_session_to_remote_host(self, host: str, remote_port: int, internal_port: int) -> Tuple[str, subprocess.Popen]:
        """
        Start a port forwarding session to a remote host.

        Args:
            host: The remote host to forward to.
            remote_port: The remote port to forward to.
            internal_port: The local port use for forwarding.
        
        Returns:
            A tuple containing the session id and the subprocess.
        """
        logger.debug(f"start port forwarding between localhost:{internal_port} and {host}:{remote_port} via {self.id}")
        with aws_session(False) as session:
            client = session.client('ssm') # we need a fresh connection where session is the same as the client

            parameters = dict(
                Target=self.id,
                DocumentName='AWS-StartPortForwardingSessionToRemoteHost',
                Parameters={
                    'host': [host],
                    'portNumber': [str(remote_port)],
                    'localPortNumber': [str(internal_port)]
                }
            )
            logger.info("calling out to ssm:StartSession")
            response = client.start_session(**parameters)

            logger.info(f"starting session: {response['SessionId']}")
            proc = subprocess.Popen(
                [
                    "session-manager-plugin",
                    json.dumps({
                        "SessionId": response["SessionId"],
                        "TokenValue": response["TokenValue"],
                        "StreamUrl": response["StreamUrl"]
                    }),
                    session.region_name,
                    "StartSession",
                    session.profile_name,
                    json.dumps(parameters),
                    f"https://ssm.{session.region_name}.amazonaws.com"
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT
            )

            # changes needed here:
            # SessionManagerPluginPortError needs to be raised when it applies
            # add a timeout for waiting on stdout
            # maybe split up stdout/stderr?
            # validate the port in stdout matches the internal port
            output = b''
            for line in proc.stdout:
                line = line.strip()
                output += line + b'\n'
                if line == b'Waiting for connections...':
                    return (response["SessionId"], proc)
                else:
                    logger.debug(f"Recieved from session-manager-plugin: {line}")
            
            raise SessionManagerPluginError("Failed to start port forwarding session", output, proc.returncode)

def _session_manager_plugin( command: list) -> int:
    """ Call out to subprocess and ignore interrupts """
    if sys.platform == "win32":
        signals_to_ignore = [signal.SIGINT]
    else:
        signals_to_ignore = [signal.SIGINT, signal.SIGQUIT, signal.SIGTSTP]

    original_signal_handlers = {}
    for sig in signals_to_ignore:
        original_signal_handlers[sig] = signal.signal(sig, signal.SIG_IGN)
    try:
        return subprocess.check_call(["session-manager-plugin", *command])
    finally:
        for sig, handler in original_signal_handlers.items():
            signal.signal(sig, handler)


class Instances:
    def select_instance(self, group_tag_value: str, selector: str) -> Instance:
        instances = sorted(self.list_instances(group_tag_value), key=lambda x: ip_as_int(x.ip))
        count = len(instances)
        if count == 1:
            return instances[0]
        if count < 1:
            return
        
        if selector not in SELECTORS:
            raise ValueError(f"invalid selector {selector}")
        
        self.selector = SELECTORS[selector]
        return self.selector(instances)

    def list_groups(self) -> List[dict]:
        groups = {}
        for resource in self._tags_get_resources():
            value = get_tag(resource['Tags'], CONFIG.group_tag_key)
            if value:
                if value not in groups:
                    groups[value] = []
                groups[value].append(resource['ResourceARN'])

        result = []
        for group in groups:
            ssm_info = self._ssm_describe_instance_information(group)
            online = len([info for info in ssm_info if info['PingStatus'] == 'Online'])
            result.append({
                'name': group,
                'total': len(groups[group]),
                'online': online
            })

        return result

    def list_instances(self, group_tag_value: str, include_missing_ssm: bool = False) -> List[Instance]:
        instances = []
        ssm_info = self._ssm_describe_instance_information(group_tag_value)
        tag_resources = self._tags_get_resources(group_tag_value)

        for resource in tag_resources:
            instance = Instance()
            instance.id = arn_to_instance_id(resource['ResourceARN'])
            instance.name = get_tag(resource['Tags'], 'Name')
            for info in ssm_info:
                if info['InstanceId'] == instance.id:
                    instance.ip = info['IPAddress']
                    instance.ping = info['PingStatus']

            if include_missing_ssm or instance.ip:
                instances.append(instance)

        return instances

    def _tags_get_resources(self, group_tag_value: str = None):
        logger.info("calling out to resourcegroupstaggingapi:GetResources")

        with aws_client('resourcegroupstaggingapi') as client:
            paginator = client.get_paginator('get_resources')
            tag_filter = {
                'Key': CONFIG.group_tag_key
            }
            if group_tag_value is not None:
                tag_filter['Values'] = [group_tag_value]

            logger.debug(f"filtering on {tag_filter}")
            page_iter = paginator.paginate(
                ResourceTypeFilters=[
                    "ec2:instance"
                ],
                TagFilters=[tag_filter]
            )
            total = 0
            for page in page_iter:
                for resource in page['ResourceTagMappingList']:
                    total += 1
                    yield resource
            logger.debug(f"yielded {total} resources")


    def _ssm_describe_instance_information(self, group_tag_value: str):
        logger.info("calling out to ssm:DescribeInstanceInformation")
        with aws_client('ssm') as client:
            response = client.describe_instance_information(
                Filters=[
                    {
                        'Key': f'tag:{CONFIG.group_tag_key}',
                        'Values': [group_tag_value]
                    }
                ]
            )
            logger.debug(f"found {len(response['InstanceInformationList'])} instances")
            return response['InstanceInformationList']



def get_tag(tags: list, key: str) -> str:
    for tag in tags:
        if tag['Key'] == key:
            return tag['Value']
    return None

@cache
def arn_to_instance_id(arn: str) -> str:
	parts = arn.split('/')
	if len(parts) != 2:
		raise ValueError(f"invalid instance arn {arn}")
	return parts[1]


def ip_as_int(ip: str) -> int:
    m = re.match(r'(\d+)\.(\d+)\.(\d+)\.(\d+)', ip)
    if not m:
        raise ValueError(f"Invalid IP address: {ip}")
    return (int(m.group(1)) << 24) + (int(m.group(2)) << 16) + (int(m.group(3)) << 8) + int(m.group(4))
