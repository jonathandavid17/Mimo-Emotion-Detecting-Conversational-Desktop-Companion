import os
import time
from google import genai
from google.genai import types
import json

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise RuntimeError("GEMINI_API_KEY is missing!")

client = genai.Client(
    api_key=API_KEY,
    http_options=types.HttpOptions(
        timeout=20000,
        retry_options=types.HttpRetryOptions(
            attempts=1
        )
    )
)

chat = client.chats.create(
    model="gemini-3.5-flash-lite",
    config=types.GenerateContentConfig(
        system_instruction="""
      Personality:
       - Warm, curious, playful, and supportive.
       - Speak naturally, like a conversational companion.
       - Be attentive to what the user says.
       - Ask relevant follow-up questions.
       - Remember previous messages in the conversation.
       - Never claim to know how someone feels based only on their face.
       - Speak only one sentence max.

       OLED EMOTION:
       Choose exactly one emotion for Mimo's OLED face:
       - sad: When responding sympathetically or showing concern.
       - happy: When celebrating, encouraging, or responding positively.
       - neutral: For ordinary conversation.
       - angry: When expressing frustration, playful annoyance, or strong disagreement.

       RULES:
       - Choose expressions based on conversational context.
       - These expressions represent Mimo's reaction, not a diagnosis of the user.
       - Change expressions naturally when the conversation changes.
       - Do not force an emotional expression into every response.

       RESPONSE FORMAT:
       - Always return valid JSON.
       - Use exactly two keys: "response" and "emotion".
       - "response" must contain one natural sentence for Mimo to speak.
       - "emotion" must be exactly one of: "sad", "happy", "neutral", "angry".
       - Do not use "oled_emotion".
       - Do not include Markdown or text outside the JSON.
       """,
        max_output_tokens=256,
        response_mime_type="application/json",
        thinking_config=types.ThinkingConfig(
            thinking_level="minimal"
        )
    )
)


def process_gemini_response(response):

    try:
        data = json.loads(response.text)

        spoken_response = data["response"].strip()
        emotion = data.get("emotion", data.get(
            "oled_emotion", "neutral")).lower().strip()

        valid_emotions = [
            "sad",
            "happy",
            "neutral",
            "angry"
        ]

        if emotion not in valid_emotions:
            emotion = "neutral"

        return {
            "response": spoken_response,
            "emotion": emotion
        }

    except Exception as e:

        print("MIMO: Response parsing error:", repr(e), flush=True)

        return {
            "response": "I'm having a little trouble thinking right now!",
            "emotion": "neutral"
        }


def generate_response(emotion):
    prompt = (
        f"The user's estimated facial emotion is {emotion}. "
        "Respond naturally as Mimo."
    )

    start = time.perf_counter()

    try:
        print("Sending request to Gemini...", flush=True)

        response = chat.send_message(prompt)
        print("RESPONSE OBJECT:", response, flush=True)
        print("RESPONSE TEXT:", repr(response.text), flush=True)
        print("CANDIDATES:", response.candidates, flush=True)

        elapsed = time.perf_counter() - start

        print(f"Response received in {elapsed:.2f}s", flush=True)
        print("RAW RESPONSE:", repr(response), flush=True)
        print("TEXT:", repr(response.text), flush=True)

        return process_gemini_response(response)

    except Exception as e:
        elapsed = time.perf_counter() - start

        print(
            f"Gemini failed after {elapsed:.2f}s: {repr(e)}",
            flush=True
        )

        return {"response": "I'm having trouble connecting right now!",
                "emotion": "neutral"}


# ==========================================
# CONTINUE CONVERSATION
# ==========================================


def continue_conversation(user_message):

    start = time.perf_counter()

    try:

        print("Sending message to Gemini...", flush=True)

        response = chat.send_message(user_message)

        elapsed = time.perf_counter() - start

        print(
            f"Response received in {elapsed:.2f}s",
            flush=True
        )

        return process_gemini_response(response)

    except Exception as e:

        elapsed = time.perf_counter() - start

        print(
            f"Gemini failed after {elapsed:.2f}s: {repr(e)}",
            flush=True
        )

        return {"response": "I'm having trouble connecting right now!",
                "emotion": "neutral"}
