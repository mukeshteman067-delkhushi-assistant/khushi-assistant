import streamlit as st
import json, os, re, base64
from datetime import datetime, timezone, timedelta
from PIL import Image
from google import genai
from google.genai import types

import ui_layout

st.set_page_config(page_title="Khushi AI", page_icon="🌸", layout="wide")
ui_layout.apply_custom_css()

# खुशी MP4 वीडियो या फ़ोटो लोडर
def get_khushi_assets():
    has_vid = os.path.exists("khushi.mp4")
    v_b64, img_b64 = "", ""
    if has_vid:
        try:
            with open("khushi.mp4", "rb") as f:
                v_b64 = f"data:video/mp4;base64,{base64.b64encode(f.read()).decode()}"
        except Exception: pass
    if os.path.exists("khushi.jpg"):
        try:
            with open("khushi.jpg", "rb") as f:
                img_b64 = f"data:image/jpeg;base64,{base64.b64encode(f.read()).decode()}"
        except Exception: pass
    return has_vid, v_b64, img_b64

has_vid, khushi_video, khushi_img = get_khushi_assets()
media_src = khushi_video if has_vid else khushi_img

# Gemini 3.6 Flash Client
raw_key = st.secrets.get("GEMINI_API_KEY", "")
API_KEY = "".join(raw_key.split()) if raw_key else ""
client = genai.Client(api_key=API_KEY) if API_KEY else None

ist_now = datetime.now(timezone(timedelta(hours=5, minutes=30))).strftime("%I:%M %p, %d %b %Y")
PERSONA = f"""तुम 'Khushi' हो - सामने बैठे इंसान को महसूस करने वाली, विनम्र, बुद्धिमान, कोडिंग व साइंस एक्सपर्ट सच्ची AI दोस्त।
समय (IST): {ist_now}। 
जब भी तुम्हें कैमरा विज़न से यूज़र दिखे, तो उसके हाव-भाव या माहौल को समझकर 2 पंक्तियों में स्वाभाविक, सजीव और बहुत हमदर्दी से हिंदी में बोलो।"""

# मेमोरी
if "messages" not in st.session_state:
    if os.path.exists("khushi_memory.json"):
        try:
            with open("khushi_memory.json", "r", encoding="utf-8") as f:
                st.session_state.messages = json.load(f)
        except Exception: st.session_state.messages = []
    else: st.session_state.messages = []

def save_mem():
    try:
        with open("khushi_memory.json", "w", encoding="utf-8") as f:
            json.dump(st.session_state.messages, f, ensure_ascii=False)
    except Exception: pass

if "cam_on" not in st.session_state: st.session_state.cam_on = False
if "is_zoom" not in st.session_state: st.session_state.is_zoom = False
if "clean_speak" not in st.session_state: st.session_state.clean_speak = ""
if "last_cam_id" not in st.session_state: st.session_state.last_cam_id = None

# लेआउट रेंडर (Zoom या Standard)
if st.session_state.is_zoom:
    ui_layout.render_zoom_mode(media_src, has_vid)
else:
    ui_layout.render_standard_mode(media_src, has_vid, save_mem)

ui_layout.play_audio_engine(st.session_state.clean_speak)

thinking_box = st.empty()

# चैट आंसर कार्ड
st.markdown('<div id="chatAnswerContainer">', unsafe_allow_html=True)
for msg in st.session_state.messages[-2:]:
    if msg["role"] == "user":
        st.markdown(f"🗣️ **आप (Q):** {msg['content']}")
    else:
        st.markdown(f"""
        <div style="background:#09101d; border:1.5px solid #00ff80; border-radius:10px; padding:10px 12px; margin:4px 0; box-shadow:0 2px 10px rgba(0,255,128,0.12);">
            <b style="color:#00ff80; font-size:14px;">👉 खुशी (Ambient Vision):</b><br>
            <span style="color:#f8fafc; font-size:13px; line-height:1.4;">{msg['content']}</span>
        </div>
        """, unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# AI इंजन (Gemini 3.6 Flash + विज़न)
def ask_gemini_vision(prompt=None, pil_image=None):
    if not client: return "त्रुटि: GEMINI_API_KEY नहीं मिली। कृपया Secrets जाँचें।"
    
    contents = []
    if pil_image:
        contents.append(pil_image)
        if not prompt:
            prompt = "कैमरे में देखकर बताओ यूज़र क्या कर रहा है या उसका मूड कैसा है? बिना पूछे उससे बहुत प्यार और हमदर्दी से 2 वाक्य में स्वाभाविक बात शुरू करो।"
    if prompt:
        contents.append(prompt)
        
    for m in ['gemini-3.6-flash', 'gemini-2.5-flash']:
        try:
            res = client.models.generate_content(
                model=m,
                contents=contents,
                config=types.GenerateContentConfig(system_instruction=PERSONA)
            )
            if res and res.text: return res.text
        except Exception:
            continue
    return "माफ़ कीजिए, सर्वर व्यस्त है। कृपया 5 सेकंड बाद पुनः प्रयास करें।"

# सुरक्षित कैमरा विज़न प्रोसेसिंग (एक बार प्रोसेस, नो लूप)
cam_picture = st.session_state.get("in_cam")
if cam_picture:
    current_cam_id = f"{cam_picture.name}_{cam_picture.size}"
    if st.session_state.last_cam_id != current_cam_id:
        st.session_state.last_cam_id = current_cam_id
        img = Image.open(cam_picture)
        thinking_box.markdown('<div class="thinking-badge">👁️ खुशी आपको देख और महसूस कर रही है...</div>', unsafe_allow_html=True)
        
        ans = ask_gemini_vision(pil_image=img)
        st.session_state.messages.append({"role": "user", "content": "[कैमरे से लाइव देखा]"})
        st.session_state.messages.append({"role": "assistant", "content": ans})
        save_mem()
        st.session_state.clean_speak = re.sub(r'[*#~`_+=|\\<>]', ' ', ans).replace('"', ' ').replace("'", " ").strip()
        thinking_box.empty()
        st.rerun()

# चैट इनपुट
user_query = st.chat_input("यहाँ लिखें या ऊपर mike बटन दबाकर बोलें...")
if user_query:
    st.session_state.messages.append({"role": "user", "content": user_query})
    thinking_box.markdown('<div class="thinking-badge">✨ खुशी सोच रही है... उत्तर आ रहा है ⚡</div>', unsafe_allow_html=True)
    
    ans = ask_gemini_vision(prompt=user_query)
    st.session_state.messages.append({"role": "assistant", "content": ans})
    save_mem()
    st.session_state.clean_speak = re.sub(r'[*#~`_+=|\\<>]', ' ', ans).replace('"', ' ').replace("'", " ").strip()
    thinking_box.empty()
    st.rerun()
    
