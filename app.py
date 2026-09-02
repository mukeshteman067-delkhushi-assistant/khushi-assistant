import streamlit as st
import json
import os
import re
import base64
from datetime import datetime, timezone, timedelta
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

# 2. Ultra-Clean Layout Styling (Mobile & Desktop Responsive)
st.markdown("""
<style>
    .block-container {
        padding-top: 0.1rem;
        padding-bottom: 5.5rem;
        padding-left: 0.6rem;
        padding-right: 0.6rem;
        max-width: 100%;
    }
    header, #MainMenu, footer { visibility: hidden; }
    
    /* Sticky Top Control Header */
    .sticky-header {
        position: -webkit-sticky;
        position: sticky;
        top: 0;
        z-index: 999;
        background: #0e1117;
        padding-bottom: 4px;
        border-bottom: 1px solid #22223b;
    }
</style>
""", unsafe_allow_html=True)

# 3. Base64 Original Image Ingestion
def get_image_base64():
    if os.path.exists("khushi.jpg"):
        try:
            with open("khushi.jpg", "rb") as img_file:
                return f"data:image/jpeg;base64,{base64.b64encode(img_file.read()).decode('utf-8')}"
        except Exception:
            return ""
    return ""

khushi_b64 = get_image_base64()

# 4. Engine & Keys Setup (Auto-Clean)
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

# Long-Term Persistent Memory
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

# 5. Top 25% Split Header: Rectangular Viewport + Zoom Controls + Speech Push/Stop
top_header_html = f"""
<div id="topHeaderContainer" class="split-viewport-wrapper">
    <!-- Left Rectangular Avatar (Corner Frame) -->
    <div id="avatarFrame" class="rect-avatar" onclick="toggleZoom()" title="टैप करके ज़ूम इन / आउट करें">
        <img id="avatarImage" src="{khushi_b64}" class="avatar-photo" />
        <div id="waveOverlay" class="eq-box">
            <div class="bar"></div><div class="bar"></div><div class="bar"></div>
            <div class="bar"></div><div class="bar"></div>
        </div>
    </div>

    <!-- Right Quick Controls & Push Engine -->
    <div class="control-panel">
        <div class="status-indicator">
            <span id="liveDot" style="color:#00ff80;">●</span> <span id="statusLabel" style="color:#e0e0e0; font-size:11px; font-weight:bold;">Khushi Live</span>
        </div>
        <div class="action-buttons">
            <button id="zoomBtn" onclick="toggleZoom()" class="tool-btn zoom-btn">⛶ ज़ूम इन</button>
            <button id="stopBtn" onclick="interruptSpeech()" class="tool-btn stop-btn">🛑 रोकें / पुश</button>
        </div>
    </div>
</div>

<style>
    .split-viewport-wrapper {{
        width: 100%;
        height: 145px;
        background: linear-gradient(135deg, #151528, #090914);
        border-radius: 14px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 8px 12px;
        border: 1px solid #3d3d66;
        box-shadow: 0 4px 20px rgba(0,0,0,0.65);
        position: relative;
        transition: all 0.4s ease;
    }}

    /* Cinema-Grade 1-Click Zoom-In Mode */
    .split-viewport-wrapper.full-zoom-mode {{
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        width: 100vw !important;
        height: 94vh !important;
        z-index: 999999 !important;
        border-radius: 0 !important;
        background: #06060c !important;
        flex-direction: column !important;
        justify-content: center !important;
        padding: 10px !important;
    }}

    .split-viewport-wrapper.full-zoom-mode .rect-avatar {{
        width: 95% !important;
        max-width: 650px !important;
        height: 82vh !important;
        border-color: #00ff80 !important;
    }}

    .split-viewport-wrapper.full-zoom-mode .control-panel {{
        position: absolute;
        top: 15px;
        right: 15px;
        width: auto !important;
    }}

    .rect-avatar {{
        position: relative;
        width: 125px;
        height: 125px;
        border-radius: 12px;
        overflow: hidden;
        border: 2px solid #ff4b4b;
        box-shadow: 0 0 15px rgba(255,75,75,0.3);
        cursor: pointer;
        background: #11111d;
        flex-shrink: 0;
        transition: all 0.3s ease;
    }}

    .avatar-photo {{
        width: 100%;
        height: 100%;
        object-fit: cover;
        object-position: center 15%;
        animation: naturalBreathing 4.5s infinite ease-in-out;
        transition: transform 0.25s ease;
    }}

    @keyframes naturalBreathing {{
        0% {{ transform: scale(1.0); }}
        50% {{ transform: scale(1.03) translateY(-1px); }}
        100% {{ transform: scale(1.0); }}
    }}

    .speaking-card {{
        border-color: #00ff80 !important;
        box-shadow: 0 0 25px rgba(0, 255, 128, 0.6) !important;
    }}

    .speaking-active .avatar-photo {{
        animation: activePulse 0.32s infinite alternate ease-in-out;
    }}

    @keyframes activePulse {{
        0% {{ transform: scale(1.02); }}
        100% {{ transform: scale(1.06); }}
    }}

    .eq-box {{
        position: absolute;
        bottom: 0;
        left: 0;
        width: 100%;
        height: 28px;
        background: linear-gradient(transparent, rgba(0,0,0,0.85));
        display: flex;
        align-items: flex-end;
        justify-content: center;
        gap: 3px;
        padding-bottom: 3px;
        opacity: 0;
        transition: opacity 0.3s ease;
        z-index: 3;
    }}

    .eq-box .bar {{
        width: 3px;
        height: 4px;
        background: #00ff80;
        border-radius: 2px;
    }}

    @keyframes waveMotion {{
        0% {{ height: 4px; }}
        50% {{ height: 18px; }}
        100% {{ height: 4px; }}
    }}

    .speaking-wave {{ opacity: 1 !important; }}
    .speaking-wave .bar:nth-child(1) {{ animation: waveMotion 0.5s infinite ease-in-out; }}
    .speaking-wave .bar:nth-child(2) {{ animation: waveMotion 0.35s infinite ease-in-out 0.1s; }}
    .speaking-wave .bar:nth-child(3) {{ animation: waveMotion 0.6s infinite ease-in-out 0.2s; }}
    .speaking-wave .bar:nth-child(4) {{ animation: waveMotion 0.45s infinite ease-in-out 0.15s; }}
    .speaking-wave .bar:nth-child(5) {{ animation: waveMotion 0.55s infinite ease-in-out 0.05s; }}

    .control-panel {{
        flex: 1;
        display: flex;
        flex-direction: column;
        align-items: flex-end;
        justify-content: center;
        padding-left: 10px;
        gap: 8px;
    }}

    .status-indicator {{
        background: rgba(255,255,255,0.06);
        padding: 3px 10px;
        border-radius: 12px;
        border: 1px solid rgba(255,255,255,0.1);
    }}

    .action-buttons {{
        display: flex;
        gap: 8px;
    }}

    .tool-btn {{
        border: none;
        padding: 7px 12px;
        border-radius: 18px;
        font-size: 11px;
        font-weight: bold;
        cursor: pointer;
        transition: all 0.2s ease;
    }}

    .zoom-btn {{
        background: #1e293b;
        color: #38bdf8;
        border: 1px solid #38bdf8;
    }}
    .zoom-btn:hover {{
        background: #38bdf8;
        color: #000;
    }}

    .stop-btn {{
        background: #3f1515;
        color: #ff6b6b;
        border: 1px solid #ff4b4b;
    }}
    .stop-btn:hover {{
        background: #ff4b4b;
        color: white;
    }}
</style>

<script>
    const wrapper = document.getElementById('topHeaderContainer');
    const zoomBtn = document.getElementById('zoomBtn');
    const avatar = document.getElementById('avatarFrame');
    const statusLabel = document.getElementById('statusLabel');
    const wave = document.getElementById('waveOverlay');

    let isZoomed = false;

    function toggleZoom() {{
        isZoomed = !isZoomed;
        if (isZoomed) {{
            wrapper.classList.add('full-zoom-mode');
            zoomBtn.innerText = '✕ छोटा करें';
            zoomBtn.style.color = '#fff';
            zoomBtn.style.borderColor = '#fff';
        }} else {{
            wrapper.classList.remove('full-zoom-mode');
            zoomBtn.innerText = '⛶ ज़ूम इन';
            zoomBtn.style.color = '#38bdf8';
            zoomBtn.style.borderColor = '#38bdf8';
        }}
    }}

    function interruptSpeech() {{
        if ('speechSynthesis' in window) {{
            window.speechSynthesis.cancel();
        }}
        avatar.classList.remove('speaking-card', 'speaking-active');
        wave.classList.remove('speaking-wave');
        statusLabel.innerText = 'Khushi Live | स्टैंडबाय';
    }}

    window.addEventListener('message', (event) => {{
        if (event.data.type === 'START_SPEAKING') {{
            avatar.classList.add('speaking-card', 'speaking-active');
            wave.classList.add('speaking-wave');
            statusLabel.innerText = '🗣️ बोल रही है...';
        }} else if (event.data.type === 'STOP_SPEAKING') {{
            avatar.classList.remove('speaking-card', 'speaking-active');
            wave.classList.remove('speaking-wave');
            statusLabel.innerText = 'Khushi Live | तैयार है';
        }}
    }});
</script>
"""

