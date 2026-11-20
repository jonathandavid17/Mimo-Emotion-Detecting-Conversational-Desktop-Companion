import asyncio
import edge_tts
import pygame
import time
import os
import uuid

VOICE = "en-US-JennyNeural"


async def generate_speech(text, filename):
    communicate = edge_tts.Communicate(
        text,
        VOICE,
        rate="+0%",
        pitch="+0Hz"
    )

    await communicate.save(filename)


def speak(text):
    print("MIMO SPEAKING:", text, flush=True)

    filename = f"mimo_{uuid.uuid4().hex}.mp3"

    try:

        asyncio.run(generate_speech(text, filename))

        if not pygame.mixer.get_init():
            pygame.mixer.init()

        pygame.mixer.music.load(filename)
        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
        pygame.mixer.music.unload()

    finally:
        if os.path.exists(filename):
            os.remove(filename)
