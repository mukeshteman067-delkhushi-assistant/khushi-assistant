import os
import json
import re
import base64
import io
from typing import Optional, List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from PIL import Image
from google import genai
from google.genai import types

# 1. FastAPI ऐप इनिशियलाइज़ेशन
app = FastAPI(title="Khushi AI Core Brain", version="2.0")

# CORS सक्षम करें (मोबाइल PWA, वेब ब्राउज़र और प्ले स्टोर वेबव्यू के लिए)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Gemini क्लाइंट और मास्टर पर्सोना
API_KEY = os.environ.get("GEMINI_API_KEY", "")
client = genai.Client(api_key=API_KEY) if API_KEY else None

MASTER_PERSONA = """तुम 'Khushi' हो - एक अत्यंत बुद्धिमान, परिपक्व, उच्च-ज्ञानी और आत्मीय AI साथी।
नियम:
1. तुम्हारे पास विज्ञान, इतिहास, तकनीक, कानून, व्यापार, स्वास्थ्य और जीवन के सभी विषयों का प्रामाणिक ज्ञान है।
2. जब भी कोई सवाल पूछा जाए, तो बिल्कुल सटीक, तथ्यपरक (100% Factually Correct) और व्यावहारिक उत्तर दो।
3. बोलने की शैली प्राकृतिक, सजीव और स्पष्ट हिंदी में हो। अनावश्यक तकनीकी सिंबल या मार्कडाउन का कम से कम उपयोग करो ताकि आवाज़ में प्रवाह रहे।
4. किसी भी ताज़ा घटना, समाचार या सटीक आंकड़ों के लिए Google Search के नवीनतम डेटा का ही उपयोग करो।"""

# 3. डेटा स्कीमा
class UserMessage(BaseModel):
    user_id: str = "guest_user"
    message: Optional[str] = None
    image_base64: Optional[str] = None

class AssistantResponse(BaseModel):
    reply: str
    voice_text: str
    sources: Optional[List[str]] = []
    status: str = "success"

# 4. परसिस्टेंट सेशन मेमोरी (RAM + JSON बैकअप)
MEMORY_FILE = "khushi_sessions.json"
user_sessions = {}

def load_memory():
    global user_sessions
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                user_sessions = json.load(f)
        except Exception:
            user_sessions = {}

def save_memory():
    try:
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(user_sessions, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

load_memory()

def clean_for_speech(text: str) -> str:
    """आवाज़ में बोलने के लिए टेक्स्ट को साफ करना ताकि TTS बिना अटके बोले"""
    clean = re.sub(r'[*#_~`>+\-\[\]\(\)\{\}\|=]', ' ', text)
    clean = re.sub(r'https?://\S+', '', clean)
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean

# 5. मुख्य AI एंडपॉइंट (Google Search + Vision + Multi-Turn Memory)
@app.post("/api/ask", response_model=AssistantResponse)
async def ask_assistant(payload: UserMessage):
    if not client:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY सेट नहीं है। सर्वर एनवायरनमेंट चेक करें।")

    user_id = payload.user_id
    query_text = (payload.message or "").strip()
    img_b64 = payload.image_base64

    if not query_text and not img_b64:
        raise HTTPException(status_code=400, detail="सवाल या इमेज में से कम से कम एक इनपुट अनिवार्य है।")

    if user_id not in user_sessions:
        user_sessions[user_id] = []

    # इनपुट तैयार करना (मल्टीमॉडल सपोर्ट)
    current_contents = []
    
    # अगर यूजर की पुरानी बातचीत है तो संदर्भ बनाए रखें
    for turn in user_sessions[user_id][-6:]:  # आखिरी 6 टर्न स्पीड बनाए रखने के लिए
        current_contents.append(types.Content(
            role=turn["role"],
            parts=[types.Part.from_text(text=turn["text"])]
        ))

    # नया इनपुट जोड़ें
    new_parts = []
    if img_b64:
        try:
            clean_b64 = img_b64.split(",")[-1]
            img_bytes = base64.b64decode(clean_b64)
            pil_img = Image.open(io.BytesIO(img_bytes))
            new_parts.append(pil_img)
            if not query_text:
                query_text = "कैमरे में देखकर बताओ क्या है और 2 पंक्तियों में आत्मीयता से प्रतिक्रिया दो।"
        except Exception:
            pass

    if query_text:
        new_parts.append(query_text)

    current_contents.append(types.Content(
        role="user",
        parts=[types.Part.from_text(text=p) if isinstance(p, str) else p for p in new_parts]
    ))

    try:
        # Google Search Grounding चालू
        config = types.GenerateContentConfig(
            system_instruction=MASTER_PERSONA,
            tools=[{"google_search": {}}],
            temperature=0.6,
        )

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=current_contents,
            config=config,
        )

        reply_text = response.text if response and response.text else "मुझे इसका उत्तर ढूँढने में थोड़ी कठिनाई हो रही है, कृपया दोबारा पूछें।"

        # वेब सर्च के स्रोत निकालना
        sources = []
        if response.candidates and response.candidates[0].grounding_metadata:
            grounding_chunks = getattr(response.candidates[0].grounding_metadata, 'grounding_chunks', [])
            if grounding_chunks:
                for chunk in grounding_chunks:
                    web = getattr(chunk, 'web', None)
                    if web and getattr(web, 'uri', None):
                        sources.append(web.uri)

        # मेमोरी में जोड़ना
        user_sessions[user_id].append({"role": "user", "text": query_text})
        user_sessions[user_id].append({"role": "model", "text": reply_text})
        save_memory()

        voice_text = clean_for_speech(reply_text)

        return AssistantResponse(
            reply=reply_text,
            voice_text=voice_text,
            sources=list(set(sources))[:3],
            status="success"
        )

    except Exception as e:
        err = str(e)
        if "429" in err:
            return AssistantResponse(
                reply="सर्वर पर अभी बहुत अधिक लोड है, कृपया 10 सेकंड बाद पुनः बोलें।",
                voice_text="सर्वर पर अभी बहुत अधिक लोड है, कृपया कुछ सेकंड बाद पुनः बोलें।",
                status="rate_limited"
            )
        return AssistantResponse(
            reply="तकनीकी समस्या के कारण संपर्क नहीं हो सका। कृपया पुनः प्रयास करें।",
            voice_text="तकनीकी समस्या के कारण संपर्क नहीं हो सका।",
            status="error"
        )

# 6. सेशन क्लियर एंडपॉइंट
@app.post("/api/clear")
def clear_user_history(user_id: str = "guest_user"):
    if user_id in user_sessions:
        user_sessions[user_id] = []
        save_memory()
    return {"status": "cleared"}

# 7. सर्वर स्टेटस
@app.get("/")
def health_check():
    return {
        "assistant": "Khushi AI",
        "engine": "Gemini 2.5 Flash + Google Grounding",
        "version": "2.0 Supernova Grade",
        "status": "Ready"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
            
