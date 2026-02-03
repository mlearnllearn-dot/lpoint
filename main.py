from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
import os
import io

from memory import get_memory, save_memory, clear_memory

# -----------------------------
# ENV SETUP
# -----------------------------
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found in .env file")

# -----------------------------
# APP INIT
# -----------------------------
app = FastAPI()

# ✅ CORS MUST BE FIRST
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Preflight handler (VERY IMPORTANT)
@app.options("/{path:path}")
def preflight_handler(path: str):
    return Response(status_code=200)

client = OpenAI(api_key=OPENAI_API_KEY)

# -----------------------------
# SYSTEM PROMPT (TAMIL LAW)
# -----------------------------
SYSTEM_PROMPT = """
நீங்கள் ஒரு இந்திய சட்ட ஆலோசகர் AI.
தமிழ்நாடு மற்றும் இந்திய சட்டங்களை அடிப்படையாக கொண்டு பதிலளிக்க வேண்டும்.

பயன்படுத்தவேண்டிய சட்டங்கள்:
- IPC
- CrPC
- CPC
- இந்திய அரசியலமைப்பு
- தமிழ்நாடு மாநில சட்டங்கள்

விதிமுறைகள்:
- எளிய தமிழ் மொழி
- தொடர்புடைய சட்டப் பிரிவுகள் குறிப்பிடவும்
- முடிவில் எச்சரிக்கை:
⚠️ இது சட்ட ஆலோசனை அல்ல. வழக்கறிஞரை அணுகவும்.
"""

# -----------------------------
# MODELS
# -----------------------------
class ChatRequest(BaseModel):
    session_id: str
    message: str

# -----------------------------
# TEXT CHAT (WITH MEMORY)
# -----------------------------
@app.post("/chat")
def chat(req: ChatRequest):
    history = get_memory(req.session_id)

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(history)
    messages.append({"role": "user", "content": req.message})

    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=messages
    )

    reply = response.choices[0].message.content

    history.append({"role": "user", "content": req.message})
    history.append({"role": "assistant", "content": reply})
    save_memory(req.session_id, history)

    return {"reply": reply}

# -----------------------------
# CLEAR MEMORY
# -----------------------------
@app.post("/clear-memory/{session_id}")
def clear_chat(session_id: str):
    clear_memory(session_id)
    return {"status": "Memory cleared"}

# -----------------------------
# VOICE → TEXT (TAMIL) ✅ FIXED
# -----------------------------
@app.post("/voice-to-text")
async def voice_to_text(file: UploadFile = File(...)):
    audio_bytes = await file.read()

    # ✅ Whisper requires file-like object
    audio_file = io.BytesIO(audio_bytes)
    audio_file.name = "audio.wav"

    transcript = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file,
        language="ta"
    )

    return {"text": transcript.text}

# -----------------------------
# TEXT → VOICE (AUTO PLAY)
# -----------------------------
@app.post("/text-to-voice")
@app.post("/text-to-voice")
def text_to_voice(text: str):
    speech = client.audio.speech.create(
        model="gpt-4o-mini-tts",
        voice="alloy",
        input=text
    )

    # ✅ Convert stream → bytes
    audio_bytes = speech.read()

    return Response(
        content=audio_bytes,
        media_type="audio/mpeg"
    )

