## Pigpen webmain
# Controls snorthandler bash script

from flask import Flask, redirect, render_template, request, Response
import subprocess, socket, os, time


## Start Snortpipe process immedualty
def startSnortPipe():
         subprocess.run(["/root/scripts/pigpen/project/snortpipe.sh &"], shell=True)

# Very crude view file contents
def viewFileContents(filePath):
        with open(filePath, "r") as f:
                content = f.read()
        return Response (content, mimetype='text/plain')

## Path to Socket on local machine, this is needef for all comms between snortpipe and webmain
socketPath = "/tmp/snortSock.sock"

## Global Snort Running Variable: just here to tell if snort is running or not
isSnort = 0

## Very simple file display for file manager, modified to show folders, subdirs, and internal files
def fileManager(filePath):
        fileList = []
        filePath = os.path.abspath(filePath)
        for dirPath, dirNames, fileNames in os.walk(filePath):
                if os.path.abspath(dirPath) == filePath:
                        for dirName in dirNames:
                                fileList.append(os.path.join(dirPath, dirName) + '/')
                        for fileName in fileNames:
                                fileList.append(os.path.join(dirPath, fileName))
                break
        return fileList

### Internal commands are for when there is no web request
## Internal Kill Snort commant
def intKillSnort():
        global isSnort
        if isSnort == 1:
                with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
                        client.connect(socketPath)
                        client.sendall(b"kill\n")
                        isSnort = 0
        else:
                print("Snort Not Running")
        return redirect('/')

##Internal Start Snort func
def intStartSnort():
        global isSnort
        print(f"Snort Status: {isSnort}")
        if isSnort == 0:
                with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
                        client.connect(socketPath)
                        client.sendall(b"start\n")
                        isSnort = 1
        else:
                 print("Snort Already Running")
        return redirect('/')

# DEfine flask app name
app = Flask(__name__)

## Path to main page, just index
@app.route('/')
def main():
        return render_template('index.html')


### Snortpipe Interface Commands
# start: Start Snort up if there isnt a session already running
# kill: Kills current snort session aslong as there is a session runnign
# quit: Quits handler script and kills current snort session if there is one running

## Starts Snort Session
# Need to add check to make sure that there is no Snort session currently running
# Could possibly send bacm infromation from snortpipe for status
@app.route('/start', methods=['POST'])
def startSnort():
        global isSnort
        print(f"Snort Status: {isSnort}")
        if isSnort == 0:
                if 'start_button' in request.form:
                        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
                                client.connect(socketPath)
                                client.sendall(b"start\n")
                                isSnort = 1
        else:
                print("Snort Already Running")

        return redirect('/')


## Kills Snort Process
# Needs Snort PID, need to add check to see whether or not snort is actually running
@app.route('/kill', methods=['POST'])
def killSnort():
        global isSnort
        if isSnort == 1:
                if 'kill_button' in request.form:
                        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
                                client.connect(socketPath)
                                client.sendall(b"kill\n")
                                isSnort = 0
        else:
                print("Snort Not Running")
        return redirect('/')

## Kills Handler Session
# Kills handler session and Snort session at the same time for a safe shutdown
@app.route('/quit', methods=['POST'])
def killHandler():
        if 'quit_button' in request.form:
                killSnort
                with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
                        client.connect(socketPath)
                        client.sendall(b"quit\n")
        return redirect('/')


## Reload route
# Used when you just need to quickly restart snort, upates to files, and so on
@app.route('/reload', methods=['POST'])
def reloadSnort():
        if 'reload' in request.form:
                intKillSnort()
                print("Reloading Snort")
                time.sleep(5)
                print("Starting Snort")
                intStartSnort()
        return redirect('/')


## Shitty text editor
# like 90% of this is stolen
@app.route('/edit', methods=['GET', 'POST'])
def editFile():
    fileToEdit = request.args.get('file') #Set file to browser argument, handy
    if not fileToEdit or not os.path.isfile(fileToEdit):
        return "Invalid file path", 404

    if request.method == 'POST':
        content = request.form.get('content')
        with open(fileToEdit, 'w') as filePtr:
            filePtr.write(content)
        redirect_url = f'/edit?file={fileToEdit}'
        return redirect(redirect_url)

    with open(fileToEdit, 'r') as filePtr:
        content = filePtr.read()

    return render_template('editor.html', content=content, fileToEdit=fileToEdit)

## File manager idea
# Could be a second page or could be something on he edit page where you create a new file or something
# Just going to use a template and url queries to traverse file system depending on there the user is at
@app.route('/files', methods=['GET'])
def fileTest():
        filePath = request.args.get('file') #File path passed in Via URL, can now use redirects
        prevPath = os.path.dirname(filePath.rstrip('/')) #Tracker for previous path when the user wants to back up, needed to add rstrip for proper directory traversal
        return render_template('filemanager.html', fileList = fileManager(filePath), path = filePath, len = len(fileManager(filePath)), prevPath = prevPath)

## Main function
if __name__ == '__main__':
        startSnortPipe()
        app.run(host='0.0.0.0', port=5959
