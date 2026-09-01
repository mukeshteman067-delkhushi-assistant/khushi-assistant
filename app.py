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

# 2. Layout Styling
st.markdown("""
<style>
    .block-container {
        padding-top: 0.4rem;
        padding-bottom: 0.4rem;
        max-width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# 3. Base64 Image Ingestion
def get_image_base64():
    if os.path.exists("khushi.jpg"):
        try:
            with open("khushi.jpg", "rb") as img_file:
                return f"data:image/jpeg;base64,{base64.b64encode(img_file.read()).decode('utf-8')}"
        except Exception:
            return ""
    return ""

khushi_b64 = get_image_base64()

# 4. Gemini Engine Setup
API_KEY = st.secrets.get("GEMINI_API_KEY", "")

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
2. जब समय पूछा जाए तो सटीक वर्तमान समय बताओ।
3. शेयर मार्केट, विज्ञान, वैदिक ज्ञान, गणित और कोडिंग के सटीक उत्तर दो।
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

# 5. Top 50%: 3D/4D Live Realistic Video Avatar (Eyes Blinking + Real Lip Movement)
avatar_html = f"""
<div style="width:100%; height:320px; background:radial-gradient(circle, #1a1a2e, #0a0a12); border-radius:18px; display:flex; flex-direction:column; align-items:center; justify-content:center; border:1px solid #3d3d5c; box-shadow:0 8px 30px rgba(0,0,0,0.7); position:relative; overflow:hidden;">
    <div id="videoContainer" style="position:relative; width:92%; height:250px; border-radius:14px; overflow:hidden; border:2px solid #ff4b4b; box-shadow:0 0 20px rgba(255,75,75,0.4); background:#12121e;">
        <canvas id="faceCanvas" width="340" height="250" style="width:100%; height:100%; object-fit:cover; display:block;"></canvas>
    </div>
    <div id="liveBadge" style="margin-top:8px; background:rgba(0, 255, 128, 0.15); color:#00ff80; padding:4px 16px; border-radius:15px; font-size:12px; font-weight:bold; font-family:sans-serif;">
        🟢 Khushi Live | 3D/4D वीडियो अवतार सक्रिय
    </div>
</div>

<script>
    const canvas = document.getElementById('faceCanvas');
    const ctx = canvas.getContext('2d');
    const container = document.getElementById('videoContainer');
    const badge = document.getElementById('liveBadge');

    let baseImg = new Image();
    baseImg.src = "{khushi_b64}";

    let isSpeaking = false;
    let mouthPhase = 0;
    let blinkPhase = 0; // 0: open, 1: blinking
    let lastBlink = Date.now();

    function render4DAvatar() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        // 1. Subtle 3D Head sway & breathing motion
        const time = Date.now() / 800;
        const breathY = Math.sin(time) * 1.5;
        const tilt = isSpeaking ? Math.sin(Date.now() / 250) * 1.2 : Math.sin(time * 0.5) * 0.5;

        ctx.save();
        ctx.translate(canvas.width / 2, canvas.height / 2);
        ctx.rotate(tilt * Math.PI / 180);
        ctx.drawImage(baseImg, -canvas.width / 2, -canvas.height / 2 + breathY, canvas.width, canvas.height);

        // Relative coordinates for face features
        const mouthX = canvas.width * 0.505;
        const mouthY = canvas.height * 0.635 + breathY;
        const leftEyeX = canvas.width * 0.405;
        const rightEyeX = canvas.width * 0.605;
        const eyeY = canvas.height * 0.405 + breathY;

        // 2. Realistic Eye Blinking Logic (every 3.5s)
        const now = Date.now();
        if (now - lastBlink > 3500) {{
            blinkPhase = 1;
            if (now - lastBlink > 3700) {{
                blinkPhase = 0;
                lastBlink = now;
            }}
        }}

        if (blinkPhase === 1) {{
            // Render eyelid closure
            ctx.fillStyle = "rgba(180, 130, 110, 0.95)";
            // Left Eyelid
            ctx.beginPath();
            ctx.ellipse(leftEyeX - canvas.width / 2, eyeY - canvas.height / 2, 12, 5, 0, 0, Math.PI * 2);
            ctx.fill();
            // Right Eyelid
            ctx.beginPath();
            ctx.ellipse(rightEyeX - canvas.width / 2, eyeY - canvas.height / 2, 12, 5, 0, 0, Math.PI * 2);
            ctx.fill();
        }}

        // 3. Dynamic 4D Lip-Syncing & Talking Motion
        if (isSpeaking) {{
            mouthPhase = (Math.sin(Date.now() / 80) + 1) / 2; // 0 to 1 fluid oscillation
            const openHeight = 1.5 + (mouthPhase * 5.5);
            const openWidth = 10 + (mouthPhase * 3);

            // Natural mouth inner depth
            ctx.fillStyle = "rgba(45, 12, 15, 0.92)";
            ctx.beginPath();
            ctx.ellipse(mouthX - canvas.width / 2, mouthY - canvas.height / 2, openWidth, openHeight, 0, 0, Math.PI * 2);
            ctx.fill();

            // Dynamic Lip Contour
            ctx.strokeStyle = "rgba(195, 80, 85, 0.85)";
            ctx.lineWidth = 1.8;
            ctx.stroke();

            // Lower lip highlight
            ctx.fillStyle = "rgba(220, 110, 115, 0.4)";
            ctx.beginPath();
            ctx.ellipse(mouthX - canvas.width / 2, mouthY - canvas.height / 2 + openHeight * 0.8, openWidth * 0.8, 2, 0, 0, Math.PI);
            ctx.fill();
        }}

        ctx.restore();
        requestAnimationFrame(render4DAvatar);
    }

    baseImg.onload = () => {{
        render4DAvatar();
    }};

    window.addEventListener('message', (event) => {{
        if (event.data.type === 'START_SPEAKING') {{
            isSpeaking = true;
            container.style.borderColor = '#00ff80';
            container.style.boxShadow = '0 0 35px rgba(0,255,128,0.7)';
            badge.innerText = '🗣️ Khushi बोल रही है... (4D Live Sync)';
        }} else if (event.data.type === 'STOP_SPEAKING') {{
            isSpeaking = false;
            container.style.borderColor = '#ff4b4b';
            container.style.boxShadow = '0 0 20px rgba(255,75,75,0.4)';
            badge.innerText = '🟢 Khushi Live | स्टैंडबाय';
        }}
    }});
</script>
"""

st.components.v1.html(avatar_html, height=330)

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

# 6. Auto Mic & Speaker Engine
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

def analyze_input(prompt, image):
    models = ['gemini-3.6-flash', 'gemini-3.5-flash', 'gemini-2.5-flash']
    default_vision_prompt = "इस तस्वीर का ध्यानपूर्वक विश्लेषण करें। यदि यह शेयर मार्केट का चार्ट है तो सपोर्ट, रेजिस्टेंस और ट्रेंड बताएं। यदि यह दस्तावेज़ या वस्तु है तो इसका विवरण दें।"
    final_prompt = prompt if prompt else default_vision_prompt

    payload = [final_prompt, Image.open(image)] if image else final_prompt

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
    return "माफ़ कीजिए, मैं अभी जवाब नहीं दे पा रही हूँ।"

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
                speak_and_animate(ans)
