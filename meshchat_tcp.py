import time
import curses
from pubsub import pub
from meshtastic.tcp_interface import TCPInterface

node_ip = '192.168.1.20'  # Replace with your Meshtastic node's IP address
channel_index = 0         # Replace with your channel index, usually 0

def get_node_info(node_ip):
    local = TCPInterface(hostname=node_ip)
    node_info = local.nodes
    local.close()
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

    # Calculate center position for "Fetching node list from radio..." text
    height, width = stdscr.getmaxyx()
    text = "Fetching node list from radio..."
    x = width // 2 - len(text) // 2
    y = height // 2

    stdscr.addstr(y, x, text, curses.A_BOLD)
    stdscr.refresh()

def display_help(stdscr):
    # Clear the screen
    stdscr.clear()

    # Display help message
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

    # Calculate position to display help message above the horizontal line
    help_start_y = curses.LINES - len(help_message) - 7  # Adjust for padding and horizontal line

    for idx, line in enumerate(help_message):
        stdscr.addstr(help_start_y + idx, 2, line)

    # Insert a solid horizontal line with padding
    stdscr.hline(curses.LINES - 3, 2, curses.ACS_HLINE, curses.COLS - 4)  # 2 spaces padding on each side

    stdscr.refresh()
    stdscr.getch()  # Wait for key press

def on_receive(packet, interface, node_list, stdscr, input_text, message_lines):
    try:
        if 'decoded' in packet and packet['decoded'].get('portnum') == 'TEXT_MESSAGE_APP':
            # Check if the packet is from the specified channel_index
            if packet.get('channel') != channel_index:
                return

            message = packet['decoded']['payload'].decode('utf-8')
            fromnum = packet['fromId']
            shortname = next((node['user']['shortName'] for node in node_list if node['num'] == fromnum), 'Unknown')
            timestamp = time.strftime("%H:%M:%S")

            # Determine if it's a private message (toId is not ^all)
            is_private_message = packet['toId'] != '^all'

            # Split message into lines
            lines = message.splitlines()

            # Push existing messages up
            while len(message_lines) + len(lines) >= curses.LINES - 5:  # -5 to leave space for the horizontal line, input line, and padding
                message_lines.pop(0)

            # Add each line of the message with timestamp
            for line in lines:
                if is_private_message:
                    dest_shortname = next((node['user']['shortName'] for node in node_list if node['num'] == packet['toId']), 'Unknown')
                    formatted_msg = f"{timestamp} {shortname} to {packet['toId']} ({dest_shortname}) 📩 {line}"
                    message_lines.append((formatted_msg, True))  # Store as tuple with PM flag
                else:
                    formatted_msg = f"{timestamp} {shortname}: {line}"
                    message_lines.append((formatted_msg, False))  # Store as tuple with PM flag

            # Clear the screen
            stdscr.clear()

            # Print message lines with padding
            for idx, (msg, is_pm) in enumerate(message_lines[::-1]):  # Print from bottom to top
                if is_pm:
                    stdscr.addstr(curses.LINES - 4 - idx, 2, msg, curses.color_pair(2) | curses.A_BOLD)  # 2 spaces padding and 1 line of padding
                else:
                    stdscr.addstr(curses.LINES - 4 - idx, 2, msg)  # 2 spaces padding and 1 line of padding

            # Insert a solid horizontal line with padding
            stdscr.hline(curses.LINES - 3, 2, curses.ACS_HLINE, curses.COLS - 4)  # 2 spaces padding on each side

            # Set the input line with padding
            stdscr.addstr(curses.LINES - 2, 2, f"{prompt_text} {input_text} ")
            stdscr.move(curses.LINES - 2, 2 + len(prompt_text) + len(input_text) + 1)

            # Refresh the screen
            stdscr.refresh()

    except KeyError:
        # Ignore KeyError for packets without 'decoded' key or 'channel' key
        pass
    except UnicodeDecodeError as e:
        print(f"UnicodeDecodeError: {e}")

