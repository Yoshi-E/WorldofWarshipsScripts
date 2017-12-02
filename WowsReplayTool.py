#title          :WowsReplayTool.py
#description    :This script access world of warship replay data and uses it to generate stats
#author		    :Yoshi_E
#date           :20171129
#version        :1.0   
#usage		    :
#notes          :Modules needed via pip install
#python-version :3.6.4
#Build command: "C:\Program Files (x86)\Python36-32\Scripts\pyinstaller" "D:\Dokumente\World of Warships\Replay meta reader\WowsReplayTool.py" --onefile

import random
import os
import io
import string
import json
import requests
import csv
import sys
import argparse
from os import listdir
from os.path import isfile, join

print ("World of Warships replay metadata reader - Yoshi_E 2017")


parser = argparse.ArgumentParser(
        description='Reads All replays in current folder an generates stats for them',
        epilog="")
        
parser.add_argument('-path', nargs=1, help='Path to replay Folder, default = current_path', default=os.path.dirname(os.path.realpath(__file__))+"/")
parser.add_argument('--wait',  help='Waits before closing window, defaut = False', action='store_const', const=True, default=False)
parser.add_argument('-app_id', nargs=1, help='Wargaming API ID (developers.wargaming.net), default is given', default="23c72eadf6267847fc48a35d03bdb2ef")
parser.add_argument('-output', nargs=1, help='Path to cvs files, default = binary_path', default=os.path.dirname(os.path.realpath(__file__))+"/")
parser.add_argument('-prefix', nargs=1, help='Prefix for cvs files, default = None', default="")
parser.add_argument('--Random', help='Tracks Random Games, defaut = False', action='store_const', const=True, default=False)
parser.add_argument('--Coop',   help='Tracks Coop Games, defaut = False',   action='store_const', const=True, default=False)
parser.add_argument('--Ranked', help='Tracks Ranked Games, defaut = False', action='store_const', const=True, default=False)
parser.add_argument('--CvC',    help='Tracks Clan Games, defaut = False',   action='store_const', const=True, default=False)
parser.add_argument('--Other',  help='Tracks Event and other Games, defaut = False', action='store_const', const=True, default=False)

args = vars(parser.parse_args())
tracked_gametypes = []
if(args['Random'] == True):
    tracked_gametypes.append('Random')
if(args['Coop'] == True):
    tracked_gametypes.append('Coop')
if(args['Ranked'] == True):
    tracked_gametypes.append('Ranked')
if(args['CvC'] == True):
    tracked_gametypes.append('CvC')
if(args['Other'] == True):
    tracked_gametypes.append('Other')

application_id = ''.join(args['app_id'])
if(args['path'][:-1] == "/" or args['path'][:-1] == "\\"):
    default_path = ''.join(args['path'])
else: 
    default_path = ''.join(args['path'])+"/"
    
cvs_output = ''.join(args['output'])+"/"
if(args['prefix'] == ""):
    cvs_prefix = ""
else:
    cvs_prefix = ''.join(args['prefix']).replace("/","").replace("\\","")
wait_before_closing = args['wait']
shipDB_path = os.path.dirname(sys.executable)
#If In script:
if("Python" in shipDB_path):
    shipDB_path = os.path.dirname(os.path.realpath(__file__))+"/"

print("Replay path: "+default_path)
print("CVS path:    "+cvs_output)
print("ShipDB path: "+shipDB_path)
if(tracked_gametypes == []):
    print("Notice: No Gamemodes selected! Use -h to see what modes you can track!")
#dont use '\' here
#default_path = "C:/Program Files/WOWS/replays/"
#application_id = ""     #Application_id from https://developers.wargaming.net/ is needed here
#List for what gamemode belongs to wich gametype
gamemode_domination = ['Skirmish_Domination_rhombus','Skirmish_Domination','Domination','Domination_rhombus','Ranked_Domination', 'CvC_Domination', 'CvC_Domination_observ0']
gamemode_standard = ['Skirmish_Domination_2_BASES','Domination_2_BASES']
gamemode_epicenter = ['Skirmish_Epicenter','Epicenter','Ranked_Epicenter']
random_gamemodes = ['Domination_2_BASES', 'MegaBase', 'Domination', 'Domination_rhombus', 'Epicenter']
#tracked_gametypes = ['Random'] #Allowed are 'Random','Coop','Ranked','CvC'
#track_trainingroom_battles = True #Does nothing atm


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
def loadReplay(path):
    #Reads file and outputs the first line with readable chars, containing the metadata of the replay
    raw_metadata = ""
    with io.open(path,'r',encoding='ascii',errors='ignore') as infile:
        while ("clientVersionFromXml" not in raw_metadata):
            raw_metadata = infile.readline()
    
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
    out= shipDB_path + "/shipDatabase.json"
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
    with open(shipDB_path + "\shipDatabase.json", "w") as outfile:
        json.dump(jsonPages, outfile)       #Writes Json Object to disk

#Asks to user to generate Database
def askForDatabase():
    global application_id
    if(os.path.isfile(shipDB_path+"/shipDatabase.json")==False):
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
    return json.load(io.open(shipDB_path+"/shipDatabase.json","r", encoding="utf8",errors='ignore'))
    
