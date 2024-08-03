import time
import curses
import os
from pubsub import pub
from meshtastic.serial_interface import SerialInterface  # Import SerialInterface for serial communication

serial_port = "/dev/ttyUSB0"  # Replace with your serial port
channel_index = 0             # Replace with your channel index

# Determine backspace key code based on the platform
if os.name == 'nt':  # For Windows
    BACKSPACE = 8
else:  # For Unix/Linux
    BACKSPACE = curses.KEY_BACKSPACE

def get_node_info():
    with SerialInterface(serial_port) as interface:
        node_info = interface.nodes
    return node_info

def parse_node_info(node_info):
    nodes = []
    for node_id, node in node_info.items():
        nodes.append({
            'num': node_id,
            'user': {
                'shortName': node.get('user', {}).get('shortName', 'Unknown')
            }
        })
    return nodes

def show_loading_screen(stdscr):
    stdscr.clear()
    stdscr.refresh()

    height, width = stdscr.getmaxyx()
    text = "Fetching node list from radio..."
    x = width // 2 - len(text) // 2
    y = height // 2

    stdscr.addstr(y, x, text, curses.A_BOLD)
    stdscr.refresh()

def display_help(stdscr):
    stdscr.clear()
    help_message = [
        "=== Help ===",
        "",
        "Commands:",
        "/help - Display this help message",
        "/nodes - Display the list of nodes",
        "/msg !nodeId message - Send a private message to nodeId",
        "Ctrl-C - Quit",
        "",
        "(Press any key to return to chat)"
    ]

    help_start_y = curses.LINES - len(help_message) - 7

    for idx, line in enumerate(help_message):
        stdscr.addstr(help_start_y + idx, 2, line)

    stdscr.hline(curses.LINES - 3, 2, curses.ACS_HLINE, curses.COLS - 4)
    stdscr.refresh()
    stdscr.getch()

def on_receive(packet, interface, node_list, stdscr, input_text, message_lines):
    try:
        if packet.get('channel') != channel_index:
            return

        if 'decoded' in packet and packet['decoded'].get('portnum') == 'TEXT_MESSAGE_APP':
            message = packet['decoded']['payload'].decode('utf-8')
            fromnum = packet['fromId']
            shortname = next((node['user']['shortName'] for node in node_list if node['num'] == fromnum), 'Unknown')
            timestamp = time.strftime("%H:%M:%S")
            is_private_message = packet['toId'] != '^all'
            lines = message.splitlines()

            while len(message_lines) + len(lines) >= curses.LINES - 5:
                message_lines.pop(0)

            for line in lines:
                if is_private_message:
                    dest_shortname = next((node['user']['shortName'] for node in node_list if node['num'] == packet['toId']), 'Unknown')
                    formatted_msg = f"{timestamp} {shortname} to {packet['toId']} ({dest_shortname}) 📩 {line}"
                    message_lines.append((formatted_msg, True))
                else:
                    formatted_msg = f"{timestamp} {shortname}: {line}"
                    message_lines.append((formatted_msg, False))

            stdscr.clear()

            for idx, (msg, is_pm) in enumerate(message_lines[::-1]):
                if is_pm:
                    stdscr.addstr(curses.LINES - 4 - idx, 2, msg, curses.color_pair(2) | curses.A_BOLD)
                else:
                    stdscr.addstr(curses.LINES - 4 - idx, 2, msg)

            stdscr.hline(curses.LINES - 3, 2, curses.ACS_HLINE, curses.COLS - 4)
            stdscr.addstr(curses.LINES - 2, 2, f"{prompt_text} {input_text} ")
            stdscr.move(curses.LINES - 2, 2 + len(prompt_text) + len(input_text) + 1)

            stdscr.refresh()

    except KeyError:
        pass
    except UnicodeDecodeError as e:
        print(f"UnicodeDecodeError: {e}")

