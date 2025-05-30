## Pigpen webmain
# Bash script no more

from flask import Flask, redirect, render_template, request, Response
import subprocess, socket, os, time, logging, signal, fcntl, sys # Thank you python for you totally not bloated packages

##Global Snort Running Variable: just here to tell if snort is running or not
isSnort = False  # Simple tracker for snort status
lastCommand = '' # Stores last executed command for tracking sake, might want to move this to a file so that snort can start automatically when the program starts?
snort = None     # Global snort tracker, tracks running process

## Flask instantiation
# Disabled the logging for now so I can see snort output better
app = Flask(__name__)
log = logging.getLogger('werkzeug')
log.disabled = True

## Start up Function
# Checks to see if the needed folders are there, if not they are created
def startUpCheck():
        # Dirlist can be changed if need be, these are jsut the directories that are somewhat hardcoded into the program
        dirList = ['/usr/local/etc/snort','/usr/local/etc/lists','/usr/local/etc/rules','/usr/local/etc/so_rules','/usr/local/etc/snort/conf','/var/log/snort']
        ## Checks to see if Snort command can be executed
        snortCheck = subprocess.run(['snort','-V'], stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,bufsize=1)
        returnCode = snortCheck.returncode
        if returnCode != 0:
                print("\033[1;31m >>> Please Install Sort <<<\033[0m")
                sys.exit(1)
        else:
                print("\033[1;32m >> Snort Install Found << \033[0m")
                pass
        ## Checks to see if there are any needed dirs missing
        for dir in dirList:
                if os.path.isdir(dir):
                        pass
                else:
                        print(f"{dir} doesnt exist, creating")
                        os.mkdir(dir)
                        print(f"Created {dir}")

### Reusable functions
# All functions that are used more than once, hooray for file size

## Very simple file display for file manager, modified to show folders, subdirs, and internal files. Added type field for HTML orgnization
def fileManager(filePath):
        fileList = []
        filePath = os.path.abspath(filePath)
        for dirPath, dirNames, fileNames in os.walk(filePath):
                if os.path.abspath(dirPath) == filePath:
                        for dirName in dirNames:
                                fileList.append({'path':os.path.join(dirPath, dirName) + '/', 'type': 'dir'})
                        for fileName in fileNames:
                                fileList.append({'path':os.path.join(dirPath, fileName), 'type': 'file'})
                break
        return fileList

#### MIGHT NOT NEED THIS LATER ON
### Internal commands are for when there is no web request
## Internal Kill Snort commant
def intKillSnort():
        global isSnort
        global snort
        if isSnort:
                snort.send_signal(signal.SIGINT)
                isSnort = False
                snort = None
        else:
                print("Snort Not Running")
        return redirect('/')

#### MIGHT NOT NEED THIS LATER ON
##Internal Start Snort func
# Reworked to work with the new way snort starts up
# Really only used for reload in text editor
def intStartSnort():
        global isSnort
        global lastCommand
        global snort
#       print(f"Snort Status: {isSnort}")
        if not isSnort:
                snort = subprocess.Popen(lastCommand,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,bufsize=1)
                isSnort = True
        else:
                print("Snort Already Running")
        return redirect('/')

### Route Functions
# Functions that are used for routing to pages, and things like that, one time use

## Path to main page, just index
# Nothing on this for now, moving everything to seperate pages, will do something with it soon.
# Might want to do a main web panel kind of deal
@app.route('/')
def main():
        global isSnort
        return render_template('index.html', isSnort = isSnort )


#### Got rid of snortpipe and handling all start and stop in python

## Snort main page
# new way of handling snort starting, takes in all the files in the snort conf dir, spits them out to html land and then lets then be used as start up commands
@app.route('/snort', methods=['GET','POST'])
def snortMain():
        global isSnort
        fileList = fileManager('/usr/local/etc/snort/conf')
        fileContent = []
        # For loop to read through files and place contents in html land
        for fileObj in fileList:
                if fileObj['type'] == 'file':
                        with open(fileObj['path'], 'r') as file: #I hate the way this object works :D
                                digest = file.read()
                                fileContent.append({'digest': digest, 'path':fileObj['path']})
        return render_template('snortmain.html', fileContent = fileContent, isSnort = isSnort)

## Starts Snort Session
# Changed this one a lot, doenst interface with snortpipe anymore, python just starts it locally
# Starts snort with stdbuf so that output can be see on screen
@app.route('/start', methods=['POST'])
def startSnort():
        global isSnort
        global snort
        global lastCommand
        userSnortCommand = request.form.get('snort_args', '').strip()
        finalCommand = ["stdbuf", "-oL", "snort"] + userSnortCommand.split() # Added stdbuf to pass stdout correctly
        lastCommand = finalCommand
