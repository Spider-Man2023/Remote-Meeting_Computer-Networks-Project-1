import asyncio
import sys
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
import aiosip
from util import *


class ConferenceClient:
    def __init__(self, loop):
        self.loop = loop
        self.is_working = True
        self.mainserver_addr = (SERVER_IP, MAIN_SERVER_PORT)  # SIP server address
        self.on_meeting = False  # Status
        self.conns = {}  # Dictionary to maintain multiple connections
        self.support_data_types = ["audio", "video", "screen"]  # Supported data types
        self.share_data = {data_type: False for data_type in self.support_data_types}
        self.conference_info = {'conference_id':0, 'manager': False}  # Store conference id and if it's manager
        self.sipapp = aiosip.Application(loop=self.loop)  # aiosip application
        self.connection = None
        self.recv_data = None
        # todo: [Additional function] self.username might be registered when first connect to mainserver?
        self.username = 'client'
        # todo: ip_addr should be the real ip address of the client
        self.ip_addr = '127.0.0.1'
        self.sip_port = 5061

    async def create_conference(self):
        """
        Create a conference: send a create-conference request to the server
        """
        if self.on_meeting:
            print("[Warn]: You are already in a conference. Quit before creating a new one.")
            return

        response = await self.connection.request(
            method="CREATE",
            from_uri=f"sip:{self.username}@{self.ip_addr}:",
            to_uri=f"sip:server@{self.mainserver_addr[0]}:{self.mainserver_addr[1]}",
            headers={},
            payload="{}",
        )
        if response.status_code == 200:
            self.on_meeting = True
            self.conference_info['conference_id'] = response.headers['Conference-ID']
            self.conference_info['manager'] = True
            print("[Info]: Conference created successfully.")
        else:
            print("[Error]: Failed to create conference.")

    async def join_conference(self, conference_id):
        """
        Join a conference: send a join-conference request to the server
        """
        if self.on_meeting:
            print("[Warn]: You are already in a conference. Quit before joining another one.")
            return

        headers = {
            "Conference-ID": conference_id
        }
        response = await self.connection.request(
            method="JOIN",
            from_uri=f"sip:{self.username}@localhost",
            to_uri=f"sip:server@{self.mainserver_addr[0]}:{self.mainserver_addr[1]}",
            headers=headers,
            payload=None,
        )
        if response.status_code == 200:
            self.on_meeting = True
            self.conference_info['conference_id'] = conference_id
            self.conference_info['manager'] = False
            print(f"[Info]: Joined conference {conference_id} successfully.")
        else:
            print("[Error]: Failed to join conference.")

    async def quit_conference(self):
        """
        Quit your on-going conference
        """
        if not self.on_meeting:
            print("[Warn]: You are not in a conference.")
            return

        headers = {
            "Conference-ID": self.conference_info['conference_id'],
        }
        response = await self.connection.request(
            method="QUIT",
            from_uri=f"sip:{self.username}@localhost",
            to_uri=f"sip:server@{self.mainserver_addr[0]}:{self.mainserver_addr[1]}",
            headers=headers,
            payload=None,
        )
        if response.status_code == 200:
            self.on_meeting = False
            print("[Info]: Quit conference successfully.")
        else:
            print("[Error]: Failed to quit conference.")

    async def cancel_conference(self):
        """
        Cancel your on-going conference
        """
        if not self.on_meeting:
            print("[Error]: You are not in a conference.")
            return
        if not self.conference_info['manager']:
            print('[Error]: You are not the manager.')
            return
        
        headers = {
            "Conference-ID": self.conference_info['conference_id']
        }
        response = await self.connection.request(
            method="CANCEL",
            from_uri=f"sip:{self.username}@localhost",
            to_uri=f"sip:server@{self.mainserver_addr[0]}:{self.mainserver_addr[1]}",
            headers=headers,
            payload=None,
        )
        if response.status_code == 200:
            self.on_meeting = False
            print("[Info]: Conference cancelled successfully.")
        else:
            print("[Error]: Failed to cancel conference.")

    async def share_switch(self, data_type):
        """
        Switch sharing status for a specific data type
        """
        if data_type not in self.support_data_types:
            print(f"[Warn]: Unsupported data type: {data_type}")
            return

        self.share_data[data_type] = not self.share_data[data_type]
        status = "started" if self.share_data[data_type] else "stopped"
        print(f"[Info]: {data_type.capitalize()} sharing {status}.")

    async def start(self):
        """
        Start the SIP Client: handle commands from input
        """
        self.connection = await self.sipapp.connect(
            local_addr=(self.ip_addr, self.sip_port),  # Local SIP client address
            remote_addr=self.mainserver_addr,
            protocol=aiosip.TCP
        )
        print("[Info]: SIP Client started.")

        while True:
            if not self.on_meeting:
                status = 'Free'
            else:
                status = f'OnMeeting-{self.conference_id}'

            recognized = True
            cmd_input = input(f'({status}) Please enter a operation (enter "?" to help): ').strip().lower()
            fields = cmd_input.split(maxsplit=1)
            if len(fields) == 1:
                if cmd_input in ('?', '?'):
                    print(HELP)
                elif cmd_input == 'create':
                    self.create_conference()
                elif cmd_input == 'quit':
                    self.quit_conference()
                elif cmd_input == 'cancel':
                    self.cancel_conference()
                else:
                    recognized = False
            elif len(fields) == 2:
                if fields[0] == 'join':
                    input_conf_id = fields[1]
                    if input_conf_id.isdigit():
                        self.join_conference(input_conf_id)
                    else:
                        print('[Warn]: Input conference ID must be in digital form')
                elif fields[0] == 'switch':
                    data_type = fields[1]
                    if data_type in self.share_data.keys():
                        self.share_switch(data_type)
                else:
                    recognized = False
            else:
                recognized = False

            if not recognized:
                print(f'[Warn]: Unrecognized cmd_input {cmd_input}')


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    client = ConferenceClient(loop)
    loop.run_until_complete(client.start())
