import streamlit as st
import json
import os
import re
import base64
from datetime import datetime, timezone, timedelta
from PIL import Image
from google import genai
from google.genai import types

# 1. Page Configuration (Responsive Mobile-First)
st.set_page_config(
    page_title="Khushi AI Companion",
    page_icon="🌸",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. Ultra-Clean Layout Styling
st.markdown("""
<style>
    .block-container {
        padding-top: 0.1rem;
        padding-bottom: 5rem;
        padding-left: 0.6rem;
        padding-right: 0.6rem;
        max-width: 100%;
    }
    header, #MainMenu, footer { visibility: hidden; }
    
    /* Fixed Top Control Header */
    .sticky-header-panel {
        position: -webkit-sticky;
        position: sticky;
        top: 0;
        z-index: 999;
        background: #0b0d14;
        padding-bottom: 6px;
        border-bottom: 1px solid #1e2238;
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

# 4. Engine & Keys Setup (Auto-Sanitized)
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

# 5. Top 50% Section: 25% Large Rectangular Avatar + 25% Action Controls + Full Action Strip
pro_header_html = f"""
<div id="masterHeader" class="pro-header-wrapper">
    <!-- 50% Upper Section Split: Left 25% Avatar + Right 25% Controls -->
    <div class="split-row">
        <!-- Left 25%: Enlarged Rectangular Avatar -->
        <div id="avatarFrame" class="avatar-portrait" onclick="toggleZoom()" title="ज़ूम करने के लिए टैप करें">
            <img id="avatarImage" src="{khushi_b64}" class="avatar-photo" />
            <div id="waveOverlay" class="eq-box">
                <div class="bar"></div><div class="bar"></div><div class="bar"></div>
                <div class="bar"></div><div class="bar"></div>
            </div>
        </div>

        <!-- Right 25%: Pro Control Grid -->
        <div class="controls-column">
            <div class="status-badge">
                <span class="pulse-dot">●</span>
                <span id="statusLabel">Khushi Live</span>
            </div>

            <div class="actions-grid">
                <button id="zoomBtn" onclick="toggleZoom()" class="pro-btn btn-zoom" title="फुल डिस्प्ले ज़ूम">
                    ⛶ ज़ूम इन
                </button>
                <button id="stopBtn" onclick="interruptSpeech()" class="pro-btn btn-pause" title="बोलना बीच में रोकें">
                    🛑 पुश / स्टॉप
                </button>
                <button id="camToggleBtn" onclick="toggleToolsModal('cameraModal')" class="pro-btn btn-camera" title="कैमरा व इमेज अपलोड">
                    📷 कैमरा
                </button>
                <button id="settingsToggleBtn" onclick="toggleToolsModal('settingsModal')" class="pro-btn btn-settings" title="टूल्स व सेटिंग्स">
                    ⚙️ सेटिंग्स
                </button>
            </div>
        </div>
    </div>

    <!-- Wide Action Strip: माइक व स्पीकर एक्टिव -->
    <div class="action-strip">
        <button id="autoMic" class="mic-trigger-btn">
            🎙️ माइक व स्पीकर एक्टिव (बोलने के लिए टैप करें)
        </button>
        <p id="micState" class="mic-hint-text">माइक तैयार है... बटन दबाकर बोलें</p>
    </div>
</div>

<style>
    .pro-header-wrapper {{
        width: 100%;
        background: linear-gradient(145deg, #111424, #080912);
        border-radius: 16px;
        padding: 10px 12px;
        border: 1px solid #252b48;
        box-shadow: 0 6px 24px rgba(0, 0, 0, 0.75);
        position: relative;
        transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
    }}

    /* Cinema-Grade 1-Click Zoom-In View */
    .pro-header-wrapper.full-zoom-mode {{
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        width: 100vw !important;
        height: 95vh !important;
        z-index: 999999 !important;
        border-radius: 0 !important;
        background: #04050a !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: center !important;
        align-items: center !important;
        padding: 12px !important;
    }}

    .pro-header-wrapper.full-zoom-mode .avatar-portrait {{
        width: 95% !important;
        max-width: 680px !important;
        height: 84vh !important;
        border-color: #00ff80 !important;
        box-shadow: 0 0 35px rgba(0, 255, 128, 0.5) !important;
    }}

    .pro-header-wrapper.full-zoom-mode .controls-column {{
        position: absolute;
        top: 15px;
        right: 15px;
    }}

    .pro-header-wrapper.full-zoom-mode .actions-grid {{
        display: flex !important;
        flex-direction: column !important;
        gap: 8px !important;
    }}

    .pro-header-wrapper.full-zoom-mode .action-strip {{
        display: none !important;
    }}

    .split-row {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 12px;
    }}

    /* Left 25% Section: Enlarged Frame for Perfect Visual Prominence */
    .avatar-portrait {{
        position: relative;
        width: 140px;
        height: 140px;
        border-radius: 14px;
        overflow: hidden;
        border: 2px solid #ff4b4b;
        box-shadow: 0 0 18px rgba(255, 75, 75, 0.35);
        cursor: pointer;
        background: #0c0d16;
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
        box-shadow: 0 0 28px rgba(0, 255, 128, 0.65) !important;
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
        background: linear-gradient(transparent, rgba(0,0,0,0.92));
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

    /* Right 25% Section: Action Controls */
    .controls-column {{
        flex: 1;
        display: flex;
        flex-direction: column;
        gap: 8px;
    }}

    .status-badge {{
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(255, 255, 255, 0.05);
        padding: 4px 10px;
        border-radius: 10px;
        width: fit-content;
        border: 1px solid rgba(255, 255, 255, 0.08);
        font-size: 11px;
        font-weight: 700;
        color: #e2e8f0;
    }}

    .pulse-dot {{
        color: #00ff80;
        font-size: 10px;
    }}

    .actions-grid {{
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 6px;
    }}

    .pro-btn {{
        padding: 7px 6px;
        border-radius: 9px;
        font-size: 11px;
        font-weight: 600;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 4px;
        border: 1px solid transparent;
        transition: all 0.2s ease;
    }}

    .btn-zoom {{
        background: #182235;
        color: #38bdf8;
        border-color: #2563eb;
    }}
    .btn-zoom:hover {{
        background: #2563eb;
        color: #fff;
    }}

    .btn-pause {{
        background: #331417;
        color: #f87171;
        border-color: #dc2626;
    }}
    .btn-pause:hover {{
        background: #dc2626;
        color: #fff;
    }}

    .btn-camera {{
        background: #262016;
        color: #fbbf24;
        border-color: #d97706;
    }}
    .btn-camera:hover {{
        background: #d97706;
        color: #000;
    }}

    .btn-settings {{
        background: #201a33;
        color: #c084fc;
        border-color: #7c3aed;
    }}
    .btn-settings:hover {{
        background: #7c3aed;
        color: #fff;
    }}

    /* Full Action Strip */
    .action-strip {{
        margin-top: 9px;
        text-align: center;
    }}

    .mic-trigger-btn {{
        width: 100%;
        background: linear-gradient(90deg, #ff4b4b, #e02424);
        color: #fff;
        border: none;
        padding: 10px 14px;
        border-radius: 22px;
        font-size: 13px;
        font-weight: 700;
        cursor: pointer;
        box-shadow: 0 4px 14px rgba(255, 75, 75, 0.35);
        transition: all 0.2s ease;
    }}
    .mic-trigger-btn:hover {{
        transform: translateY(-1px);
        box-shadow: 0 6px 18px rgba(255, 75, 75, 0.5);
    }}

    .mic-hint-text {{
        font-size: 11px;
        color: #94a3b8;
        margin-top: 4px;
        margin-bottom: 0;
    }}
</style>

<script>
    const wrapper = document.getElementById('masterHeader');
    const zoomBtn = document.getElementById('zoomBtn');
    const avatar = document.getElementById('avatarFrame');
    const statusLabel = document.getElementById('statusLabel');
    const wave = document.getElementById('waveOverlay');
    const autoMicBtn = document.getElementById('autoMic');
    const micStatus = document.getElementById('micState');

    let isZoomed = false;

    // 1-Click Zoom Toggle
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
            zoomBtn.style.borderColor = '#2563eb';
        }}
    }}

    // Push / Speech Stop Interruption
    function interruptSpeech() {{
        if ('speechSynthesis' in window) {{
            window.speechSynthesis.cancel();
        }}
        avatar.classList.remove('speaking-card', 'speaking-active');
        wave.classList.remove('speaking-wave');
        statusLabel.innerText = 'Khushi Live | शांत';
    }}

    // Toggle Camera & Settings Floating Panels
    function toggleToolsModal(toolId) {{
        const target = window.parent.document.getElementById(toolId);
        if (target) {{
            target.style.display = target.style.display === 'none' ? 'block' : 'none';
            target.scrollIntoView({{ behavior: 'smooth' }});
        }}
    }}

    // One-Touch Speech Recognition
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
                        input.dispatchEvent(new KeyboardEvent('keydown', {{ key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true }));
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
            statusLabel.innerText = '🗣️ बोल रही है...';
        }} else if (event.data.type === 'STOP_SPEAKING') {{
            avatar.classList.remove('speaking-card', 'speaking-active');
            wave.classList.remove('speaking-wave');
            statusLabel.innerText = 'Khushi Live | तैयार है';
        }}
    }});
