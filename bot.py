import socket
import os
import pynput
from pynput.keyboard import Listener, Key

import PySimpleGUI as sg

from dotenv import load_dotenv

load_dotenv()


layout = [[sg.Text("Press a key or scroll mouse")],
          [sg.Text("", size=(18, 1), key='text')],
          [sg.Button("OK", key='OK')],
          [sg.Button("START", key='START')]
          ]

window = sg.Window("Keyboard Test", layout,
                   return_keyboard_events=True, use_default_focus=False, margins=(500, 200))



def missing_env_var(var_name):
    raise ValueError(
        (
            f"Please populate the {var_name} environment variable to run the bot. "
            "See README for more details."
        )
    )


#Get the value for this here: https://twitchapps.com/tmi/
if "TWITCH_OAUTH_TOKEN" not in os.environ:
    missing_env_var("TWITCH_OAUTH_TOKEN")

if "BOT_NAME" not in os.environ:
    missing_env_var("BOT_NAME")

if "CHANNEL" not in os.environ:
    missing_env_var("CHANNEL")


TOKEN = os.getenv("TWITCH_OAUTH_TOKEN")

# Note the bot name will not be what is specified here,
# unless the OAUTH token was generated for a Twitch Account with the same name.
BOT_NAME = os.getenv("BOT_NAME")

CHANNEL = os.getenv("CHANNEL")

ENCODING = "utf-8"

# Define your own trigger for commands:
COMMAND_TRIGGER = "!"


def _handshake(server):
    print(f"Connecting to #{CHANNEL} as {BOT_NAME}")
    print(server.send(bytes("PASS " + TOKEN + "\r\n", ENCODING)))
    print(server.send(bytes("NICK " + BOT_NAME + "\r\n", ENCODING)))
    print(server.send(bytes("JOIN " + f"#{CHANNEL}" + "\r\n", ENCODING)))


def _connect_to_twitch():
    connection_data = ("irc.chat.twitch.tv", 6667)
    server = socket.socket()
    server.connect(connection_data)
    _handshake(server)
    return server


def pong(server):
    server.sendall(bytes("PONG" + "\r\n", ENCODING))


def send_message(server, msg):
    server.send(bytes("PRIVMSG " + f"#{CHANNEL}" + " :" + msg + "\n", ENCODING))


def _is_command_msg(msg):
    return msg[0] == COMMAND_TRIGGER and msg[1] != COMMAND_TRIGGER


def process_msg(irc_response):
    # TODO: improve the specificity of detecting Pings
    if "PING" in irc_response:
        pong(server)

    split_response = irc_response.split()

    if len(split_response) < 4:
        return

    user, msg = _parse_user_and_msg(irc_response)

    if _is_command_msg(msg):
        print(f"We want to run command {msg}")
    else:
        print(f"{user}: {msg}")
        text_elem.update(f"{user}: {msg}")


# TODO: refactor this sillyness
def _parse_user_and_msg(irc_response):
    user_info, _, _, *raw_msg = irc_response.split()
    raw_first_word, *raw_rest_of_the_message = raw_msg
    first_word = raw_first_word[1:]
    rest_of_the_message = " ".join(raw_rest_of_the_message)
    user = user_info.split("!")[0][1:]
    msg = f"{first_word} {rest_of_the_message}"
    return user, msg


def run_bot(server):
    chat_buffer = ""

    while True:
        chat_buffer = chat_buffer + server.recv(2048).decode("utf-8")
        messages = chat_buffer.split("\r\n")
        chat_buffer = messages.pop()

        for message in messages:
            process_msg(message)


if __name__ == "__main__":
    
    def on_press(key):
        print("Key pressed: {0}".format(key))
        if "{0}".format(key) == "Key.home":
            Listener.stop()
    
        ##commented out for now to work on GUI
        #send_message(server, "Key pressed: {0}".format(key))

    def on_release(key):
        print("Key released: {0}".format(key))
    

    # Create an event loop
    while True:
        event, values = window.read()
        text_elem = window['text']

        
        #with Listener(on_press=on_press, on_release=on_release) as listener:
        #    listener.join()

        # End program if user closes window or
        # presses the Exit button
        if event in ("OK", None):
            print(event, "exiting")
            break

        if event in ("START", None):
            print("Starting Server")
            server = _connect_to_twitch()
            run_bot(server)
            send_message(server, "Test")
        

        if len(event) == 1:
            text_elem.update(value='%s - %s' % (event, ord(event)))

        if event is not None:
            text_elem.update(event)

    window.close()
    