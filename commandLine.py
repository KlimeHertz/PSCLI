import typer
from configManager import *
from getpass import getpass

class commandManager:
    
    def __init__(self):
        self.app = typer.Typer()
        
        #pull a project from database to local
        @self.app.command()
        def pullproject(id,dbname):
            from reqManager import Manager           
            cfg = configManager()
            
            if not cfg.checkDbParams(dbname):
                typer.echo("configiration de la base de données manquante.")
                return
        
            userpass=getpass()
            if userpass == "":
                typer.echo("mot de passe vide!")
                return
            
            if cfg.CheckUserPassword(userpass):                    
                manager = Manager(cfg)
                manager.connectDb(dbname,cfg)
                manager.SelectProjectsFromId(id,"pull")
            else:
                typer.echo("le mot de passe n'est pas enregistré. Merci de passer par la commande 'register'.")
        
        #compare two databases
        @self.app.command()
        def comparedatabase(id,dbname1,dbname2):
            from multmanager import MultManager
            
            cfg = configManager()
            projlist = list()
            
            if not cfg.checkDbParams(dbname1):
                typer.echo(f"configuration {dbname1} de la base de données manquante.")
                return
            
            if not cfg.checkDbParams(dbname2):
                typer.echo(f"configuration {dbname2} de la base de données manquante.")
                return
            
            if id.strip()=="" or dbname1.strip()=="" or dbname2.strip()=="":
                typer.echo("paramértre vide.")
                return
            
            if ',' in id:
                projlist = [prj for prj in id.split(",")]
            else:
                projlist.append(id)
                
            userpass=getpass()
            if userpass == "":
                typer.echo("mot de passe vide!")
                return
            
            if cfg.CheckUserPassword(userpass):                    
                manager = MultManager(cfg)
                for prj in projlist:
                    manager.compareDatabase(prj,cfg,dbname1,dbname2)
                    
                manager.runApp()
            else:
                typer.echo("le mot de passe n'est pas enregistré. Merci de passer par la commande 'register'.")
            
        #compare local code to database code
        @self.app.command()   
        def comparetolocal(id:str,dbname:str,user:str="",dbpassword:str=""):
            """ded"""
            from reqManager import Manager    
            cfg = configManager()
            #check db and params
            if not cfg.checkDbParams(dbname):
                typer.echo("paramétrage de la base de donnée manquant! Merci de passer par 'loadora' ou 'registerdb'.")
                return
            
            userpass=getpass()
            if userpass == "":
                typer.echo("mot de passe vide!")
                return
            
            if cfg.CheckUserPassword(userpass):                    
                manager = Manager(cfg,dbname)
                manager.connectDb(dbname,cfg)
                manager.SelectProjectsFromId(id,'')
            else:
                typer.echo("le mot de passe n'est pas enregistré. Merci de passer par la commande 'register'.")
        
        #register user
        @self.app.command()
        def register():
            """permet de crée un mot de passe user CLI. (si le mot de passe change les mot de passe des bases de données sont effacés)"""
            cfg = configManager()
            typer.echo("Merci de saisir votre mot de passe utilisateur CLI.")
            userpass=getpass()
            if userpass == "":
                typer.echo("mot de passe vide!")
                return
            cfg.setUserPassword(userpass)
        
        #load ora file into config
        @self.app.command()
        def loadora():
            """Permet de charger un fichier .ora pour la configuration des bases de données en masse."""
            cfg = configManager()
            if cfg.loadConfigurationFromOraFile() :
                typer.echo("Chargement effectué.")
            else:
                typer.echo("le chemin 'oradir' est vide ou incorrecte!")   
        
        #configurate db 
        @self.app.command()
        def configuredb(config):
            """mot de passe : mot de passe CLI (si aucun mot de passe n'est configuré passez par la commande 'register')
               \n config : paramétre d'entrée de la forme  dbname1/cs1/user1/password1,dbname2/cs2/user2/password2
               \n cs de la forme (DESCRIPTION =(ADDRESS_LIST =(ADDRESS = (PROTOCOL = TCP)(HOST = 0.0.0.0)(PORT = 1000)))(CONNECT_DATA =(SERVER = DEDICATED)(SERVICE_NAME = DBNAME))) """
            
            clipassword = getpass()
            cfgManager = configManager()
            if not cfgManager.CheckUserPassword(clipassword):
                typer.echo("Mot de passe invalide.")
                return
                
            configs = config.split(",")
            for cfg in configs:
                if cfg.strip() != "":
                    if len(cfg.split("/")) % 4 != 0:
                       typer.echo("Paramétres manquants sur la configuration assurez-vous de cette forme : dbname1/cs1/user1/password1,dbname2/cs2/user2/password2")
                       return
                   
                    dbname,cs,user,password = cfg.split("/")                    
                    if dbname.strip() == "" or user.strip() =="" or password.strip() =="" or cs.strip() =="":
                        typer.echo("Paramétres vide sur la configuration.")
                        return
                    
                    if cfgManager.setEnvPasswordAndUserName(dbname,cs,password,user,clipassword) == 0:
                        typer.echo("Erreur lors du traitement.")
                        return
                else:
                    typer.echo("Configuration vide saisie!")
                    return
                
            cfgManager.saveConfigFile()
            return

    #run CLI
    def run(self):
        self.app()