</script>
"""

# Render Sticky Top 50% Section
st.markdown('<div class="sticky-header-panel">', unsafe_allow_html=True)
st.components.v1.html(pro_header_html, height=210)
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

# 6. Integrated Tool Popups (Camera & Settings - No Duplication)
active_image = None
with st.container():
    st.markdown('<div id="cameraModal" style="display:none; padding:10px; background:#131826; border-radius:12px; margin-bottom:8px; border:1px solid #28334f;">', unsafe_allow_html=True)
    st.markdown("<p style='font-size:12px; color:#fbbf24; font-weight:bold; margin-bottom:6px;'>📷 कैमरा स्कैन या चार्ट फ़ोटो अपलोड करें:</p>", unsafe_allow_html=True)
    col_c1, col_c2 = st.columns([1, 1])
    with col_c1:
        cam_shot = st.camera_input("कैमरा", label_visibility="collapsed")
    with col_c2:
        file_doc = st.file_uploader("गैलरी / चार्ट", type=["png", "jpg", "jpeg"], label_visibility="collapsed")
    active_image = cam_shot if cam_shot else file_doc
    st.markdown('</div>', unsafe_allow_html=True)

with st.container():
    st.markdown('<div id="settingsModal" style="display:none; padding:10px; background:#131826; border-radius:12px; margin-bottom:8px; border:1px solid #28334f;">', unsafe_allow_html=True)
    st.markdown("<p style='font-size:12px; color:#c084fc; font-weight:bold; margin-bottom:4px;'>⚙️ सिस्टम टूल्स व मेमोरी:</p>", unsafe_allow_html=True)
    if st.button("🗑️ चैट हिस्ट्री साफ़ करें"):
        st.session_state.messages = []
        save_memory([])
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# 7. Clean Chat Messages History Display
for msg in st.session_state.messages[-4:]:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# Multi-Model Smart Cascade (1,500 RPD Shield - Never Stops)
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
user_prompt = st.chat_input("यहाँ लिखें या माइक बटन दबाकर बोलें...")

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
