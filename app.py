import streamlit as st
import json, os, re, base64
from datetime import datetime, timezone, timedelta
from PIL import Image
from google import genai
from google.genai import types

# 1. पेज कॉन्फ़िगरेशन
st.set_page_config(page_title="Khushi AI", page_icon="🌸", layout="wide")

st.markdown("""
<style>
    .block-container { padding: 0.1rem 0.3rem 4rem 0.3rem !important; max-width: 100% !important; }
    header, footer, #MainMenu { visibility: hidden !important; }
</style>
""", unsafe_allow_html=True)

# 2. खुशी ओरिजिनल इमेज (Base64)
def get_khushi_b64():
    if os.path.exists("khushi.jpg"):
        try:
            with open("khushi.jpg", "rb") as f:
                return f"data:image/jpeg;base64,{base64.b64encode(f.read()).decode()}"
        except Exception: pass
    return ""

khushi_b64 = get_khushi_b64()

# 3. Gemini 3.6 API Client
raw_key = st.secrets.get("GEMINI_API_KEY", "")
API_KEY = "".join(raw_key.split()) if raw_key else ""
client = genai.Client(api_key=API_KEY) if API_KEY else None

ist_now = datetime.now(timezone(timedelta(hours=5, minutes=30))).strftime("%I:%M %p, %d %b %Y")
PERSONA = f"तुम 'Khushi' हो - हमदर्द, बुद्धिमान और सच्ची AI दोस्त। समय (IST): {ist_now}। शेयर बाजार, कोडिंग, विज्ञान और सामान्य प्रश्नों के सरल, संक्षिप्त व स्पष्ट हिंदी में उत्तर दो।"

# सेशन व मेमोरी
if "messages" not in st.session_state:
    if os.path.exists("khushi_memory.json"):
        try:
            with open("khushi_memory.json", "r", encoding="utf-8") as f:
                st.session_state.messages = json.load(f)
        except Exception: st.session_state.messages = []
    else: st.session_state.messages = []

def save_mem():
    try:
        with open("khushi_memory.json", "w", encoding="utf-8") as f:
            json.dump(st.session_state.messages, f, ensure_ascii=False)
    except Exception: pass