#       print("Starting Snort with command:", finalCommand)
        if not isSnort:
                if 'snort_args' in request.form:
                        snort = subprocess.Popen(finalCommand,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,bufsize=1)
                        isSnort = True
        else:
                print("Snort Already Running")

        return redirect('/snort')

## Kills Snort Process
# Moved away from snortpipe, python kills locally now with a sigint 2 instead of 15
@app.route('/kill', methods=['POST'])
def killSnort():
        global isSnort
        global snort
        if isSnort:
                if 'kill_button' in request.form:
                        snort.send_signal(signal.SIGINT)
                        isSnort = False
                        snort = None
        else:
                print("Snort Not Running")
        return redirect('/snort')

## Reload route
# Added this to the snort control page for quicker reloads
# Used when you just need to quickly restart snort, upates to files, and so on
@app.route('/reload', methods=['POST'])
def reloadSnort():
        global isSnort
        if 'reload' in request.form and isSnort:
                intKillSnort()
                time.sleep(1)
                intStartSnort()
        else:
                print("Snort is not running")
        return redirect('/snort')

## Text editor
# like 90% of this is stolen
# prebuilt ones were all rich text (yuck)
@app.route('/edit', methods=['GET', 'POST'])
def editFile():
        fileToEdit = request.args.get('file') #Set file to browser argument, handy
        if not fileToEdit or not os.path.isfile(fileToEdit):
                return "File doesnt exist", 404
        if request.method == 'POST':
                content = request.form.get('content')
                with open(fileToEdit, 'w') as filePtr:
                        filePtr.write(content)
                redirectUrl = f'/edit?file={fileToEdit}'
                return redirect(redirectUrl)
        with open(fileToEdit, 'r') as filePtr:
                content = filePtr.read()
        return render_template('editor.html', content=content, fileToEdit=fileToEdit)

## Need add a way to create files
# Get current directory
# Create file in that current directory
# Redirect to editFile at file location
@app.route('/create', methods=['GET','POST'])
def createFile():
        filePath = request.args.get('file')
        fileName = request.args.get('filename')
        currDir = os.path.abspath(filePath.rstrip('/'))
        fullName = os.path.join(currDir, fileName)
        ## Create file
        with open(fullName, "w") as newFile:
                newFile.write("")
        return redirect(f'/edit?file={fullName}')


## Delete method
# Literally just OS delete at file location, nothing special
@app.route('/delete', methods=['GET', 'POST'])
def deleteFile():
        fileToDel = request.args.get('file') #Set file to browser argument, handy
        currDir = os.path.dirname(fileToDel.rstrip('/'))
        if not fileToDel or not os.path.isfile(fileToDel):
                return "File doesnt exist", 404
        if request.method == 'GET':
                os.remove(fileToDel)
        return redirect(f'/files?file={currDir}')

## File manager idea
# Could be a second page or could be something on he edit page where you create a new file or something
# Just going to use a template and url queries to traverse file system depending on there the user is at
@app.route('/files', methods=['GET'])
def fileHandler():
        filePath = request.args.get('file') #File path passed in Via URL, can now use redirects
        prevPath = os.path.dirname(filePath.rstrip('/')) #Tracker for previous path when the user wants to back up, needed to add rstrip for proper directory traversal
        fileList = fileManager(filePath)
        return render_template('filemanager.html', fileList = fileList, path = filePath, len = len(fileList), prevPath = prevPath)


## Main Dir list
# Logs, configs, things like that all in one place
@app.route('/dirs', methods=['GET'])
def dirList():
        dirs = ['/usr/local/etc','/usr/local/etc/snort/conf' ,'/var/log/snort']
        return render_template('dirlist.html', dirs = dirs, len = len(dirs))

## Output termianl code for snort page, stolen cause I was lost
# Takes in STDOUT from the snort process, usses fcntl to get the FD and flags, set proper flags, and then read chunks to an output
@app.route('/out', methods=['GET'])
def getOutput():
        global snort
        if not snort:
                return "Snort not running "
        fd = snort.stdout.fileno() # Gets FD int for fcntl to work with
        flags = fcntl.fcntl(fd, fcntl.F_GETFL) # Gets flags with FD int by using F_GETGL (File Get Flags of provided FD)
        fcntl.fcntl(fd, fcntl.F_SETFL, flags | os.O_NONBLOCK) # Sets all flags with O_NONBLOCK using F_SETFL (Add provided property to provided flags of provided FD)
        output = ""
        while True:
                chunk = snort.stdout.read(1024) # FD (STDOUT) has proper permissions, can append to buffer
                if not chunk:
                        break
                output += chunk
        return Response(f"<pre>{output}</pre>", mimetype="text/html")

## Main function
if __name__ == '__main__':
        startUpCheck() #Startup check for snort, see function def for docs
        app.run(host='0.0.0.0', port='9091') #Random port for funsies
