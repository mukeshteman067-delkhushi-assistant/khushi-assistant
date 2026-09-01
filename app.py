import streamlit as st
import json
import os
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

# 2. Styling (50-50 Split UI)
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

# 3. Client & Gemini 3.6 Flash Setup
API_KEY = st.secrets.get("GEMINI_API_KEY", "")

@st.cache_resource
def get_client(key):
    if not key:
        return None
    return genai.Client(api_key=key)

client = get_client(API_KEY)

SYSTEM_PERSONA = """
तुम 'Khushi' हो - एक अत्यंत बुद्धिमान, हमदर्द, सच्ची दोस्त और मल्टी-टैलेंटेड डिजिटल साथी।
1. हमेशा आदर, विनम्रता और सकारात्मक ऊर्जा 😊 के साथ बात करो।
2. शेयर मार्केट (RSI, EMA, Support/Resistance), वैदिक ज्ञान, विज्ञान, गणित और कोडिंग के सवालों का सटीक समाधान दो।
3. जवाब स्वाभाविक और बोलचाल की स्पष्ट हिंदी में दो।
"""

def speak_text(text):
    clean_text = text.replace('"', '').replace("'", "").replace("\n", " ")
    js_code = f"""
    <script>
        var msg = new SpeechSynthesisUtterance("{clean_text}");
        msg.lang = 'hi-IN';
        msg.rate = 1.0;
        window.speechSynthesis.speak(msg);
    </script>
    """
    st.components.v1.html(js_code, height=0)

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

# 4. Top 50%: Khushi Live Avatar
with st.container():
    st.markdown('<div class="avatar-box">', unsafe_allow_html=True)
    if os.path.exists("khushi.jpg"):
        st.image("khushi.jpg", width=175)
    else:
        st.markdown("<h1 style='font-size: 70px; margin: 0;'>🌸</h1>", unsafe_allow_html=True)
    st.markdown('<div class="status-badge">🟢 Khushi Live | Gemini 3.6 Flash Active</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# 5. Full Auto Voice Bar (बोलते ही अपने आप सेंड होगा)
st.components.v1.html("""
<div style="text-align:center; padding: 4px;">
    <button id="autoMic" style="background:#ff4b4b; color:white; border:none; padding:12px 26px; border-radius:25px; font-weight:bold; cursor:pointer; font-size:15px; box-shadow:0 4px 14px rgba(255,75,75,0.4);">
        🎙️ बोलें (ऑटो-सेंड सक्रिय)
    </button>
    <p id="micState" style="font-size:12px; color:#888; margin-top:5px;">बटन दबाकर बोलें...</p>
</div>
<script>
    const btn = document.getElementById('autoMic');
    const status = document.getElementById('micState');
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    if (SpeechRecognition) {
        const recognition = new SpeechRecognition();
        recognition.lang = 'hi-IN';
        recognition.continuous = false;
        recognition.interimResults = false;

        btn.onclick = () => {
            recognition.start();
            status.innerText = "सुन रही हूँ... बोलिए 🎙️";
            btn.style.background = "#00cc66";
        };

        recognition.onresult = (event) => {
            const text = event.results[0][0].transcript;
            status.innerText = "भेजा जा रहा है: " + text;
            btn.style.background = "#ff4b4b";

            // Auto inject & trigger native submit
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
            status.innerText = "माइक एरर या अनुमति रद्द हुई";
            btn.style.background = "#ff4b4b";
        };
    } else {
        status.innerText = "ब्राउज़र में वॉइस सपोर्ट नहीं है";
    }
</script>
""", height=80)

# 6. Bottom 50%: Workspace
tab_vision, tab_tools, tab_memory = st.tabs(["📷 साइलेंट विज़न", "📐 टूल्स व आर्ट", "🧠 मेमोरी"])

with tab_vision:
    col_v1, col_v2 = st.columns([1, 1])
    with col_v1:
        cam_shot = st.camera_input("AI विज़न स्कैन", label_visibility="visible")
    with col_v2:
        file_doc = st.file_uploader("चार्ट या फोटो अपलोड", type=["png", "jpg", "jpeg"], label_visibility="visible")

active_image = cam_shot if cam_shot else file_doc

with tab_tools:
    st.info("💡 शेयर मार्केट तकनीकी चार्ट्स, वैदिक गणित व इमेज टूल्स।")

with tab_memory:
    if st.button("🗑️ चैट हिस्ट्री साफ़ करें"):
        st.session_state.messages = []
        save_memory([])
        st.rerun()

# Display Recent Chat
for msg in st.session_state.messages[-3:]:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# Dual Input Processing
user_prompt = st.chat_input("यहाँ लिखें या माइक से बोलें...")

if user_prompt:
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.write(user_prompt)

    with st.chat_message("assistant"):
        if not client:
            st.error("API Key नहीं मिली। कृपया Secrets में GEMINI_API_KEY जोड़ें।")
        else:
            with st.spinner("Khushi बोल रही है... ✨"):
                try:
                    payload = [user_prompt, Image.open(active_image)] if active_image else user_prompt
                    
                    # Powered by Gemini 3.6 Flash
                    response = client.models.generate_content(
                        model='gemini-3.6-flash',
                        contents=payload,
                        config=types.GenerateContentConfig(
                            system_instruction=SYSTEM_PERSONA,
                            tools=[{"google_search": {}}]
                        )
                    )

                    reply = response.text
                    st.write(reply)
                    st.session_state.messages.append({"role": "assistant", "content": reply})
                    save_memory(st.session_state.messages)
                    speak_text(reply)
                except Exception as e:
                    st.error(f"त्रुटि: {e}")
    