def main(stdscr):
    showcounter = 0

    input_text = ""
    message_lines = []
    suggestions = []
    display_suggestions = False

    try:
        # Initialize curses settings
        curses.curs_set(1)  # Show cursor
        curses.start_color()
        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)  # Default color
        curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)  # Yellow for PMs

        # Enable echo mode explicitly
        curses.echo()

        # Show loading screen while retrieving node information
        show_loading_screen(stdscr)

        # Retrieve and parse node information
        node_info = get_node_info(node_ip)
        node_list = parse_node_info(node_info)

        # Use the first node's short name as the prompt if available
        global prompt_text
        if node_list:
            prompt_text = f"{node_list[0]['user']['shortName']}:"  # Adjust prompt formatting here
        else:
            prompt_text = "Unknown:"  # Fallback if node list is empty

        # Clear loading screen and refresh
        stdscr.clear()
        stdscr.refresh()

        # Insert a solid horizontal line with padding
        stdscr.hline(curses.LINES - 3, 2, curses.ACS_HLINE, curses.COLS - 4)  # 2 spaces padding on each side

        # Set the input line prompt with padding
        stdscr.addstr(curses.LINES - 2, 2, f"{prompt_text} {input_text} ")
        stdscr.move(curses.LINES - 2, 2 + len(prompt_text) + len(input_text) + 1)
        stdscr.refresh()

        # Subscribe the callback function to message reception
        def on_receive_wrapper(packet, interface):
            on_receive(packet, interface, node_list, stdscr, input_text, message_lines)

        pub.subscribe(on_receive_wrapper, "meshtastic.receive")

        # Set up the TcpInterface for message listening
        local = TCPInterface(hostname=node_ip)

        # Main loop for user interaction
        while True:
            key = stdscr.getch()
            if key != curses.ERR:
                if key in (curses.KEY_BACKSPACE, 127, 8):  # Check for backspace, delete, and Ctrl+H
                    if len(input_text) > 0:
                        # Delete character from input_text
                        input_text = input_text[:-1]
                        display_suggestions = False

                elif key == curses.KEY_ENTER or key == 10 or key == 13:
                    if input_text.strip() == '/nodes':
                        # Display nodes
                        for idx, node in enumerate(node_list[::-1]):  # Print from bottom to top
                            formatted_msg = f"Node {node['num']}: {node['user']['shortName']}"
                            message_lines.append((formatted_msg, False))

                        # Push existing messages up
                        while len(message_lines) >= curses.LINES - 5:
                            message_lines.pop(0)

                        # Clear the input line
                        input_text = ""

                    elif input_text.strip().startswith('/msg !'):
                        # Extract nodeId and message from input
                        command_parts = input_text.strip().split(maxsplit=2)
                        if len(command_parts) >= 3:
                            nodeId = command_parts[1]
                            message = command_parts[2]
                            # Send private message
                            local.sendText(message, nodeId, channelIndex=channel_index)
                            # Display own message immediately
                            timestamp = time.strftime("%H:%M:%S")
                            dest_shortname = next((node['user']['shortName'] for node in node_list if node['num'] == nodeId), 'Unknown')
                            message_lines.append((f"{timestamp} {prompt_text} to {nodeId} ({dest_shortname}) 📩 {message}", True))  # Store as tuple with PM flag
                            input_text = ""
                        else:
                            message_lines.append(("Invalid command format. Use '/msg !nodeId message'", False))

                    elif input_text.strip() == '/help':
                        # Show help screen
                        display_help(stdscr)
                        input_text = ""

                    else:
                        # Send public message
                        local.sendText(input_text, channelIndex=channel_index)
                        # Display own message immediately
                        timestamp = time.strftime("%H:%M:%S")
                        message_lines.append((f"{timestamp} {prompt_text} {input_text}", False))
                        input_text = ""

                    # Push existing messages up
                    while len(message_lines) >= curses.LINES - 5:
                        message_lines.pop(0)

                    display_suggestions = False  # Reset suggestions after sending a message

                elif key == curses.KEY_UP:
                    if showcounter == 0:
                        showcounter = len(message_lines)
                    if showcounter > 1:
                        showcounter -= 1

                elif key == curses.KEY_DOWN:
                    if showcounter < len(message_lines) - 1:
                        showcounter += 1

                else:
                    input_text += chr(key)
                    display_suggestions = True  # Show suggestions on input

                # Clear the screen
                stdscr.clear()

                # Display message lines
                for idx, (msg, is_pm) in enumerate(message_lines[-showcounter:][::-1]):  # Print from bottom to top
                    if is_pm:
                        stdscr.addstr(curses.LINES - 4 - idx, 2, msg, curses.color_pair(2) | curses.A_BOLD)  # 2 spaces padding and 1 line of padding
                    else:
                        stdscr.addstr(curses.LINES - 4 - idx, 2, msg)  # 2 spaces padding and 1 line of padding

                # Insert a solid horizontal line with padding
                stdscr.hline(curses.LINES - 3, 2, curses.ACS_HLINE, curses.COLS - 4)  # 2 spaces padding on each side

                # Set the input line with padding
                stdscr.addstr(curses.LINES - 2, 2, f"{prompt_text} {input_text} ")
                stdscr.move(curses.LINES - 2, 2 + len(prompt_text) + len(input_text) + 1)

                # Display suggestions if applicable
                if display_suggestions:
                    # Add code to display suggestions based on input_text
                    pass

                stdscr.refresh()

    except KeyboardInterrupt:
        pass
    finally:
        # Ensure the interface is closed on exit
        if local:
            local.close()

if __name__ == "__main__":
    curses.wrapper(main)
