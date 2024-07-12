# meshtastic-cli-chat
Meshtastic interactive command-line chat

![Screenshot 2024-07-12 144636](https://github.com/user-attachments/assets/cb2ede57-237c-4ba7-b78b-800cb8018c5b)

![Screenshot 2024-07-12 144749](https://github.com/user-attachments/assets/258a6614-f863-4f75-a19a-367765ae0525)

![Screenshot 2024-07-12 144318](https://github.com/user-attachments/assets/50d9c3d1-c448-417e-b404-f4d1fddac3e4)

# Installation
* git clone https://github.com/brad28b/meshtastic-cli-chat.git
* cd meshtastic-cli-chat
* python3 -m venv myvenv
* pip3 install -r requirements.txt

If using Windows, you will need to install curses with:
* pip3 install windows-curses


# Configuration
* Decide if you will be connecting to your node via TCP or Serial. If using TCP, edit <b>'meshchat_tcp.py'</b>, and configure both your Nodes IP address, and the channel index you want to operate on (normally 0). If using Serial, edit <b>'meshchat_serial.py'</b>, and configure both your serial port address for your node (usually either /dev/ttyUSB0 or /dev/ACM0), and the channel index you want to operate on (normally 0).

# Usage
* If using Serial: python meshchat_serial.py
* If using Tcp: python meshchat_tcp.py
* Use the /help command for, funnily enough, help!

# TODO
* Handle screen resizes gracefully
