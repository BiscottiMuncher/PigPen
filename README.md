# PigPen
### Web based Snort3 admin panel
Early stages of development


--- 
## Current Features

- Complete Snort3 control
- Web based text editor and file browser
- Custom Snort argument configs passed to CLI
- Web terminal output
- Slightly better CSS and site flow

--- 
## Planned Features

- Better CSS and site flow (I am not good at web design)
- Add File upload for pcap analysis and config upload

--- 
## Setup

Grab project files
``` bash
git clone https://github.com/BiscottiMuncher/PigPen
```
##
Install Snort using an automated installer 
``` bash
git clone https://github.com/BiscottiMuncher/Snort3Auto
```
~ or ~ 

Install manually
```
https://docs.snort.org/start/installation
```
##

Install required packages
``` python
pip install -r requirements.txt
```
##

Start pigpen server
``` python
python pigpen.py
```
##
--- 
## Screenshots

### Control Panel
Main control panel, everything snort is found here
![image](https://github.com/user-attachments/assets/14050555-52ec-42e4-8a33-4970ca3381cb)

### Text Editor
Quick text editor for configs and files
![image](https://github.com/user-attachments/assets/506f0f72-d708-47f6-a226-d1753370c642)

### File Browser
Cheao "file browser" to edit, create, and delete files
![image](https://github.com/user-attachments/assets/ea6f769b-5577-4891-890a-f389cceff6a8)

### Main Page
Landing page with a little how-to
![image](https://github.com/user-attachments/assets/3f73db24-9270-4921-bb81-6fc33f88dde3)

--- 
Used best in conjunction with Snort3 auto install script if you are lazy like me

https://github.com/BiscottiMuncher/Snort3Auto

