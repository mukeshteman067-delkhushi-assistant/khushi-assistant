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

# 2. Custom Styling (50-50 Screen Layout)
st.markdown("""
<style>
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        max-width: 100%;
    }
    .avatar-box {
        width: 100%;
        height: 38vh;
        background: linear-gradient(145deg, #1e1e2f, #11111a);
        border-radius: 16px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        border: 1px solid #33334d;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
        overflow: hidden;
        margin-bottom: 10px;
    }
    .avatar-box img {
        height: 75%;
        width: auto;
        border-radius: 50%;
        border: 3px solid #ff4b4b;
        box-shadow: 0 0 25px rgba(255, 75, 75, 0.4);
        object-fit: cover;
    }
    .status-badge {
        margin-top: 8px;
        background: rgba(0, 255, 128, 0.15);
        color: #00ff80;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# 3. API & Client Setup
API_KEY = st.secrets.get("GEMINI_API_KEY", "")

@st.cache_resource
def get_client(key):
    if not key:
        return None
    return genai.Client(api_key=key)

client = get_client(API_KEY)

# 4. Khushi Multi-Talented Persona
SYSTEM_PERSONA = """
तुम 'Khushi' हो - एक अत्यंत बुद्धिमान, हमदर्द, सच्ची दोस्त और मल्टी-टैलेंटेड डिजिटल साथी।
1. हमेशा आदर, विनम्रता और सकारात्मक ऊर्जा 😊 के साथ बात करो।
2. शेयर मार्केट (RSI, EMA, Support/Resistance), वेदों, विज्ञान, गणित और कोडिंग के सवालों के सटीक और सीधे जवाब दो।
3. जवाब स्वाभाविक और स्पष्ट हिंदी में दो ताकि सुनकर बात करने का अनुभव मिले।
"""

# Voice Output Function
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

# Memory Management
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

# 5. Top 50%: Khushi HD Live Avatar
with st.container():
    st.markdown('<div class="avatar-box">', unsafe_allow_html=True)
    if os.path.exists("khushi.jpg"):
        st.image("khushi.jpg", width=180)
    else:
        st.markdown("<h1 style='font-size: 80px; margin: 0;'>🌸</h1>", unsafe_allow_html=True)
    st.markdown('<div class="status-badge">🟢 Khushi Live | विज़न और माइक एक्टिव</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# 6. Bottom 50%: Multi-Talented Workspace
tab_live, tab_tools, tab_memory = st.tabs(["🎙️ लाइव इंटरेक्शन", "📐 टूल्स और चार्ट्स", "🧠 मेमोरी व इतिहास"])

with tab_live:
    col1, col2 = st.columns([1, 1])
    with col1:
        st.caption("📷 बैकग्राउंड विज़न (AI के देखने हेतु):")
        cam_feed = st.camera_input("कैमरा स्कैन", label_visibility="collapsed")
    with col2:
        st.caption("📁 चार्ट / फोटो अपलोड:")
        up_file = st.file_uploader("फाइल चुनें", type=["png", "jpg", "jpeg"], label_visibility="collapsed")

active_image = cam_feed if cam_feed else up_file

with tab_tools:
    st.info("💡 यहाँ इमेज जनरेशन, गणितीय समीकरण ($LaTeX$), और लाइव मार्केट चार्ट एनालाइजर लोड होगा।")

with tab_memory:
    if st.button("🗑️ मेमोरी साफ़ करें"):
        st.session_state.messages = []
        save_memory([])
        st.rerun()
    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.write(m["content"])

# Display Recent Chat
for msg in st.session_state.messages[-4:]:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# Chat Input & Processing
if user_prompt := st.chat_input("Khushi से कुछ भी पूछें या निर्देश दें..."):
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.write(user_prompt)

    with st.chat_message("assistant"):
        if not client:
            st.error("API Key उपलब्ध नहीं है। कृपया Streamlit Secrets में GEMINI_API_KEY जोड़ें।")
        else:
            with st.spinner("Khushi सोच रही है... 😊"):
                try:
                    if active_image:
                        img = Image.open(active_image)
                        response = client.models.generate_content(
                            model='gemini-2.5-flash',
                            contents=[user_prompt, img],
                            config=types.GenerateContentConfig(
                                system_instruction=SYSTEM_PERSONA,
                                tools=[{"google_search": {}}]
                            )
                        )
                    else:
                        response = client.models.generate_content(
                            model='gemini-2.5-flash',
                            contents=user_prompt,
                            config=types.GenerateContentConfig(
                                system_instruction=SYSTEM_PERSONA,
                                tools=[{"google_search": {}}]
                            )
                        )

                    reply_text = response.text
                    st.write(reply_text)
                    st.session_state.messages.append({"role": "assistant", "content": reply_text})
                    save_memory(st.session_state.messages)
                    speak_text(reply_text)
                except Exception as e:
                    st.error(f"त्रुटि: {e}")