#Tests if the current replay should be tracked in the stats
def testTracking(gamemode):
    global tracked_gametypes
    return  (('Coop' in tracked_gametypes and 'Skirmish' in gamemode) or
            ('Ranked' in tracked_gametypes and 'Ranked' in gamemode) or
            ('CvC' in tracked_gametypes and 'CvC' in gamemode) or
            ('Random' in tracked_gametypes and gamemode in random_gamemodes))
 
def calcAvrg(A,B):
    if(A > 0 and B>0):
        return (("%.2f" % (float(A) / B)).replace(".",","))
    else:
        return 0
#Program stats here :) 

askForDatabase()                        #Ensures you have the information about the ships         
replayFiles = getFiles(default_path)    #Gets a List with all replay file paths
shipDatabase = loadShipDatbase()        #Loads Database from file
currentpath = cvs_output

#Init Vars
counter = {}
counter['battles_total'] = 0
counter['player_sum'] = 0
counter['gamemode'] = {}
counter['ByOwnTier'] = {}
counter['avrg_tier_sum'] = 0
counter['avrg_top_tier_sum'] = 0
counter['player_tier_sum'] = 0
counter['ship_CV_sum'] = 0
counter['ship_DD_sum'] = 0
counter['ship_BB_sum'] = 0
counter['ship_CA_sum'] = 0