# 4. स्केच अनुसार: बड़ा आयताकार फ्रेम (320px), ऑल-ओवर वॉइस और ऑटो-हाइड ज़ूम
st.components.v1.html(f"""
<div id="masterBoard" style="width:100%; box-sizing:border-box; background:#0a0c16; padding:8px; border-radius:14px; border:1px solid #1e2640; position:relative; overflow:hidden;">
    
    <!-- मुख्य लेआउट ग्रिड: बायाँ आयताकार फ्रेम + दायाँ स्विचेस -->
    <div id="standardGrid" style="display:flex; width:100%; gap:8px;">
        
        <!-- बायाँ 50%: बड़ा आयताकार (Portrait) विज़ुअल + नीचे Puss और Zoom -->
        <div style="width:52%; display:flex; flex-direction:column; gap:6px;">
            <div id="portraitFrame" style="width:100%; height:310px; background:#000; border:2px solid #ff4b4b; border-radius:12px; overflow:hidden; position:relative; box-shadow:0 0 18px rgba(255,75,75,0.35); transition:all 0.35s ease;">
                <img id="avatarPic" src="{khushi_b64}" style="width:100%; height:100%; object-fit:cover; object-position:center 12%; animation:breathe 4s infinite ease-in-out;" />
            </div>
            
            <!-- Puss & Zoom बटन ठीक नीचे -->
            <div style="display:flex; gap:5px; width:100%;">
                <button onclick="pussSpeech()" style="flex:1; background:#451212; color:#ff6b6b; border:1px solid #ff4b4b; padding:9px 2px; border-radius:8px; font-size:12px; font-weight:bold; cursor:pointer;">
                    🛑 Puss
                </button>
                <button onclick="enterZoomMode()" style="flex:1; background:#12283d; color:#38bdf8; border:1px solid #38bdf8; padding:9px 2px; border-radius:8px; font-size:12px; font-weight:bold; cursor:pointer;">
                    ⛶ Zoom
                </button>
            </div>
        </div>

        <!-- दायाँ 48%: स्विचेस (कैमरा, माइक-स्पीकर, सेटिंग) -->
        <div id="switchesPanel" style="width:48%; display:flex; flex-direction:column; justify-content:space-between; gap:8px;">
            <!-- 1. कैमरा ON - OFF स्विच -->
            <button onclick="toggleCamModal()" style="width:100%; background:#221b0e; color:#facc15; border:1px solid #ca8a04; padding:12px 2px; border-radius:10px; font-size:12px; font-weight:bold; cursor:pointer;">
                📷 कैमरा on — off
            </button>

            <!-- 2. mike - spiker (बोलने के लिए) -->
            <div style="display:flex; flex-direction:column; align-items:center;">
                <button id="micBtn" style="width:100%; background:#ff4b4b; color:white; border:none; padding:15px 2px; border-radius:10px; font-size:13px; font-weight:bold; cursor:pointer; box-shadow:0 3px 12px rgba(255,75,75,0.45);">
                    🎙️ mike - spiker (बोलें)
                </button>
                <span id="micStatus" style="font-size:10px; color:#9ca3af; margin-top:4px;">माइक व स्पीकर एक्टिव</span>
            </div>

            <!-- 3. सेटिंग स्विच -->
            <button onclick="clearHistoryDirect()" style="width:100%; background:#1c172d; color:#c084fc; border:1px solid #9333ea; padding:12px 2px; border-radius:10px; font-size:12px; font-weight:bold; cursor:pointer;">
                ⚙️ सेटिंग (मेमोरी रीसेट)
            </button>
        </div>
    </div>

    <!-- ज़ूम स्थिति (Pure Half-Screen Cinema Mode - सारे स्विच हिडन) -->
    <div id="zoomOverlayContainer" style="display:none; width:100%; height:50vh; position:relative; background:#000; border-radius:14px; overflow:hidden; border:2px solid #00ff80; box-shadow:0 0 25px rgba(0,255,128,0.5);">
        <img src="{khushi_b64}" style="width:100%; height:100%; object-fit:cover; object-position:center 15%;" />
        
        <!-- ज़ूम आउट (सामान्य स्थिति में वापसी) बटन -->
        <button onclick="exitZoomMode()" style="position:absolute; top:12px; right:12px; z-index:100; background:#ff4b4b; color:#fff; border:none; padding:8px 16px; border-radius:20px; font-size:12px; font-weight:bold; cursor:pointer;">
            ✕ सामान्य डिस्प्ले
        </button>

        <!-- ज़ूम मोड में ऑल-ओवर बोलने का वॉयस बटन -->
        <div style="position:absolute; bottom:12px; left:0; width:100%; display:flex; justify-content:center; z-index:100;">
            <button onclick="triggerMicVoice()" style="background:linear-gradient(90deg, #10b981, #059669); color:#fff; border:none; padding:12px 24px; border-radius:25px; font-weight:bold; font-size:14px; cursor:pointer; box-shadow:0 4px 15px rgba(0,0,0,0.6);">
                🎙️ बोलिए (खुशी सुन रही है...)
            </button>
        </div>
    </div>
</div>

<style>
    @keyframes breathe {{ 0%{{transform:scale(1);}} 50%{{transform:scale(1.025) translateY(-1.5px);}} 100%{{transform:scale(1);}} }}
</style>

<script>
    const standardGrid = document.getElementById('standardGrid');
    const zoomOverlay = document.getElementById('zoomOverlayContainer');
    const micStatus = document.getElementById('micStatus');
    const portraitFrame = document.getElementById('portraitFrame');

    // 1. Zoom Mode (सारे स्विच हिडन, सिर्फ 50% डिस्प्ले पर खुशी और वॉयस)
    function enterZoomMode() {{
        standardGrid.style.display = 'none';
        zoomOverlay.style.display = 'block';
        
        // कीपैड और चैट इनपुट को पूरी तरह छुपा दें
        const chatInp = window.parent.document.querySelector('div[data-testid="stChatInput"]');
        if (chatInp) chatInp.style.display = 'none';
        
        const chatCards = window.parent.document.getElementById('chatAnswerContainer');
        if (chatCards) chatCards.style.display = 'none';
    }}

    function exitZoomMode() {{
        zoomOverlay.style.display = 'none';
        standardGrid.style.display = 'flex';
        
        // कीपैड और चैट वापस सामान्य करें
        const chatInp = window.parent.document.querySelector('div[data-testid="stChatInput"]');
        if (chatInp) chatInp.style.display = 'block';
        
        const chatCards = window.parent.document.getElementById('chatAnswerContainer');
        if (chatCards) chatCards.style.display = 'block';
    }}

    // 2. Puss (बोलना बीच में रोकें)
    function pussSpeech() {{
        if ('speechSynthesis' in window) window.speechSynthesis.cancel();
        portraitFrame.style.borderColor = '#ff4b4b';
        micStatus.innerText = 'शांत';
    }}

    // 3. कैमरा बॉक्स ऑन/ऑफ
    function toggleCamModal() {{
        const el = window.parent.document.getElementById('hiddenCameraBlock');
        if (el) {{
            el.style.display = (el.style.display === 'none') ? 'block' : 'none';
            el.scrollIntoView({{ behavior: 'smooth' }});
        }}
    }}

    // 4. सेटिंग (मेमोरी साफ़)
    function clearHistoryDirect() {{
        const btn = window.parent.document.querySelector('button[data-testid="baseButton-secondary"]');
        if (btn) btn.click();
    }}

    // 5. माइक रिकग्निशन
    const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
    let rec = null;
    if (SpeechRec) {{
        rec = new SpeechRec();
        rec.lang = 'hi-IN';
        rec.onresult = (e) => {{
            const text = e.results[0][0].transcript;
            micStatus.innerText = "भेजा: " + text;
            const inp = window.parent.document.querySelector('textarea[data-testid="stChatInputTextArea"]');
            if (inp) {{
                const nativeVal = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, "value").set;
                nativeVal.call(inp, text);
                inp.dispatchEvent(new Event('input', {{ bubbles: true }}));
                setTimeout(() => {{
                    const send = window.parent.document.querySelector('button[data-testid="stChatInputSubmitButton"]');
                    if (send) send.click();
                }}, 300);
            }}
        }};
        rec.onerror = () => {{ micStatus.innerText = "माइक एरर"; }};
    }}

    function triggerMicVoice() {{
        if ('speechSynthesis' in window) window.speechSynthesis.speak(new SpeechSynthesisUtterance(""));
        if (rec) {{
            rec.start();
            micStatus.innerText = "सुन रही हूँ...";
        }}
    }}

    document.getElementById('micBtn').onclick = triggerMicVoice;
</script>
""", height=385)

