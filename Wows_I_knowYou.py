#title          :WowsReplayTool.py
#description    :This script access world of warship replay data and uses it to generate stats
#author         :Yoshi_E
#date           :20171129
#version        :1.0   
#usage          :
#notes          :Modules needed via pip install
#python-version :3.6.4
#Build command: "C:\Program Files (x86)\Python36-32\Scripts\pyinstaller" "D:\Dokumente\_Git\Wows\Wows_I_knowYou.py" --onefile --icon=wows.ico

import random
import os
import io
import string
import json
import requests
import csv
import sys
import argparse
import pickle
from collections import OrderedDict
import time
import math
import configparser
from os import listdir
from os.path import isfile, join
from datetime import datetime
line = "------------------------------------------------------------------------"

print(line)
print ("World of Warships replay metadata reader - Yoshi_E 2017")
print(line)

config = configparser.ConfigParser()

base_path = os.path.dirname(sys.executable)+"/" #os.getcwd() or this?
#If In script:
if("Python" in base_path):
    base_path = os.path.dirname(os.path.realpath(__file__))+"/"
    
base_path = base_path.replace("//", "/")

if(os.path.isfile(base_path+"config.ini")==False):
    path = input("Enter path to replays: ")+"/".replace("//", "/")

    config['DEFAULT'] = {       'path': path,
                                'refreshRate': '10',
                                'application_id': "23c72eadf6267847fc48a35d03bdb2ef"}

                            
    with open(base_path+'config.ini', 'w') as configfile:
        config.write(configfile)
                            
else: 
    config.read(base_path+'config.ini')


default_path = config['DEFAULT']['path']
refreshRate = int(config['DEFAULT']['refreshRate'])
application_id = config['DEFAULT']['application_id']          
            
if(os.path.exists(default_path)==False or os.path.isdir(default_path) == False):
    print("Failed to find path: "+default_path)
    sys.exit()





print("[path]: "+default_path)
print("[database]: "+base_path)

if(os.path.isdir(default_path)==False):
    print("Error no folder found in: "+default_path)
    sys.exit()
    
    
#Gets all files in replay folder
def getFiles(path):
    return [f for f in listdir(path) if (isfile(join(path, f)) and os.path.splitext(join(path, f))[1]==".wowsreplay")]

#Returns File exention of path
def getFileExtension(path):
    filename, file_extension = os.path.splitext(path)
    return file_extension

#Loads a replay file from given path and retuns its Json meta data
#Returns false if loading failed
def loadReplay(path):
    #Reads file and outputs the first line with readable chars, containing the metadata of the replay
    raw_metadata = ""
    safty=0
    with io.open(path,'r',encoding='ascii',errors='ignore') as infile:
        while (safty<10 and "clientVersionFromXml" not in raw_metadata):
            raw_metadata = infile.readline()
            safty += 1
    if(safty>=10):
        #print("ERROR failed to load replay: "+path)
        return False;
    printable = set(string.printable)
    raw_metadata = ''.join(filter(lambda x: x in printable, raw_metadata))  #Filters non Ascii chars and Binary Data from string
    #Cuts faulty data from the json
    raw_metadata = '{"'+raw_metadata.split('{"', 1)[1] 
    raw_metadata = raw_metadata[:raw_metadata.index('"}', raw_metadata.index("playerVehicle"))]+'"}'
    #Prints full json data
    #print(raw_metadata)
    return json.loads(raw_metadata)

#Uses Application_id to fetch data about ships from the WG API and stores it on you disk
def generateShipData(application_id):
    url = "https://api.worldofwarships.eu/wows/encyclopedia/ships/?application_id="+application_id+"&page_no="
    out= base_path + "/shipDatabase.json"
    data = json.loads(requests.get(url+"1").text)
    for i in range(data["meta"]["page_total"]):
        data = requests.get(url+str(i+1)).text  #GET request to WG API Server
        data = json.loads(data)["data"]
        data = json.dumps(data)
        data = data[1:][:-1]
        #Merges Json pages to one large page
        if(i+1 > 1):
            jsonPages = jsonPages+","+data
        else:
            jsonPages = "{"+data            #Opening and closing bracket for the large page
    jsonPages = json.loads(jsonPages+"}")   #Converts into Json Object
    with open(base_path + "\shipDatabase.json", "w") as outfile:
        json.dump(jsonPages, outfile)       #Writes Json Object to disk

#Asks to user to generate Database
def askForDatabase():
    global application_id
    if(os.path.isfile(base_path+"/shipDatabase.json")==False):
        print("Error Ship Database not found!")
        if(application_id == ""):
            print("To download the ship database you need a Wargaming Application ID!")
            print("https://developers.wargaming.net/")
            application_id = input("Please enter the Application ID here: ")
            generateShipData(application_id)
            print("Completed!")
        else: 
            generateShipData(application_id)
            print("Ship Database Generated!")

#Loads Ship database from disk
def loadShipDatbase():
    return json.load(io.open(base_path+"/shipDatabase.json","r", encoding="utf8",errors='ignore'))
    
    
