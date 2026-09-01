import streamlit as st
import json
import os
from PIL import Image
from google import genai
from google.genai import types

st.set_page_config(
    page_title="Khushi AI Companion",
    page_icon="🌸",
    layout="wide",
    initial_sidebar_state="collapsed"
)

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
2. शेयर मार्केट, विज्ञान, वैदिक ज्ञान और गणित के सटीक व त्वरित जवाब दो।
3. जवाब स्वाभाविक और बोलचाल की हिंदी में दो।
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

# Top 50% Avatar Container
with st.container():
    st.markdown('<div class="avatar-box">', unsafe_allow_html=True)
    if os.path.exists("khushi.jpg"):
        st.image("khushi.jpg", width=175)
    else:
        st.markdown("<h1 style='font-size: 70px; margin: 0;'>🌸</h1>", unsafe_allow_html=True)
    st.markdown('<div class="status-badge">🟢 Khushi Live | विज़न व वॉइस एक्टिव</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# Workspace
tab_vision, tab_tools, tab_memory = st.tabs(["📷 साइलेंट विज़न", "📐 टूल्स व आर्ट", "🧠 मेमोरी"])

with tab_vision:
    col_v1, col_v2 = st.columns([1, 1])
    with col_v1:
        cam_shot = st.camera_input("AI विज़न स्कैन", label_visibility="visible")
    with col_v2:
        file_doc = st.file_uploader("चार्ट या फोटो अपलोड", type=["png", "jpg", "jpeg"], label_visibility="visible")

active_image = cam_shot if cam_shot else file_doc

with tab_tools:
    st.info("💡 शेयर मार्केट तकनीकी विश्लेषण, गणितीय गणनाएँ और इमेज टूल्स।")

with tab_memory:
    if st.button("🗑️ चैट हिस्ट्री साफ़ करें"):
        st.session_state.messages = []
        save_memory([])
        st.rerun()

# Display Recent Interaction
for msg in st.session_state.messages[-3:]:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# Dual Input: Text/Voice Chat Bar
user_prompt = st.chat_input("यहाँ लिखें या माइक से बोलें...")

if user_prompt:
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.write(user_prompt)

    with st.chat_message("assistant"):
        if not client:
            st.error("API Key नहीं मिली।")
        else:
            with st.spinner("Khushi बोल रही है... ✨"):
                try:
                    # Updated to latest supported Gemini Flash model
                    target_model = 'gemini-2.5-flash'
                    try:
                        if active_image:
                            img = Image.open(active_image)
                            resp = client.models.generate_content(
                                model='gemini-2.5-flash',
                                contents=[user_prompt, img],
                                config=types.GenerateContentConfig(
                                    system_instruction=SYSTEM_PERSONA,
                                    tools=[{"google_search": {}}]
                                )
                            )
                        else:
                            resp = client.models.generate_content(
                                model='gemini-2.5-flash',
                                contents=user_prompt,
                                config=types.GenerateContentConfig(
                                    system_instruction=SYSTEM_PERSONA,
                                    tools=[{"google_search": {}}]
                                )
                            )
                    except Exception:
                        # Auto-fallback to gemini-2.0-flash / 3.6-flash if deprecated
                        if active_image:
                            img = Image.open(active_image)
                            resp = client.models.generate_content(
                                model='gemini-2.0-flash',
                                contents=[user_prompt, img],
                                config=types.GenerateContentConfig(
                                    system_instruction=SYSTEM_PERSONA
                                )
                            )
                        else:
                            resp = client.models.generate_content(
                                model='gemini-2.0-flash',
                                contents=user_prompt,
                                config=types.GenerateContentConfig(
                                    system_instruction=SYSTEM_PERSONA
                                )
                            )

                    ans = resp.text
                    st.write(ans)
                    st.session_state.messages.append({"role": "assistant", "content": ans})
                    save_memory(st.session_state.messages)
                    speak_text(ans)
                except Exception as e:
                    st.error(f"त्रुटि: {e}")
                    
