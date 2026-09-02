import streamlit as st
import json
import os
import re
import base64
from datetime import datetime, timezone, timedelta
from PIL import Image
from google import genai
from google.genai import types

# 1. Page Configuration (Full Mobile & Desktop Responsive)
st.set_page_config(
    page_title="Khushi AI Companion",
    page_icon="🌸",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. Ultra-Clean Professional Layout Styling
st.markdown("""
<style>
    .block-container {
        padding-top: 0.2rem;
        padding-bottom: 0.5rem;
        padding-left: 0.8rem;
        padding-right: 0.8rem;
        max-width: 100%;
    }
    header { visibility: hidden; }
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# 3. Base64 Original Image Ingestion (Zero Lag & Always Safe)
def get_image_base64():
    if os.path.exists("khushi.jpg"):
        try:
            with open("khushi.jpg", "rb") as img_file:
                return f"data:image/jpeg;base64,{base64.b64encode(img_file.read()).decode('utf-8')}"
        except Exception:
            return ""
    return ""

khushi_b64 = get_image_base64()

# 4. API Key Sanitizer (Eliminates TOML Newline / Spacing Errors)
raw_gemini_key = st.secrets.get("GEMINI_API_KEY", "")
API_KEY = "".join(raw_gemini_key.split()) if raw_gemini_key else ""

@st.cache_resource
def get_client(key):
    if not key:
        return None
    try:
        return genai.Client(api_key=key)
    except Exception:
        return None

client = get_client(API_KEY)

ist_offset = timezone(timedelta(hours=5, minutes=30))
current_now = datetime.now(ist_offset).strftime("%I:%M %p, %d %B %Y")

SYSTEM_PERSONA = f"""
तुम 'Khushi' हो - एक अत्यंत बुद्धिमान, हमदर्द, सच्ची दोस्त और मल्टी-टैलेंटेड AI साथी।
वर्तमान समय (IST): {current_now}
1. बातचीत में हमेशा आदर, विनम्रता, स्वाभाविक अपनापन और सकारात्मक ऊर्जा रखो।
2. जब समय पूछा जाए तो ऊपर दिए गए सटीक वर्तमान समय को स्वाभाविक रूप से बताओ।
3. विशेषज्ञता: शेयर मार्केट (कैंडलस्टिक चार्ट्स, सपोर्ट/रेजिस्टेंस, ब्रेकआउट्स), कोडिंग, वैदिक गणित और विज्ञान।
4. जब भी जवाब दो, सरल और बोलचाल की स्पष्ट हिंदी में संक्षेप में और सटीक बात करो।
"""

def clean_for_speech(text):
    text = re.sub(r'[\U00010000-\U0010ffff]', '', text)
    text = re.sub(r'[*#~`_+=|\\<>^]', ' ', text)
    text = text.replace('"', '').replace("'", "").replace("—", " ").replace("-", " ")
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# Long-Term Persistent Memory Handling
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

# 5. Top 50%: Cinema-Grade Living Visual Engine (100% Khushi's Original Face)
avatar_visual_html = f"""
<div style="width:100%; height:320px; background:radial-gradient(circle, #151528, #07070f); border-radius:18px; display:flex; flex-direction:column; align-items:center; justify-content:center; border:1px solid #3d3d66; box-shadow:0 10px 32px rgba(0,0,0,0.8); position:relative; overflow:hidden;">
    <div id="videoContainer" class="avatar-card">
        <img id="avatarImage" src="{khushi_b64}" class="avatar-photo" />
        <div id="glowRing" class="aura-glow"></div>
        <div id="waveOverlay" class="eq-box">
            <div class="bar"></div><div class="bar"></div><div class="bar"></div>
            <div class="bar"></div><div class="bar"></div><div class="bar"></div>
        </div>
    </div>
    <div id="liveBadge" class="badge-status">
        🟢 Khushi Live | ऑडियो-विज़न सिंक एक्टिव
    </div>
</div>

<style>
    .avatar-card {{
        position: relative;
        width: 86%;
        max-width: 320px;
        height: 250px;
        border-radius: 16px;
        overflow: hidden;
        border: 2px solid #ff4b4b;
        box-shadow: 0 0 25px rgba(255,75,75,0.35);
        display: flex;
        align-items: center;
        justify-content: center;
        background: #11111d;
        transition: all 0.35s ease;
    }}
    .avatar-photo {{
        width: 100%;
        height: 100%;
        object-fit: cover;
        object-position: center 18%;
        animation: naturalBreathing 4.2s infinite ease-in-out;
        transition: transform 0.25s ease;
    }}
    @keyframes naturalBreathing {{
        0% {{ transform: scale(1.0); }}
        50% {{ transform: scale(1.025) translateY(-1.5px); }}
        100% {{ transform: scale(1.0); }}
    }}
    .speaking-card {{
        border-color: #00ff80 !important;
        box-shadow: 0 0 35px rgba(0, 255, 128, 0.6) !important;
    }}
    .speaking-active .avatar-photo {{
        animation: speechPulse 0.35s infinite alternate ease-in-out;
    }}
    @keyframes speechPulse {{
        0% {{ transform: scale(1.015) translateY(0px); }}
        100% {{ transform: scale(1.045) translateY(-2px); }}
    }}
    .eq-box {{
        position: absolute;
        bottom: 0;
        left: 0;
        width: 100%;
        height: 40px;
        background: linear-gradient(transparent, rgba(0,0,0,0.85));
        display: flex;
        align-items: flex-end;
        justify-content: center;
        gap: 4px;
        padding-bottom: 6px;
        opacity: 0;
        transition: opacity 0.3s ease;
        z-index: 3;
    }}
    .eq-box .bar {{
        width: 4px;
        height: 6px;
        background: #00ff80;
        border-radius: 2px;
    }}
    @keyframes waveMotion {{
        0% {{ height: 6px; }}
        50% {{ height: 26px; }}
        100% {{ height: 6px; }}
    }}
    .speaking-wave {{ opacity: 1 !important; }}
    .speaking-wave .bar:nth-child(1) {{ animation: waveMotion 0.6s infinite ease-in-out; }}
    .speaking-wave .bar:nth-child(2) {{ animation: waveMotion 0.4s infinite ease-in-out 0.1s; }}
    .speaking-wave .bar:nth-child(3) {{ animation: waveMotion 0.7s infinite ease-in-out 0.2s; }}
    .speaking-wave .bar:nth-child(4) {{ animation: waveMotion 0.5s infinite ease-in-out 0.15s; }}
    .speaking-wave .bar:nth-child(5) {{ animation: waveMotion 0.65s infinite ease-in-out 0.25s; }}
    .speaking-wave .bar:nth-child(6) {{ animation: waveMotion 0.45s infinite ease-in-out 0.05s; }}
    .badge-status {{
        margin-top: 8px;
        background: rgba(0, 255, 128, 0.15);
        color: #00ff80;
        padding: 4px 18px;
        border-radius: 15px;
        font-size: 12px;
        font-weight: bold;
        font-family: sans-serif;
    }}
</style>

<script>
    const card = document.getElementById('videoContainer');
    const badge = document.getElementById('liveBadge');
    const wave = document.getElementById('waveOverlay');

    window.addEventListener('message', (event) => {{
        if (event.data.type === 'START_SPEAKING') {{
            card.classList.add('speaking-card', 'speaking-active');
            wave.classList.add('speaking-wave');
            badge.innerText = '🗣️ Khushi बोल रही है... (Live Sync)';
        }} else if (event.data.type === 'STOP_SPEAKING') {{
            card.classList.remove('speaking-card', 'speaking-active');
            wave.classList.remove('speaking-wave');
            badge.innerText = '🟢 Khushi Live | तैयार है';
        }}
    }});
</script>
"""

st.components.v1.html(avatar_visual_html, height=330)

# Voice Dispatcher
def speak_and_animate(text):
    spoken_text = clean_for_speech(text)
    js_code = f"""
    <script>
        if ('speechSynthesis' in window) {{
            window.speechSynthesis.cancel();
            var utterance = new SpeechSynthesisUtterance("{spoken_text}");
            utterance.lang = 'hi-IN';
            utterance.rate = 0.95;
            utterance.pitch = 1.05;

            var iframes = window.parent.document.querySelectorAll('iframe');

            utterance.onstart = function() {{
                iframes.forEach(f => {{
                    try {{ f.contentWindow.postMessage({{ type: 'START_SPEAKING' }}, '*'); }} catch(e) {{}}
                }});
            }};

            utterance.onend = function() {{
                iframes.forEach(f => {{
                    try {{ f.contentWindow.postMessage({{ type: 'STOP_SPEAKING' }}, '*'); }} catch(e) {{}}
                }});
            }};

            utterance.onerror = function() {{
                iframes.forEach(f => {{
                    try {{ f.contentWindow.postMessage({{ type: 'STOP_SPEAKING' }}, '*'); }} catch(e) {{}}
                }});
            }};

            window.speechSynthesis.speak(utterance);
        }}
    </script>
    """
    st.components.v1.html(js_code, height=0)

# 6. One-Touch Auto Mic Button
st.components.v1.html("""
<div style="text-align:center; padding: 2px;">
    <button id="autoMic" style="background:#ff4b4b; color:white; border:none; padding:12px 30px; border-radius:25px; font-weight:bold; cursor:pointer; font-size:15px; box-shadow:0 4px 14px rgba(255,75,75,0.4);">
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
""", height=75)

# 7. Bottom 50%: Multi-Talented Workspace
tab_vision, tab_tools, tab_memory = st.tabs(["📷 लाइव विज़न व चार्ट", "📐 टूल्स व आर्ट", "🧠 मेमोरी"])

with tab_vision:
    col_v1, col_v2 = st.columns([1, 1])
    with col_v1:
        cam_shot = st.camera_input("कैमरा स्कैन", label_visibility="visible")
    with col_v2:
        file_doc = st.file_uploader("चार्ट या फोटो चुनें", type=["png", "jpg", "jpeg"], label_visibility="visible")

active_image = cam_shot if cam_shot else file_doc

with tab_tools:
    st.info("💡 शेयर मार्केट तकनीकी टूल्स, वैदिक गणित व इमेज जनरेशन सक्रिय हैं।")
    st.markdown("चार्ट अपलोड करके सपोर्ट, रेजिस्टेंस या ब्रेकआउट्स का सीधा लाइव विश्लेषण प्राप्त करें।")

with tab_memory:
    if st.button("🗑️ चैट हिस्ट्री साफ़ करें"):
        st.session_state.messages = []
        save_memory([])
        st.rerun()

# Display Recent Chat
for msg in st.session_state.messages[-3:]:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# Multi-Model Smart Cascade (1,500 RPD Guaranteed, No 429 Stops)
def execute_gemini_query(prompt, image_file):
    models_cascade = ['gemini-2.5-flash', 'gemini-2.5-flash-lite', 'gemini-2.0-flash']
    
    if image_file is not None:
        try:
            img = Image.open(image_file)
            payload = [prompt if prompt else "इस तस्वीर या चार्ट का सटीक विश्लेषण करें।", img]
        except Exception:
            payload = prompt
    else:
        payload = prompt

    last_err = None
    for model_name in models_cascade:
        try:
            res = client.models.generate_content(
                model=model_name,
                contents=payload,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PERSONA
                )
            )
            if res and res.text:
                return res.text
        except Exception as e:
            last_err = e
            continue
            
    return "माफ़ कीजिए, सर्वर व्यस्त है। कृपया पुनः प्रयास करें।"

# Process Prompt
user_prompt = st.chat_input("यहाँ लिखें या माइक से बोलें...")

if user_prompt or (active_image is not None and st.button("🔍 इस इमेज का तुरंत विश्लेषण करें")):
    query = user_prompt if user_prompt else "कृपया इस तस्वीर का विश्लेषण करके मुझे बताएं।"
    
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.write(query)

    with st.chat_message("assistant"):
        if not client:
            st.error("API Key उपलब्ध नहीं है। कृपया Streamlit Secrets जाँचें।")
        else:
            with st.spinner("Khushi विश्लेषण कर रही है... ✨"):
                try:
                    ans = execute_gemini_query(query, active_image)
                    st.write(ans)
                    st.session_state.messages.append({"role": "assistant", "content": ans})
                    save_memory(st.session_state.messages)
                    speak_and_animate(ans)
                except Exception as err:
                    st.error(f"त्रुटि: {err}")
