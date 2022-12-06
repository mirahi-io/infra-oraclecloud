#!/usr/bin/env python

import sys
import argparse
import oci
import subprocess
import time

# Arguments Options
parser = argparse.ArgumentParser(description='Move NSG Rules from one OCID to another one')
parser.add_argument('-t','--ticket', type=str, help='Ticket number, TICKET-XXXX', required=True )
parser.add_argument('-os','--sourceocid', type=str, help='Put the SOURCE OCID of the NSG', required=True)
parser.add_argument('-od','--destinationocid', type=str, help='Put the DESTINATION OCID of the NSG', required=True)
args = parser.parse_args()

# Variables Assignment
ticket=args.ticket
sourceocid=args.sourceocid
destinationocid=args.destinationocid

# Variables
maxrules = 240

# Functions
def get_displayName(ocid):
    result = subprocess.check_output(f"oci network nsg get --nsg-id {ocid} | jq '.data.\"display-name\"' | tr -d '\"'", shell=True, encoding="utf8")
    result = result.replace("\n","")
    return result

def get_numberOfRules(ocid,name):
    rules = subprocess.check_output(f"oci network nsg rules list --all --nsg-id {ocid} | jq '.data | length'", shell=True, encoding="utf8")
    rules = rules.replace("\n","") 
    if not rules:
        rules = "0"
    print ("The NSG "+ name +" contain "+ rules +" rules")
    return int(rules)

def get_concatenate(sourcenumber,destinationnumber): 
    total = sourcenumber + destinationnumber
    if total <= maxrules:
        print ("Merging is possible")
        answer = input("Continue? [y/n]")
        if answer.lower() in ["y","yes"]:
            print("Confirmed")
            status = True
        elif answer.lower() in ["n","no"]:
            print ("Aborting")
            status = False
        else:
            print ("Wrong input")
            status = False
    else: 
        status = False
        exceed = maxrules - total
        print("Cannot merge as the total rules are exceded by "+ str(exceed))
    return bool(status)


def set_concatenate(status):
    if status == True:
        filename = str(ticket) + "_export.json"
        file_ = open(filename, "w")
        #REMOVE useless key --> time-created + id + is-valid
        subprocess.Popen(f"oci network nsg rules list --all --nsg-id {sourceocid} | jq '.data' | jq 'del(.[].id)' | jq 'del(.[].\"time-created\")' | jq 'del(.[].\"is-valid\")'", shell=True, encoding="utf8", stdout=file_)
        time.sleep(10)
        subprocess.check_output(f"oci network nsg rules add --nsg-id {destinationocid} --security-rules file://{filename}", shell=True, encoding="utf8")
        task = True
    else:
        print ("Exiting as the merge is not allowed / possible, please fix it")
        task = False
        sys.exit()
    return task

def set_clean(task):
    if task == True:
        answer = input("Do you want to remove the source NSG ? [y/n]")
        if answer.lower() in ["y","yes"]:
            print("REMOVAL CONFIRMED")
            subprocess.check_output(f"oci network nsg delete --nsg-id {sourceocid} --force", shell=True, encoding="utf8")
        elif answer.lower() in ["n","no"]:
            print ("SOURCE NSG WILL REMAIN UNTOUCHED")
        else:
            print ("Wrong input")
            set_clean(True)
    else: 
        print("Something went wrong, I cannot help more, I'm just a script dude")
    return

# Code
print("Checking source...") 
print("The source OCID is "+ sourceocid)
sourcename = get_displayName(sourceocid)
sourcenumber = get_numberOfRules(sourceocid,sourcename)
print("Checking destination...") 
print("The destination OCID is "+ destinationocid)
destinationname = get_displayName(destinationocid)
destinationnumber = get_numberOfRules(destinationocid,destinationname)
print("Checking if we can merge...") 
status = get_concatenate(sourcenumber,destinationnumber)
task = set_concatenate(status)
set_clean(task)
