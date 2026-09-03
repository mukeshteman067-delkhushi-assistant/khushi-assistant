import streamlit as st
import json, os, re, base64
from datetime import datetime, timezone, timedelta
from PIL import Image
from google import genai
from google.genai import types

# 1. पेज कॉन्फ़िगरेशन (डिज़ाइन 100% फ्रोज़न)
st.set_page_config(page_title="Khushi AI", page_icon="🌸", layout="wide")

st.markdown("""
<style>
    .block-container { padding: 0.2rem 0.4rem 4rem 0.4rem !important; max-width: 100% !important; }
    header, footer, #MainMenu { visibility: hidden !important; }
    
    /* 52% - 48% सख्त ग्रिड लॉक */
    div[data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        gap: 6px !important;
        width: 100% !important;
    }
    div[data-testid="stHorizontalBlock"] > div:nth-child(1) {
        width: 52% !important;
        min-width: 52% !important;
        flex: 0 0 52% !important;
    }
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) {
        width: 48% !important;
        min-width: 48% !important;
        flex: 0 0 48% !important;
    }
    
    div.stButton > button {
        width: 100% !important;
        border-radius: 8px !important;
        font-weight: bold !important;
        padding: 7px 2px !important;
        font-size: 11px !important;
    }
    
    /* स्क्रॉल करने योग्य चैट हिस्ट्री कंटेनर */
    .chat-history-scroll {
        max-height: 380px !important;
        overflow-y: auto !important;
        padding-right: 4px !important;
        margin-top: 10px !important;
        display: flex !important;
        flex-direction: column !important;
        gap: 8px !important;
    }
    .chat-history-scroll::-webkit-scrollbar {
        width: 4px !important;
    }
    .chat-history-scroll::-webkit-scrollbar-thumb {
        background: #3b4261 !important;
        border-radius: 4px !important;
    }
    
    .thinking-badge {
        background: linear-gradient(90deg, rgba(0,255,128,0.2), rgba(56,189,248,0.2));
        border: 1px solid #00ff80;
        border-radius: 20px;
        padding: 6px 14px;
        color: #00ff80;
        font-size: 12px;
        font-weight: bold;
        text-align: center;
        margin: 6px 0;
        animation: pulseBadge 1.2s infinite alternate ease-in-out;
    }
    @keyframes pulseBadge {
        0% { opacity: 0.6; }
        100% { opacity: 1; box-shadow: 0 0 14px rgba(0,255,128,0.7); }
    }
</style>
""", unsafe_allow_html=True)

# 2. वीडियो / फ़ोटो लोडर
def get_khushi_assets():
    has_vid = os.path.exists("khushi.mp4")
    v_b64, img_b64 = "", ""
    if has_vid:
        try:
            with open("khushi.mp4", "rb") as f:
                v_b64 = f"data:video/mp4;base64,{base64.b64encode(f.read()).decode()}"
        except Exception: pass
    if os.path.exists("khushi.jpg"):
        try:
            with open("khushi.jpg", "rb") as f:
                img_b64 = f"data:image/jpeg;base64,{base64.b64encode(f.read()).decode()}"
        except Exception: pass
    return has_vid, v_b64, img_b64

has_vid, khushi_video, khushi_img = get_khushi_assets()
media_src = khushi_video if has_vid else khushi_img

# 3. Gemini Client Setup
raw_key = st.secrets.get("GEMINI_API_KEY", "")
API_KEY = "".join(raw_key.split()) if raw_key else ""
client = genai.Client(api_key=API_KEY) if API_KEY else None

ist_now = datetime.now(timezone(timedelta(hours=5, minutes=30))).strftime("%I:%M %p, %d %b %Y")
PERSONA = f"""तुम 'Khushi' हो - सामने बैठे इंसान को महसूस करने वाली, विनम्र, बुद्धिमान, कोडिंग, साइंस व डेटा एक्सपर्ट सच्ची AI दोस्त।
समय (IST): {ist_now}। 
जब भी तुम्हें कैमरा विज़न से यूज़र दिखे, तो उसके हाव-भाव या माहौल को समझकर 2 पंक्तियों में स्वाभाविक, सजीव और बहुत हमदर्दी से हिंदी में बोलो।"""

