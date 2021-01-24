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
import json as js
import gc
import threading
import requests
import RPi.GPIO as GPIO

from .local_save import LocalSave
import _thread, time
import json

import gc

from datetime import datetime, timedelta

ws_connected = False

print('Setting up client to connect to a local mycroft instance')
client = MessageBusClient()
client.run_in_thread()

sms_entries = "sms_entries"
device_cd = "device_credentials"
ws_url = "ws://[IP]:[PORT]/"

stopSig = False
contacts = ["+316xxxxxx"]
contact_name = ["Tom"]
device_id = "ZOD69XXX420"
virtual_number = "+3197010252540"

register = {"register": False, "device_id": device_id}
device_id = "ZOD_69XXX420"
ws_url = "ws://yeplab.com:6456/"

def ws_message(ws, message):
    temp_sms = LocalSave(sms_entries)
    LOG.info("WebSocket thread: %s" % message)
    # data = {'message': str(message)}
    try:
        message = js.loads(message)
    except Exception as e:
        print(e)

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
                LOG.info("Correct device")
                temp_sms.update_file(message)

                client.emit(Message('speak', data={'utterance': f'you have a new message from {sender_id}'}))
                
                ws.send('{"event": "verify", "message_received": "True"}')
            # client.emit(Message('speak', data={'utterance': f'{sender_id} said: {msg}'}))
        
        if event == "close_con":
            stopSig = True
            try:
                ws.close()
            except Exception as e:
                print(e)

def ws_open(ws):
    content = '{"event": "authenticate", "device_id": "'+ device_id +'"}'
    ws.send(content)

def on_close(ws):
    LOG.info("### socket closed ###")

def on_error(ws,error):
    print(error)


class Zod(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)
        self.authenticate = False
        self.message_log = LocalSave(sms_entries)
        # self.device_log = LocalSave(device_cd)
        self.ws_url = "ws://192.168.178.31:8123/"
        self.led = 27

        self.ls = LocalSave(sms_entries)
    
    def initialize(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self.led, GPIO.OUT)
        self.schedule_event(self.initialize_websocket, datetime.now(),
                            name='socket_connection')
        GPIO.output(self.led, GPIO.LOW)
        self.add_event('recognizer_loop:record_begin', self.handle_listener_started)
        self.add_event('recognizer_loop:record_end', self.handle_listener_ended)
    
    def handle_listener_started(self, message):
        GPIO.output(self.led, GPIO.HIGH)

    def handle_listener_ended(self, message):
        GPIO.output(self.led, GPIO.LOW)

    def initialize_websocket(self):
        # Start a new thread for the WebSocket interface
        _thread.start_new_thread(self.__create_ws, ())
        
    @intent_file_handler('zod.intent')
    def handle_zod(self, message):
        self.speak_dialog('zod')

    @intent_file_handler('zod.speak_message')
    def read_message(self):
        temp_msg = self.ls.get_contents()
        temp_entries = self.ls.check_entries()
        if temp_entries == 0:
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
            if temp_entries == 1:
                client.emit(Message('speak', data={'utterance': f'There is {temp_entries}'}))
            else:
                client.emit(Message('speak', data={'utterance': f'There are {temp_entries}'}))
    
    # For future warning functionalities
    @intent_file_handler('zod.warning')
    def warning_message(self):
        contacts = "+316xxxxxxx"
        try:

            temp_obj = {'event': "warning", 'device_id': device_id, 'contact':contacts, 'virtual_number': virtual_number}
            requests.post("http://192.168.178.31:8000/warning", data= temp_obj, timeout= 1) # POST to server

        except Exception as e:
            print(e)
        

    def message_filter(self, message):
        pass

    def get_contacts(self):
        pass

    def __create_ws(self):

        while True:

            try: 
                websocket.enableTrace(False)
                self.__WSCONNECTION = websocket.WebSocketApp(self.ws_url,
                                            on_open= ws_open,
                                            on_message = ws_message,
                                            on_error = on_error,
                                            on_close = on_close
                                            )
                self.__WSCONNECTION.run_forever(skip_utf8_validation=True,ping_interval=10,ping_timeout=8)
                
            except Exception as e:
                gc.collect()
                LOG.debug("Websocket connection Error  : {0}".format(e))                    
            LOG.debug("Reconnecting websocket  after 5 sec")
            time.sleep(5)


def create_skill():
    return Zod()
