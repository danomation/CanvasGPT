import os
from openai import OpenAI
#some of these are probably not needed.
from dotenv import load_dotenv
import secrets
import ssl
import requests
import json
from operator import itemgetter
import asyncio
import time
from random import *
import re
from threading import Timer
import queue

from flask import request, session, Flask, send_file, jsonify
from flask_socketio import SocketIO, Namespace, disconnect

import base64

import cv2
import numpy as np

##
# Danomation
# GitHub: https://github.com/danomation
# Patreon https://www.patreon.com/Wintermute310
##

#env variables
load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')
CANVAS_GPT_PORT = 6969
# these should end in /
IMAGES_PATH = "/var/www/html/images/" #replace with your path
IMAGES_URL = "https://127.0.0.1/images/" #replace 127.0.0.1 with your webserver address


#init openai client
client = OpenAI(api_key=OPENAI_API_KEY)

app = Flask("CanvasVision")
socketio = SocketIO(app, cors_allowed_origins="*")

from flask_cors import CORS
CORS(app, resources={r"/*": {"origins": "*"}})

#yes, you must have SSL certs! use letsencrypt if you want.
ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
ssl_context.check_hostname = False
ssl_cert = "/path/to/your/fullchain.pem"
ssl_key = "/path/to/your/privkey.pem"
ssl_context.load_cert_chain(ssl_cert, keyfile=ssl_key)

history = []
@app.errorhandler(Exception)
def handle_exception(e):
    if isinstance(e, HTTPException):
        return e
    return render_template("500_generic.html", e=e), 500