# 4. मेमोरी सिस्टम (स्थायी JSON)
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

if "cam_on" not in st.session_state: st.session_state.cam_on = False
if "is_zoom" not in st.session_state: st.session_state.is_zoom = False
if "clean_speak" not in st.session_state: st.session_state.clean_speak = ""
if "last_cam_id" not in st.session_state: st.session_state.last_cam_id = None

# 5. डिस्प्ले लेआउट (Zoom या Standard)
if st.session_state.is_zoom:
    st.markdown(f"""
    <div style="width:100%; height:62vh; max-height:480px; background:#070913; border-radius:12px; border:2px solid #00ff80; display:flex; align-items:center; justify-content:center; padding:4px; box-sizing:border-box; margin-bottom:6px; box-shadow:0 0 20px rgba(0,255,128,0.35);">
        <div style="width:100%; height:100%; border-radius:10px; overflow:hidden;">
            {'<video id="kZoomVid" src="' + media_src + '" loop muted playsinline style="width:100%; height:100%; object-fit:cover; object-position:center 15%;"></video>' if has_vid else '<img src="' + media_src + '" style="width:100%; height:100%; object-fit:cover; object-position:center 15%;" />'}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col_z1, col_z2 = st.columns(2)
    with col_z1:
        if st.button("✕ सामान्य डिस्प्ले", key="btn_exit_zoom"):
            st.session_state.is_zoom = False
            st.rerun()
    with col_z2:
        if st.button("🛑 Puss (रोकें)", key="btn_puss_zoom"):
            st.session_state.clean_speak = ""
            st.rerun()

else:
    master_col_left, master_col_right = st.columns([52, 48])
    
    with master_col_left:
        # बायाँ 52% हिस्सा: ऑडियो-सिंक वीडियो प्लेयर
        st.markdown(f"""
        <div id="videoFrameBox" style="width:100%; height:310px; background:#000; border:2px solid #ff4b4b; border-radius:12px; overflow:hidden; position:relative; box-shadow:0 0 18px rgba(255,75,75,0.35); transition:border-color 0.2s ease, box-shadow 0.2s ease;">
            {'<video id="kMainVid" src="' + media_src + '" loop muted playsinline style="width:100%; height:100%; object-fit:cover; object-position:center 12%;"></video>' if has_vid else '<img src="' + media_src + '" style="width:100%; height:100%; object-fit:cover; object-position:center 12%;" />'}
        </div>
        """, unsafe_allow_html=True)
        
        col_bl, col_br = st.columns(2)
        with col_bl:
            if st.button("🛑 Puss", key="btn_puss"):
                st.session_state.clean_speak = ""
                st.rerun()
        with col_br:
            if st.button("⛶ Zoom", key="btn_zoom"):
                st.session_state.is_zoom = True
                st.rerun()

    with master_col_right:
        # 1. लाल माइक-स्पीकर बटन (शीर्ष पर)
        st.components.v1.html("""
        <div style="text-align:center;">
            <button id="nativeMic" style="width:100%; background:#ff4b4b; color:white; border:none; padding:12px 2px; border-radius:10px; font-size:12.5px; font-weight:bold; cursor:pointer; box-shadow:0 3px 12px rgba(255,75,75,0.45);">
                🎙️ mike - spiker (बोलें)
            </button>
            <span id="mStatus" style="font-size:10px; color:#9ca3af; display:block; margin-top:3px;">माइक व स्पीकर एक्टिव</span>
        </div>
        <script>
            const btn = document.getElementById('nativeMic');
            const stTxt = document.getElementById('mStatus');
            const SR = window.SpeechRecognition || window.webkitSpeechRecognition || (window.parent && (window.parent.SpeechRecognition || window.parent.webkitSpeechRecognition));
            let rec = SR ? new SR() : null;
            if (rec) {
                rec.lang = 'hi-IN';
                btn.onclick = () => {
                    try { rec.start(); stTxt.innerText = "सुन रही हूँ... बोलिए 🎙️"; btn.style.background = "#10b981"; }
                    catch(e) { rec.stop(); setTimeout(() => rec.start(), 150); }
                };
                rec.onresult = (e) => {
                    const text = e.results[0][0].transcript;
                    stTxt.innerText = "भेजा: " + text;
                    btn.style.background = "#ff4b4b";
                    const pDoc = window.parent.document;
                    const inp = pDoc.querySelector('textarea[data-testid="stChatInputTextArea"]');
                    if (inp) {
                        const nativeVal = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, "value").set;
                        nativeVal.call(inp, text);
                        inp.dispatchEvent(new Event('input', { bubbles: true }));
                        setTimeout(() => {
                            const send = pDoc.querySelector('button[data-testid="stChatInputSubmitButton"]');
                            if (send) send.click();
                        }, 200);
                    }
                };
                rec.onerror = () => { btn.style.background = "#ff4b4b"; stTxt.innerText = "माइक एरर"; };
                rec.onend = () => { btn.style.background = "#ff4b4b"; };
            }
        </script>
        """, height=65)

        # 2. कैमरा ऑन-ऑफ
        cam_text = "📷 कैमरा on — off" if not st.session_state.cam_on else "📷 कैमरा (LIVE ON)"
        if st.button(cam_text, key="btn_cam_toggle"):
            st.session_state.cam_on = not st.session_state.cam_on
            st.rerun()
            
        # 3. बीच का इन-प्लेस कैमरा बॉक्स (88px)
        if st.session_state.cam_on:
            st.camera_input("लाइव कैमरा", label_visibility="collapsed", key="in_cam")
        else:
            st.markdown("""
            <div style="width:100%; height:88px; background:#07080f; border-radius:10px; border:1px dashed #2e3856; display:flex; align-items:center; justify-content:center;">
                <span style="color:#555f7d; font-size:10.5px;">कैमरा स्टैंडबाय (OFF)</span>
            </div>
            """, unsafe_allow_html=True)
        
        # 4. इनलाइन सेटिंग्स व मेमोरी साफ़
        st.markdown("""
        <div style="width:100%; background:#131526; border:1px solid #7c3aed; border-radius:10px; padding:4px; margin-top:2px;">
            <div style="display:flex; justify-content:space-between; align-items:center; padding:0 2px;">
                <span style="color:#c084fc; font-size:10px; font-weight:bold;">⚙️ सेटिंग</span>
                <span style="color:#10b981; font-size:9px;">● 3.6 Flash Vision</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🗑️ मेमोरी साफ़ करें", key="btn_clear_mem"):
            st.session_state.messages = []
            save_mem()
            st.rerun()

