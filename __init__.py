from adapt.intent import IntentBuilder
from mycroft import MycroftSkill, intent_file_handler
from mycroft.messagebus.message import Message
from mycroft_bus_client import MessageBusClient, Message
from mycroft.util.log import LOG

from mycroft.util.parse import extract_datetime
from mycroft.util import play_wav
from mycroft.util import time as m_time


import websocket
import _thread
import time
import json

from datetime import datetime, timedelta

print('Setting up client to connect to a local mycroft instance')
client = MessageBusClient()
client.run_in_thread()

stopSig = False

device_id = "ZOD_69XXX420"

# Define WebSocket callback functions
def ws_message(ws, message):
    LOG.info("WebSocket thread: %s" % message)
    # data = {'message': str(message)}
    message = json.loads(message)
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
                client.emit(Message('speak', data={'utterance': f'{sender_id} said: {msg}'}))
        
        if event == "close_con":
            stopSig = True
            try:
                ws.close()
            except Exception as e:
                pass
        
        #calendar listener
        if event == "calendar_push":
            if message.get("sync") == True:

                client.emit(Message(msg_type="recognizer_loop:utterance", data={'utterances': ['refresh the reminders']}))

def ws_open(ws):
    ws.send('{"event":"authenticate", "device_id":"'+ device_id +'"}')

def on_close(ws):
    LOG.info("### socket closed ###")
    

class Zod(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)
    
    @intent_file_handler('zod.intent')
    def handle_zod(self, message):
        self.speak_dialog('zod')

    def initialize(self):
        self.schedule_event(self.initialize_websocket, datetime.now(),
                            name='socket_connection')
    
    def initialize_websocket(self):
        # Start a new thread for the WebSocket interface
        _thread.start_new_thread(self.ws_thread, ())
    
    # def _speak_dialog(self, dialog, data=None, response =False):
    #     self.speak_dialog(dialog, data, response)

    def ws_thread(self, *args):
        ws = websocket.WebSocketApp("ws://192.168.86.48:8123/", on_open = ws_open, on_message = ws_message, on_close= on_close)
        ws.run_forever()


def create_skill():
    return Zod()