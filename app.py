import streamlit as st
import json
import os
import re
import datetime
import pytz
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

# 2. UI Layout & Split Styling
st.markdown("""
<style>
    .block-container {
        padding-top: 0.4rem;
        padding-bottom: 0.4rem;
        max-width: 100%;
    }
    .video-viewport {
        width: 100%;
        height: 38vh;
        background: radial-gradient(circle, #20203a, #0d0d17);
        border-radius: 20px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        border: 1px solid #3d3d5c;
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.7);
        position: relative;
        overflow: hidden;
        margin-bottom: 6px;
    }
</style>
""", unsafe_allow_html=True)

# 3. Gemini Engine Configuration
API_KEY = st.secrets.get("GEMINI_API_KEY", "")

@st.cache_resource
def get_client(key):
    if not key:
        return None
    return genai.Client(api_key=key)

client = get_client(API_KEY)

# Get Live Current Time in IST
ist = pytz.timezone('Asia/Kolkata')
current_now = datetime.datetime.now(ist).strftime("%I:%M %p, %d %B %Y")

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

# 4. Top 50%: Real-Time Interactive Talking Video Canvas Avatar
st.components.v1.html("""
<div class="video-viewport" style="width:100%; height:260px; background:radial-gradient(circle, #20203a, #0d0d17); border-radius:20px; display:flex; flex-direction:column; align-items:center; justify-content:center; border:1px solid #3d3d5c; position:relative; overflow:hidden;">
    <canvas id="avatarCanvas" width="220" height="220" style="border-radius:50%; border:3px solid #ff4b4b; box-shadow:0 0 25px rgba(255,75,75,0.4);"></canvas>
    <div id="liveBadge" style="margin-top:8px; background:rgba(0, 255, 128, 0.15); color:#00ff80; padding:3px 14px; border-radius:15px; font-size:12px; font-weight:bold; font-family:sans-serif;">
        🟢 Khushi Live | टॉकिंग वीडियो अवतार सक्रिय
    </div>
</div>

<script>
    const canvas = document.getElementById('avatarCanvas');
    const ctx = canvas.getContext('2d');
    const badge = document.getElementById('liveBadge');
    
    let img = new Image();
    img.src = 'app/static/khushi.jpg';
    img.onerror = () => { img.src = 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=400&q=80'; };

    let isSpeaking = false;
    let mouthOpen = 0;
    let scaleDirection = 1;

    function renderLoop() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        ctx.save();
        ctx.beginPath();
        ctx.arc(110, 110, 108, 0, Math.PI * 2, true);
        ctx.closePath();
        ctx.clip();

        if (img.complete && img.naturalWidth > 0) {
            // Subtle breathing idle video loop
            let breathe = Math.sin(Date.now() / 600) * 2;
            ctx.drawImage(img, -10, -10 + breathe, 240, 240);
            
            // Real-Time Lip Sync Video Animation when speaking
            if (isSpeaking) {
                mouthOpen += scaleDirection * 0.15;
                if (mouthOpen > 1) scaleDirection = -1;
                if (mouthOpen < 0) scaleDirection = 1;
                
                // Animate mouth opening and talking gesture
                ctx.fillStyle = "rgba(40, 15, 15, 0.75)";
                ctx.beginPath();
                ctx.ellipse(110, 142, 11 + (mouthOpen * 4), 3 + (mouthOpen * 6), 0, 0, Math.PI * 2);
                ctx.fill();

                // Lip accent
                ctx.strokeStyle = "rgba(220, 80, 80, 0.6)";
                ctx.lineWidth = 2;
                ctx.stroke();
            }
        } else {
            ctx.fillStyle = '#ff4b4b';
            ctx.font = '60px sans-serif';
            ctx.fillText('🌸', 80, 130);
        }
        ctx.restore();

        requestAnimationFrame(renderLoop);
    }
    img.onload = () => { renderLoop(); };
    renderLoop();

    // Listen to parent speech events
    window.addEventListener('message', (event) => {
        if (event.data.type === 'START_SPEAKING') {
            isSpeaking = true;
            canvas.style.borderColor = '#00ff80';
            canvas.style.boxShadow = '0 0 35px rgba(0,255,128,0.7)';
            badge.innerText = '🗣️ Khushi बोल रही है... (Live Video Sync)';
        } else if (event.data.type === 'STOP_SPEAKING') {
            isSpeaking = false;
            canvas.style.borderColor = '#ff4b4b';
            canvas.style.boxShadow = '0 0 25px rgba(255,75,75,0.4)';
            badge.innerText = '🟢 Khushi Live | स्टैंडबाय';
        }
    });
</script>
""", height=270)

# Voice Dispatcher to Canvas Video
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

# 5. Full Auto Mic & Audio Engine
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

# 6. Bottom 50%: Workspace
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

# Display Recent Messages
for msg in st.session_state.messages[-3:]:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# Multi-Model Smart Execution
def analyze_input(prompt, image):
    models = ['gemini-3.6-flash', 'gemini-3.5-flash', 'gemini-2.5-flash']
    default_vision_prompt = "इस इमेज का ध्यानपूर्वक विश्लेषण करें। यदि यह शेयर मार्केट का चार्ट है तो सपोर्ट, रेजिस्टेंस और ट्रेंड बताएं। यदि यह दस्तावेज़ या वस्तु है तो इसका विवरण दें।"
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

# Processing Prompt
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