def main(stdscr):
    input_text = ""
    message_lines = []
    display_suggestions = False

    interface = None

    try:
        curses.curs_set(1)
        curses.start_color()
        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.echo()

        show_loading_screen(stdscr)

        node_info = get_node_info()
        node_list = parse_node_info(node_info)

        global prompt_text
        if node_list:
            prompt_text = f"{node_list[0]['user']['shortName']}:"
        else:
            prompt_text = "Unknown:"

        stdscr.clear()
        stdscr.refresh()
        stdscr.hline(curses.LINES - 3, 2, curses.ACS_HLINE, curses.COLS - 4)
        stdscr.addstr(curses.LINES - 2, 2, f"{prompt_text} {input_text} ")
        stdscr.move(curses.LINES - 2, 2 + len(prompt_text) + len(input_text) + 1)
        stdscr.refresh()

        def on_receive_wrapper(packet, interface):
            on_receive(packet, interface, node_list, stdscr, input_text, message_lines)

        pub.subscribe(on_receive_wrapper, "meshtastic.receive")

        interface = SerialInterface(serial_port)

        while True:
            key = stdscr.getch()
            if key != curses.ERR:
                if key == BACKSPACE:
                    if len(input_text) > 0:
                        input_text = input_text[:-1]
                        stdscr.move(curses.LINES - 2, 2 + len(prompt_text) + len(input_text))
                        stdscr.clrtoeol()  # Clear the rest of the line
                elif key == curses.KEY_ENTER or key == 10 or key == 13:
                    if input_text.strip() == '/nodes':
                        for idx, node in enumerate(node_list[::-1]):
                            formatted_msg = f"Node {node['num']}: {node['user']['shortName']}"
                            message_lines.append((formatted_msg, False))

                        while len(message_lines) >= curses.LINES - 5:
                            message_lines.pop(0)

                        input_text = ""
                    elif input_text.strip().startswith('/msg !'):
                        command_parts = input_text.strip().split(maxsplit=2)
                        if len(command_parts) >= 3:
                            nodeId = command_parts[1]
                            message = command_parts[2]
                            interface.sendText(message, nodeId, channelIndex=channel_index)
                            timestamp = time.strftime("%H:%M:%S")
                            dest_shortname = next((node['user']['shortName'] for node in node_list if node['num'] == nodeId), 'Unknown')
                            message_lines.append((f"{timestamp} {prompt_text} to {nodeId} ({dest_shortname}) 📩 {message}", True))
                            input_text = ""
                        else:
                            message_lines.append(("Invalid command format. Use '/msg !nodeId message'", False))
                            input_text = ""
                    elif input_text.strip() == '/help':
                        display_help(stdscr)
                        input_text = ""
                    elif input_text.strip():
                        interface.sendText(input_text.strip(), channelIndex=channel_index)
                        timestamp = time.strftime("%H:%M:%S")
                        message_lines.append((f"{timestamp} {prompt_text} {input_text}", False))
                        input_text = ""

                    display_suggestions = False

                    stdscr.clear()

                    for idx, (msg, is_pm) in enumerate(message_lines[::-1]):
                        if is_pm:
                            stdscr.addstr(curses.LINES - 4 - idx, 2, msg, curses.color_pair(2) | curses.A_BOLD)
                        else:
                            stdscr.addstr(curses.LINES - 4 - idx, 2, msg)

                    stdscr.hline(curses.LINES - 3, 2, curses.ACS_HLINE, curses.COLS - 4)

                elif 0 <= key <= 255:
                    input_text += chr(key)
                    display_suggestions = False

                stdscr.clear()

                for idx, (msg, is_pm) in enumerate(message_lines[::-1]):
                    if is_pm:
                        stdscr.addstr(curses.LINES - 4 - idx, 2, msg, curses.color_pair(2) | curses.A_BOLD)
                    else:
                        stdscr.addstr(curses.LINES - 4 - idx, 2, msg)

                stdscr.hline(curses.LINES - 3, 2, curses.ACS_HLINE, curses.COLS - 4)
                stdscr.addstr(curses.LINES - 2, 2, f"{prompt_text} {input_text} ")
                stdscr.move(curses.LINES - 2, 2 + len(prompt_text) + len(input_text) + 1)
                stdscr.refresh()

    except KeyboardInterrupt:
        pass
    finally:
        if interface is not None:
            interface.close()

if __name__ == "__main__":
    curses.wrapper(main)
