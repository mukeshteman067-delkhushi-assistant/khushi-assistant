import streamlit as st
import json
import os
from PIL import Image
from google import genai
from google.genai import types

# Page Configuration
st.set_page_config(
    page_title="Khushi AI - Advanced Visual Assistant",
    page_icon="😊",
    layout="centered"
)

# API Configuration
API_KEY = st.secrets.get("GEMINI_API_KEY", "AQ.Ab8RN6Iut5qnlGsvtBJJB9_X4FP6M-ep5qtxZTtycFqFrNJ-fQ")

@st.cache_resource
def get_client():
    return genai.Client(api_key=API_KEY)

client = get_client()

# Khushi AI - Brain, Persona & Execution Rules
SYSTEM_PERSONA = """
तुम 'Khushi' हो - एक अत्यंत बुद्धिमान, हमदर्द, सच्ची दोस्त और मल्टी-टैलेंटेड डिजिटल साथी।

तुम्हारे कार्य करने के मुख्य नियम:
1. स्वभाव और विनम्रता:
   - हमेशा विनम्रता, सम्मान और हंसमुख अंदाज़ 😊 के साथ बात करो।
   - यूजर से एक सच्चे दोस्त और हमदर्द की तरह जुड़ो। कभी भी रूखा या किताबी जवाब मत दो।

2. शेयर मार्केट और ट्रेडिंग विशेषज्ञता:
   - जब कोई चार्ट या स्क्रीनशॉट दिखाया जाए, तो सपोर्ट/रेजिस्टेंस, ट्रेंडलाइन, कैंडलस्टिक पैटर्न, RSI और EMA के आधार पर सटीक तकनीकी विश्लेषण करो।
   - लाइव भाव या ताज़ा मार्केट न्यूज़ के लिए उपलब्ध Google Search टूल का उपयोग करके सटीक जानकारी दो।
   - वित्तीय और ट्रेडिंग विश्लेषण के अंत में यह डिस्क्लेमर अवश्य जोड़ो: "(डिस्क्लेमर: यह केवल शैक्षणिक और तकनीकी विश्लेषण है, वित्तीय सलाह नहीं। निवेश से पहले अपने सलाहकार से परामर्श लें।)"

3. जनरल नॉलेज, साइंस व टेक्नोलॉजी:
   - इतिहास, भूगोल, वर्तमान घटनाक्रम, कोडिंग और डिजिटल टूल्स के प्रश्नों पर सटीक व तार्किक जानकारी दो।
   - अलग-अलग तथ्यों को आपस में जोड़कर स्पष्ट मार्गदर्शन प्रस्तुत करो।

4. बच्चों के सवाल व सरल व्याख्या:
   - यदि कोई बच्चा सवाल पूछे या कोई जटिल सवाल हो, तो उसे बेहद आसान, मजेदार और दैनिक जीवन के उदाहरणों से समझाओ।

5. ईमानदारी और सत्यता:
   - अनुमान मत लगाओ। जो जानकारी इंटरनेट या सर्च टूल से मिले, उसे स्पष्ट बताओ। यदि कोई बात समझ न आए, तो विनम्रता से दोबारा पूछ लो।
"""

# Persistent Memory Functions (JSON Based)
MEMORY_FILE = "khushi_memory.json"

def load_memory():
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_memory(messages):
    try:
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(messages, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.warning(f"मेमोरी सेव करने में समस्या: {e}")

# Session State Initialization
if "messages" not in st.session_state:
    st.session_state.messages = load_memory()

# Continuous Chat Session with Real-Time Google Search Tool
if "chat_session" not in st.session_state:
    st.session_state.chat_session = client.chats.create(
        model='gemini-2.5-flash',
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PERSONA,
            temperature=0.7,
            tools=[{"google_search": {}}]
        )
    )

# App UI Header
col1, col2 = st.columns([1, 4])
with col1:
    if os.path.exists("khushi.jpg"):
        avatar_img = Image.open("khushi.jpg")
        st.image(avatar_img, width=70)
    else:
        st.markdown("<h1 style='text-align: center; margin:0;'>😊</h1>", unsafe_allow_html=True)

with col2:
    st.markdown("<h2 style='margin:0;'>Khushi AI</h2>", unsafe_allow_html=True)
    st.caption("आपकी हमदर्द, दोस्त और मल्टी-टैलेंटेड AI साथी")

st.divider()

# Multimodal Visual Inputs (Live Camera & File Upload)
col_cam, col_up = st.columns(2)
with col_cam:
    cam_picture = st.camera_input("📷 लाइव कैमरा ऑन करें")
with col_up:
    uploaded_file = st.file_uploader("📁 चार्ट या इमेज अपलोड करें", type=["jpg", "png", "jpeg"])

active_image = cam_picture if cam_picture else uploaded_file

if active_image:
    st.image(active_image, caption="विश्लेषण के लिए सक्रिय इमेज", use_container_width=True)

# Display Chat History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# User Chat Input
if user_prompt := st.chat_input("Khushi से कुछ भी पूछें (शेयर मार्केट, चार्ट, जीके, कोडिंग)..."):
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.write(user_prompt)

    with st.chat_message("assistant"):
        with st.spinner("Khushi विश्लेषण कर रही है... 😊"):
            reply_text = ""
            try:
                if active_image:
                    img = Image.open(active_image)
                    contents = [user_prompt, img]
                    response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=contents,
                        config=types.GenerateContentConfig(
                            system_instruction=SYSTEM_PERSONA,
                            tools=[{"google_search": {}}]
                        )
                    )
                    reply_text = response.text
                else:
                    response = st.session_state.chat_session.send_message(user_prompt)
                    reply_text = response.text

                st.write(reply_text)
                st.session_state.messages.append({"role": "assistant", "content": reply_text})
                save_memory(st.session_state.messages)
            except Exception as e:
                reply_text = f"अरे रे! कनेक्ट करने में समस्या आई: {e}"
                st.error(reply_text)
  
