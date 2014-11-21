# -*- coding:Utf-8 -*-
# Vivado-CI Package
prog_name = "VivadoCI - Client Side"
# version:
version = 1
# By Viq
# License: Creative Commons Attribution-ShareAlike 3.0 (CC BY-SA 3.0) 
# (http://creativecommons.org/licenses/by-sa/3.0/)

##############
### IMPORT ###
##############
import os, time, socket, sys, json

###############
### GLOBALS ###
###############

MAX_SIZE = 1024 * 1024

###############
### CLASSES ###
###############


###################
### DEFINITIONS ###
###################

##################
###  __MAIN__  ###
##################

if __name__ == "__main__":
    # Arguments are ci_server, ci_port, repo_url, repo_commit, xpr_file
    if len(sys.argv) < 6:
        print "[ERROR] Not enough args"
        sys.exit(1)
    if "--before_install" in sys.argv:
        # Currently we do nothing on before_install
        sys.exit(0)
    if "--install" in sys.argv:
        # Currently we do nothing on install
        sys.exit(0)
    server = sys.argv[1]
    port = sys.argv[2]
    repo = sys.argv[3]
    commit = sys.argv[4]
    xpr = sys.argv[5]
    j = json.dumps({"repo" : repo, "commit" : commit, "xpr" : xpr})
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print "[DEBUG]: " + str(j)
    print "[CI]> Connecting to " + str(server) + ":" + str(port) + "..."
    s.connect((server, int(port)))
    print "[CI]-> Connected"
    # First send the data
    s.send(j+"\n")
    data = "1"
    while data != "":
        previous_data = data
        data = s.recv(MAX_SIZE)
        print str(data)
    s.close()
    # Return the return code
    sys.exit(int(previous_data.replace("\n","")))
