from enum import Enum
from typing import Tuple

import boto3

class ServerStatus(Enum):
    RUNNING = 1
    PENDING = 2
    SHUTTING_DOWN = 3
    TERMINATED = 4
    STOPPING = 5
    STOPPED = 6
    UNKNOWN = 7

class MinecraftAwsClient:
    def __init__(self, aws_access_key_id=None, aws_secret_access_key=None):
        if bool(aws_access_key_id) != bool(aws_secret_access_key):
            raise ValueError("Both aws_access_key_id and aws_secret_access_key must be provided together.")

        self._REGION = "us-east-1"
        self._INSTANCE_ID = "i-0a70e43874886f1fe"

        self._session = self._get_session(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key
        )
        self.__secrets_client = None
        self.__ec2_client = None

    def _get_session(self, aws_access_key_id=None, aws_secret_access_key=None):
        if aws_access_key_id and aws_secret_access_key:
            self._session = boto3.session.Session(
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key
            )
            return self._session

        if not self._session:
            self._session = boto3.session.Session()
        
        return self._session
    
    def _get_secrets_client(self):
        # We don't create a new client if it already exists. If it doesn't already exist, we cache it
        session = self._get_session()
        if not self.__secrets_client:
            self.__secrets_client = session.client(
                service_name='secretsmanager',
                region_name=self._REGION
            )
        
        return self.__secrets_client

    def _get_ec2_client(self):
        session = self._get_session()
        if not self.__ec2_client:
            self.__ec2_client = session.client(
                service_name='ec2',
                region_name=self._REGION
            )
        
        return self.__ec2_client

    def _translate_status_from_aws(self, raw_status) -> ServerStatus:
        instance_state = raw_status.replace('-', '_').upper()

        try:
            return ServerStatus[instance_state]
        except:
            return ServerStatus.UNKNOWN

    def start_server(self) -> Tuple[ServerStatus, ServerStatus]:
        """
        Returns a tuple of `ServerStatus`es.
        The first server status shows the previous state of the server.
        The second server status shows the current state of the server after the starting command.
        """
        response = self._get_ec2_client().start_instances(InstanceIds=[self._INSTANCE_ID])

        begin_state_raw = response['StartingInstances'][0]['PreviousState']['Name']
        begin_state = self._translate_status_from_aws(begin_state_raw)
        end_state_raw = response['StartingInstances'][0]['CurrentState']['Name']
        end_state = self._translate_status_from_aws(end_state_raw)

        return begin_state, end_state

    def stop_server(self) -> Tuple[ServerStatus, ServerStatus]:
        """
        Returns a tuple of `ServerStatus`es.
        The first server status shows the previous state of the server.
        The second server status shows the current state of the server after the ending command.
        """
        response = self._get_ec2_client().stop_instances(InstanceIds=[self._INSTANCE_ID])

        print(response)
        begin_state_raw = response['StoppingInstances'][0]['PreviousState']['Name']
        begin_state = self._translate_status_from_aws(begin_state_raw)
        end_state_raw = response['StoppingInstances'][0]['CurrentState']['Name']
        end_state = self._translate_status_from_aws(end_state_raw)

        return begin_state, end_state

    def get_minecraft_server_status(self) -> ServerStatus:
        """
        Returns the current `ServerStatus` for the Minecraft server
        """
        ec2_client = self._get_ec2_client()
        response = ec2_client.describe_instance_status(InstanceIds=[self._INSTANCE_ID])

        if not response['InstanceStatuses']:
            return ServerStatus.STOPPED
        
        instance_state_raw = response['InstanceStatuses'][0]['InstanceState']['Name']

        return self._translate_status_from_aws(instance_state_raw)

    def minecraft_server_is_running(self) -> bool:
        """
        Returns a boolean showing if the server is on or not
        """
        return self.get_minecraft_server_status() == ServerStatus.RUNNING