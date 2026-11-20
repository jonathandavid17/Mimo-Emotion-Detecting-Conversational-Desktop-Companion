import speech_recognition as sr

recognizer = sr.Recognizer()
recognizer.pause_threshold = 1.2
recognizer.phrase_threshold = 0.3
recognizer.non_speaking_duration = 0.5
recognizer.dynamic_energy_threshold = True
recognizer.dynamic_energy_adjustment_ratio = 1.5


def listen():
    try:
        with sr.Microphone() as source:

            print("MIMO: Listening...", flush=True)

            recognizer.adjust_for_ambient_noise(
                source,
                duration=0.5
            )

            audio = recognizer.listen(
                source,
                timeout=10,
                phrase_time_limit=30
            )

        print("MIMO: Processing...", flush=True)

        text = recognizer.recognize_google(audio, language="en-US")

        print("RECOGNIZED TEXT:", repr(text), flush=True)
        print("WORD COUNT:", len(text.split()), flush=True)

        return text

        print("YOU:", text, flush=True)

        return text

    except sr.WaitTimeoutError:
        print("MIMO: No speech detected.")
        return None

    except sr.UnknownValueError:
        print("MIMO: I couldn't understand that.")
        return None

    except sr.RequestError as e:
        print("MIMO: Recognition service error:", e)
        return None


if __name__ == "__main__":

    with sr.Microphone() as source:
        print("MIMO: Calibrating microphone...", flush=True)
        recognizer.adjust_for_ambient_noise(source, duration=1)

    print("MIMO: Ready!", flush=True)
    while True:
        result = listen()

        if result:
            if result.lower() in ["stop", "exit", "quit"]:
                print("MIMO: Goodbye!")
                break
