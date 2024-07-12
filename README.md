# meshtastic-cli-chat
Meshtastic interactive command-line chat

# Installation
* git clone https://github.com/brad28b/meshtastic-cli-chat.git
* cd meshtastic-cli-chat
* python3 -m venv myvenv
* pip3 install -r requirements.txt

# Configuration
* Decide if you will be connecting to your node via TCP or Serial. If using TCP, edit <b>'meshchat_tcp.py'</b>, and configure both your Nodes IP address, and the channel index you want to operate on (normally 0). If using Serial, edit <b>'meshchat_serial.py'</b>, and configure both your serial port address for your node (usually either /dev/ttyUSB0 or /dev/ACM0), and the channel index you want to operate on (normally 0).

# Usage
* If using Serial: python meshchat_serial.py
* If using Tcp: python meshchat_tcp.py
* Use the /help command for, funnily enough, help!

# TODO
* Handle screen resizes gracefully
