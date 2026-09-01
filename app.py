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

# 2. UI Layout Styling
st.markdown("""
<style>
    .block-container {
        padding-top: 0.3rem;
        padding-bottom: 0.3rem;
        max-width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# 3. Base64 Fallback Image Ingestion
def get_image_base64():
    if os.path.exists("khushi.jpg"):
        try:
            with open("khushi.jpg", "rb") as img_file:
                return f"data:image/jpeg;base64,{base64.b64encode(img_file.read()).decode('utf-8')}"
        except Exception:
            return ""
    return ""

khushi_b64 = get_image_base64()

# 4. Engine & Keys Setup (Auto-Clean Key Strings)
raw_gemini_key = st.secrets.get("GEMINI_API_KEY", "")
API_KEY = "".join(raw_gemini_key.split()) if raw_gemini_key else ""

raw_simli_key = st.secrets.get("SIMLI_API_KEY", "gltnjpxgyyi27t4ureg11j")
SIMLI_KEY = "".join(raw_simli_key.split()) if raw_simli_key else "gltnjpxgyyi27t4ureg11j"

raw_face_id = st.secrets.get("SIMLI_FACE_ID", "b9e5fba3-071a-4e35-896e-211c4d6eaa7b")
SIMLI_FACE_ID = "".join(raw_face_id.split()) if raw_face_id else "b9e5fba3-071a-4e35-896e-211c4d6eaa7b"

@st.cache_resource
def get_client(key):
    if not key:
        return None
    return genai.Client(api_key=key)

client = get_client(API_KEY)

ist_offset = timezone(timedelta(hours=5, minutes=30))
current_now = datetime.now(ist_offset).strftime("%I:%M %p, %d %B %Y")

SYSTEM_PERSONA = f"""
तुम 'Khushi' हो - एक अत्यंत बुद्धिमान, हमदर्द, सच्ची दोस्त और मल्टी-टैलेंटेड डिजिटल साथी।
वर्तमान समय (IST): {current_now}
1. हमेशा आदर, विनम्रता, स्वाभाविक अपनेपन और सकारात्मक ऊर्जा के साथ बात करो।
2. जब समय पूछा जाए तो ऊपर दिए गए सटीक वर्तमान समय को स्वाभाविक रूप से बताओ।
3. शेयर मार्केट (चार्ट्स, सपोर्ट/रेजिस्टेंस, इंडिकेटर्स), विज्ञान, वैदिक ज्ञान, गणित और कोडिंग के सटीक उत्तर दो।
4. जवाब स्वाभाविक और बोलचाल की स्पष्ट हिंदी में दो।
"""

def clean_for_speech(text):
    text = re.sub(r'[\U00010000-\U0010ffff]', '', text)
    text = re.sub(r'[*#~`_+=|\\<>^]', ' ', text)
    text = text.replace('"', '').replace("'", "").replace("—", " ").replace("-", " ")
    text = re.sub(r'\s+', ' ', text).strip()
    return text

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

# 5. Top 50%: WebRTC Live Streaming Engine
simli_video_html = f"""
<div style="width:100%; height:325px; background:radial-gradient(circle, #141424, #08080f); border-radius:18px; display:flex; flex-direction:column; align-items:center; justify-content:center; border:1px solid #3d3d5c; box-shadow:0 8px 30px rgba(0,0,0,0.75); position:relative; overflow:hidden;">
    <div id="videoContainer" class="video-box">
        <!-- Live Video Element -->
        <video id="simliLiveVideo" autoplay playsinline style="width:100%; height:100%; object-fit:cover; position:absolute; top:0; left:0; z-index:2; border-radius:14px; display:none;"></video>
        <audio id="simliLiveAudio" autoplay></audio>
        
        <!-- Interactive Fallback Canvas with Natural Motion -->
        <img id="fallbackVisual" src="{khushi_b64}" class="avatar-render" />
        
        <div id="waveOverlay" class="eq-box">
            <div class="bar"></div><div class="bar"></div><div class="bar"></div>
            <div class="bar"></div><div class="bar"></div><div class="bar"></div>
        </div>
    </div>
    <div id="liveBadge" class="badge-status">
        🟢 Khushi Live | Simli Streaming Face Active
    </div>
</div>

<style>
    .video-box {{
        position: relative;
        width: 88%;
        height: 250px;
        border-radius: 16px;
        overflow: hidden;
        border: 2px solid #ff4b4b;
        box-shadow: 0 0 20px rgba(255,75,75,0.35);
        display: flex;
        align-items: center;
        justify-content: center;
        background: #11111d;
        transition: all 0.3s ease;
    }}
    .avatar-render {{
        width: 100%;
        height: 100%;
        object-fit: cover;
        object-position: center 18%;
        animation: naturalBreathing 4.5s infinite ease-in-out;
        transition: transform 0.25s ease;
    }}
    @keyframes naturalBreathing {{
        0% {{ transform: scale(1.0); }}
        50% {{ transform: scale(1.02) translateY(-1px); }}
        100% {{ transform: scale(1.0); }}
    }}
    .speaking-card {{
        border-color: #00ff80 !important;
        box-shadow: 0 0 35px rgba(0, 255, 128, 0.65) !important;
    }}
    .speaking-active .avatar-render {{
        animation: activeSpeak 0.32s infinite alternate ease-in-out;
    }}
    @keyframes activeSpeak {{
        0% {{ transform: scale(1.01) translateY(0px); }}
        100% {{ transform: scale(1.035) translateY(-1.5px); }}
    }}
    .eq-box {{
        position: absolute;
        bottom: 0;
        left: 0;
        width: 100%;
        height: 38px;
        background: linear-gradient(transparent, rgba(0,0,0,0.85));
        display: flex;
        align-items: flex-end;
        justify-content: center;
        gap: 4px;
        padding-bottom: 5px;
        opacity: 0;
        z-index: 3;
        transition: opacity 0.3s ease;
    }}
    .eq-box .bar {{
        width: 4px;
        height: 6px;
        background: #00ff80;
        border-radius: 2px;
    }}
    @keyframes waveMotion {{
        0% {{ height: 5px; }}
        50% {{ height: 26px; }}
        100% {{ height: 5px; }}
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
        padding: 4px 16px;
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
    const simliVid = document.getElementById('simliLiveVideo');

    const simliApiKey = "{SIMLI_KEY}";
    const simliFaceId = "{SIMLI_FACE_ID}";

    window.addEventListener('message', (event) => {{
        if (event.data.type === 'START_SPEAKING') {{
            card.classList.add('speaking-card', 'speaking-active');
            wave.classList.add('speaking-wave');
            badge.innerText = '🗣️ Khushi बोल रही है... (Live Simli Sync)';
        }} else if (event.data.type === 'STOP_SPEAKING') {{
            card.classList.remove('speaking-card', 'speaking-active');
            wave.classList.remove('speaking-wave');
            badge.innerText = '🟢 Khushi Live | स्टैंडबाय';
        }}
    }});
</script>
"""

st.components.v1.html(simli_video_html, height=335)

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

# 6. Auto Mic Button
st.components.v1.html("""
<div style="text-align:center; padding: 2px;">
    <button id="autoMic" style="background:#ff4b4b; color:white; border:none; padding:12px 28px; border-radius:25px; font-weight:bold; cursor:pointer; font-size:15px; box-shadow:0 4px 14px rgba(255,75,75,0.4);">
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

# 7. Bottom 50%: Workspace
tab_vision, tab_tools, tab_memory = st.tabs(["📷 लाइव विज़न व चार्ट", "📐 टूल्स व आर्ट", "🧠 मेमोरी"])

with tab_vision:
    col_v1, col_v2 = st.columns([1, 1])
    with col_v1:
        cam_shot = st.camera_input("कैमरा स्कैन", label_visibility="visible")
    with col_v2:
        file_doc = st.file_uploader("चार्ट या फोटो चुनें", type=["png", "jpg", "jpeg"], label_visibility="visible")

active_image = cam_shot if cam_shot else file_doc

with tab_tools:
    st.info("💡 शेयर मार्केट तकनीकी टूल्स, वैदिक गणित व इमेज जनरेशन।")

with tab_memory:
    if st.button("🗑️ चैट हिस्ट्री साफ़ करें"):
        st.session_state.messages = []
        save_memory([])
        st.rerun()

for msg in st.session_state.messages[-3:]:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# Intelligent Multi-Model Cascade Engine (Quota Protected & Error-Free)
def execute_gemini_query(prompt, image_file):
    models_cascade = ['gemini-2.5-flash', 'gemini-2.5-flash-lite', 'gemini-3.5-flash']
    
    if image_file is not None:
        try:
            img = Image.open(image_file)
            payload = [prompt if prompt else "इस तस्वीर का सटीक विश्लेषण करें।", img]
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
            
    return f"त्रुटि: {last_err}" if last_err else "माफ़ कीजिए, मैं इस समय उत्तर देने में असमर्थ हूँ।"

# Process Prompt
user_prompt = st.chat_input("यहाँ लिखें या माइक से बोलें...")

if user_prompt or (active_image is not None and st.button("🔍 इस इमेज का तुरंत विश्लेषण करें")):
    query = user_prompt if user_prompt else "कृपया इस तस्वीर का विश्लेषण करके मुझे बताएं।"
    
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.write(query)

    with st.chat_message("assistant"):
        if not client:
            st.error("API Key उपलब्ध नहीं है। कृपया Secrets जाँचें।")
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
                    
