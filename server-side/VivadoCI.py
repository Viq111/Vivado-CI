# -*- coding:Utf-8 -*-
# Vivado-CI Package
prog_name = "VivadoCI - Server Side"
# version:
version = 1
# By Viq - Vianney Tran
# License: Creative Commons Attribution-ShareAlike 3.0 (CC BY-SA 3.0) 
# (http://creativecommons.org/licenses/by-sa/3.0/)

##############
### IMPORT ###
##############
import os, time, glob, threading, json, SocketServer, socket, Queue, re, tempfile, subprocess, shutil
import random, string

if os.name == "posix":
    import fcntl # This is for non-block stdout check on linux

###############
### GLOBALS ###
###############

DEFAULT_PORT = 4545

###################
### DEFINITIONS ###
###################

def random_string(size = 8):
    "Return a random string"
    return ''.join(random.choice(string.ascii_lowercase + string.digits) for i in range(size))

def execute(args_list, stdout_queue):
    "Execute as subprocess.Popen, write the stdout to the queue and return the error code at the end"
    class Watcher(threading.Thread):
        "Watch a pipe and write to queue"
        def __init__(self, prog, queue):
            self.prog = prog # subprocess.Popen instance
            self.queue = queue
            self.running = False
            threading.Thread.__init__(self)
        def run(self):
            self.running = True
            while self.running:
                try:
                    data = self.prog.stdout.readline()
                    self.queue.put(data)
                except IOError: # Because with fcntl, we set the readline to non-blocking
                    time.sleep(0.05)
                try:
                    data = self.prog.stderr.readline()
                    self.queue.put(data)
                except IOError:
                    time.sleep(0.05)
        def stop(self):
            self.running = False
    # Let's create the program
    prog = subprocess.Popen(args_list, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
    if os.name == "posix":
        fcntl.fcntl(prog.stdout.fileno(), fcntl.F_SETFL, os.O_NONBLOCK) # This is for non-blocking stdout on linux
        fcntl.fcntl(prog.stderr.fileno(), fcntl.F_SETFL, os.O_NONBLOCK)
    thread = Watcher(prog, stdout_queue)
    thread.start()
    prog.wait()
    time.sleep(1) # Wait for the program to flush itself
    thread.stop()
    thread.join()
    return prog.returncode

###############
### CLASSES ###
###############

class Build(object):
    "Contains information about a particular build"
    def __init__(self, repo, commit, xpr):
        "Create a build on a particular GIT commit and a XPR file"
        self.messages = Queue.Queue() # All received message in the connection
        self.exit_status = None # Will be set when the build exits
        self.git_repo = repo
        self.git_commit = commit
        self.xpr_to_find = xpr
        self.current_step = "Just arrived..." # Current step: arrived, prepare_build, build, done

class ConnectionHandler(SocketServer.StreamRequestHandler):
    "Handle a TCP connection"
    timeout = 5 # 5s Timeout
    def handle(self):
        "Handle a new connection"
        #print "[REST]> New conn from " + str(self.client_address[0])
        try:
            data = self.rfile.readline()
        except socket.timeout:
            #print "-> Timed out"
            return False
        except socket.error as e:
            if e.errno == 10054: # This is if the client stopped the socket
                return False
            else:
                raise e
        try:
            j = json.loads(data)
            repo = j["repo"]
            if '"' in repo: # This could be an attack -_-
                print "[WARNING] Malformed repo: " + str(repo)
                return False
            commit = j["commit"]
            try: # Check if Hexa
                int(commit, 16)
            except ValueError:
                print "[WARNING] Malformed commit: " + str(commit)
                return False
            xpr = j["xpr"]
        except:
            print "[REST]-> Input not correct: " + str(data)
            return False
        # Ok JSON seems nice, let's build the object
        print "[REST]> New build request from " + str(self.client_address[0])
        b = Build(repo, commit, xpr)
        # Add build to work
        self.server.build_queue.put(b)
        while b.exit_status == None: # While build not done
            try:
                msg = b.messages.get_nowait()
            except Queue.Empty:
                time.sleep(0.5)
            else:
                try:
                    self.wfile.write(msg)
                except socket.error as e:
                    if e.errno == 10054: # This is if the client stopped the socket
                        return False
                    else:
                        raise e
                    
        # Flush the queue
        while 1:
            try:
                msg = b.messages.get_nowait()
            except:
                break
            else:
                try:
                    self.wfile.write(msg)
                except socket.error as e:
                    if e.errno == 10054: # This is if the client stopped the socket
                        return False
                    else:
                        raise e
        # Last message should be the exit status code
        print "[REST] > Build for client "  + str(self.client_address[0]) + " terminated: " + str(b.exit_status)
        try:
            self.wfile.write("\n"+str(b.exit_status)+"\n")
        except socket.error as e:
            if e.errno == 10054: # This is if the client stopped the socket
                return False
            else:
                raise e
        return True

class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    "The SocketServer"
    build_queue = Queue.Queue()

class Worker(threading.Thread):
    "This is the worker which will do all the work for us when he is available"
    def __init__(self, build_queue):
        "Create the worker"
        self.queue = build_queue
        self.running = False
        threading.Thread.__init__(self)
    def stop(self):
        "Graceful shutdown of the build server"
        self.running = False
    def run(self):
        "Start the worker"
        self.running = True
        while self.running:
            # Get work
            build = None
            while build == None: # No work to do, check
                try:
                    build = self.queue.get_nowait()
                except Queue.Empty:
                    if not self.running:
                        return
                    time.sleep(0.5)
            # OK, we got work
            print "[WORKER]> Starting work: " + str(build.git_repo)
            # Change dir
            current_path = os.getcwd()
            temp_dir = tempfile.mkdtemp() 
            os.chdir(temp_dir)
            # Work
            r_code = self.work(build)
            build.exit_status = r_code
            print "[WORKER]> Build finished with: " + str(build.exit_status)
            # Clean
            os.chdir(current_path)
            shutil.rmtree(temp_dir)

    def work(self, build):
        "Work on a build"
        # Create a temporary directory and go to it
        current_path = os.getcwd()
        temp_dir = tempfile.mkdtemp()
        os.chdir(temp_dir)
        # Let's clone first
        print "[WORKER]-> Cloning repo..."
        build.messages.put("[CI] > Cloning repository\n")
        r_code = execute(['git', 'clone', build.git_repo, '.'], build.messages)
        if r_code != 0: # There was an error
            return r_code
        # Let's add the pull request branches
        r_code = execute(["git", "config", "remote.origin.fetch", "+refs/pull/*/merge:refs/remotes/origin/pr/*", "--add"], build.messages)
        r_code += execute(["git", "fetch"], build.messages)
        if r_code != 0:
            return r_code
        # Checkout
        r_code = execute(['git', 'checkout','-qf', str(build.git_commit)], build.messages)
        if r_code != 0: # There was an error
            return r_code
        # Find XPR
        xprs = glob.glob(build.xpr_to_find)
        if len(xprs) == 0:
            build.messages.put("ERROR: Can't find your XPR according to: " + str(build.xpr_to_find) + "\n")
            return 5
        if len(xprs) > 1:
            build.messages.put("ERROR: Multiple XPR found for rule: " + str(build.xpr_to_find) + "\n")
            return 6
        xpr = str(xprs[0])
        build.messages.put("[CI] > Found XPR file: " + str(xpr) + "\n")
        # Build script
        script_name = "script_" + random_string() + ".tcl"
        with open(script_name, "w") as f:
            f.write("open_project " + xpr + "\n")
            # Synthetisis
            f.write("reset_run synth_1\n")
            f.write("launch_runs synth_1\n")
            f.write("wait_on_run synth_1\n")
            # Implementation
            f.write("launch_runs impl_1\n")
            f.write("wait_on_run impl_1\n")
            # Bitstream
            f.write("launch_runs impl_1 -to_step write_bitstream\n")
            f.write("wait_on_run impl_1\n")
        # Execute script
        print "[WORKER]-> Building..."
        vivado = glob.glob("/opt/Xilinx/Vivado/*/bin/vivado")[0]
        r_code = execute([vivado, "-mode" ,"batch" ,"-source" , script_name], build.messages)
        if r_code = 0: # Vivado don't tell us if the generate bitstream fails
            if len(glob.glob("*.runs/impl_1/*.bit")) <= 0: # We did not generate any bitstream file
                return 4
        return r_code

##################
###  __MAIN__  ###
##################

if __name__ == "__main__":
    print "> Welcome to " + str(prog_name) + " (r" + str(version) + ")"
    print "> By Viq (under CC BY-SA 3.0 license)"
    print "> Loading program ..."
    server = ThreadedTCPServer(("", DEFAULT_PORT), ConnectionHandler)
    # Create build server
    build_server = Worker(server.build_queue)
    build_server.start()
    print "-> Serving on " + str(DEFAULT_PORT) + "...\n"
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()
    build_server.stop()
    