#Opens a CSV file to store the data in
with open(currentpath+cvs_prefix+'stats.csv', 'w', newline='') as csvfile:
    for file in replayFiles:
        jsonData = loadReplay(default_path+file)
        #print(file) #prints Current replay file name
        #Some examples that you could use:
        #print(jsonData["mapDisplayName"])
        #print(jsonData["playersPerTeam"])
        #print(jsonData["vehicles"])
        #print(len(jsonData["vehicles"]))
        #print(jsonData["playerVehicle"])
        #Index = 0 #Index of ship in the team, ranges from 0 to len(jsonData["vehicles"])
        #ship = str(jsonData["vehicles"][Index]["shipId"])
        user_tier = 0
        for ship_data in jsonData["vehicles"]:
            ship = str(ship_data["shipId"])
            if(ship in shipDatabase and testTracking(jsonData["scenario"])):
                if(jsonData["playerName"] == ship_data['name']):
                    user_tier = shipDatabase[ship]["tier"]
                    #print(shipDatabase[ship]['name'])
                    #print(user_tier)
        if(user_tier not in counter['ByOwnTier']):
            counter['ByOwnTier'][user_tier] = {}
            counter['ByOwnTier'][user_tier]['ship_CV_sum'] = 0
            counter['ByOwnTier'][user_tier]['ship_BB_sum'] = 0
            counter['ByOwnTier'][user_tier]['ship_CA_sum'] = 0
            counter['ByOwnTier'][user_tier]['ship_DD_sum'] = 0
            counter['ByOwnTier'][user_tier]['battles_per_tier'] = 0
            counter['ByOwnTier'][user_tier]['avrg_team_tier_sum'] = 0
            #print("reset: " + str(user_tier))
            
        counter['ByOwnTier'][user_tier]['battles_per_tier'] += 1
        #print(counter['ByOwnTier'])
        
        
        top_tier = 0
        for ship_data in jsonData["vehicles"]:
            ship = str(ship_data["shipId"])
            
            if(ship in shipDatabase and testTracking(jsonData["scenario"])):
                #############################################
                counter['avrg_tier_sum'] += shipDatabase[ship]["tier"]
                counter['player_sum'] += 1
                if(shipDatabase[ship]["tier"] > top_tier):
                    top_tier = shipDatabase[ship]["tier"]
                if(jsonData["playerName"] == ship_data['name']):
                    counter['player_tier_sum'] += shipDatabase[ship]["tier"] 
                if(shipDatabase[ship]['type'] == 'AirCarrier'):
                    counter['ship_CV_sum'] += 1
                    counter['ByOwnTier'][user_tier]['ship_CV_sum'] += 1
                if(shipDatabase[ship]['type'] == 'Battleship'):
                    counter['ship_BB_sum'] += 1    
                    counter['ByOwnTier'][user_tier]['ship_BB_sum'] += 1
                if(shipDatabase[ship]['type'] == 'Cruiser'):
                    counter['ship_CA_sum'] += 1
                    counter['ByOwnTier'][user_tier]['ship_CA_sum'] += 1
                if(shipDatabase[ship]['type'] == 'Destroyer'):
                    counter['ship_DD_sum'] += 1
                    counter['ByOwnTier'][user_tier]['ship_DD_sum'] += 1
                counter['ByOwnTier'][user_tier]['avrg_team_tier_sum'] += shipDatabase[ship]["tier"] 
        
        #############################################
        if(testTracking(jsonData["scenario"])):
            counter['avrg_top_tier_sum'] +=  top_tier
            counter['battles_total'] += 1
        if(jsonData["scenario"] in counter['gamemode']):
            counter['gamemode'][jsonData["scenario"]] += 1
        else:
            counter['gamemode'][jsonData["scenario"]] = 1
        
        
    #############################################    
    #First Block - Overall Info
    battles_NT_total = 0
    battles_domination_total =  0
    battles_standard_total = 0
    battles_epicenter_total = 0
    

    for gamemode in counter['gamemode']:
        if(testTracking(gamemode)):
            if(gamemode in gamemode_domination):
                battles_domination_total += counter['gamemode'][gamemode]
            elif (gamemode in gamemode_standard):
                battles_standard_total += counter['gamemode'][gamemode]
            elif (gamemode in gamemode_epicenter):
                battles_epicenter_total += counter['gamemode'][gamemode]
            else: 
                print("Warning unknown Gamemode: "+gamemode)
        else:
            battles_NT_total += counter['gamemode'][gamemode]
    fieldnames = ['battles_total', 'battles_NT_total', 'avrg_tier', 'avrg_players_per_game']
    csvw = csv.DictWriter(csvfile, fieldnames=fieldnames)
    csvw.writeheader()
    csvw.writerow({
                    'battles_total': counter['battles_total'],
                    'avrg_tier': calcAvrg(counter['avrg_tier_sum'], counter['player_sum']),   
                    'avrg_players_per_game': calcAvrg(counter['player_sum'], counter['battles_total']),
                    'battles_NT_total': battles_NT_total
                    })   
    #############################################
    #Second Block - Helper Vars

    #Second Block - Gamemodes   
    fieldnames = ['Gametype', 'battles_domination_total', 'battles_standard_total', 'battles_epicenter_total']        
    csvw = csv.DictWriter(csvfile, fieldnames=fieldnames)
    csvw.writeheader()
    csvw.writerow({
                    'Gametype': ','.join(tracked_gametypes),
                    'battles_domination_total': battles_domination_total,
                    'battles_standard_total': battles_standard_total,
                    'battles_epicenter_total': battles_epicenter_total
                    })                
    #############################################                
    #Third Block - Avrg
    fieldnames = ['user_tier', 'avrg_toptier', '%CV','%BB','%CA','%DD']
    csvw = csv.DictWriter(csvfile, fieldnames=fieldnames)
    csvw.writeheader()
    csvw.writerow({
                    'user_tier':    calcAvrg(counter['player_tier_sum'], counter['battles_total']),
                    'avrg_toptier': calcAvrg(counter['avrg_top_tier_sum'], counter['battles_total']),
                    '%CV':          calcAvrg(counter['ship_CV_sum'], counter['player_sum']),
                    '%BB':          calcAvrg(counter['ship_BB_sum'], counter['player_sum']),
                    '%CA':          calcAvrg(counter['ship_CA_sum'], counter['player_sum']),
                    '%DD':          calcAvrg(counter['ship_DD_sum'], counter['player_sum'])
                    }) 
    #############################################
    #Forth Block:
    fieldnames = ['user_tier', 'avrg_team_tier', '%CV','%BB','%CA','%DD','battles_per_tier']
    csvw = csv.DictWriter(csvfile, fieldnames=fieldnames)
    csvw.writeheader()
    for tier in range(1,11):
        avrg_team_tier = 0
                
        if(tier in counter['ByOwnTier']):
            sum =   (counter['ByOwnTier'][tier]['ship_CV_sum']+
                 counter['ByOwnTier'][tier]['ship_BB_sum']+ 
                 counter['ByOwnTier'][tier]['ship_CA_sum']+
                 counter['ByOwnTier'][tier]['ship_DD_sum'])
            csvw.writerow({
                    'user_tier':     tier,
                    'avrg_team_tier': calcAvrg(counter['ByOwnTier'][tier]['avrg_team_tier_sum'],sum) ,
                    '%CV':          calcAvrg(counter['ByOwnTier'][tier]['ship_CV_sum'], sum),
                    '%BB':          calcAvrg(counter['ByOwnTier'][tier]['ship_BB_sum'], sum),
                    '%CA':          calcAvrg(counter['ByOwnTier'][tier]['ship_CA_sum'], sum),
                    '%DD':          calcAvrg(counter['ByOwnTier'][tier]['ship_DD_sum'], sum),
                    'battles_per_tier':  counter['ByOwnTier'][tier]['battles_per_tier']
                    }) 
        else:
            csvw.writerow({
                    'user_tier':     tier,
                    'avrg_team_tier': 0,
                    '%CV':          0,
                    '%BB':          0,
                    '%CA':          0,
                    '%DD':          0,
                    'battles_per_tier':  0
                    }) 
    
#Opens a CSV file to store the data in
with open(currentpath+cvs_prefix+'json.csv', 'w', newline='') as csvfile:
    for file in replayFiles:  
        jsonData = loadReplay(default_path+file)
        csvw = csv.DictWriter(csvfile, fieldnames=jsonData.keys())
        csvw.writeheader()
        csvw.writerow(jsonData) 
    
if(counter['battles_total'] ==0):
    print("Warning: No replays found in: "+default_path)
print("Done! Data Stored in .csv files")
if(wait_before_closing==True):
    input("Press Enter to continue...")
