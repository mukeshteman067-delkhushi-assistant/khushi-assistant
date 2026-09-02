import streamlit as st

def apply_custom_css():
    st.markdown("""
    <style>
        .block-container { padding: 0.2rem 0.4rem 4rem 0.4rem !important; max-width: 100% !important; }
        header, footer, #MainMenu { visibility: hidden !important; }
        div[data-testid="column"] { padding: 2px !important; }
        div.stButton > button {
            width: 100% !important;
            border-radius: 10px !important;
            font-weight: bold !important;
            padding: 8px 2px !important;
            font-size: 12px !important;
            border: 1px solid transparent !important;
            transition: all 0.2s ease !important;
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

def render_zoom_mode(media_src):
    st.markdown(f"""
    <div style="width:100%; height:62vh; max-height:480px; background:#070913; border-radius:12px; border:2px solid #00ff80; display:flex; align-items:center; justify-content:center; padding:4px; box-sizing:border-box; margin-bottom:6px;">
        <canvas id="khushiCanvasZoom" style="width:100%; height:100%; border-radius:10px; object-fit:cover;"></canvas>
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

def render_standard_mode(media_src, save_mem_callback):
    master_col_left, master_col_right = st.columns([52, 48])
    
    with master_col_left:
        st.markdown(f"""
        <div id="avatarFrame" style="width:100%; height:310px; background:#000; border:2px solid #ff4b4b; border-radius:12px; overflow:hidden; position:relative; box-shadow:0 0 18px rgba(255,75,75,0.35); transition:transform 0.1s ease, border-color 0.2s ease;">
            <canvas id="khushiCanvas" style="width:100%; height:100%; object-fit:cover; display:block;"></canvas>
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
        # 1. लाल माइक-स्पीकर बटन (कैमरा के ऊपर)
        st.components.v1.html("""
        <div style="text-align:center;">
            <button id="nativeMic" style="width:100%; background:#ff4b4b; color:white; border:none; padding:12px 2px; border-radius:10px; font-size:13px; font-weight:bold; cursor:pointer; box-shadow:0 3px 12px rgba(255,75,75,0.45);">
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
            
        # 3. इन-प्लेस कैमरा बॉक्स (प्रोएक्टिव विज़न)
        if st.session_state.cam_on:
            st.camera_input("लाइव कैमरा (विज़न एक्टिव)", label_visibility="collapsed", key="in_cam")
        else:
            st.markdown("""
            <div style="width:100%; height:88px; background:#07080f; border-radius:10px; border:1px dashed #2e3856; display:flex; align-items:center; justify-content:center;">
                <span style="color:#555f7d; font-size:11px;">कैमरा स्टैंडबाय (OFF)</span>
            </div>
            """, unsafe_allow_html=True)
        
        # 4. इनलाइन सेटिंग्स व मेमोरी साफ़
        st.markdown("""
        <div style="width:100%; background:#131526; border:1px solid #7c3aed; border-radius:10px; padding:4px; margin-top:2px;">
            <div style="display:flex; justify-content:space-between; align-items:center; padding:0 2px;">
                <span style="color:#c084fc; font-size:10.5px; font-weight:bold;">⚙️ सेटिंग</span>
                <span style="color:#10b981; font-size:9px;">● 3.6 Flash Vision</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🗑️ मेमोरी साफ़ करें", key="btn_clear_mem"):
            st.session_state.messages = []
            save_mem_callback()
            st.success("मेमोरी रीसेट हो गई!")
            st.rerun()

def init_mesh_canvas_engine(img_b64, clean_speak):
    st.components.v1.html(f"""
    <script>
        const win = window.parent || window;
        const doc = win.document;
        
        let canvas = doc.getElementById('khushiCanvas');
        if (!canvas) canvas = doc.getElementById('khushiCanvasZoom');
        
        if (canvas) {{
            const ctx = canvas.getContext('2d');
            const img = new Image();
            img.src = "{img_b64}";
            
            let isSpeaking = false;
            let jawOffset = 0;
            
            img.onload = () => {{
                canvas.width = img.naturalWidth || 400;
                canvas.height = img.naturalHeight || 500;
                startRenderLoop();
            }};
            
            function startRenderLoop() {{
                let tick = 0;
                function loop() {{
                    tick++;
                    ctx.clearRect(0, 0, canvas.width, canvas.height);
                    ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
                    
                    if (isSpeaking && jawOffset > 1) {{
                        const mouthY = canvas.height * 0.62;
                        const mouthH = canvas.height * 0.22;
                        ctx.drawImage(
                            img,
                            0, mouthY, canvas.width, mouthH,
                            0, mouthY + (jawOffset * 0.8), canvas.width, mouthH + jawOffset
                        );
                    }}
                    requestAnimationFrame(loop);
                }}
                loop();
            }}
            
            const toSpeak = "{clean_speak}";
            if (toSpeak && toSpeak.length > 0 && 'speechSynthesis' in win) {{
                win.speechSynthesis.cancel();
                const u = new win.SpeechSynthesisUtterance(toSpeak);
                u.lang = 'hi-IN';
                u.rate = 1.0;
                
                let mouthInterval = null;
                u.onstart = () => {{
                    isSpeaking = true;
                    const frame = doc.getElementById('avatarFrame');
                    if (frame) {{
                        frame.style.borderColor = '#00ff80';
                        frame.style.boxShadow = '0 0 25px rgba(0,255,128,0.5)';
                    }}
                    mouthInterval = setInterval(() => {{
                        jawOffset = (Math.sin(Date.now() * 0.02) + 1) * 3.5;
                    }}, 40);
                }};
                
                u.onend = () => {{
                    isSpeaking = false;
                    jawOffset = 0;
                    if (mouthInterval) clearInterval(mouthInterval);
                    const frame = doc.getElementById('avatarFrame');
                    if (frame) {{
                        frame.style.borderColor = '#ff4b4b';
                        frame.style.boxShadow = '0 0 18px rgba(255,75,75,0.35)';
                    }}
                }};
                u.onerror = u.onend;
                setTimeout(() => {{ win.speechSynthesis.speak(u); }}, 100);
            }}
        }}
    </script>
    """, height=0)
          