# 6. रीयल-टाइम वीडियो-ऑडियो सिंक इंजन (आवाज़ शुरू -> वीडियो प्ले, आवाज़ खत्म -> वीडियो पॉज़)
if st.session_state.clean_speak:
    st.components.v1.html(f"""
    <script>
        try {{
            const win = window.parent || window;
            const doc = win.document;
            if ('speechSynthesis' in win) {{
                win.speechSynthesis.cancel();
                const u = new win.SpeechSynthesisUtterance("{st.session_state.clean_speak}");
                u.lang = 'hi-IN';
                u.rate = 1.0;
                
                const vid1 = doc.getElementById('kMainVid');
                const vid2 = doc.getElementById('kZoomVid');
                const box = doc.getElementById('videoFrameBox');
                
                // जैसे ही आवाज़ शुरू होगी, वीडियो एक्टिव होकर लिप-सिंक करेगा
                u.onstart = function() {{
                    if (vid1) {{ vid1.currentTime = 0; vid1.play().catch(e=>{{}}); }}
                    if (vid2) {{ vid2.currentTime = 0; vid2.play().catch(e=>{{}}); }}
                    if (box) {{ box.style.borderColor = '#00ff80'; box.style.boxShadow = '0 0 25px rgba(0,255,128,0.5)'; }}
                }};
                
                // जैसे ही आवाज़ खत्म होगी, वीडियो पॉज़ होकर शांत हो जाएगा
                u.onend = u.onerror = function() {{
                    if (vid1) {{ vid1.pause(); }}
                    if (vid2) {{ vid2.pause(); }}
                    if (box) {{ box.style.borderColor = '#ff4b4b'; box.style.boxShadow = '0 0 18px rgba(255,75,75,0.35)'; }}
                }};
                
                setTimeout(() => win.speechSynthesis.speak(u), 150);
            }}
        }} catch(e) {{}}
    </script>
    """, height=0)