# Render Sticky Top 25% Viewport
st.markdown('<div class="sticky-header">', unsafe_allow_html=True)
st.components.v1.html(top_header_html, height=155)
st.markdown('</div>', unsafe_allow_html=True)

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
    <button id="autoMic" style="background:#ff4b4b; color:white; border:none; padding:10px 26px; border-radius:22px; font-weight:bold; cursor:pointer; font-size:14px; box-shadow:0 4px 12px rgba(255,75,75,0.35);">
        🎙️ बोलें (माइक व स्पीकर एक्टिव)
    </button>
    <p id="micState" style="font-size:11px; color:#888; margin-top:4px;">बटन दबाकर बोलें...</p>
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
""", height=65)

# 7. On-Demand Tools Expander (No Always-On Camera taking screen space)
active_image = None
with st.expander("📷 चार्ट या इमेज कैप्चर करें (ऑन-डिमांड कैमरा व स्कैनर)", expanded=False):
    col_opt1, col_opt2 = st.columns([1, 1])
    with col_opt1:
        cam_shot = st.camera_input("कैमरा स्कैन", label_visibility="collapsed")
    with col_opt2:
        file_doc = st.file_uploader("चार्ट या गैलरी फोटो", type=["png", "jpg", "jpeg"], label_visibility="collapsed")
    active_image = cam_shot if cam_shot else file_doc

with st.expander("⚙️ सेटिंग्स, टूल्स व मेमोरी", expanded=False):
    st.info("💡 शेयर मार्केट तकनीकी विश्लेषण, वैदिक गणित और मेमोरी मैनेजमेंट।")
    if st.button("🗑️ चैट हिस्ट्री साफ़ करें"):
        st.session_state.messages = []
        save_memory([])
        st.rerun()

# Display Recent Chat
for msg in st.session_state.messages[-3:]:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# Intelligent Multi-Model Cascade (1,500 RPD Shield)
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
