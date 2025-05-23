## Pigpen webmain
# Controls snorthandler bash script

from flask import Flask, redirect, render_template, request, Response
import subprocess, socket, os, time, logging

## Path to Socket on local machine, this is needef for all comms between snortpipe and webmain
socketPath = "/tmp/snortSock.sock"

## Global Snort Running Variable: just here to tell if snort is running or not
# Need to track ths with a live process, sometimes snort will crash or hang, need to see PID instead of flying blind (Would probably need threading)
isSnort = False
snortStartCommand = '' #Not pre-encoded, I lied

## Flask instantiation
# Disabled the logging for now so I can see snort output better
app = Flask(__name__)
log = logging.getLogger('werkzeug')
log.disabled = True


### Reusable functions
# All functions that are used more than once, hooray for file size

# Super old method, not really used anymore :(
def viewFileContents(filePath):
        with open(filePath, "r") as f:
                content = f.read()
        return Response (content, mimetype='text/plain')

## Start Snortpipe process right away
def startSnortPipe():
        scriptPath = os.path.join(os.path.dirname(__file__), 'snortpipe.sh')
        subprocess.run(f"{scriptPath} &", shell=True)
        #subprocess.run(["/root/scripts/pigpen/project/snortpipe.sh &"], shell=True)


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

### Internal commands are for when there is no web request
## Internal Kill Snort commant
def intKillSnort():
        global isSnort
        if isSnort:
                with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
                        client.connect(socketPath)
                        client.sendall(b"kill\n")
                        isSnort = False
        else:
                print("Snort Not Running")
        return redirect('/')

##Internal Start Snort func
# Reworked to work with the new way snort starts up
# Really only used for reload in text editor
def intStartSnort():
        global isSnort
        global snortStartCommand
        print(f"Snort Status: {isSnort}")
        if not isSnort:
                with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
                        client.connect(socketPath)
                        client.sendall(snortStartCommand.encode()) # <- new shit
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

### Snortpipe Interface Commands
# start: Start Snort up if there isnt a session already running
# kill: Kills current snort session aslong as there is a session runnign
# quit: Quits handler script and kills current snort session if there is one running

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
# Changed this one up a lot, it sends arguments over to snortpipe and they get executed there, this is good for flexibility
# Need to find a way of saving them all somewhere on the server so thay they user doesnt have to type them in one million times
@app.route('/start', methods=['POST'])
def startSnort():
        global isSnort
        global snortStartCommand
        userSnortCommand = request.form.get('snort_args', '').strip()
        startCommand = f"start {userSnortCommand}\n"
        snortStartCommand = startCommand
        print(f"Starting Snort with: {snortStartCommand}")
        if not isSnort:
                if 'snort_args' in request.form:
                        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
                                client.connect(socketPath)
                                client.sendall(startCommand.encode())
                                isSnort = True
        else:
                print("Snort Already Running")
        return redirect('/snort')

## Kills Snort Process
# Needs Snort PID, need to add check to see whether or not snort is actually running
@app.route('/kill', methods=['POST'])
def killSnort():
        global isSnort
        if isSnort:
                if 'kill_button' in request.form:
                        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
                                client.connect(socketPath)
                                client.sendall(b"kill\n")
                                isSnort = False
        else:
                print("Snort Not Running")
        return redirect('/snort')

## Kills Handler Session (Not really used anymore)
# Kills handler session and Snort session at the same time for a safe shutdown
@app.route('/quit', methods=['POST'])
def killHandler():
        global isSnort
        if 'quit_button' in request.form:
                killSnort
                with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
                        client.connect(socketPath)
                        client.sendall(b"quit\n")
        return render_template('index.html', isSnort = isSnort )


## Reload route
# Used when you just need to quickly restart snort, upates to files, and so on
@app.route('/reload', methods=['POST'])
def reloadSnort():
        global isSnort
        if 'reload' in request.form:
                intKillSnort()
                print("Reloading Snort")
                time.sleep(5)
                print("Starting Snort")
                intStartSnort()
        return render_template('index.html', isSnort = isSnort)


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

## Main function
if __name__ == '__main__':
        startSnortPipe()
        app.run(host='0.0.0.0', port=5959) #Random port for funsies
