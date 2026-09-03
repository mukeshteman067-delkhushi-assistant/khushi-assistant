from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import os, json, base64, io
from datetime import datetime, timezone, timedelta
from PIL import Image
from google import genai
from google.genai import types

app = FastAPI(title="Khushi AI Core Engine")

# CORS सक्षम करना (ताकि फ्रंटएंड बिना किसी रुकावट के कनेक्ट हो सके)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. Gemini Client सेटअप
API_KEY = os.environ.get("GEMINI_API_KEY", "")
client = genai.Client(api_key=API_KEY) if API_KEY else None

MEMORY_FILE = "khushi_memory.json"

def get_ist_time():
    return datetime.now(timezone(timedelta(hours=5, minutes=30))).strftime("%I:%M %p, %d %b %Y")

PERSONA = f"""तुम 'Khushi' हो - सामने बैठे इंसान को गहराई से महसूस करने वाली, उच्च-बुद्धिमान, हमदर्द और सजीव AI साथी।
समय (IST): {get_ist_time()}।
जब भी तुम्हें कैमरा विज़न या चैट से यूज़र दिखे, तो उसके हाव-भाव, काम या माहौल को समझकर 2 पंक्तियों में सजीव, आत्मीय और संक्षिप्त हिंदी में बोलो।"""

# 2. मेमोरी लोड / सेव फंक्शन
def load_memory() -> List[dict]:
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_memory(messages: List[dict]):
    try:
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(messages, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

# 3. डेटा मॉडल्स (Request / Response)
class ChatRequest(BaseModel):
    message: Optional[str] = None
    image_base64: Optional[str] = None

class ChatResponse(BaseModel):
    reply: str
    history: List[dict]

# 4. API एंडपॉइंट्स

@app.get("/")
def home():
    return {"status": "online", "model": "gemini-3.6-flash", "assistant": "Khushi"}

@app.get("/api/history")
def get_history():
    """पूरी चैट हिस्ट्री लोड करने के लिए"""
    return {"history": load_memory()}

@app.post("/api/clear")
def clear_history():
    """मेमोरी साफ़ करने के लिए"""
    save_memory([])
    return {"status": "cleared", "history": []}

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    """टेक्स्ट संवाद एवं स्वायत्त कैमरा विज़न प्रोसेसिंग"""
    if not client:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY कॉन्फ़िगर नहीं है।")

    contents = []
    user_label = req.message or "[कैमरे से लाइव देखा]"

    # यदि कैमरे का लाइव फ्रेम आया है
    if req.image_base64:
        try:
            clean_b64 = req.image_base64.split(",")[-1]
            img_bytes = base64.b64decode(clean_b64)
            pil_img = Image.open(io.BytesIO(img_bytes))
            contents.append(pil_img)
            if not req.message:
                contents.append("कैमरे में देखकर बताओ यूजर क्या कर रहा है या उसका मूड और माहौल कैसा है? अगर कुछ खास या नया दिखे तो 1 छोटा हमदर्द सवाल पूछो या बात शुरू करो।")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"इमेज डिकोडिंग में त्रुटि: {str(e)}")

    if req.message:
        contents.append(req.message)

    # Gemini 3.6 Flash (Fallback 2.5 Flash)
    reply_text = ""
    models_to_try = ['gemini-3.6-flash', 'gemini-2.5-flash']
    
    for m in models_to_try:
        try:
            res = client.models.generate_content(
                model=m,
                contents=contents,
                config=types.GenerateContentConfig(system_instruction=PERSONA)
            )
            if res and res.text:
                reply_text = res.text.strip()
                break
        except Exception:
            continue

    if not reply_text:
        reply_text = "माफ़ कीजिए, मैं अभी थोड़ा व्यस्त हूँ। कृपया कुछ सेकंड बाद पुनः बोलें।"

    # मेमोरी में सुरक्षित जोड़ना
    history = load_memory()
    history.append({"role": "user", "content": user_label})
    history.append({"role": "assistant", "content": reply_text})
    save_memory(history)

    return ChatResponse(reply=reply_text, history=history)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
      