# अदृश्य कैमरा ब्लॉक (जब स्विच चालू हो तभी दिखेगा)
active_image = None
st.markdown('<div id="hiddenCameraBlock" style="display:none; background:#141724; padding:8px; border-radius:10px; margin:6px 0; border:1px solid #ca8a04;">', unsafe_allow_html=True)
st.markdown("<span style='color:#facc15; font-size:12px; font-weight:bold;'>📷 कैमरा या चार्ट फ़ोटो लें:</span>", unsafe_allow_html=True)
col_c1, col_c2 = st.columns(2)
with col_c1: cam_shot = st.camera_input("कैमरा", label_visibility="collapsed")
with col_c2: file_doc = st.file_uploader("गैलरी से चुनें", type=["jpg", "png"], label_visibility="collapsed")
active_image = cam_shot if cam_shot else file_doc
st.markdown('</div>', unsafe_allow_html=True)

# हिडन मेमोरी क्लियर ट्रिगर
st.markdown('<div style="display:none;">', unsafe_allow_html=True)
if st.button("ClearHiddenTrigger"):
    st.session_state.messages = []
    save_mem()
    st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

# 5. चैट व आंसर कार्ड
st.markdown('<div id="chatAnswerContainer">', unsafe_allow_html=True)
for msg in st.session_state.messages[-2:]:
    if msg["role"] == "user":
        st.markdown(f"🗣️ **आप (Q):** {msg['content']}")
    else:
        st.markdown(f"""
        <div style="background:#09101d; border:1.5px solid #00ff80; border-radius:10px; padding:10px 12px; margin:4px 0; box-shadow:0 2px 10px rgba(0,255,128,0.12);">
            <b style="color:#00ff80; font-size:14px;">👉 खुशी Answer:</b><br>
            <span style="color:#f8fafc; font-size:13px; line-height:1.4;">{msg['content']}</span>
        </div>
        """, unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# 6. आधिकारिक Gemini 3.6 Flash इंजन (404 एरर का स्थायी समाधान)
def ask_gemini(prompt, img):
    if not client:
        return "त्रुटि: GEMINI_API_KEY नहीं मिली। कृपया Secrets जाँचें।"
    
    # सक्रिय और मान्य मॉडल
    models_to_try = ['gemini-3.6-flash', 'gemini-3.5-flash-lite']
    contents_payload = [prompt, Image.open(img)] if img else prompt
    
    for m in models_to_try:
        try:
            res = client.models.generate_content(
                model=m,
                contents=contents_payload,
                config=types.GenerateContentConfig(system_instruction=PERSONA)
            )
            if res and res.text:
                return res.text
        except Exception:
            continue
            
    return "माफ़ कीजिए, सर्वर व्यस्त है। कृपया पुनः प्रयास करें।"

def speak(text):
    clean = re.sub(r'[*#~`_+=|\\<>]', ' ', text).replace('"', '').replace("'", "")
    st.components.v1.html(f"""
    <script>
        if ('speechSynthesis' in window) {{
            window.speechSynthesis.cancel();
            const u = new SpeechSynthesisUtterance("{clean}");
            u.lang = 'hi-IN';
            window.speechSynthesis.speak(u);
        }}
    </script>
    """, height=0)

# 7. निचला चैट इनपुट
user_query = st.chat_input("यहाँ लिखें या ऊपर mike बटन दबाकर बोलें...")

if user_query or (active_image and st.button("🔍 इस फ़ोटो का विश्लेषण करें")):
    q = user_query if user_query else "कृपया इस तस्वीर का विश्लेषण करें।"
    st.session_state.messages.append({"role": "user", "content": q})
    
    with st.spinner("खुशी सोच रही है... ✨"):
        ans = ask_gemini(q, active_image)
        st.session_state.messages.append({"role": "assistant", "content": ans})
        save_mem()
        speak(ans)
        st.rerun()
            
