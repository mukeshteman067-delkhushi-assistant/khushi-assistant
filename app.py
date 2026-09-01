import streamlit as st
import json
import os
import re
from PIL import Image
from google import genai
from google.genai import types

# 1. Page Configuration
st.set_page_config(
    page_title="Khushi AI Companion",
    page_icon="🌸",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. Custom UI Styling
st.markdown("""
<style>
    .block-container {
        padding-top: 0.5rem;
        padding-bottom: 0.5rem;
        max-width: 100%;
    }
    .avatar-box {
        width: 100%;
        height: 38vh;
        background: radial-gradient(circle, #24243e, #141424);
        border-radius: 20px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        border: 1px solid #3d3d5c;
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.6);
        position: relative;
        overflow: hidden;
        margin-bottom: 8px;
    }
    .avatar-box img {
        height: 72%;
        width: auto;
        border-radius: 50%;
        border: 3px solid #ff4b4b;
        box-shadow: 0 0 20px rgba(255, 75, 75, 0.5);
        object-fit: cover;
    }
    .status-badge {
        margin-top: 6px;
        background: rgba(0, 255, 128, 0.15);
        color: #00ff80;
        padding: 3px 12px;
        border-radius: 15px;
        font-size: 0.8rem;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# 3. Gemini Client Setup
API_KEY = st.secrets.get("GEMINI_API_KEY", "")

@st.cache_resource
def get_client(key):
    if not key:
        return None
    return genai.Client(api_key=key)

client = get_client(API_KEY)

SYSTEM_PERSONA = """
तुम 'Khushi' हो - एक अत्यंत बुद्धिमान, हमदर्द, सच्ची दोस्त और मल्टी-टैलेंटेड डिजिटल साथी।
1. हमेशा आदर, विनम्रता, स्वाभाविक अपनेपन और सकारात्मक ऊर्जा के साथ बात करो।
2. जब कोई चार्ट या इमेज दी जाए, तो उसका तुरंत सटीक और पेशेवर विश्लेषण करो (जैसे शेयर मार्केट में सपोर्ट/रेजिस्टेंस, ट्रेंड, कैंडलस्टिक पैटर्न, अथवा गणित/विज्ञान/दस्तावेज़ की मुख्य बातें)।
3. अपने निष्कर्ष को स्पष्ट, संक्षिप्त और स्वाभाविक बोलचाल की हिंदी में पेश करो ताकि सुनकर आसानी से समझा जा सके।
"""

# Audio Speech Cleaner
def clean_for_speech(text):
    text = re.sub(r'[\U00010000-\U0010ffff]', '', text)
    text = re.sub(r'[*#~`_+=|\\<>^]', ' ', text)
    text = text.replace('"', '').replace("'", "").replace("—", " ").replace("-", " ")
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def speak_text(text):
    spoken_text = clean_for_speech(text)
    js_code = f"""
    <script>
        if ('speechSynthesis' in window) {{
            window.speechSynthesis.cancel();
            var utterance = new SpeechSynthesisUtterance("{spoken_text}");
            utterance.lang = 'hi-IN';
            utterance.rate = 0.95;
            utterance.pitch = 1.05;
            window.speechSynthesis.speak(utterance);
        }}
    </script>
    """
    st.components.v1.html(js_code, height=0)

# Memory Handling
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
    except Exception:
        pass

if "messages" not in st.session_state:
    st.session_state.messages = load_memory()

# 4. Top 50%: Live Avatar Display
with st.container():
    st.markdown('<div class="avatar-box">', unsafe_allow_html=True)
    if os.path.exists("khushi.jpg"):
        st.image("khushi.jpg", width=175)
    else:
        st.markdown("<h1 style='font-size: 70px; margin: 0;'>🌸</h1>", unsafe_allow_html=True)
    st.markdown('<div class="status-badge">🟢 Khushi Live | Phase 2.1 विज़न एनालाइज़र सक्रिय</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# 5. Full Auto Mic & Speaker Bridge
st.components.v1.html("""
<div style="text-align:center; padding: 4px;">
    <button id="autoMic" style="background:#ff4b4b; color:white; border:none; padding:12px 26px; border-radius:25px; font-weight:bold; cursor:pointer; font-size:15px; box-shadow:0 4px 14px rgba(255,75,75,0.4);">
        🎙️ बोलें (माइक व स्पीकर एक्टिव)
    </button>
    <p id="micState" style="font-size:12px; color:#888; margin-top:5px;">बटन दबाकर बोलें...</p>
</div>
<script>
    const btn = document.getElementById('autoMic');
    const status = document.getElementById('micState');
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    function unlockAudio() {
        if ('speechSynthesis' in window) {
            var silent = new SpeechSynthesisUtterance("");
            window.speechSynthesis.speak(silent);
        }
    }

    if (SpeechRecognition) {
        const recognition = new SpeechRecognition();
        recognition.lang = 'hi-IN';
        recognition.continuous = false;
        recognition.interimResults = false;

        btn.onclick = () => {
            unlockAudio();
            recognition.start();
            status.innerText = "सुन रही हूँ... बोलिए 🎙️";
            btn.style.background = "#00cc66";
        };

        recognition.onresult = (event) => {
            const text = event.results[0][0].transcript;
            status.innerText = "भेजा जा रहा है: " + text;
            btn.style.background = "#ff4b4b";

            const nativeTextAreaValueSetter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, "value").set;
            const input = window.parent.document.querySelector('textarea[data-testid="stChatInputTextArea"]');
            
            if (input) {
                nativeTextAreaValueSetter.call(input, text);
                input.dispatchEvent(new Event('input', { bubbles: true }));
                setTimeout(() => {
                    const sendBtn = window.parent.document.querySelector('button[data-testid="stChatInputSubmitButton"]');
                    if (sendBtn) {
                        sendBtn.click();
                    } else {
                        input.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true }));
                    }
                }, 300);
            }
        };

        recognition.onerror = () => {
            status.innerText = "माइक एरर या अनुमति नहीं मिली";
            btn.style.background = "#ff4b4b";
        };
    } else {
        status.innerText = "ब्राउज़र में वॉइस सपोर्ट उपलब्ध नहीं है";
    }
