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
import gc

from .local_save import LocalSave

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
        self.authenticate = False
        self.message_log = LocalSave(sms_entries)
        self.device_log = LocalSave(device_cd)
        self.ws_url = "ws://192.168.178.32:8123/"

        self.device_id = self.check_device_id()

        self.ls = LocalSave(sms_entries)
    
    def initialize(self):
        self.schedule_event(self.initialize_websocket, datetime.now(),
                            name='socket_connection')

    def initialize_websocket(self):
        # Start a new thread for the WebSocket interface
        _thread.start_new_thread(self.__create_ws, ())
        
    @intent_file_handler('zod.intent')
    def handle_zod(self, message):
        self.speak_dialog('zod')

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

    @staticmethod
    def on_error(ws):
        pass

    def __create_ws(self):
        while True:
            try:
                websocket.enableTrace(False)
                self.__WSCONNECTION = websocket.WebSocketApp(self.ws_url,
                                            on_open= Zod.ws_open,
                                            on_message = Zod.ws_message,
                                            on_error = Zod.on_error,
                                            on_close = Zod.on_close
                                            )
                self.__WSCONNECTION.run_forever(skip_utf8_validation=True,ping_interval=10,ping_timeout=8)
            except Exception as e:
                gc.collect()
                LOG.debug("Websocket connection Error  : {0}".format(e))                    
            LOG.debug("Reconnecting websocket  after 5 sec")
            time.sleep(5)

    # def _speak_dialog(self, dialog, data=None, response =False):
    #     self.speak_dialog(dialog, data, response)

def create_skill():
    return Zod()
