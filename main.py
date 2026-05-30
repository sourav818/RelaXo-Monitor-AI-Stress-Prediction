import serial
import cv2
from deepface import DeepFace
import time
import pickle
import pandas as pd
from datetime import datetime
import os
import numpy as np
import sounddevice as sd
from openai import OpenAI
from twilio.rest import Client
import firebase_admin
from firebase_admin import credentials, firestore

# PATH
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "data.csv")

# FIREBASE
cred = credentials.Certificate("firebase_key.json")

firebase_admin.initialize_app(cred)

db = firestore.client()

# OPENAI
client = OpenAI(api_key="Your OpenAI API Key")

# TWILIO
account_sid = "sid account"
auth_token = "token"

twilio_client = Client(account_sid, auth_token)

twilio_number = "Number"
your_number = "your number"

# SERIAL
try:
    ser = serial.Serial('COM7', 9600)
    time.sleep(2)
except:
    print("❌ Serial not connected")
    exit()

# CAMERA
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("❌ Camera not working")
    exit()

# FACE
face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
)

# MODEL
model = pickle.load(open(os.path.join(BASE_DIR, 'model.pkl'), 'rb'))

# CSV INIT
COLUMNS = ['Time','BPM','Temp','Humidity',
           'Emotion','Movement','Voice',
           'Stress','Suggestion']

if not os.path.exists(CSV_PATH):
    pd.DataFrame(columns=COLUMNS).to_csv(CSV_PATH, index=False)

# VARIABLES
last_emotion = "Detecting..."
prev_gray = None
last_emotion_time = 0
last_voice_time = 0
last_ai_time = 0
last_sms_time = 0
last_stress = ""

voice = "LOW"
suggestion = "Stay calm and relax."

# VOICE FUNCTION
def get_voice_stress():
    try:
        audio = sd.rec(int(0.5 * 16000), samplerate=16000, channels=1)
        sd.wait()
        volume = np.linalg.norm(audio)
        return "HIGH" if volume > 0.8 else "LOW"
    except:
        return "LOW"

# OPENAI AI SUGGESTION
def get_ai_suggestion(stress, emotion, bpm):

    prompt = f"""
    Stress Level: {stress}
    Emotion: {emotion}
    BPM: {bpm}

    Give one short wellness suggestion.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=30
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        print("OpenAI Error:", e)
        return "Stay calm and relax."

# SMS ALERT
def send_sms_alert(stress, bpm, emotion):

    try:

        twilio_client.messages.create(

            body=f"""
⚠ HIGH STRESS ALERT

Stress: {stress}
BPM: {bpm}
Emotion: {emotion}

Please relax and take a break.
""",

            from_=twilio_number,
            to=your_number
        )

        print("✅ SMS Sent")

    except Exception as e:
        print("SMS Error:", e)

# MAIN LOOP
while True:

    # CAMERA
    ret, frame = cap.read()
    if not ret:
        continue

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # SERIAL READ
    try:
        data = ser.readline().decode().strip()
        parts = data.split(",")

        if len(parts) == 3:
            bpm, temp, hum = map(float, parts)
        else:
            bpm, temp, hum = 0, 0, 0
    except:
        bpm, temp, hum = 0, 0, 0

    # FACE DETECTION
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)
    emotion = last_emotion

    # EMOTION (every 2 sec)
    if len(faces) > 0 and time.time() - last_emotion_time > 2:
        try:
            result = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)
            emotion = result[0]['dominant_emotion']
            last_emotion = emotion
            last_emotion_time = time.time()
        except:
            emotion = last_emotion

    # MOVEMENT
    movement_score = 0
    if prev_gray is not None:
        diff = cv2.absdiff(prev_gray, gray)
        movement_score = diff.mean()
    prev_gray = gray

    movement = "HIGH" if movement_score > 15 else "LOW"

    # VOICE (every 2 sec)
    if time.time() - last_voice_time > 2:
        voice = get_voice_stress()
        last_voice_time = time.time()

    # SAVE DATA
    if 50 <= bpm <= 150:

        pred = model.predict([[bpm, temp]])[0]
        stress = ["LOW","MEDIUM","HIGH"][pred]

        # FUSION LOGIC
        if emotion in ["angry","fear","sad"]:
            stress = "HIGH"

        if movement == "HIGH" and bpm > 85:
            stress = "HIGH"

        if voice == "HIGH":
            stress = "HIGH"

        # SEND SMS ONLY EVERY 5 MIN
        if stress == "HIGH" and time.time() - last_sms_time > 300:

            send_sms_alert(stress, bpm, emotion)

            last_sms_time = time.time()

        # OPENAI AI SUGGESTION
        # only when stress changes OR every 2 min
        if stress != last_stress or time.time() - last_ai_time > 120:

            suggestion = get_ai_suggestion(stress, emotion, bpm)

            last_ai_time = time.time()
            last_stress = stress

        new_data = pd.DataFrame([[datetime.now(), bpm, temp, hum,
                                  emotion, movement, voice,
                                  stress, suggestion]],
                                columns=COLUMNS)

        # SAFE SAVE (retry)
        for _ in range(3):
            try:
                new_data.to_csv(CSV_PATH, mode='a', header=False, index=False)

                # FIREBASE SAVE
                db.collection("stress_data").add({

                    "bpm": bpm,
                    "temp": temp,
                    "humidity": hum,
                    "emotion": emotion,
                    "movement": movement,
                    "voice": voice,
                    "stress": stress,
                    "suggestion": suggestion,
                    "time": str(datetime.now())

                })

                print(f"✅ Saved | BPM:{bpm} Temp:{temp} "
                      f"Move:{movement} Voice:{voice} Stress:{stress}")

                break

            except:
                print("⚠ CSV busy, retrying...")
                time.sleep(0.2)

    else:
        stress = "--"
        suggestion = "--"

    # DISPLAY
    cv2.putText(frame, f"BPM: {bpm}", (10,30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)

    cv2.putText(frame, f"Temp: {temp}", (10,60),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,0,0), 2)

    cv2.putText(frame, f"Emotion: {emotion}", (10,90),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,0), 2)

    cv2.putText(frame, f"Move: {movement}", (10,120),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)

    cv2.putText(frame, f"Voice: {voice}", (10,150),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)

    cv2.putText(frame, f"Stress: {stress}", (10,180),
                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0,0,255), 2)

    cv2.putText(frame, f"AI Tip: {suggestion[:45]}", (10,210),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,255), 2)

    cv2.imshow("AI Stress Detection System", frame)

    if cv2.waitKey(1) == 27:
        break

# CLEANUP
cap.release()
cv2.destroyAllWindows()
ser.close()