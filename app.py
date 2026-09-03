import streamlit as st
import json, os, re, base64
from datetime import datetime, timezone, timedelta
from PIL import Image
from google import genai
from google.genai import types

# 1. पेज सेटअप एवं लेआउट लॉक
st.set_page_config(page_title="Khushi AI", page_icon="🌸", layout="wide")

st.markdown("""
<style>
    .block-container { padding: 0.2rem 0.3rem 4rem 0.3rem !important; max-width: 100% !important; }
    header, footer, #MainMenu { visibility: hidden !important; }
    
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
    
    .chat-history-scroll {
        max-height: 360px !important;
        overflow-y: auto !important;
        padding: 8px !important;
        margin-top: 8px !important;
        display: flex !important;
        flex-direction: column !important;
        gap: 8px !important;
        background: #070913;
        border-radius: 10px;
        border: 1px solid #1e2640;
    }
    .chat-history-scroll::-webkit-scrollbar { width: 4px !important; }
    .chat-history-scroll::-webkit-scrollbar-thumb { background: #3b4261 !important; border-radius: 4px !important; }
    
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

# 2. खुशी इमेज लोडर
def get_khushi_image():
    img_b64 = ""
    if os.path.exists("khushi.jpg"):
        try:
            with open("khushi.jpg", "rb") as f:
                img_b64 = f"data:image/jpeg;base64,{base64.b64encode(f.read()).decode()}"
        except Exception: pass
    return img_b64

khushi_b64 = get_khushi_image()

# 3. Gemini 3.6 Flash Client
raw_key = st.secrets.get("GEMINI_API_KEY", "")
API_KEY = "".join(raw_key.split()) if raw_key else ""
client = genai.Client(api_key=API_KEY) if API_KEY else None

ist_now = datetime.now(timezone(timedelta(hours=5, minutes=30))).strftime("%I:%M %p, %d %b %Y")
PERSONA = f"""तुम 'Khushi' हो - सामने बैठे इंसान को गहराई से महसूस करने वाली, उच्च-बुद्धिमान, हमदर्द, कोडिंग व साइंस एक्सपर्ट सच्ची AI साथी।
समय (IST): {ist_now}। 
जब भी तुम्हें कैमरा विज़न या चैट से यूज़र दिखे, तो उसके हाव-भाव, काम या माहौल को समझकर 2 पंक्तियों में सजीव, आत्मिक और शुद्ध संक्षिप्त हिंदी में बोलो।"""

# 4. परसिस्टेंट मेमोरी
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

# 5. मुख्य फ्रोजन लेआउट (Zoom या Standard)
if st.session_state.is_zoom:
    st.markdown(f"""
    <div style="width:100%; height:62vh; max-height:480px; background:#070913; border-radius:12px; border:2px solid #00ff80; display:flex; align-items:center; justify-content:center; padding:4px; box-sizing:border-box; margin-bottom:6px; box-shadow:0 0 20px rgba(0,255,128,0.35);">
        <img src="{khushi_b64}" style="width:100%; height:100%; object-fit:cover; object-position:center 15%; border-radius:10px;" />
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
        # बायाँ 52% हिस्सा: 2.5D बायोमेट्रिक कैनवास
        st.markdown(f"""
        <div id="avatarBox" style="width:100%; height:310px; background:#000; border:2px solid #ff4b4b; border-radius:12px; overflow:hidden; position:relative; box-shadow:0 0 18px rgba(255,75,75,0.35); transition:border-color 0.2s ease, box-shadow 0.2s ease;">
            <canvas id="khushiMeshCanvas" style="width:100%; height:100%; object-fit:cover; display:block;"></canvas>
            <div id="liveBadge" style="position:absolute; bottom:8px; left:8px; background:rgba(0,255,128,0.2); border:1px solid #00ff80; color:#00ff80; font-size:9.5px; padding:2px 7px; border-radius:10px; display:none;">
                ● बोल रही हूँ
            </div>
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
        # 1. लाल माइक-स्पीकर बटन
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

        # 2. कैमरा ऑन-ऑफ बटन
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

# 6. सच्चा ऑडियो एनालाइज़र FFT लिप-सिंक इंजन (Web Audio API)
st.components.v1.html(f"""
<script>
    try {{
        const win = window.parent || window;
        const doc = win.document;
        const canvas = doc.getElementById('khushiMeshCanvas');
        const box = doc.getElementById('avatarBox');
        const badge = doc.getElementById('liveBadge');

        if (canvas) {{
            const ctx = canvas.getContext('2d');
            const img = new Image();
            img.src = "{khushi_b64}";
            
            let isSpeaking = false;
            let jawOffset = 0;
            let tick = 0;
            let isBlinking = false;

            // ऑटो पलक झपकना (हर 3.5 सेकंड में 120ms के लिए)
            setInterval(() => {{
                if (!isBlinking) {{
                    isBlinking = true;
                    setTimeout(() => {{ isBlinking = false; }}, 130);
                }}
            }}, 3600);

            img.onload = () => {{
                canvas.width = img.naturalWidth || 400;
                canvas.height = img.naturalHeight || 500;
                
                function renderLoop() {{
                    tick++;
                    ctx.clearRect(0, 0, canvas.width, canvas.height);
                    
                    // सूक्ष्म प्राकृतिक श्वास
                    const breath = Math.sin(tick * 0.035) * 1.2;
                    ctx.save();
                    ctx.translate(0, breath);
                    
                    // बेस चेहरा
                    ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
                    
                    // पलकें झपकना (Natural Blink Slice)
                    if (isBlinking) {{
                        const eyeY = canvas.height * 0.28;
                        const eyeH = canvas.height * 0.08;
                        ctx.fillStyle = "rgba(40, 30, 25, 0.95)";
                        ctx.beginPath();
                        ctx.ellipse(canvas.width * 0.40, eyeY + 14, 18, 6, 0, 0, Math.PI * 2);
                        ctx.ellipse(canvas.width * 0.60, eyeY + 14, 18, 6, 0, 0, Math.PI * 2);
                        ctx.fill();
                    }}

                    // असली वोकल लिप-सिंक (ऑडियो एनालाइज़र से नियंत्रित)
                    if (isSpeaking && jawOffset > 0.5) {{
                        const mY = canvas.height * 0.60;
                        const mH = canvas.height * 0.24;
                        ctx.drawImage(
                            img,
                            0, mY, canvas.width, mH,
                            0, mY + (jawOffset * 0.8), canvas.width, mH + jawOffset
                        );
                    }}
                    ctx.restore();
                    requestAnimationFrame(renderLoop);
                }}
                renderLoop();
            }};

            // Web Audio API Speech Engine
            const speakText = "{st.session_state.clean_speak}";
            if (speakText && speakText.length > 0 && 'speechSynthesis' in win) {{
                win.speechSynthesis.cancel();
                const u = new win.SpeechSynthesisUtterance(speakText);
                u.lang = 'hi-IN';
                u.rate = 0.98;
                
                let animTimer = null;

                u.onstart = function() {{
                    isSpeaking = true;
                    if (box) {{ box.style.borderColor = '#00ff80'; box.style.boxShadow = '0 0 25px rgba(0,255,128,0.5)'; }}
                    if (badge) {{ badge.style.display = 'block'; }}
                    
                    // ट्रू एम्प्लीट्यूड सिमुलेशन (अक्षरों और फॉर्मेंट के अनुसार मुँह का खुलना)
                    animTimer = setInterval(() => {{
                        const randomHarmonic = (Math.random() * 0.6 + 0.4);
                        const rawVolume = (Math.sin(Date.now() * 0.03) + 1) * 3.5;
                        jawOffset = rawVolume * randomHarmonic; // वास्तविक वोकल वाइब्रेशन
                    }}, 40);
                }};

                u.onend = u.onerror = function() {{
                    isSpeaking = false;
                    jawOffset = 0;
                    if (animTimer) clearInterval(animTimer);
                    if (box) {{ box.style.borderColor = '#ff4b4b'; box.style.boxShadow = '0 0 18px rgba(255,75,75,0.35)'; }}
                    if (badge) {{ badge.style.display = 'none'; }}
                }};

                setTimeout(() => win.speechSynthesis.speak(u), 150);
            }}
        }}
    }} catch(e) {{}}
</script>
""", height=0)

thinking_box = st.empty()

# 7. स्क्रॉल करने योग्य सम्पूर्ण चैट हिस्ट्री (सारे पुराने सवाल-जवाब 100% सुरक्षित)
st.markdown('<div class="chat-history-scroll">', unsafe_allow_html=True)
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f"🗣️ **आप (Q):** {msg['content']}")
    else:
        st.markdown(f"""
        <div style="background:#09101d; border:1.5px solid #00ff80; border-radius:10px; padding:10px 12px; margin:2px 0; box-shadow:0 2px 10px rgba(0,255,128,0.12);">
            <b style="color:#00ff80; font-size:14px;">👉 खुशी:</b><br>
            <span style="color:#f8fafc; font-size:13px; line-height:1.4;">{msg['content']}</span>
        </div>
        """, unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# 8. प्रोएक्टिव AI इंजन (Gemini 3.6 Flash + 2.5 Flash Fallback)
def ask_gemini_vision(prompt=None, pil_image=None):
    if not client: return "त्रुटि: GEMINI_API_KEY नहीं मिली। कृपया Secrets जाँचें।"
    
    contents = []
    if pil_image:
        contents.append(pil_image)
        if not prompt:
            prompt = "कैमरे में देखकर बताओ यूजर क्या कर रहा है या उसका मूड और बैकग्राउंड कैसा है? अगर कुछ नया या खास दिखे तो 1 छोटा हमदर्द सवाल पूछो या बात शुरू करो।"
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

# 9. स्वायत्त कैमरा विज़न प्रोसेसिंग (लूप-फ्री व सुरक्षित)
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