prompt_list = ["Pyramid",
"Phone",
"Wallet",
"Keys",
"Pen",
"Notebook",
"Coffee mug",
"Sunglasses",
"Water bottle",
"Watch",
"Laptop",
"Backpack",
"Toothbrush",
"Television",
"Shampoo",
"Soap",
"Chair",
"Fork",
"Knife",
"Spoon",
"Plate",
"Pillow",
"Bed",
"Towels",
"Headphones",
"Microwave",
"Refrigerator",
"Oven",
"Toaster",
"Remote control",
"Shoes",
"T-shirt",
"Jeans",
"Glasses",
"Hat",
"Book",
"Toothpaste",
"Hairbrush",
"Umbrella",
"Earbuds",
"Trash can",
"Blanket",
"Desk",
"Calendar",
"Lamp",
"Hand sanitizer",
"Tissues",
"Clock",
"Comb",
"Socks",
"Belt",
"Scissors",
"Notebook",
"Stapler",
"Computer mouse",
"Printer",
"Paper clips",
"Rubber bands",
"Glue stick",
"Tape dispenser",
"Highlighter",
"Calculator",
"Ruler",
"Envelopes",
"Post-it notes",
"Binder",
"Hole punch",
"Index cards",
"Whiteboard marker",
"Calendar",
"Desk organizer",
"File folder",
"Drawer dividers",
"Clipboard",
"Wastebasket",
"Push pins",
"Corkboard",
"Label maker",
"Desk lamp",
"Paper shredder",
"Charging cable",
"Webcam",
"External hard drive",
"USB flash drive",
"Desk fan",
"Mouse pad",
"Pencil holder",
"Magazine rack",
"Document tray",
"Bookend",
"Surge protector",
"Monitor stand",
"Keyboard",
"Briefcase",
"Laptop stand",
"Smart speaker",
"Tea coaster",
"Plant pot",
"Camera",
"Fitness tracker",
"Stress ball",
"Broom",
"Candle",
"Dice",
"Envelope",
"Flip flops",
"Glasses",
"Helmet",
"Iron",
"Jack-in-the-box",
"Kettle",
"Lemon",
"Mittens",
"Notebook",
"Orange",
"Paintbrush",
"Quilt",
"Rubber duck",
"Scarecrow",
"Television",
"Unicorn",
"Vuvuzela",
"Waffle",
"Xylophone mallet",
"Yacht",
"Zipper",
"Acorn",
"Ball",
"Croissant",
"Drum",
"Eiffel Tower",
"Feather",
"Gift box",
"Hanger",
"Ice skate",
"Jellyfish",
"Kangaroo",
"Ladder",
"Maple leaf",
"Nightcap",
"Oar",
"Popsicle",
"Question mark",
"Robot",
"Sunglasses",
"Trophy",
"Unicycle",
"Violin bow",
"Whistle",
"Zucchini",
"Apple",
"Banana",
"Car",
"Dog",
"Elephant",
"Fish",
"Grapes",
"House",
"Ice cream cone",
"Jar",
"Kite",
"Leaf",
"Moon",
"Necklace",
"Orange",
"Pizza",
"Chess piece",
"Rose",
"Sun",
"Tree",
"Umbrella",
"Violin",
"Windmill",
"Xylophone",
"Yak",
"Zebra",
"Airplane",
"Boat",
"Cup",
"Duck",
"Egg",
"Frog",
"Guitar",
"Hammer",
"Igloo",
"Juice box",
"Key",
"Lollipop",
"Mushroom",
"Nail",
"Owl",
"Pencil",
"Quill",
"Ring",
"Snake",
"Teapot",
"Vase",
"Watch",
"Anchor",
"Barbell",
"Compass",
"Dumpling",
"Elevator buttons",
"Flashlight",
"Garden gnome",
"Harmonica",
"Inkwell",
"Jigsaw puzzle",
"Koi fish",
"Lava lamp",
"Motorcycle",
"Nutcracker",
"Origami crane",
"Pinwheel",
"Queen",
"Raccoon",
"Saxophone",
"Trowel",
"Ukulele",
"Vent",
"Wind chime",
"X-ray",
"Yo-yo string",
"Zither",
"Apple core",
"Bookshelf",
"Cactus",
"Dart",
"Escalator",
"Fishing rod",
"Gumball machine",
"Hamburger",
"Ice pack",
"Jingle bell",
"Kiwi",
"Lightbulb",
"Mop",
"Nose",
"Oboe",
"Pumpkin",
"Quiver",
"Rainbow",
"Sandcastle",
"Turkey",
"USB cable",
"Velvet ribbon",
"Window",
"Zeppelin",
"Accordion",
"Bingo card",
"Croquet mallet",
"Dandelion",
"Espresso machine",
"Fedora hat",
"Gazebo",
"Hourglass",
"Incense burner",
"Javelin",
"Kaleidoscope",
"Lighthouse",
"Mandolin",
"Nectarine",
"Oscilloscope",
"Pterodactyl",
"Quiche",
"Roulette wheel",
"Sushi roll",
"Typewriter",
"Ukulele",
"Volleyball net",
"Wishing well",
"Yearbook",
"Artichoke",
"Bass drum",
"Compass rose",
"Dumbbell",
"Etch A Sketch",
"Flamingo",
"Gear",
"Harpsichord",
"Isoceles triangle",
"Jackal",
"Log cabin",
"Observatory",
"Pomegranate",
"Harbor",
"Rowboat",
"Sabertooth Tiger",
"Tardigrade",
"Unicycle",
"Vignette",
"Wagon wheel",
"Yurt",
"Amphitheater",
"Diffraction pattern",
"Electrocardiogram",
"Fractal",
"Gyroscope",
"Labyrinth",
"Hypercube",
"Orrery",
"Particle accelerator",
"Bow",
"Recurved bow",
"Seismogram",
"Tesla coil",
"Organ",
"Heart",
"Wormhole",
"Telescope",
"DNA helix",
"Espresso",
"lens",
"Harp",
"Gate",
"planet",
"probe",
"Maelstrom",
"lake",
"Star",
"Crystal",
"Supernova",
"Lizard",
"algae",
"Water",
"Yaw",
"Zodiac",
"black hole",
"processor",
"wave",
"Hydrofoil",
"Life",
"Neural network",
"mountain",
"painting",
"Vexillology",
"Xenomorph",
"Arm",
"Head",
"Biofilm",
"Jet engine",
"Squid",
"Cloud",
"Neocortex",
"Brain",
"Obelisk",
"Phage",
"Trebuchet",
"Escapement",
]

user_sessions = {}
image_queue = queue.Queue()

def gethighscore():
    filePath = IMAGES_PATH + "scores.json"
    f = open(filePath, "r")
    scores = json.load(f)
    f.close()
    x = 0
    i = 0
    for score in scores:
        print("checking item number " + str(i))
        if score["score"] > x:
            print("score " + str(score["score"]) + " is larger than last. setting y = " + str(i))
            x = score["score"]
            y = i
        i += 1
    return scores[y]["name"], scores[y]["score"]

def sethighscore(name, score):
    filePath = IMAGES_PATH + "scores.json"
    f = open(filePath, "r")
    scores = json.load(f)
    f.close()
    scores.append({"name" : name, "score": score})
    print(scores)
    with open(filePath, "w") as f1:
        json.dump( scores , f1 )
    f1.close()

