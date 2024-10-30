from comparator import *
import oracledb
import json
import pathlib
import re
from  compWindow import *
import threading
from winController import *
from configManager import *
from multThreading import *

class Manager():
    def __init__(self,confmanager):
        
        self.chunkSize = 900000
        self.path = confmanager.getPath()
        self.ObjectsEvents = dict()
        self.comWinThread = None
        self.compareWindow = None
        self.comparator = FileComparator()
        self.conrollersList = list()
        self.windowsList = list(tuple())
        self.winThreads = list()
        self.app = QApplication(sys.argv)

    def connectDb(self,dbname,confmanager):
        oracledb.init_oracle_client(config_dir= rf"{confmanager.getPath()}")
        cs = confmanager.getDbCs(dbname)
        print(f"pass {confmanager.getDbPassword(dbname)}")
        self.connection = oracledb.connect(
                    user=confmanager.getUser(dbname),
                    password=confmanager.getDbPassword(dbname),
                    dsn=cs)
        self.cursor = self.connection.cursor()
    
    def SelectProjectsFromId(self,id,cmd):
        self.cmd = cmd
        self.cursor.execute(f"SELECT DISTINCT(PROJECTNAME) FROM SYSADM.PSPROJECTITEM WHERE PROJECTNAME LIKE '%{id}%'")
        rows = [item for sublist in self.cursor.fetchall() for item in sublist]
        print(f"Merci de choisir un projet parmis les suivants: {rows}")
        proj = ""
        while proj not in rows:
            proj = input()
            if proj not in rows:
                print("Merci de choisir un projet valable.")        
        self.projectId = proj
        self.__CheckOrCreateFilesForProject()
                
    def __CreateWindowCompare(self,controller):
        app = QApplication(sys.argv)
        self.compareWindow = MainWindow(controller)
        self.compareWindow.setWindowTitle(f"Project {self.projectId} compare")
        self.compareWindow.resize(800, 600)
        self.compareWindow.setProjectId(self.projectId)
        self.compareWindow.setComparator(self.comparator)
        self.compareWindow.setProjectPath(self.path)
        self.compareWindow.show()
        sys.exit(app.exec_())
        
    def __pullRequestForCompare(self):
        path = self.path +self.projectId + "/tempdir/"
        try:    
            os.mkdir(path)      
            Objects = self.__SelectPeoplecodeObjsFromProj()
            for obj in Objects:
                print(f"pull pour compare : {obj}")                
                with open(os.path.join(path,obj+'.pplc'),"a") as file:                
                    for eventStr in self.__GetObjectEventsString(obj) :
                        try:                          
                            file.write(f"[*{eventStr}*]\n")
                            pplc, = self.__SelectPeoplecodeTxtFomObject(eventStr)                                          
                            offset = 1
                            while True:
                                data = pplc.read(offset, self.chunkSize)
                                if data:
                                    data = data.replace("<![CDATA[","")
                                    data = data.replace("]]>","")
                                    file.write(data)
                                if len(data) < self.chunkSize:
                                    break
                                offset += len(data)                              
                        except:
                           print("Erreur lors de l'ecriture pplc.")
        except:
            print("Pull en erreur depuis la base.")
        
    
    def __CheckOrCreateFilesForProject(self):
        path = self.path +self.projectId
        try:      
            preDict = list(tuple())      
            os.mkdir(path)
            Objects = self.__SelectPeoplecodeObjsFromProj()
            for obj in Objects:
                print(f"importation de l'objet : {obj}")                
                with open(os.path.join(path,obj+'.pplc'),"a") as file:                
                    for eventStr in self.__GetObjectEventsString(obj) :
                        try:       
                            preDict.append((obj,eventStr))                    
                            file.write(f"[*{eventStr}*]\n")
                            pplc, = self.__SelectPeoplecodeTxtFomObject(eventStr)                                          
                            offset = 1
                            while True:
                                data = pplc.read(offset, self.chunkSize)
                                if data:
                                    data = data.replace("<![CDATA[","")
                                    data = data.replace("]]>","")
                                    file.write(data)
                                if len(data) < self.chunkSize:
                                    break
                                offset += len(data)                              
                        except:
                           print("Erreur lors de l'ecriture pplc.")
                    self.ObjectsEvents = self.__TransformArrayToDict(preDict)
            self.__createSummaryFile()
        except FileExistsError:
            if self.cmd == "pull":
                shutil.rmtree(path, ignore_errors=False, onerror=handleRemoveReadonly)
                self.__CheckOrCreateFilesForProject()
            else:
                self.__summerize()
                self.controller = WindowController()
                self.comWinThread = threading.Thread(target=self.__CreateWindowCompare,args=(self.controller,))
                self.comWinThread.start()
                while not self.compareWindow:
                    if self.compareWindow :
                        self.__getTextFromPpcFiles()
                        break
                
            
    def __GetObjectEventsString(self,object):
        self.cursor.execute(f"SELECT NVL(OBJECTVALUE1, '') || '.' || NVL(OBJECTVALUE2, '') || '.' || NVL(OBJECTVALUE3, '') || '.' || NVL(OBJECTVALUE4, '') AS CONCATENATED_COLUMN FROM SYSADM.PSPROJECTITEM WHERE PROJECTNAME = '{self.projectId}' AND OBJECTTYPE IN (8,9,39,40,42,43,44,45,46,47,48,58,66) AND OBJECTVALUE1 = '{object}' order by OBJECTVALUE1,OBJECTVALUE2,OBJECTVALUE3,OBJECTVALUE4 asc")
        rows = [item for sublist in self.cursor.fetchall() for item in sublist]
        return rows
    
    def __SelectPeoplecodeObjsFromProj(self):
        self.cursor.execute(f"SELECT DISTINCT(OBJECTVALUE1) FROM SYSADM.PSPROJECTITEM WHERE PROJECTNAME = '{self.projectId}' AND OBJECTTYPE IN (8,9,39,40,42,43,44,45,46,47,48,58,66)")
        rows = [item for sublist in self.cursor.fetchall() for item in sublist]
        return rows
        
    def __SelectPeoplecodeTxtFomObject(self,Object):
        ObjectLevels = Object.split(".")
        ObjectLevel1 = ObjectLevels[0].strip()
        ObjectLevel2 = ObjectLevels[1].strip()
        ObjectLevel3 = ObjectLevels[2].strip()
        ObjectLevel4 = ObjectLevels[3].strip()
        
        
        if 'OnExecute' in Object:   
            """ AE case """   
            ObjectLevel2 = ObjectLevel2.split('GBLdefault')[0].strip()
            ObjectLevel6 = ObjectLevel3
            ObjectLevel7 = ObjectLevel4
            ObjectLevel5 = '1900-01-01'
            ObjectLevel4 = 'default'
            ObjectLevel3 = 'GBL'  
            #print(f"SELECT TO_CLOB (XMLAGG (XMLELEMENT (E, XMLCDATA(PCTEXT)) ORDER BY PROGSEQ).EXTRACT ('//text()').getclobval ())    AS CONCAT_HUGECLOB FROM SYSADM.PSPCMTXT WHERE OBJECTVALUE1 = '{ObjectLevel1}' AND OBJECTVALUE2 = '{ObjectLevel2}'  AND OBJECTVALUE3 = '{ObjectLevel3}' AND OBJECTVALUE4 = '{ObjectLevel4}' AND OBJECTVALUE5 = '{ObjectLevel5}' AND OBJECTVALUE6 = '{ObjectLevel6}' AND OBJECTVALUE7 = '{ObjectLevel7}' ORDER BY PROGSEQ") 
            self.cursor.execute(f"SELECT TO_CLOB (XMLAGG (XMLELEMENT (E, XMLCDATA(PCTEXT)) ORDER BY PROGSEQ).EXTRACT ('//text()').getclobval ())    AS CONCAT_HUGECLOB FROM SYSADM.PSPCMTXT WHERE OBJECTVALUE1 = '{ObjectLevel1}' AND OBJECTVALUE2 = '{ObjectLevel2}'  AND OBJECTVALUE3 = '{ObjectLevel3}' AND OBJECTVALUE4 = '{ObjectLevel4}' AND OBJECTVALUE5 = '{ObjectLevel5}' AND OBJECTVALUE6 = '{ObjectLevel6}' AND OBJECTVALUE7 = '{ObjectLevel7}' ORDER BY PROGSEQ")            
            return self.cursor.fetchone()        
        elif ObjectLevel1 and ObjectLevel2 and ObjectLevel3 and ObjectLevel4:
            self.cursor.execute(f"SELECT TO_CLOB (XMLAGG (XMLELEMENT (E, XMLCDATA(PCTEXT)) ORDER BY PROGSEQ).EXTRACT ('//text()').getclobval ())    AS CONCAT_HUGECLOB FROM SYSADM.PSPCMTXT WHERE OBJECTVALUE1 = '{ObjectLevel1}' AND OBJECTVALUE2 = '{ObjectLevel2}'  AND OBJECTVALUE3 = '{ObjectLevel3}' AND OBJECTVALUE4 = '{ObjectLevel4}' ORDER BY PROGSEQ")            
            return self.cursor.fetchone()
        elif ObjectLevel1 and ObjectLevel2 and ObjectLevel3:
            #print(f"SELECT TO_CLOB (XMLAGG (XMLELEMENT (E, XMLCDATA(PCTEXT)) ORDER BY PROGSEQ).EXTRACT ('//text()').getclobval ())    AS CONCAT_HUGECLOB FROM SYSADM.PSPCMTXT WHERE OBJECTVALUE1 = '{ObjectLevel1}' AND OBJECTVALUE2 = '{ObjectLevel2}'  AND OBJECTVALUE3 = '{ObjectLevel3}' ORDER BY PROGSEQ")
            self.cursor.execute(f"SELECT TO_CLOB (XMLAGG (XMLELEMENT (E, XMLCDATA(PCTEXT)) ORDER BY PROGSEQ).EXTRACT ('//text()').getclobval ())    AS CONCAT_HUGECLOB FROM SYSADM.PSPCMTXT WHERE OBJECTVALUE1 = '{ObjectLevel1}' AND OBJECTVALUE2 = '{ObjectLevel2}'  AND OBJECTVALUE3 = '{ObjectLevel3}' ORDER BY PROGSEQ")            
            return self.cursor.fetchone()
        elif ObjectLevel1 and ObjectLevel2:
            self.cursor.execute(f"SELECT TO_CLOB (XMLAGG (XMLELEMENT (E, XMLCDATA(PCTEXT)) ORDER BY PROGSEQ).EXTRACT ('//text()').getclobval ())    AS CONCAT_HUGECLOB FROM SYSADM.PSPCMTXT WHERE OBJECTVALUE1 = '{ObjectLevel1}' AND OBJECTVALUE2 = '{ObjectLevel2}' ORDER BY PROGSEQ")            
            return self.cursor.fetchone()
        elif ObjectLevel1 :
            self.cursor.execute(f"SELECT TO_CLOB (XMLAGG (XMLELEMENT (E, XMLCDATA(PCTEXT)) ORDER BY PROGSEQ).EXTRACT ('//text()').getclobval ())    AS CONCAT_HUGECLOB FROM SYSADM.PSPCMTXT WHERE OBJECTVALUE1 = '{ObjectLevel1}' ORDER BY PROGSEQ")            
            return self.cursor.fetchone()
        else:
            print("Erreur l'objet de niveau 1 n'est pas disponible")
            return ()
        
    def __createSummaryFile(self):
        path = self.path+self.projectId
        with open(os.path.join(path,'summary.fs'),"a") as file:
            file.write(json.dumps(self.ObjectsEvents))
    
    def __TransformArrayToDict(self,array):
        output_dict = {}
        for key, value in array:
            if key in output_dict:
                output_dict[key].append(value)
            else:
                output_dict[key] = [value]
        return output_dict
    
    def __getEventsInsideFile(self, filename):
        path = self.path+self.projectId
        eventsInFile = list()
        try:
            with open(os.path.join(path,filename),"r") as f:
                pplc = f.read()
                if len(pplc)> 0:
                    eventsInFile = [line.lstrip('[*').rstrip('*]') for line in pplc.splitlines() if re.search(r'\[\*.*?\*\]', line)]
        except:
            print("Erreur lors de processing du fichier peoplecode.")
            
        return eventsInFile
    
    def __getTextFromPpcFiles(self) :
        #get files from dir
        path = self.path+self.projectId
        temppath = self.path +self.projectId + "/tempdir/"
        filesInDir = [f for f in os.listdir(path) if f.endswith('.pplc')]
        localfiles = list()
        tempfiles = list()
        rightFilesDict = dict()
        for file in filesInDir:            
            with open(os.path.join(path,file),"r") as f:
                rightText = f.read()
                localfiles.append(file)
                #self.controller.addNewTab.emit(file,"textleft",rightText)
                rightFilesDict[file] = rightText
                
        self.__pullRequestForCompare()
          
        filesInTempDir = [f for f in os.listdir(temppath) if f.endswith('.pplc')] 
        for file in filesInTempDir:
            with open(os.path.join(temppath,file),"r") as f:
                leftText = f.read()
                tempfiles.append(file)
                #get right part if exists 
                rightText = ""
                if file in rightFilesDict.keys():
                    rightText = rightFilesDict[file]
                else:
                    rightText = ""
                    
                if file in localfiles:
                    #self.controller.setTextLeft.emit(file,leftText)                    
                    self.comparator.compareTexts(leftText,rightText,file,self.controller)
                else:
                    #self.controller.addNewTab.emit(file,leftText,"")
                    self.comparator.compareTexts(leftText,rightText,file,self.controller)
                    
        #delete temp path                    
        shutil.rmtree(temppath, ignore_errors=False, onerror=handleRemoveReadonly)
                
    def __summerize(self):
        #check for new files and add them to summary
        path = self.path+self.projectId        

        filesInDir = [f for f in os.listdir(path) if f.endswith('.pplc')]
        
        #check every file for events
        dictSum = {}
        for file in filesInDir:
              obj = file.rstrip(".pplc")
              eventsArray =self.__getEventsInsideFile(file)
              if obj in dictSum:
                dictSum[obj].append(eventsArray)
              else:
                dictSum[obj] = eventsArray
                
        with open(os.path.join(path,'summary.fs'),"w") as file:
            file.write(json.dumps(dictSum))
            