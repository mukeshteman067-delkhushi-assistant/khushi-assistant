import os
import json
from typing import Optional, List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google import genai
from google.genai import types

# 1. FastAPI ऐप इनिशियलाइज़ेशन
app = FastAPI(title="Khushi AI Core Brain", version="2.0")

# CORS सक्षम करें (ब्राउज़र / मोबाइल ऐप से बिना रुकावट कनेक्शन के लिए)
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

MASTER_PERSONA = """तुम 'Khushi' हो - एक अत्यंत बुद्धिमान, परिपक्व, ज्ञानी और आत्मीय AI साथी।
नियम:
1. तुम्हारे पास विज्ञान, इतिहास, तकनीक, कानून, व्यापार और जीवन के सभी विषयों का गहरा ज्ञान है।
2. जब भी कोई सवाल पूछा जाए, तो बिल्कुल सटीक, तथ्यपरक (100% Factually Correct) और व्यावहारिक उत्तर दो।
3. उत्तर बहुत लंबा और उबाऊ न हो; सटीक, ऊर्जावान और आत्मीय भाषा (शुद्ध हिंदी) में हो।
4. यदि किसी ताज़ा घटना या सटीक तथ्य की बात हो, तो Google Search के नवीनतम डेटा के आधार पर ही बोलो।"""

# 3. डेटा स्कीमा
class UserMessage(BaseModel):
    user_id: str = "guest_user"
    message: str
    stream: bool = False

class AssistantResponse(BaseModel):
    reply: str
    sources: Optional[List[str]] = []
    status: str = "success"

# 4. इन-मेमोरी चैट हिस्ट्री (यूज़र के हिसाब से अलग-अलग)
user_sessions = {}

# 5. मुख्य AI एंडपॉइंट (Google Search Grounding के साथ)
@app.post("/api/ask", response_model=AssistantResponse)
async def ask_assistant(payload: UserMessage):
    if not client:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY कॉन्फ़िगर नहीं है।")

    user_id = payload.user_id
    query = payload.message.strip()

    if not query:
        raise HTTPException(status_code=400, detail="सवाल खाली नहीं हो सकता।")

    # यूज़र की पुरानी हिस्ट्री बनाए रखना
    if user_id not in user_sessions:
        user_sessions[user_id] = []

    # संदर्भ (Context) जोड़ना
    user_sessions[user_id].append({"role": "user", "parts": [{"text": query}]})
    
    # मेमोरी लिमिट: आख़िरी 10 बातचीत सुरक्षित रखें ताकि गति तेज़ बनी रहे
    if len(user_sessions[user_id]) > 10:
        user_sessions[user_id] = user_sessions[user_id][-10:]

    try:
        # Google Search Grounding टूल सक्रिय करें
        config = types.GenerateContentConfig(
            system_instruction=MASTER_PERSONA,
            tools=[{"google_search": {}}],  # गूगल लाइव सर्च ऑन
            temperature=0.7,
        )

        # सुपरफ़ास्ट Gemini 2.5 Flash मॉडल को कॉल
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=query,
            config=config,
        )

        reply_text = response.text if response and response.text else "मुझे इसका उत्तर ढूँढने में थोड़ी कठिनाई हो रही है, कृपया दोबारा पूछें।"

        # अगर गूगल सर्च से जानकारी मिली है तो स्रोतों की जानकारी
        sources = []
        if response.candidates and response.candidates[0].grounding_metadata:
            grounding_chunks = getattr(response.candidates[0].grounding_metadata, 'grounding_chunks', [])
            if grounding_chunks:
                for chunk in grounding_chunks:
                    web = getattr(chunk, 'web', None)
                    if web and getattr(web, 'uri', None):
                        sources.append(web.uri)

        # हिस्ट्री में जवाब सुरक्षित करें
        user_sessions[user_id].append({"role": "model", "parts": [{"text": reply_text}]})

        return AssistantResponse(
            reply=reply_text,
            sources=list(set(sources))[:3],  # टॉप 3 स्रोत
            status="success"
        )

    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg:
            return AssistantResponse(
                reply="सर्वर पर अभी बहुत अधिक ट्रैफ़िक है, कृपया 10 सेकंड बाद पुनः प्रयास करें।",
                status="rate_limited"
            )
        return AssistantResponse(
            reply=f"तकनीकी समस्या: {error_msg[:100]}",
            status="error"
        )

# 6. हेल्थ चेक रूट (यह जांचने के लिए कि सर्वर ज़िंदा है या नहीं)
@app.get("/")
def health_check():
    return {
        "engine": "Khushi AI High-Speed Brain",
        "search_grounding": "Active",
        "status": "Ready for Commercial PWA"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
                
