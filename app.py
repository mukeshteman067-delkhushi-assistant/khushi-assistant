import streamlit as st
import json
import os
import re
import base64
from datetime import datetime, timezone, timedelta
from PIL import Image
from google import genai
from google.genai import types

# 1. Page Configuration (Full Responsive Mobile-First)
st.set_page_config(
    page_title="Khushi AI Companion",
    page_icon="🌸",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. Modern UI Layout & Viewport Lock Styling
st.markdown("""
<style>
    .block-container {
        padding-top: 0.1rem;
        padding-bottom: 5rem;
        padding-left: 0.5rem;
        padding-right: 0.5rem;
        max-width: 100%;
    }
    header, #MainMenu, footer { visibility: hidden; }
    
    /* Fixed Top Control Header */
    .sketch-header-box {
        position: -webkit-sticky;
        position: sticky;
        top: 0;
        z-index: 999;
        background: #0e1117;
        padding-bottom: 2px;
        border-bottom: 1px solid #1f293d;
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

# 5. Hand-Drawn Sketch Layout (Top 25% Section + Zoom + Push + Icons)
sketch_layout_html = f"""
<div id="masterSketchContainer" class="sketch-wrapper">
    <!-- Top Row: Left Avatar (25%) + Right Control Grid (75%) -->
    <div class="top-row">
        <!-- Left: Khushi Rectangular Avatar -->
        <div id="avatarFrame" class="avatar-rect" onclick="toggleZoom()" title="टैप करके ज़ूम इन / आउट करें">
            <img id="avatarImage" src="{khushi_b64}" class="avatar-photo" />
            <div id="waveOverlay" class="eq-box">
                <div class="bar"></div><div class="bar"></div><div class="bar"></div>
                <div class="bar"></div><div class="bar"></div>
            </div>
        </div>

        <!-- Right: Header & 4 Icon Grid -->
        <div class="controls-grid-container">
            <div class="header-status">
                <span class="dot-live">●</span>
                <span id="statusText" class="title-text">खुशी Live</span>
            </div>

            <!-- 2x2 Action Icons Grid (① ज़ूम इन, ② पुश, ③ कैमरा, ④ सेटिंग्स) -->
            <div class="icon-grid">
                <button id="zoomBtn" onclick="toggleZoom()" class="grid-btn btn-zoom" title="① ज़ूम इन">
                    <span class="btn-num">①</span> ⛶ ज़ूम इन
                </button>
                <button id="stopBtn" onclick="interruptSpeech()" class="grid-btn btn-push" title="② पुश (बोलना रोकें)">
                    <span class="btn-num">②</span> 🛑 पुश
                </button>
                <button onclick="triggerCameraExpander()" class="grid-btn btn-cam" title="③ कैमरा">
                    <span class="btn-num">③</span> 📷 कैमरा
                </button>
                <button onclick="triggerSettingsExpander()" class="grid-btn btn-gear" title="④ सेटिंग्स">
                    <span class="btn-num">④</span> ⚙️ सेटिंग्स
                </button>
            </div>
        </div>
    </div>

    <!-- ⑤ Wide Action Bar: माइक व स्पीकर एक्टिव (One-Touch Audio & Voice) -->
    <div class="mic-speaker-bar">
        <button id="autoMic" class="wide-mic-btn">
            🎙️ ⑤ माइक व स्पीकर एक्टिव (टैप करें और बोलें)
        </button>
        <p id="micState" class="mic-status-msg">तैयार है... बटन दबाकर बोलें</p>
    </div>
</div>

<style>
    .sketch-wrapper {{
        width: 100%;
        background: linear-gradient(145deg, #131526, #090a14);
        border-radius: 14px;
        padding: 8px 10px;
        border: 1px solid #2e3856;
        box-shadow: 0 4px 20px rgba(0,0,0,0.7);
        position: relative;
        transition: all 0.35s ease;
    }}

    /* Cinema-Grade 1-Click Zoom-In Mode */
    .sketch-wrapper.full-zoom-mode {{
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        width: 100vw !important;
        height: 94vh !important;
        z-index: 999999 !important;
        border-radius: 0 !important;
        background: #06060c !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: center !important;
        align-items: center !important;
        padding: 12px !important;
    }}

    .sketch-wrapper.full-zoom-mode .avatar-rect {{
        width: 95% !important;
        max-width: 650px !important;
        height: 82vh !important;
        border-color: #00ff80 !important;
    }}

    .sketch-wrapper.full-zoom-mode .controls-grid-container {{
        position: absolute;
        top: 15px;
        right: 15px;
        width: auto !important;
    }}

    .sketch-wrapper.full-zoom-mode .icon-grid {{
        display: flex !important;
        flex-direction: column !important;
        gap: 6px !important;
    }}

    .sketch-wrapper.full-zoom-mode .mic-speaker-bar {{
        display: none !important;
    }}

    .top-row {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 10px;
    }}

    /* Left Rectangular Avatar (25% Width Frame) */
    .avatar-rect {{
        position: relative;
        width: 110px;
        height: 110px;
        border-radius: 12px;
        overflow: hidden;
        border: 2px solid #ff4b4b;
        box-shadow: 0 0 15px rgba(255,75,75,0.35);
        cursor: pointer;
        background: #0e0e18;
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
        box-shadow: 0 0 25px rgba(0, 255, 128, 0.65) !important;
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
        height: 24px;
        background: linear-gradient(transparent, rgba(0,0,0,0.9));
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
        50% {{ height: 16px; }}
        100% {{ height: 4px; }}
    }}

    .speaking-wave {{ opacity: 1 !important; }}
    .speaking-wave .bar:nth-child(1) {{ animation: waveMotion 0.5s infinite ease-in-out; }}
    .speaking-wave .bar:nth-child(2) {{ animation: waveMotion 0.35s infinite ease-in-out 0.1s; }}
    .speaking-wave .bar:nth-child(3) {{ animation: waveMotion 0.6s infinite ease-in-out 0.2s; }}
    .speaking-wave .bar:nth-child(4) {{ animation: waveMotion 0.45s infinite ease-in-out 0.15s; }}
    .speaking-wave .bar:nth-child(5) {{ animation: waveMotion 0.55s infinite ease-in-out 0.05s; }}

    /* Right Controls Container */
    .controls-grid-container {{
        flex: 1;
        display: flex;
        flex-direction: column;
        gap: 6px;
    }}

    .header-status {{
        display: flex;
        align-items: center;
        gap: 6px;
        background: rgba(255,255,255,0.05);
        padding: 3px 8px;
        border-radius: 8px;
        width: fit-content;
    }}

    .dot-live {{
        color: #00ff80;
        font-size: 11px;
    }}

    .title-text {{
        color: #f1f5f9;
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 0.5px;
    }}

    .icon-grid {{
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 5px;
    }}

    .grid-btn {{
        padding: 6px 4px;
        border-radius: 8px;
        font-size: 11px;
        font-weight: 600;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 3px;
        border: 1px solid transparent;
        transition: all 0.2s ease;
    }}

    .btn-num {{
        font-size: 10px;
        opacity: 0.75;
    }}

    .btn-zoom {{
        background: #1e293b;
        color: #38bdf8;
        border-color: #38bdf8;
    }}
    .btn-zoom:hover {{
        background: #38bdf8;
        color: #0f172a;
    }}

    .btn-push {{
        background: #3b1414;
        color: #f87171;
        border-color: #ef4444;
    }}
    .btn-push:hover {{
        background: #ef4444;
        color: #fff;
    }}

    .btn-cam {{
        background: #1e293b;
        color: #fbbf24;
        border-color: #f59e0b;
    }}
    .btn-cam:hover {{
        background: #f59e0b;
        color: #0f172a;
    }}

    .btn-gear {{
        background: #1e293b;
        color: #a78bfa;
        border-color: #8b5cf6;
    }}
    .btn-gear:hover {{
        background: #8b5cf6;
        color: #fff;
    }}

    /* ⑤ Wide Mic & Speaker Bar */
    .mic-speaker-bar {{
        margin-top: 8px;
        text-align: center;
    }}

    .wide-mic-btn {{
        width: 100%;
        background: linear-gradient(90deg, #ff4b4b, #e02424);
        color: #fff;
        border: none;
        padding: 9px 12px;
        border-radius: 20px;
        font-size: 13px;
        font-weight: 700;
        cursor: pointer;
        box-shadow: 0 4px 12px rgba(255,75,75,0.35);
        transition: all 0.2s ease;
    }}
    .wide-mic-btn:hover {{
        transform: translateY(-1px);
        box-shadow: 0 6px 16px rgba(255,75,75,0.5);
    }}

    .mic-status-msg {{
        font-size: 11px;
        color: #94a3b8;
        margin-top: 3px;
        margin-bottom: 0;
    }}
</style>

<script>
    const wrapper = document.getElementById('masterSketchContainer');
    const zoomBtn = document.getElementById('zoomBtn');
    const avatar = document.getElementById('avatarFrame');
    const statusText = document.getElementById('statusText');
    const wave = document.getElementById('waveOverlay');
    const autoMicBtn = document.getElementById('autoMic');
    const micStatus = document.getElementById('micState');

    let isZoomed = false;

    // ① ज़ूम इन / ज़ूम आउट टॉगल
    function toggleZoom() {{
        isZoomed = !isZoomed;
        if (isZoomed) {{
            wrapper.classList.add('full-zoom-mode');
            zoomBtn.innerHTML = '<span class="btn-num">①</span> ✕ छोटा करें';
            zoomBtn.style.color = '#fff';
            zoomBtn.style.borderColor = '#fff';
        }} else {{
            wrapper.classList.remove('full-zoom-mode');
            zoomBtn.innerHTML = '<span class="btn-num">①</span> ⛶ ज़ूम इन';
            zoomBtn.style.color = '#38bdf8';
            zoomBtn.style.borderColor = '#38bdf8';
        }}
    }}

    // ② पुश (बीच में बोलना रोकें)
    function interruptSpeech() {{
        if ('speechSynthesis' in window) {{
            window.speechSynthesis.cancel();
        }}
        avatar.classList.remove('speaking-card', 'speaking-active');
        wave.classList.remove('speaking-wave');
        statusText.innerText = 'खुशी Live | शांत';
    }}

    // ③ कैमरा स्क्रोल/ओपनर
    function triggerCameraExpander() {{
        const exp = window.parent.document.querySelector('details[data-testid="stExpander"]');
        if (exp) {{
            exp.open = true;
            exp.scrollIntoView({{ behavior: 'smooth' }});
        }}
    }}

    // ④ सेटिंग्स ओपनर
    function triggerSettingsExpander() {{
        const expanders = window.parent.document.querySelectorAll('details[data-testid="stExpander"]');
        if (expanders.length > 1) {{
            expanders[1].open = true;
            expanders[1].scrollIntoView({{ behavior: 'smooth' }});
        }}
    }}

    // ⑤ माइक व वॉइस रिकग्निशन
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    function unlockAudio() {{
        if ('speechSynthesis' in window) {{
            var silent = new SpeechSynthesisUtterance("");
            window.speechSynthesis.speak(silent);
        }}
    }}

    if (SpeechRecognition) {{
        const recognition = new SpeechRecognition();
        recognition.lang = 'hi-IN';
        recognition.continuous = false;
        recognition.interimResults = false;

        autoMicBtn.onclick = () => {{
            unlockAudio();
            recognition.start();
            micStatus.innerText = "सुन रही हूँ... बोलिए 🎙️";
            autoMicBtn.style.background = "linear-gradient(90deg, #10b981, #059669)";
        }};

        recognition.onresult = (event) => {{
            const text = event.results[0][0].transcript;
            micStatus.innerText = "भेजा जा रहा है: " + text;
            autoMicBtn.style.background = "linear-gradient(90deg, #ff4b4b, #e02424)";

            const nativeTextAreaValueSetter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, "value").set;
            const input = window.parent.document.querySelector('textarea[data-testid="stChatInputTextArea"]');
            
            if (input) {{
                nativeTextAreaValueSetter.call(input, text);
                input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                setTimeout(() => {{
                    const sendBtn = window.parent.document.querySelector('button[data-testid="stChatInputSubmitButton"]');
                    if (sendBtn) {{
                        sendBtn.click();
                    }} else {{
                        input.dispatchEvent(new KeyboardEvent('keydown', {{ key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true }}));
                    }}
                }}, 300);
            }}
        }};

        recognition.onerror = () => {{
            micStatus.innerText = "माइक एरर या अनुमति नहीं मिली";
            autoMicBtn.style.background = "linear-gradient(90deg, #ff4b4b, #e02424)";
        }};
    }} else {{
        micStatus.innerText = "ब्राउज़र में वॉइस सपोर्ट उपलब्ध नहीं है";
    }}

    window.addEventListener('message', (event) => {{
        if (event.data.type === 'START_SPEAKING') {{
            avatar.classList.add('speaking-card', 'speaking-active');
            wave.classList.add('speaking-wave');
            statusText.innerText = '🗣️ बोल रही है...';
        }} else if (event.data.type === 'STOP_SPEAKING') {{
            avatar.classList.remove('speaking-card', 'speaking-active');
            wave.classList.remove('speaking-wave');
            statusText.innerText = 'खुशी Live | तैयार है';
        }}
    }});
</script>
"""

# Render Sketch Layout as Fixed Header
st.markdown('<div class="sketch-header-box">', unsafe_allow_html=True)
st.components.v1.html(sketch_layout_html, height=195)
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

# 6. Expandable Tools (③ कैमरा व स्कैनर & ④ सेटिंग्स)
active_image = None
with st.expander("📷 ③ कैमरा स्कैन व चार्ट अपलोडर", expanded=False):
    col_c1, col_c2 = st.columns([1, 1])
    with col_c1:
        cam_shot = st.camera_input("कैमरा स्कैन", label_visibility="collapsed")
    with col_c2:
        file_doc = st.file_uploader("चार्ट या गैलरी फोटो", type=["png", "jpg", "jpeg"], label_visibility="collapsed")
    active_image = cam_shot if cam_shot else file_doc

with st.expander("⚙️ ④ सेटिंग्स व मेमोरी", expanded=False):
    st.info("💡 शेयर मार्केट तकनीकी विश्लेषण, वैदिक गणित और मेमोरी मैनेजमेंट।")
    if st.button("🗑️ चैट हिस्ट्री साफ़ करें"):
        st.session_state.messages = []
        save_memory([])
        st.rerun()

# 7. Chat Messages Display Window
for msg in st.session_state.messages[-4:]:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# Intelligent Multi-Model Cascade (1,500 RPD Shield - Never Stops)
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

# Bottom Input Bar (Sticky above keypad)
user_prompt = st.chat_input("यहाँ लिखें या ऊपर ⑤ माइक बटन दबाकर बोलें...")

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