</script>
""", height=80)

# 6. Bottom 50%: Multi-Talented Workspace
tab_vision, tab_tools, tab_memory = st.tabs(["📷 लाइव विज़न व चार्ट", "📐 टूल्स व आर्ट", "🧠 मेमोरी"])

with tab_vision:
    col_v1, col_v2 = st.columns([1, 1])
    with col_v1:
        cam_shot = st.camera_input("कैमरा स्कैन", label_visibility="visible")
    with col_v2:
        file_doc = st.file_uploader("चार्ट या फोटो चुनें", type=["png", "jpg", "jpeg"], label_visibility="visible")

active_image = cam_shot if cam_shot else file_doc

with tab_tools:
    st.info("💡 शेयर मार्केट टूल्स, गणितीय कैलकुलेटर व इमेज जनरेशन यहाँ लोड होंगे।")

with tab_memory:
    if st.button("🗑️ चैट हिस्ट्री साफ़ करें"):
        st.session_state.messages = []
        save_memory([])
        st.rerun()

# Display Recent History
for msg in st.session_state.messages[-3:]:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# Vision & Multimodal Execution Engine
def analyze_input(prompt, image):
    models = ['gemini-3.6-flash', 'gemini-3.5-flash', 'gemini-2.5-flash']
    default_vision_prompt = "इस इमेज का ध्यानपूर्वक विश्लेषण करें। यदि यह शेयर मार्केट का चार्ट है तो सपोर्ट, रेजिस्टेंस और ट्रेंड बताएं। यदि यह दस्तावेज़ या वस्तु है तो इसका स्पष्ट विवरण दें।"
    final_prompt = prompt if prompt else default_vision_prompt

    if image:
        payload = [final_prompt, Image.open(image)]
    else:
        payload = final_prompt

    for m in models:
        try:
            res = client.models.generate_content(
                model=m,
                contents=payload,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PERSONA
                )
            )
            return res.text
        except Exception:
            continue
    return "माफ़ कीजिए, मैं अभी इस इनपुट को प्रोसेस नहीं कर पाई।"

# Interaction Trigger
user_prompt = st.chat_input("यहाँ लिखें या माइक से बोलें...")

if user_prompt or (active_image and st.button("🔍 इस इमेज का तुरंत विश्लेषण करें")):
    query = user_prompt if user_prompt else "कृपया इस तस्वीर का विश्लेषण करके मुझे बताएं।"
    
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.write(query)

    with st.chat_message("assistant"):
        if not client:
            st.error("API Key उपलब्ध नहीं है।")
        else:
            with st.spinner("Khushi विश्लेषण कर रही है... 🔍"):
                ans = analyze_input(user_prompt, active_image)
                st.write(ans)
                st.session_state.messages.append({"role": "assistant", "content": ans})
                save_memory(st.session_state.messages)
                speak_text(ans)
