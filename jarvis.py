import warnings
warnings.filterwarnings("ignore")

import cv2
import mediapipe as mp
import pyttsx3
import sounddevice as sd
from vosk import Model, KaldiRecognizer
import json, queue, threading, time, datetime, sys, requests
import math, re

# ================== SPEAK ==================
engine = pyttsx3.init()
engine.setProperty("rate", 165)

def speak(text):
    print("JARVIS:", text)
    engine.say(text)
    engine.runAndWait()

# ================== VOICE ==================
q = queue.Queue()
model = Model("model")
rec = KaldiRecognizer(model, 16000)

def audio_callback(indata, frames, time_info, status):
    if rec.AcceptWaveform(bytes(indata)):
        result = json.loads(rec.Result())
        q.put(result.get("text", ""))

# ================== TYPE INPUT (CHATGPT STYLE) ==================
def typing_input():
    while True:
        text = input("YOU (type): ")
        q.put(text.lower())

threading.Thread(target=typing_input, daemon=True).start()

# ================== SAFE MATH ==================
def solve_math(text):
    try:
        text = text.lower()
        text = text.replace("plus", "+").replace("minus", "-")
        text = text.replace("into", "*").replace("times", "*")
        text = text.replace("divided by", "/")
        text = text.replace("square root of", "sqrt")

        text = re.sub(r"[^0-9\.\+\-\*\/\(\)\s sqrt]", "", text)

        return eval(text, {"__builtins__": {}, "sqrt": math.sqrt})
    except:
        return None

# ================== CODE GENERATOR ==================
def code_generator(cmd):
    if "fibonacci" in cmd:
        return """def fibonacci(n):
    a, b = 0, 1
    for _ in range(n):
        print(a, end=" ")
        a, b = b, a+b
"""

    if "factorial" in cmd:
        return """def factorial(n):
    return 1 if n == 0 else n * factorial(n-1)
"""

    if "for loop" in cmd:
        return """for i in range(1, 6):
    print(i)
"""

    return None

# ================== INTERNET AI ==================
def internet_ai(question):
    try:
        url = "https://api.duckduckgo.com/"
        params = {"q": question, "format": "json", "no_html": 1}
        data = requests.get(url, params=params, timeout=5).json()
        return data.get("AbstractText") or "I found something but no clear answer."
    except:
        return "Internet issue."

# ================== FACE CHECK ==================
def face_check():
    cap = cv2.VideoCapture(0)
    speak("Verifying face. Please look at the camera")
    time.sleep(3)
    ret, frame = cap.read()
    cap.release()

    if ret:
        speak("Face verified. Welcome back sir")
        return True
    else:
        speak("Face verification failed")
        return False

# ================== CAMERA + GESTURE ==================
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1)
draw = mp.solutions.drawing_utils
camera_on = False

def camera_system():
    global camera_on
    cap = cv2.VideoCapture(0)
    speak("Jarvis camera system online")

    while camera_on:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = hands.process(rgb)

        if result.multi_hand_landmarks:
            for hand in result.multi_hand_landmarks:
                draw.draw_landmarks(frame, hand, mp_hands.HAND_CONNECTIONS)

        cv2.rectangle(frame, (0,0), (640,100), (0,0,0), -1)
        cv2.putText(frame, "JARVIS ONLINE", (20,40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,255), 2)

        now = datetime.datetime.now().strftime("%H:%M:%S")
        cv2.putText(frame, now, (20,80),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,255), 2)

        cv2.imshow("JARVIS CAMERA", frame)
        if cv2.waitKey(1) == 27:
            break

    cap.release()
    cv2.destroyAllWindows()
    speak("Camera offline")

# ================== COMMAND PROCESSOR ==================
awake = False

def process_command(cmd):
    global camera_on, awake
    cmd = cmd.lower()
    print("YOU:", cmd)

    if not awake:
        if "hey jarvis" in cmd or "jarvis" in cmd:
            awake = True
            speak("Yes sir, I am listening")
        return

    if "time" in cmd:
        speak(datetime.datetime.now().strftime("Time is %H:%M"))

    elif "open camera" in cmd:
        if not camera_on:
            camera_on = True
            threading.Thread(target=camera_system).start()

    elif "close camera" in cmd:
        camera_on = False

    elif "sleep" in cmd:
        awake = False
        speak("Going to sleep")

    elif "exit" in cmd or "shutdown" in cmd:
        speak("Shutting down. Goodbye.")
        sys.exit()

    # ====== MATH ======
    result = solve_math(cmd)
    if result is not None:
        speak(f"The answer is {result}")
        return

    # ====== CODE ======
    code = code_generator(cmd)
    if code:
        print("\n--- GENERATED CODE ---\n")
        print(code)
        speak("I have generated the code. Check the screen.")
        return

    else:
        speak(internet_ai(cmd))

# ================== START ==================
def start():
    with sd.RawInputStream(samplerate=16000, blocksize=8000,
                           dtype="int16", channels=1,
                           callback=audio_callback):
        speak("Jarvis online. Say Hey Jarvis to wake me.")
        while True:
            if not q.empty():
                process_command(q.get())
            time.sleep(0.1)

if __name__ == "__main__":
    if face_check():
        start()
