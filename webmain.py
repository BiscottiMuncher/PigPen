## Pigpen webmain
# Controls snorthandler bash script

from flask import Flask, redirect, render_template, request
import subprocess, socket


## Start Snortpipe process immedualty
def startSnortPipe():
         subprocess.run(["snortpipe.sh &"], shell=True)

## Path to Socket on local machine
socketPath = "/tmp/snortSock.sock"


## Global Snort Running Variable
isSnort = 0

# DEfine flask app name
app = Flask(__name__)

## Path to main page, holds all control 
@app.route('/')
def main():
        return render_template('index.html')


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
                                # Added in Response Code
#                               response = client.recv(1024).decode()
#                               print(response)
#                               if response == "!> STARTED":
#                                       isSnort = 1
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


## Main function
if __name__ == '__main__':
        startSnortPipe()
        app.run(host='0.0.0.0', port=5959)