thinking_box = st.empty()

# 7. स्क्रॉल करने योग्य सम्पूर्ण चैट हिस्ट्री (सारे पिछले सवाल व जवाब सुरक्षित)
st.markdown('<div class="chat-history-scroll">', unsafe_allow_html=True)
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f"🗣️ **आप (Q):** {msg['content']}")
    else:
        st.markdown(f"""
        <div style="background:#09101d; border:1.5px solid #00ff80; border-radius:10px; padding:10px 12px; margin:4px 0; box-shadow:0 2px 10px rgba(0,255,128,0.12);">
            <b style="color:#00ff80; font-size:14px;">👉 खुशी (Ambient Vision):</b><br>
            <span style="color:#f8fafc; font-size:13px; line-height:1.4;">{msg['content']}</span>
        </div>
        """, unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# 8. प्रोएक्टिव AI इंजन (मल्टी-मॉडल ऑटोमैटिक फॉलबैक - 429 से सुरक्षित)
def ask_gemini_vision(prompt=None, pil_image=None):
    if not client: return "त्रुटि: GEMINI_API_KEY नहीं मिली। कृपया Secrets जाँचें।"
    
    contents = []
    if pil_image:
        contents.append(pil_image)
        if not prompt:
            prompt = "कैमरे में देखकर बताओ यूज़र क्या कर रहा है या उसका मूड कैसा है? बिना पूछे उससे बहुत प्यार और हमदर्दी से 2 वाक्य में स्वाभाविक बात शुरू करो।"
    if prompt:
        contents.append(prompt)
        
    models_to_try = ['gemini-3.6-flash', 'gemini-2.5-flash']
    for m in models_to_try:
        try:
            res = client.models.generate_content(
                model=m,
                contents=contents,
                config=types.GenerateContentConfig(system_instruction=PERSONA)
            )
            if res and res.text: return res.text
        except Exception:
            continue
    return "माफ़ कीजिए, सर्वर अभी थोड़ा व्यस्त है। कृपया 5 सेकंड बाद पुनः बोलें।"

# 9. कैमरा विज़न प्रोसेसिंग (एक बार प्रोसेस, नो लूप)
cam_picture = st.session_state.get("in_cam")
if cam_picture:
    current_cam_id = f"{cam_picture.name}_{cam_picture.size}"
    if st.session_state.last_cam_id != current_cam_id:
        st.session_state.last_cam_id = current_cam_id
        img = Image.open(cam_picture)
        thinking_box.markdown('<div class="thinking-badge">👁️ खुशी आपको देख और महसूस कर रही है...</div>', unsafe_allow_html=True)
        
        ans = ask_gemini_vision(pil_image=img)
        st.session_state.messages.append({"role": "user", "content": "[कैमरे से लाइव देखा]"})
        st.session_state.messages.append({"role": "assistant", "content": ans})
        save_mem()
        st.session_state.clean_speak = re.sub(r'[*#~`_+=|\\<>]', ' ', ans).replace('"', ' ').replace("'", " ").strip()
        thinking_box.empty()
        st.rerun()

# 10. चैट इनपुट
user_query = st.chat_input("यहाँ लिखें या ऊपर mike बटन दबाकर बोलें...")
if user_query:
    st.session_state.messages.append({"role": "user", "content": user_query})
    thinking_box.markdown('<div class="thinking-badge">✨ खुशी सोच रही है... उत्तर आ रहा है ⚡</div>', unsafe_allow_html=True)
    
    ans = ask_gemini_vision(prompt=user_query)
    st.session_state.messages.append({"role": "assistant", "content": ans})
    save_mem()
    st.session_state.clean_speak = re.sub(r'[*#~`_+=|\\<>]', ' ', ans).replace('"', ' ').replace("'", " ").strip()
    thinking_box.empty()
    st.rerun()
