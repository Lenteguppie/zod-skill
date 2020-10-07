from mycroft import MycroftSkill, intent_file_handler


class Zod(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)

    @intent_file_handler('zod.intent')
    def handle_zod(self, message):
        self.speak_dialog('zod')


def create_skill():
    return Zod()

