import streamlit as st

def apply_custom_css():
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

def render_zoom_mode(media_src, has_vid):
    st.markdown(f"""
    <div style="width:100%; height:62vh; max-height:480px; background:#070913; border-radius:12px; border:2px solid #00ff80; display:flex; align-items:center; justify-content:center; padding:4px; box-sizing:border-box; margin-bottom:6px; box-shadow:0 0 20px rgba(0,255,128,0.35);">
        <div style="width:100%; height:100%; border-radius:10px; overflow:hidden;">
            {'<video id="kZoomVid" src="' + media_src + '" autoplay loop muted playsinline style="width:100%; height:100%; object-fit:cover; object-position:center 15%;"></video>' if has_vid else '<img src="' + media_src + '" style="width:100%; height:100%; object-fit:cover; object-position:center 15%;" />'}
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

def render_standard_mode(media_src, has_vid, save_mem_callback):
    master_col_left, master_col_right = st.columns([52, 48])
    
    with master_col_left:
        st.markdown(f"""
        <div id="videoFrameBox" style="width:100%; height:310px; background:#000; border:2px solid #ff4b4b; border-radius:12px; overflow:hidden; position:relative; box-shadow:0 0 18px rgba(255,75,75,0.35);">
            {'<video id="kMainVid" src="' + media_src + '" autoplay loop muted playsinline style="width:100%; height:100%; object-fit:cover; object-position:center 12%;"></video>' if has_vid else '<img src="' + media_src + '" style="width:100%; height:100%; object-fit:cover; object-position:center 12%;" />'}
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
        # लाल माइक-स्पीकर बटन (शीर्ष पर)
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

        cam_text = "📷 कैमरा on — off" if not st.session_state.cam_on else "📷 कैमरा (LIVE ON)"
        if st.button(cam_text, key="btn_cam_toggle"):
            st.session_state.cam_on = not st.session_state.cam_on
            st.rerun()
            
        if st.session_state.cam_on:
            st.camera_input("लाइव कैमरा", label_visibility="collapsed", key="in_cam")
        else:
            st.markdown("""
            <div style="width:100%; height:88px; background:#07080f; border-radius:10px; border:1px dashed #2e3856; display:flex; align-items:center; justify-content:center;">
                <span style="color:#555f7d; font-size:10.5px;">कैमरा स्टैंडबाय (OFF)</span>
            </div>
            """, unsafe_allow_html=True)
        
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
            save_mem_callback()
            st.rerun()

# लाइन 68 वाला आवश्यक फंक्शन:
def play_audio_engine(clean_speak):
    if clean_speak:
        st.components.v1.html(f"""
        <script>
            try {{
                const win = window.parent || window;
                if ('speechSynthesis' in win) {{
                    win.speechSynthesis.cancel();
                    const u = new win.SpeechSynthesisUtterance("{clean_speak}");
                    u.lang = 'hi-IN';
                    u.rate = 1.0;
                    
                    u.onstart = function() {{
                        const f = win.document.getElementById('videoFrameBox');
                        if (f) {{ f.style.borderColor = '#00ff80'; f.style.boxShadow = '0 0 25px rgba(0,255,128,0.5)'; }}
                    }};
                    u.onend = u.onerror = function() {{
                        const f = win.document.getElementById('videoFrameBox');
                        if (f) {{ f.style.borderColor = '#ff4b4b'; f.style.boxShadow = '0 0 18px rgba(255,75,75,0.35)'; }}
                    }};
                    
                    setTimeout(() => win.speechSynthesis.speak(u), 100);
                }}
            }} catch(e) {{}}
        </script>
        """, height=0)