def addToDatabase(data, newdata, ship_data):
    username = ship_data["name"]
    if(newdata["playerName"] != ship_data["name"]):
        timestamp = newdata["dateTime"]
        if(username not in data):
            data[username] = {}
        if(timestamp not in data[username]):
            data[username][timestamp] = {}
        
        data[username][timestamp]["mapName"]    = newdata["mapName"]
        data[username][timestamp]["logic"]      = newdata["logic"]
        data[username][timestamp]["shipId"]     = ship_data["shipId"]
        data[username][timestamp]["userId"]     = ship_data["id"]
        data[username][timestamp]["relation"]   = ship_data["relation"]
        data[username][timestamp]["id"]         = ship_data["id"]
    return data
    
    
def generateUserDBJson():
    if(os.path.isfile(base_path+"/userDatabase.json")==False):
        data = {}
    else:
        data = json.load(io.open(base_path+"/userDatabase.json","r", encoding="utf8",errors='ignore'))
    if(os.path.isfile(base_path+"/replayDatabase.json")==False):
        replayData = {}
    else:
        replayData = json.load(io.open(base_path+"/replayDatabase.json","r", encoding="utf8",errors='ignore'))
    replayFiles = getFiles(default_path)
    for file in replayFiles:
            jsonData = loadReplay(default_path+file)
            if(jsonData != False): #Skips faulty replays
                replayData[jsonData["dateTime"]] = {}
                replayData[jsonData["dateTime"]] = jsonData
                
                for ship_data in jsonData["vehicles"]: #For all players (vehicles) in game do:
                    data = addToDatabase(data, jsonData, ship_data)

    with open(base_path + "/userDatabase.json", "w") as outfile:
        json.dump(data, outfile)       #Writes Json Object to disk
    with open(base_path + "/replayDatabase.json", "w") as outfile:
        json.dump(replayData, outfile)       #Writes Json Object to disk
    return data
    
def cmp_to_key(mycmp):
    'Convert a cmp= function into a key= function'
    class K(object):
        def __init__(self, obj, *args):
            self.obj = obj
        def __lt__(self, other):
            return mycmp(self.obj, other.obj) < 0
        def __gt__(self, other):
            return mycmp(self.obj, other.obj) > 0
        def __eq__(self, other):
            return mycmp(self.obj, other.obj) == 0
        def __le__(self, other):
            return mycmp(self.obj, other.obj) <= 0  
        def __ge__(self, other):
            return mycmp(self.obj, other.obj) >= 0
        def __ne__(self, other):
            return mycmp(self.obj, other.obj) != 0
    return K
    
    
def dataCompare(item1, item2):
    date_format = "%d.%m.%Y %H:%M:%S"
    a = datetime.strptime(item1, date_format)
    b = datetime.strptime(item2, date_format)
    
    if a < b:
        return -1
    elif a > b:
        return 1
    else:
        return 0
        
def detectCurrentGame():
    global default_path, userData
    
    shipDB = loadShipDatbase()
    lastgame = ""
    newgame = ""
    while True:
        if(os.path.isfile(default_path+"tempArenaInfo.json")==True):
            jsonData = json.load(io.open(default_path+"tempArenaInfo.json","r", encoding="utf8",errors='ignore'))
            newgame = jsonData["dateTime"]
            
        if(lastgame < newgame):
            lastgame    = newgame
            timestamp   = jsonData["dateTime"]
            mapName     = jsonData["mapName"]
            logic       = jsonData["logic"]
            print(timestamp+" "+mapName.replace("spaces/","")+":")
            
            for ship_data in jsonData["vehicles"]:
                shipId =    str(ship_data["shipId"])
                username =  str(ship_data["name"])
                
                if(username in userData):
                    met_num = len(userData[username])
                    sort =  OrderedDict(userData[username])
                    last_met_time = list(sort.keys()) #[-1]
                    print(last_met_time)
                    last_met_time = sorted(last_met_time, key=cmp_to_key(dataCompare))[-1]
                    date_format = "%d.%m.%Y %H:%M:%S"
                    
                    a = datetime.strptime(last_met_time, date_format)
                    
                    b = datetime.today()
                    b = datetime.strptime(str(b.strftime("%d.%m.%Y %H:%M:%S")), date_format)
                    delta = b - a
                    days = str(delta.days)
                    
                    days = days + " " * (3-len(days))
                    last_met_data = userData[username][last_met_time]
                    last_met_shipid = str(userData[username][last_met_time]["shipId"])
                    
                    username_t  = username + " " * (24-len(username))
                    map_name    = (last_met_data["mapName"] + " " * (30-len(last_met_data["mapName"]))).replace("spaces/","")
                    met_num_t   = str(met_num) + " " * (4-len(str(met_num)))
                    #print(shipDB["4293834736"])
                    if(last_met_shipid in shipDB):
                        print(username_t+" Played "+met_num_t+" Days: "+days+" at "+map_name+"Last Ship: "+shipDB[last_met_shipid]["name"])
                    else:
                        print(username_t+" Played "+met_num_t+" day since last battle: "+days+ " at "+map_name)
                else:
                    userData = addToDatabase(userData, jsonData, ship_data)
            
            #Save UserData  to Disk       
            with open(base_path + "/userDatabase.json", "w") as outfile:
                json.dump(userData, outfile)       
                        
           # userData = generateUserDBJson() # This is very ineffective, as it checks all replays all over again
            print(line)
        time.sleep(refreshRate)


print(line)

askForDatabase()  #ensures a Database is present 
userData = generateUserDBJson()
print("Found "+str(len(getFiles(default_path)))+" replays")
print("User List Updated")
print("Attempting to detect current game...")
print(line)
detectCurrentGame()


input("Error! Press Enter to continue...")
