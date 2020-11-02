from adapt.intent import IntentBuilder
from mycroft import MycroftSkill, intent_file_handler
from mycroft.messagebus.message import Message
from mycroft_bus_client import MessageBusClient, Message
from mycroft.util.log import LOG

from mycroft.util.parse import extract_datetime
from mycroft.util import play_wav
from mycroft.util import time as m_time

import os
import websocket
import _thread
import time
import json as js

from datetime import datetime, timedelta

print('Setting up client to connect to a local mycroft instance')
client = MessageBusClient()
client.run_in_thread()

sms_entries = "sms_entries"
device_cd = "device_credentials"

stopSig = False

device_id = "ZOD_69XXX420"

test_msg = {"time": "123412", "date": "21424","from": 'Obiwan','body': "I have the high ground"}

class Zod(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)
        self.ls = LocalSave(sms_entries)
    
    @intent_file_handler('zod.intent')
    def handle_zod(self, message):
        self.speak_dialog('zod')

    def initialize(self):
        self.schedule_event(self.initialize_websocket, datetime.now(),
                            name='socket_connection')
    
    @intent_file_handler('zod.speak_message')
    def read_message(self):
        temp_msg = self.ls.get_contents()
        if temp_msg == 0:
            self.speak_dialog('There are no new messages')
        else:
            sender_id = temp_msg[0]["sender"]
            msg = temp_msg[0]["message"]
            client.emit(Message('speak', data={'utterance': f'{sender_id} said: {msg}'}))
            self.ls.keep_sms()

    @intent_file_handler('zod.message_list')
    def check_messages(self):
        temp_entries = self.ls.check_entries()
        if temp_entries == 0:
            client.emit(Message('speak', data={'utterance': f'there are no new entries'}))
        else:
            client.emit(Message('speak', data={'utterance': f'There are {temp_entries}'}))

    def initialize_websocket(self):
        # Start a new thread for the WebSocket interface
        _thread.start_new_thread(self.ws_thread, ())
    
    # def _speak_dialog(self, dialog, data=None, response =False):
    #     self.speak_dialog(dialog, data, response)

    def ws_thread(self, *args):
        ws = websocket.WebSocketApp("ws://192.168.178.32:8123/", on_open = WebSocketManager.ws_open, on_message = WebSocketManager.ws_message, on_close= WebSocketManager.on_close)
        ws.run_forever()


def create_skill():
    return Zod()

class WebSocketManager:
    def __init__(self):

        self.authenticate = False
        self.message_log = LocalSave(sms_entries)
        self.device_log = LocalSave(device_cd)
        
        self.device_id = self.check_device_id()

    def check_device_id(self):
        try:
            temp_arr = self.device_log.get_contents()
            temp_id = temp_arr[0]["device_id"]
            return temp_id
        except:
            print("[Warning] No device ID given")
            LOG.info(f"[Warning] No device ID given")
            return ""

    @staticmethod
    def ws_message(ws, message):
        temp_sms = LocalSave(sms_entries)
        LOG.info("WebSocket thread: %s" % message)
        # data = {'message': str(message)}
        message = js.loads(message)
        if 'event' in message:
            event = message.get("event")
            LOG.info(f"Event: {event}")
            if event == "direct_message": 
                msg = message.get("message")
                LOG.info(f"msg: {msg}")
                sender_id = message.get("sender")
                receiver_id = message.get("receiver")
                LOG.info(f"receiver: {receiver_id}")
                if receiver_id == device_id:
                    LOG.info("same device :D")
                    temp_sms.update_file(message)
                    client.emit(Message('speak', data={'utterance': f'you have a new message from {sender_id}'}))
                # client.emit(Message('speak', data={'utterance': f'{sender_id} said: {msg}'}))
            
            if event == "close_con":
                stopSig = True
                try:
                    ws.close()
                except Exception as e:
                    pass

    @staticmethod
    def ws_open(ws):
        content = '{"event": "authenticate", "device_id": "'+ device_id +'"}'
        ws.send(content)
   
    @staticmethod
    def on_close(ws):
        LOG.info("### socket closed ###")

class LocalSave:
    def __init__(self, name = "temp"):
        self.file_name = (name+".txt")
        self.file = open(self.file_name,"a")
        self.content = {}
        self.entry_name = "Entries"
        self.content[self.entry_name] = []
        self.amount_of_entries = 0

        if os.path.isfile(self.file_name): # Check if sms log is already created
            self.check_entries()
            self.set_content()

    def check_entries(self): # To check the amount of entries in the sms log
        try:
            with open(self.file_name) as json_file:
                data = js.load(json_file)
                try: 
                    self.amount_of_entries = len(data[self.entry_name])
                    return self.amount_of_entries
                except:
                    print("[Info] Currently no entries")
                    return 0
        except:
            print("[Warning] File doesn't exist yet")
            return 0

    def set_content(self):  # Add content from the local file to local variable
        try:
            with open(self.file_name) as json_file:
                data = js.load(json_file)
                for i in range(self.amount_of_entries):
                    self.content[self.entry_name].append(data[self.entry_name][i])
        except:
            print("[Warning] contents not found")
                
    def update_file(self, content:dict): # Updates the localfile by overwritting the current file content , add dictonary to the param to store on a local file
        
        if content == {}:
            return 0

        temp_dict = {}
        temp_array = []

        for x, y in content.items():
            temp_array.append((x,y))
        
        temp_dict = dict(temp_array)    

        self.content[self.entry_name].append(temp_dict)

        with open(self.file_name,'w+') as outfile: # Overwrite content from the sms log
            js.dump(self.content,outfile, indent= 2) 

    def get_contents(self): # get content from local file and returns it in a list.
        temp_list = []
        try:
            with open(self.file_name) as json_file:
                data = js.load(json_file)
                for i in range(self.amount_of_entries):
                    temp_list.append(data[self.entry_name][i])
        except:
            print("[Warning] Empty")
            return 0
        return temp_list # Returns a list of logs

    def keep_sms(self, store= False): # Option to keep the sms, give a boolean to save if you want to.
        temp_list = self.get_contents()
        
        try:
            return_list = {}
            if store:
                return_list = temp_list[0]

            temp_list.pop(0)
            temp_content = {}
            temp_content[self.entry_name] = temp_list
            with open(self.file_name,'w+') as outfile: # Overwrite content from the sms log
                js.dump(temp_content,outfile, indent= 2) 
        except:
            print("[Warning] no entries")
            return 0

        return return_list