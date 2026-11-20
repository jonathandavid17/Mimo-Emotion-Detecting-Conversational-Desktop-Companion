# Mimo — Emotion-Aware Conversational Desktop Companion

A physical AI desktop companion that observes your facial expression without jumping to conclusions, initiates a natural voice conversation, and reacts through synthesized speech and an animated OLED face



Mimo bridges computer vision, conversational AI, voice I/O, and microcontroller hardware into a single loop

1. **Emotion Observation (`main.py`):** Captures webcam frames via OpenCV and runs facial emotion detection with DeepFace (`RetinaFace`).
2. **Streak Confirmation:** Requires 5 consecutive matching detections (`CONFIRMATION_THRESHOLD = 5`) before confirming an expression so momentary facial movements don't trigger false reactions.
3. **Contextual AI Response (`mimo_ai.py`):** Sends the confirmed expression to the Gemini API with a system prompt instructing Mimo to respond naturally in one sentence—without assuming how the user feels—and return structured JSON (`{"response", "emotion"}`).
4. **Hardware:** Sends the chosen emotion state (`happy`, `sad`, `angry`, `neutral`) over serial (`COM6` at `9600` baud) to an ESP32 driving an OLED display
5. **Voice Output (`mimo_voice.py`):** speaks the reply using `edge-tts` and `pygame`.
6. **Multi-Turn Voice Chat (`mimo_listen.py`):** Listens via microphone (`SpeechRecognition`) for follow-up replies until the user says `"goodbye mimo"`, `"stop"`, or `"exit"`.
