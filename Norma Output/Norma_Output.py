# -*- coding: utf-8 -*-
# Kapitel 4 – Norma Chat
# Python 2.7 / NAOqi
# TTS + Tablet + Gesture-cycling
# ==========================================================
# 1: Ímport af nødvendige biblioteker til interaktion.
# ==========================================================

#Import OS
import os
import time
import codecs
import base64
from naoqi import ALProxy

# ==========================================================
# 1: BILLEDE TIL TABLET
# ==========================================================
LOCAL_IMAGE_PATH = r""
if not os.path.exists(LOCAL_IMAGE_PATH):
    raise IOError("Billedfil ikke fundet: %s" % LOCAL_IMAGE_PATH)

# ==========================================================
# 2: KONFIGURATION
# ==========================================================
#Tryk på Norma's maveknap hvis du ikke tror hun er på den rigtige IP adresse. Ændre til hvad hun siger! 
ROBOT_IP   = "xxx.xxx.xxx.xxx"
ROBOT_PORT = 9559

BASE_DIR = r"C:\projects\Norma_Chat_3_UI"
RESPONSE_FILE = os.path.join(BASE_DIR, "latest_response.txt")
STATE_FILE = os.path.join(BASE_DIR, "latest_state.txt")

# ==========================================================
# 3: NAOqi PROXIES
# ==========================================================
tts       = ALProxy("ALTextToSpeech",    ROBOT_IP, ROBOT_PORT)
animation = ALProxy("ALAnimationPlayer", ROBOT_IP, ROBOT_PORT)
tablet    = ALProxy("ALTabletService",   ROBOT_IP, ROBOT_PORT)

# ==========================================================
# 4: GESTURE-OPSÆTNING
# ==========================================================
GESTURES = [
    "hello",
    "happy",
    "calm",
    "enthusiastic",
    "beseech",
    "cool",
    "bow",
    "body language",
    "exalted",
    "but"
]

interaction_count = 0
last_state = ""
last_spoken_text = ""

# ==========================================================
# 5: VIS BILLEDE PÅ TABLET (INTRO)
# ==========================================================
data = open(LOCAL_IMAGE_PATH, "rb").read()
b64 = base64.b64encode(data)

html = """
<html>
  <head>
    <meta name="viewport" content="width=device-width, initial-scale=2.0"/>
    <style>
      body {
        margin: 0; padding: 0; height: 100vh;
        display: flex; justify-content: center; align-items: center;
        background: #fff;
      }
      img {
        max-width: 200%%; max-height: 200%%;
      }
    </style>
  </head>
  <body>
    <img src="data:image/png;base64,%s"/>
  </body>
</html>
""" % b64

uri = "data:text/html;base64," + base64.b64encode(html)

animation.runTag("cloud")
tts.say("Jeg hedder Norma og du kan snakke med mig")
tablet.hideWebview()
tablet.showWebview(uri)

# ==========================================================
# 6: STARTBESKYTTELSE (UNDGÅ GAMMEL TEKST)
# ==========================================================
if os.path.exists(RESPONSE_FILE):
    last_mod_time = os.path.getmtime(RESPONSE_FILE)
else:
    last_mod_time = 0

print("Norma Chat Kapitel 4 startet – venter på input...")

# ==========================================================
# 7: HOVEDLOOP – TTS + GESTURES
# ==========================================================
while True:
    try:
        if os.path.exists(RESPONSE_FILE):
            mod_time = os.path.getmtime(RESPONSE_FILE)

            if mod_time > last_mod_time:
                with codecs.open(RESPONSE_FILE, "r", encoding="utf-8") as f:
                    text = f.read().strip()

                if text:
                    interaction_count += 1
                    print(text.encode("utf-8"))

                    # TTS
                    tts.say(text.encode("utf-8"))

                    # Gesture hver anden interaktion
                    if interaction_count % 2 == 0:
                        gesture = GESTURES[interaction_count % len(GESTURES)]
                        animation.runTag(gesture)

                last_mod_time = mod_time

        time.sleep(0.5)

    except KeyboardInterrupt:
        print("Stopper Norma Chat Kapitel 4")
        break

    except Exception as e:
        print("Fejl:", e)
        time.sleep(1)

