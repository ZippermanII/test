import socket
import sys
import re
import keypresser
import asyncio
import os
import json
import time


login_user = "";
oauth_password = ""; ###get from here http://twitchapps.com/tmi/
sock = None

def twitch_login_status(data):
    if not re.match(r'^:(testserver\.local|tmi\.twitch\.tv) NOTICE \* :Login unsuccessful\r\n$', data): return True
    else: return False

def twitch_connect():
    print("Connecting to twitch.tv");
    sock.settimeout(0.6);
    connect_host = "irc.twitch.tv";
    connect_port = 6667;
    while True:
        sock.setblocking(True)
        try:
            sock.connect((connect_host, connect_port));
            break
        except:
            print("Failed to connect to twitch");
            time.sleep (5)
            #sys.exit();
    print("Connected to twitch");
    print("Sending our details to twitch...");
    sock.send(bytes('USER {user}\r\n'.format(user=login_user),"utf-8"));
    sock.send(bytes('PASS {key}\r\n'.format(key=oauth_password),"utf-8"));
    sock.send(bytes('NICK {user}\r\n'.format(user=login_user),"utf-8"));

    if not twitch_login_status(sock.recv(1024).decode('utf-8')):
        print("... and they didn't accept our details");
        sys.exit();
    else:
        print("... they accepted our details");
        print("Connected to twitch.tv!")
        sock.send(bytes('JOIN #{user}\r\n'.format(user=login_user),"utf-8"))
        sock.recv(1024);
        sock.setblocking(False)

def check_has_message(data):
    return re.match(r'^:[a-zA-Z0-9_]+\![a-zA-Z0-9_]+@[a-zA-Z0-9_]+(\.tmi\.twitch\.tv|\.testserver\.local) PRIVMSG #[a-zA-Z0-9_]+ :.+$', data)

def parse_message(data):
    return {
        'channel': re.findall(r'^:.+\![a-zA-Z0-9_]+@[a-zA-Z0-9_]+.+ PRIVMSG (.*?) :', data)[0],
        'username': re.findall(r'^:([a-zA-Z0-9_]+)\!', data)[0],
        'message': re.findall(r'PRIVMSG #[a-zA-Z0-9_]+ :(.+)', data)[0]#######################.decode('utf-8')
    }

async def twitch_recieve_messages(amount=1024):
    while True:
        data = None
        try:
            data = await event_loop.sock_recv(sock,1024)
            data = data.decode('utf-8')
        except Exception as e:
            print(f"Exception: {e}")
            time.sleep(3)
            continue

        if not data:
            print("Lost connection to Twitch, attempting to reconnect...");
            twitch_connect();
            continue

        #ping(data)


        if check_has_message(data):
            new_messages = [parse_message(line) for line in filter(None, data.split('\r\n'))]
        else:
            continue

        if not new_messages:
            # No new messages...
            break
        else:
            for message in new_messages:
                # Wuhu we got a message. Let's extract some details from it
                comment = message['message'].lower()
                comment_author = message['username'].lower()
                print(comment_author + ": " + comment);

                # This is where you change the keys that shall be pressed and listened to.
                # The code below will simulate the key q if "q" is typed into twitch by someone
                # .. the same thing with "w"
                # Change this to make Twitch fit to your game!
                initial = comment[0]
                second = comment[-1]
                enabled_command = ["a", "b", "x", "y", "u", "d", "l", "r"]
                enabled_second = ["1", "2", "3", "4", "5", "6", "7", "8", "9"]
                if initial in enabled_command:
                    initial = 't' + initial
                    print(initial)
                    waitsecond = 0.5
                    if second in enabled_second:
                        waitsecond = int(second)
                    print(comment)
                    print("コマンドです")
                    key = int(KEYDICT[initial], 0)
                    keypress_convert(key, waitsecond, KEYDICT)
                else:
                    print(comment)




if __name__ == '__main__':

    config_json_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'config.json')
    keyditc_json_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'keydict.json')
    CONFIG = json.load(open(config_json_path))
    KEYDICT = json.load(open(keyditc_json_path))


    login_user = CONFIG["twitch_user"]
    oauth_password = CONFIG["twitch_oauth"]


    event_loop = asyncio.get_event_loop()
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM);
    keypress_convert = keypresser.keypress_convert


    twitch_connect()

    event_loop.run_until_complete(twitch_recieve_messages())