class CanvasNamespace(Namespace):
    def __init__(self, namespace=None):
        super().__init__(namespace)
        self.user_sessions = {}
    def on_connect(self):
        #print(gethighscore())
        session['sid'] = request.sid
        name, score = gethighscore()
        print("High score is: " + name + " with score: " + str(score))
        session['highscore'] = score
        session['color'] = str(secrets.token_hex(3))
        print('-- Session ' + str(session['sid']) + ' connected to /canvas')
        session['score'] = 0;
        session['prompt'] = str(choice(prompt_list))
        dataToSend = {'type': 'text', 'data': session['prompt']}
        self.emit('prompt', dataToSend, room=session['sid'])
        dataToSend = {'type': 'text', 'data': session['highscore']}
        self.emit('highscore', dataToSend, room=session['sid'])


    def on_disconnect(self):
        print('-- Session ' + str(session['sid']) + ' disconnected from /canvas')

    def on_canvas(self, data):
        current_session = self.user_sessions[request.sid]

    def on_upload_photo(self, photoData):
        print('-- Received uploaded image file for session ' + str(session['sid']))
        imageBuffer = base64.b64decode(photoData.split(",")[1])
        filePath = IMAGES_PATH
        if not os.path.exists(filePath):
            os.makedirs(filePath)
        stamp = int(time.time())
        outputfile = f"{stamp}_image.jpg"
        filePath = os.path.join(filePath, outputfile)
        with open(filePath, "wb") as imageFile:
            imageFile.write(imageBuffer)
            print('-- File saved for session ' + str(session['sid']))
        #convert to png
        from PIL import Image
        im = Image.open(filePath)
        im.save(IMAGES_PATH + str(stamp) + "_image.png")

        #shrinkwrap image https://stackoverflow.com/questions/48395434/how-to-crop-or-remove-white-background-from-an-image
        import cv2
        import numpy as np
        img = cv2.imread(IMAGES_PATH + str(stamp) + "_image.png")
        try:
            ## (1) Convert to gray, and threshold
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            th, threshed = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY_INV)
            ## (2) Morph-op to remove noise
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11,11))
            morphed = cv2.morphologyEx(threshed, cv2.MORPH_CLOSE, kernel)
            ## (3) Find the max-area contour
            cnts = cv2.findContours(morphed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]
            cnt = sorted(cnts, key=cv2.contourArea)[-1]
            ## (4) Crop and save it
            x,y,w,h = cv2.boundingRect(cnt)
            dst = img[y-50:y+h+50, x-50:x+w+50]
            cv2.imwrite(IMAGES_PATH + str(stamp) + "_image_1.png", dst)
        except:
            print("Error forming auto-cropping")
        file3 = 0
        file2 = 0
        file1 = 0
        prompt_true = 0
        if os.path.isfile(IMAGES_PATH + str(stamp) + "_image_1.png"):
            file3 = 1
        if os.path.isfile(IMAGES_PATH + str(stamp) + "_image.png"):
            file2 = 1
        if os.path.isfile(IMAGES_PATH + str(stamp) + "_image.jpg"):
            file1 = 1

        if file3:
            try:
                response = client.chat.completions.create(
                    model="gpt-4-vision-preview",
                    messages=[
                        {"role": "user","content": [
                            {"type": "text", "text": "If you see a picture of a " + session['prompt'] + " then return " + session['prompt'] + ". If not say fail"},
                            {"type": "image_url","image_url": {"url": IMAGES_URL + str(stamp) + "_image_1.png",},},
                        ],}
                    ],max_tokens=500,
                )
                gpt_reply = str(response.choices[0].message.content).lower();
            except:
                print("openai error")
                gpt_reply = "openai error"
            if session['prompt'].lower() in gpt_reply.lower():
                prompt_true = 1
                dataToSend = {'type': 'text', 'data': "** WIN - gpt said: " + str(response.choices[0].message.content).lower() + " vs: " + session['prompt'].lower()}
                self.emit('reply', dataToSend, room=session['sid'])
            else:
                prompt_true = 0
                print("**round 1** " + str(session['sid']))
                print("** FAIL - gpt said: " + str(response.choices[0].message.content).lower() + " vs: " + session['prompt'].lower())
                dataToSend = {'type': 'text', 'data': "** FAIL 1 - gpt said: " + str(response.choices[0].message.content).lower() + " vs: " + session['prompt'].lower()}
                self.emit('reply', dataToSend, room=session['sid'])
        if file2 and prompt_true == 0:
            try:
                response = client.chat.completions.create(
                    model="gpt-4-vision-preview",
                    messages=[
                        {"role": "user","content": [
                            {"type": "text", "text": "If you see a picture of a " + session['prompt'] + " then return " + session['prompt'] + ". If not say fail"},
                            {"type": "image_url","image_url": {"url": IMAGES_URL + str(stamp) + "_image.png",},},
                        ],}
                    ],max_tokens=500,
                )
                gpt_reply = str(response.choices[0].message.content).lower();
            except:
                print("openai error")
                gpt_reply = "openai error"
            if session['prompt'].lower() in gpt_reply.lower():
                prompt_true = 2
                dataToSend = {'type': 'text', 'data': "** WIN - gpt said: " + str(response.choices[0].message.content).lower() + " vs: " + session['prompt'].lower()}
                self.emit('reply', dataToSend, room=session['sid'])
            else:
                prompt_true = 0
                print("**round 2** " + str(session['sid']))
                print("** FAIL - gpt said: " + str(response.choices[0].message.content).lower() + " vs: " + session['prompt'].lower())
                dataToSend = {'type': 'text', 'data': "** FAIL 2 - gpt said: " + str(response.choices[0].message.content).lower() + " vs: " + session['prompt'].lower()}
                self.emit('reply', dataToSend, room=session['sid'])
        if prompt_true < 1:
            if not file1 and not file2 and not file3:
                print("*** ERROR NO FILES GENERATED *** SESSION " + str(session['sid']))
            print("** session failed ** " + str(session['sid']))

        if prompt_true == 1:
            #write file
            queue_filepath = IMAGES_PATH + "queue.txt"
            queue_file = open(queue_filepath, "a")
            queue_file.write(str(IMAGES_URL + str(stamp) + "_image_1.png\n"))
            queue_file.close()
            #send success
            dataToSend = {'type': 'text', 'data': "Success! <br>Prompt was " + session['prompt'].lower()}
            self.emit('prompt', dataToSend, room=session['sid'])
            self.emit('reply', dataToSend, room=session['sid'])
            #send to discord
            url = DISCORD_WEBHOOK_URL
            data = {
                "content" : "" + str(session['sid']) + " has score: " + str(session['score']) + ".\n" + session['prompt'] + "\n " + IMAGES_URL + str(stamp) + "_image_1.png",
                "username" : "CanvasGPT"
            }
            result = requests.post(url, json = data)
            try:
                result.raise_for_status()
            except requests.exceptions.HTTPError as err:
                print(err)
            else:
                print("Image of " + session['prompt'] + " sent to discord.")
            #increment score and change prompt
            session['score'] = session['score'] + 15;
            session['prompt'] = str(choice(prompt_list))
            #send updated prompt to client
            promptupdate = {'type': 'text', 'data': session['prompt']}
            self.emit('prompt', promptupdate, room=session['sid'])
            #send updated score to client
            scoreupdate = {'type': 'text', 'data': session['score']}
            self.emit('score', scoreupdate, room=session['sid'])
            if session["score"] > session["highscore"]:
                print("New high score!")
                sethighscore("unknown", session["score"])
                highupdate = {'type': 'text', 'data': session['score']}
                self.emit('highscore', highupdate, room=session['sid'])
        elif prompt_true == 2:
            #write file
            queue_filepath = IMAGES_PATH + "queue.txt"
            queue_file = open(queue_filepath, "a")
            queue_file.write(str(IMAGES_URL + str(stamp) + "_image.png\n"))
            queue_file.close()
            #send success
            dataToSend = {'type': 'text', 'data': "Success! <br>Prompt was " + session['prompt'].lower()}
            self.emit('prompt', dataToSend, room=session['sid'])
            self.emit('reply', dataToSend, room=session['sid'])
            #send to discord
            url = DISCORD_WEBHOOK_URL
            data = {
                "content" : "" + str(session['sid']) + " has score: " + str(session['score']) + ".\n" + session['prompt'] + "\n " + IMAGES_URL + str(stamp) + "_image_1.png",
                "username" : "CanvasGPT"
            }
            result = requests.post(url, json = data)
            try:
                result.raise_for_status()
            except requests.exceptions.HTTPError as err:
                print(err)
            else:
                print("Image of " + session['prompt'] + " sent to discord.")
            #increment score and change prompt
            session['score'] = session['score'] + 10;
            session['prompt'] = str(choice(prompt_list))
            #send updated prompt to client
            promptupdate = {'type': 'text', 'data': session['prompt']}
            self.emit('prompt', promptupdate, room=session['sid'])
            #send updated score to client
            scoreupdate = {'type': 'text', 'data': session['score']}
            self.emit('score', scoreupdate, room=session['sid'])
            if session["score"] > session["highscore"]:
                print("New high score!")
                sethighscore("unknown", session["score"])
                highupdate = {'type': 'text', 'data': session['score']}
                self.emit('highscore', highupdate, room=session['sid'])
        else:
            #send failure
            if session["score"] > session["highscore"]:
                sethighscore("unknown", session["score"])
            dataToSend = {'type': 'text', 'data': "Failure! <br>Prompt was " + session['prompt'].lower()}
            self.emit('prompt', dataToSend, room=session['sid'])
            dataToSend2 = {'type': 'text', 'data': gpt_reply}
            self.emit('reply', dataToSend2, room=session['sid'])

socketio.on_namespace(CanvasNamespace('/canvas'))
socketio.run(app, host='0.0.0.0', port=CANVAS_GPT_PORT, ssl_context=ssl_context, allow_unsafe_werkzeug=True)
