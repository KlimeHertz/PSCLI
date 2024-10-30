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

class MultManager(QObject):
    def __init__(self,confmanager):
        super().__init__()
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
        self.compareResults = list(tuple())
        
    def runApp(self):
        for id,win in self.windowsList:
            win.show()  
        self.__FillWindowsWithComapreRes()
        sys.exit(self.app.exec_())
            
        
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
    
    def __MultEnvWindowCompare(self,controller,projectid):
        compareWindow = MainWindow(controller)
        compareWindow.setWindowTitle(f"Project {projectid} compare")
        compareWindow.resize(800, 600)
        compareWindow.setProjectId(projectid)
        compareWindow.setComparator(self.comparator)
        compareWindow.setProjectPath(self.path)
        self.windowsList.append((projectid,compareWindow))
        
    def compareDatabase(self,id,cfgmanager,dbname1,dbname2):
        cs1 = cfgmanager.getDbCs(dbname1)
        cs2 = cfgmanager.getDbCs(dbname2)
        
        if cs1.strip() !="" or cs2.strip() != "":            
            self.connection1 = oracledb.connect(
                        user=cfgmanager.getUser(dbname1),
                        password=cfgmanager.getDbPassword(dbname1),
                        dsn=cs1)
            
            self.connection2 = oracledb.connect(
                        user=cfgmanager.getUser(dbname2),
                        password=cfgmanager.getDbPassword(dbname2),
                        dsn=cs2)
            
            self.projectId = id
            
            self.connection = self.connection1
            self.cursor = self.connection.cursor()           
            objectsDb1 = self.__SelectPeoplecodeObjsFromProj()
            self.connection = self.connection2
            self.cursor = self.connection.cursor()
            objectsDb2 = self.__SelectPeoplecodeObjsFromProj()
            
            codePerTab1 = list()
            
            for obj in objectsDb1:
                ObjectDb1Lines = list()
                self.connection = self.connection1
                self.cursor = self.connection.cursor()
                for eventStr in self.__GetObjectEventsString(obj) :
                    try: 
                        ObjectDb1Lines.append(f"[*{eventStr}*]\n")
                        pplc, = self.__SelectPeoplecodeTxtFomObject(eventStr)                                          
                        offset = 1
                        while True:
                            data = pplc.read(offset, self.chunkSize)
                            if data:
                                data = data.replace("<![CDATA[","")
                                data = data.replace("]]>","")
                                ObjectDb1Lines.append(data)
                            if len(data) < self.chunkSize:
                                break
                            offset += len(data)   
                    except:
                        print("pplc Extarction error.")
                        return 0
                    
                codePerTab1.append((obj,''.join(ObjectDb1Lines)))
                    
            codePerTab2 = list()
                    
            offset = 1
            
            for obj in objectsDb2:
                ObjectDb2Lines = list()
                self.connection = self.connection2
                self.cursor = self.connection.cursor()
                for eventStr in self.__GetObjectEventsString(obj) :
                    try: 
                        ObjectDb2Lines.append(f"[*{eventStr}*]\n")
                        pplc, = self.__SelectPeoplecodeTxtFomObject(eventStr)                                          
                        offset = 1
                        while True:
                            data = pplc.read(offset, self.chunkSize)
                            if data:
                                data = data.replace("<![CDATA[","")
                                data = data.replace("]]>","")
                                ObjectDb2Lines.append(data)
                            if len(data) < self.chunkSize:
                                break
                            offset += len(data)   
                    except:
                        print("pplc Extarction error.")
                        return 0
                    
                codePerTab2.append((obj,''.join(ObjectDb2Lines)))

            controller = WindowController()
            self.__MultEnvWindowCompare(controller,id)
            print(f"comparing project : {id}")
            count = 0
            self.compareResults.append((id,codePerTab1,codePerTab2,controller))
                            
        else:
            return 0
        
    def __FillWindowsWithComapreRes(self):
        for id,codePerTab1,codePerTab2,controller in self.compareResults:
            count = 0      
            if len(codePerTab1) > len(codePerTab2):
                for tabname,code in codePerTab1:
                    if count >= len(codePerTab2):
                        self.comparator.compareTexts(code," ",tabname,controller)
                    else:
                        self.comparator.compareTexts(code,codePerTab2[count][1],tabname,controller)
                    count+=1
                    
            elif len(codePerTab2) > len(codePerTab1):
                for tabname,code in codePerTab2:
                    if count >= len(codePerTab1):
                        self.comparator.compareTexts(" ",code,tabname,controller)
                    else:
                        self.comparator.compareTexts(codePerTab1[count][1],code,tabname,controller)
                    count+=1
            else:
                for tabname,code in codePerTab2:
                    self.comparator.compareTexts(codePerTab1[count][1],code,tabname,controller)
                    count+=1