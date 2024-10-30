import json
import cryptocode
import os
import sys

class configManager:
    def __init__(self):
        self.userpassword = ""
        try:
            with open(self.__getJsonConfigFile("psvsconfig.json"),'r') as config:
                self.configData = json.load(config)
        except:
            print("fichier de configuration psvsconfig.json introuvable.")
            return
    
    def __getJsonConfigFile(self,filename):
        if hasattr(sys, '_MEIPASS'):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.abspath(".")
        
        return os.path.join(base_path, filename)
    
    def setConfig(self,dbname,dbpass="",user="",tosave=True):
        if dbpass == "":
            return False
        elif user == "":
            return False
        else:
            if tosave:
                if dbpass != "":
                    self.configData["envdata"][dbname]["password"] = self.__encyptDbPassword(dbpass,self.userpassword)
                elif user != "":
                    self.configData["envdata"][dbname]["user"] = user
                with open(self.__getJsonConfigFile("psvsconfig.json"), "w") as jsonFile:
                    json.dump(self.configData, jsonFile)      
            return True
        
    def getPath(self):
        return self.configData['projectpath']
    
    def getDbCs(self,dbname):
        return self.configData["envdata"][dbname]["dbcs"]
    
    def getDbPassword(self,dbname):
        encdbpass = self.configData["envdata"][dbname]["password"]
        #print(f"pass : {encdbpass} / user pass : {self.userpassword}")
        return self.__decryptDbPassword(encdbpass,self.userpassword)

    def getUser(self,dbname):
        return self.configData["envdata"][dbname]["user"]
    
    def __encyptDbPassword(self,dbpassword,userpassword):
        encoded = cryptocode.encrypt(dbpassword,userpassword)
        return encoded
   
    def __decryptDbPassword(self,encodedbpass,userpassword):
        decoded = cryptocode.decrypt(encodedbpass,userpassword)
        return decoded
    
    def saveDbPasswordAndUserName(self,dbname,dbpass,username):        
        self.configData["envdata"][dbname]["user"] = username
        self.configData["envdata"][dbname]["password"] = self.__encyptDbPassword(dbpass,self.userpassword)
        
        with open(self.__getJsonConfigFile("psvsconfig.json"), "w") as jsonFile:
            json.dump(self.configData, jsonFile)
        
    def CheckUserPassword(self,userpassword)-> bool:
        savedpass = self.configData["passhash"]      
        entredpass = self.hash(userpassword)
        if savedpass==entredpass:
            self.userpassword = userpassword
        return savedpass==entredpass
    
    def hash(self,text:str):
        hash=0
        for ch in text:
            hash = ( hash*281  ^ ord(ch)*997) & 0xFFFFFFFF
        return hash
    
    def setUserPassword(self,userpassword):
        self.configData["passhash"] = self.hash(userpassword)
        with open(self.__getJsonConfigFile("psvsconfig.json"), "w") as jsonFile:
            json.dump(self.configData, jsonFile)
            
    def setEnvPasswordAndUserName(self,dbname,cs,dbpass,username,clipass) -> int:
        try :
            self.configData["envdata"][dbname] = {}
            self.configData["envdata"][dbname]["dbcs"] = cs
            self.configData["envdata"][dbname]["user"] = username
            self.configData["envdata"][dbname]["password"] = self.__encyptDbPassword(dbpass,clipass)
            return 1
        except:
            return 0            
        
    def checkDb(self,dbname) -> bool:
        try:
            if self.configData["envdata"][dbname] == "":
                return False
            else:
                return True
        except:
            return False
    
    def checkDbParams(self,dbname) -> bool:
        try:
            if self.configData["envdata"][dbname]["dbcs"].strip() == "" or self.configData["envdata"][dbname]["user"].strip() == "" or self.configData["envdata"][dbname]["password"].strip() == "":
                return False
            else:
                return True
        except:
            return False
    
    def saveConfigFile(self):
        with open(self.__getJsonConfigFile("psvsconfig.json"), "w") as jsonFile:
            json.dump(self.configData, jsonFile)             
            
    def loadConfigurationFromOraFile(self) -> bool:
        #check for ora file
        result = {}
        if self.configData["oradir"].strip() != "":
            params = ""
            newKey = ""
            dictparam = {}
            with open(self.configData["oradir"],"r") as orafile :
                lines = [line for line in orafile]
 
                for line in lines:
                    if not line.startswith("#"):                        
                        #line that contains params
                        if line.strip().startswith("(") or line.strip().startswith(")"):
                            params += line.strip()                           
                        elif line.strip() != "" and "=" in line:
                            if newKey != "":
                                dictparam[newKey]=params
                                params=""
                            newKey=line.replace("=","").strip()
        else :
            return False
        
        for key in dictparam.keys():
            self.configData["envdata"][key] = {}
            self.configData["envdata"][key]["dbcs"] = dictparam[key]
            self.configData["envdata"][key]["user"] = ""
            self.configData["envdata"][key]["password"] = ""
            
        with open(self.__getJsonConfigFile("psvsconfig.json"), "w") as jsonFile:
            json.dump(self.configData, jsonFile)
        
        return True       
    
    def registerDb(self,clipassword,dbname,cs,user,password):
        self.configData["envdata"][dbname] = {}
        self.configData["envdata"][dbname]["dbcs"] = cs
        self.configData["envdata"][dbname]["user"] = user
        self.configData["envdata"][dbname]["password"] = self.__encyptDbPassword(password,clipassword)
        
        with open(self.__getJsonConfigFile("psvsconfig.json"), "w") as jsonFile:
            json.dump(self.configData, jsonFile)
                