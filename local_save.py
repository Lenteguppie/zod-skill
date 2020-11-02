import os
import json as js
import datetime as dt

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



# content = {"device_id": "ZOD", "customer_id": "Obiwan"}
new = {"Time": "123412", "Date": "21424","From": 'Obiwan','Body': "I have the high ground"}
ls = LocalSave("device")
# ls.update_file(new)
ls.get_contents()
print(ls.get_contents())
# ls.update_file(new)
# ls.set_content()


# old = LocalSave("old_sms")
# old.update_file(ls.keep_sms(True))
# print(old.get_contents())