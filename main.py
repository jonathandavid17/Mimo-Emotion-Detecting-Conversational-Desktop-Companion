import cv2
from deepface import DeepFace
import serial
import time
from mimo_ai import generate_response, continue_conversation
import threading
from mimo_voice import speak
from mimo_listen import listen


PORT = 'COM6'
BAUD_RATE = 9600

try:
    esp32 = serial.Serial(PORT, BAUD_RATE, timeout=0.1)
    time.sleep(2)
    print(f"Connected successfully to Arduino on {PORT}")

except Exception as e:
    print(f"Could not open {PORT}: {e}")
    esp32 = None
# ==========================================
# MIMO RESPONSES
# ==========================================


# ==========================================
# OPENCV VERSION
# ==========================================

print("OpenCV version:", cv2.__version__)


# ==========================================
# CAMERA SETUP
# ==========================================

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Camera failed to open.")
    raise SystemExit


# ==========================================
# EMOTION DETECTION SETTINGS
# ==========================================

analysis_interval = 0.5
last_analysis = 0

current_emotion = "Waiting..."


last_mimo_emotion = None
current_response = ""
mimo_state = "DETECTING"
session_emotion = None


emotion_streaks = {}
CONFIRMATION_THRESHOLD = 5

gemini_generating = False

gemini_lock = threading.Lock()


def request_mimo_response(emotion):
    global current_response, gemini_generating

    gemini_generating = True

    print("GEMINI: Requesting response...", flush=True)

    try:
        result = generate_response(emotion)
        current_response = result["response"]
        mimo_emotion = result["emotion"]

        print("MIMO:", result, flush=True)

        if esp32 is not None and esp32.is_open:
            esp32.write((mimo_emotion + "\n").encode("utf-8"))

        speak(current_response)
        mimo_conversation()

    except Exception:
        import traceback
        traceback.print_exc()
        current_response = "I'm having trouble connecting!"
        speak(current_response)
    finally:
        gemini_generating = False
        gemini_lock.release()


def mimo_conversation():
    global current_response

    while True:

        # Listen to the user
        user_message = listen()

        # Stop if no speech was detected
        if user_message is None:
            print("MIMO: I didn't catch that. Could you repeat?")
            speak("I didn't catch that. Could you repeat?")
            continue

        # End conversation
        if user_message.lower() in ["goodbye mimo", "stop", "exit"]:
            speak("Goodbye! Talk to you later.")
            break

        # Get Gemini's response
        reply = continue_conversation(user_message)

        current_response = reply["response"]
        mimo_emotion = reply["emotion"]

        # Update OLED expression
        if esp32 is not None and esp32.is_open:
            esp32.write((mimo_emotion + "\n").encode("utf-8"))

        # Make Mimo speak
        speak(current_response)


# ==========================================
# MAIN LOOP
# ==========================================

try:

    while cap.isOpened():

        success, frame = cap.read()

        if not success:
            print("Camera failed to read a frame.")
            break

        # Mirror webcam
        frame = cv2.flip(frame, 1)

        current_time = time.time()

        # Analyze at most once per interval
        if mimo_state == "DETECTING" and current_time - last_analysis >= analysis_interval:

            # Update timer immediately so failed detections
            # do not cause analysis on every camera frame.
            last_analysis = current_time

            try:

                # Resize for faster analysis
                small = cv2.resize(
                    frame,
                    (
                        480,
                        int(frame.shape[0] * 480 / frame.shape[1])
                    )
                )

                # DeepFace handles face detection and emotion analysis
                result = DeepFace.analyze(
                    small,
                    actions=["emotion"],
                    detector_backend="retinaface",
                    enforce_detection=True,
                    silent=True
                )

                emotion = result[0]["dominant_emotion"]

                print("FRAME:", emotion, flush=True)

                if emotion not in emotion_streaks:
                    emotion_streaks[emotion] = 0

                emotion_streaks[emotion] = min(
                    emotion_streaks[emotion] + 1, CONFIRMATION_THRESHOLD)

                # Keep the latest five successful predictions

                # Wait for enough predictions before deciding
                if emotion_streaks[emotion] >= CONFIRMATION_THRESHOLD:

                    current_emotion = emotion

                    for other_emotion in emotion_streaks:
                        if other_emotion != emotion:
                            emotion_streaks[other_emotion] = 0

                    # Respond only when the detected emotion changes
                    if current_emotion != last_mimo_emotion:

                        # Start Gemini in a separate thread

                        if gemini_lock.acquire(blocking=False):
                            last_mimo_emotion = current_emotion

                            session_emotion = current_emotion
                            mimo_state = "CONVERSING"
                            threading.Thread(
                                target=request_mimo_response,
                                args=(current_emotion,),
                                daemon=True
                            ).start()

                        print(
                            "MIMO:",
                            current_emotion,
                            "->",
                            current_response,
                            flush=True
                        )

            except Exception as e:

                # Keep the previous emotion on a failed detection
                print(
                    "FACE ANALYSIS FAILED:",
                    str(e),
                    flush=True
                )

        # ==========================================
        # DISPLAY
        # ==========================================

        cv2.putText(
            frame,
            "Emotion: " + current_emotion,
            (30, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2
        )

        mimo_display = current_response

        cv2.putText(
            frame,
            "Mimo: " + mimo_display,
            (30, 90),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0),
            2
        )

        cv2.imshow(
            "Mimo Emotion Detection",
            frame
        )

        # Press Q to quit
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

finally:

    # Always release the camera
    cap.release()
    cv2.destroyAllWindows()
