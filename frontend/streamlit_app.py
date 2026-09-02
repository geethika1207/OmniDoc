import streamlit as st
import requests

# 1. Page Configuration
st.set_page_config(page_title="OmniDoc", page_icon="📄", layout="wide")
st.title("📄 OmniDoc Dashboard")
st.write("Upload your PDF documents and get instant answers powered by AI.")

st.info(
    "👋 **Welcome to OmniDoc!**\n\n"
    "Upload one or more PDF documents to analyze their content, get smart starter questions, "
    "and chat with your files in real time."
)

# Live Render backend URL
API_URL = "https://omnidoc-fiak.onrender.com"

# --- INIT SESSION STATE ---
if "auth_token" not in st.session_state:
    st.session_state.auth_token = None
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "suggested_questions" not in st.session_state:
    st.session_state.suggested_questions = []
if "messages" not in st.session_state:
    st.session_state.messages = []

# Helper function to safely parse API error response
def get_error_message(res, action_type=""):
    if res is None:
        return "Failed to connect to the server."
    
    try:
        data = res.json()
        detail = data.get("detail", "")
    except Exception:
        detail = res.text

    # Registration specific error handling
    if action_type == "register":
        if res.status_code == 400:
            if "already registered" in str(detail).lower():
                return "⚠️ This email is already registered! Please switch to 'Log In' above to authenticate."
            return f"⚠️ Registration failed: {detail}"
        elif res.status_code == 422:
            return "⚠️ Invalid email format. Please enter a valid email address (e.g., name@gmail.com)."

    # Login specific error handling
    elif action_type == "login":
        if res.status_code == 401:
            return "⚠️ Invalid email or password. If you haven't created an account yet, please select 'Register' above."
        elif res.status_code == 422:
            return "⚠️ Please enter a valid email address and password."

    # Generic handling
    if isinstance(detail, list):
        return "⚠️ Please ensure all fields are filled out correctly."
    if detail:
        return f"⚠️ {detail}"
    return f"⚠️ Server returned HTTP {res.status_code}"

# 2. Sidebar Setup
with st.sidebar:
    st.header("Account")
    
    if st.session_state.auth_token:
        st.success("✅ Logged in securely")
        if st.button("Logout", use_container_width=True):
            st.session_state.auth_token = None
            st.session_state.session_id = None
            st.session_state.suggested_questions = []
            st.session_state.messages = []
            st.rerun()
            
    else:
        auth_mode = st.radio("Select Action", ["Log In", "Register", "Manual Token"])
        
        if auth_mode == "Log In":
            with st.form("login_form"):
                email = st.text_input("Email", placeholder="name@example.com")
                password = st.text_input("Password", type="password", placeholder="••••••••")
                submit_login = st.form_submit_button("Log In", use_container_width=True)
                
                if submit_login:
                    if not email or not password:
                        st.error("⚠️ Please enter both your email and password.")
                    else:
                        with st.spinner("Logging in..."):
                            try:
                                login_res = requests.post(
                                    f"{API_URL}/login", 
                                    data={"username": email, "password": password},
                                    timeout=90
                                )
                                if login_res.status_code in [200, 201]:
                                    data = login_res.json()
                                    st.session_state.auth_token = data.get("access_token")
                                    st.success("Logged in successfully!")
                                    st.rerun()
                                else:
                                    err_msg = get_error_message(login_res, action_type="login")
                                    st.error(err_msg)
                            except Exception as e:
                                st.error(f"Connection Error: {e}")
                            
        elif auth_mode == "Register":
            with st.form("register_form"):
                reg_email = st.text_input("Email", placeholder="name@example.com")
                reg_password = st.text_input("Password", type="password", placeholder="••••••••")
                submit_register = st.form_submit_button("Create Account", use_container_width=True)
                
                if submit_register:
                    if not reg_email or not reg_password:
                        st.error("⚠️ Please enter both an email and a password.")
                    elif len(reg_password) < 4:
                        st.warning("⚠️ Password must be at least 4 characters long.")
                    else:
                        with st.spinner("Creating account..."):
                            try:
                                reg_res = requests.post(
                                    f"{API_URL}/user", 
                                    json={"email": reg_email, "password": reg_password},
                                    timeout=90
                                )
                                if reg_res.status_code == 201:
                                    st.success("✅ Account created successfully! Please select 'Log In' above to authenticate.")
                                else:
                                    err_msg = get_error_message(reg_res, action_type="register")
                                    st.error(err_msg)
                            except Exception as e:
                                st.error(f"Connection Error: {e}")
                            
        elif auth_mode == "Manual Token":
            manual_token = st.text_input("Access Token / JWT", type="password")
            if st.button("Set Token", use_container_width=True):
                if manual_token:
                    st.session_state.auth_token = manual_token
                    st.success("Token set!")
                    st.rerun()
                else:
                    st.warning("Please enter a token.")

    st.divider()
    
    if st.session_state.session_id:
        st.header("Active Document Session")
        st.info("📄 Documents loaded and active")
        if st.button("➕ Upload New Documents", use_container_width=True):
            st.session_state.session_id = None
            st.session_state.suggested_questions = []
            st.session_state.messages = []
            st.rerun()

# 3. Main Action Section
if not st.session_state.auth_token:
    st.warning("🔒 Please log in or register in the sidebar to begin.")

elif not st.session_state.session_id:
    st.subheader("📤 Step 1: Upload Your PDF Document(s)")
    uploaded_files = st.file_uploader(
        "Choose one or more PDF files to analyze",
        type=["pdf"],
        accept_multiple_files=True
    )
    
    upload_btn = st.button("🚀 Analyze Documents", type="primary")

    if upload_btn:
        if not uploaded_files:
            st.warning("Please select at least one PDF file to upload!")
        else:
            with st.spinner(
                "Reading documents, organizing key sections, and preparing AI search...\n\n"
                "⏳ *This usually takes a few seconds. Please wait...*"
            ):
                try:
                    headers = {
                        "Authorization": f"Bearer {st.session_state.auth_token}"
                    }
                    
                    files_payload = [
                        ("files", (f.name, f.getvalue(), "application/pdf")) 
                        for f in uploaded_files
                    ]

                    response = requests.post(
                        f"{API_URL}/upload",
                        headers=headers,
                        files=files_payload,
                        timeout=180
                    )

                    if response.status_code == 200:
                        data = response.json()
                        st.session_state.session_id = data.get("session_id")
                        st.session_state.suggested_questions = data.get("suggested_questions", [])
                        st.success("✅ Documents Ready! You can now ask questions below.")
                        st.rerun()

                    elif response.status_code == 401:
                        st.error("🔒 Unauthorized: Session expired. Please log out and log back in.")
                    else:
                        err_msg = get_error_message(response)
                        st.error(f"🚨 Upload Error: {err_msg}")

                except requests.exceptions.Timeout:
                    st.error("The request timed out. Document processing took longer than expected.")
                except requests.exceptions.RequestException as e:
                    st.error(f"Failed to connect to the backend: {e}")

else:
    st.subheader("💬 Step 2: Chat with Your Documents")

    if st.session_state.suggested_questions:
        st.write("💡 **Suggested Questions:**")
        cols = st.columns(len(st.session_state.suggested_questions[:3]))
        for i, question_text in enumerate(st.session_state.suggested_questions[:3]):
            if cols[i].button(f"🔍 {question_text}", key=f"sug_q_{i}", use_container_width=True):
                st.session_state.messages.append({"role": "user", "content": question_text})
                st.rerun()

    st.divider()

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_query = st.chat_input("Ask any question about your documents...")

    needs_response = False
    query_to_send = ""

    if user_query:
        query_to_send = user_query
        st.session_state.messages.append({"role": "user", "content": query_to_send})
        with st.chat_message("user"):
            st.markdown(query_to_send)
        needs_response = True

    elif st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
        if len(st.session_state.messages) % 2 == 1:
            query_to_send = st.session_state.messages[-1]["content"]
            needs_response = True

    if needs_response:
        with st.chat_message("assistant"):
            try:
                headers = {
                    "Authorization": f"Bearer {st.session_state.auth_token}",
                    "Content-Type": "application/json"
                }

                stream_res = requests.post(
                    f"{API_URL}/chat/{st.session_state.session_id}",
                    headers=headers,
                    json={"question": query_to_send},
                    stream=True,
                    timeout=60
                )

                if stream_res.status_code == 200:
                    def stream_generator():
                        for chunk in stream_res.iter_content(chunk_size=128, decode_unicode=True):
                            if chunk:
                                yield chunk

                    full_answer = st.write_stream(stream_generator)
                    st.session_state.messages.append({"role": "assistant", "content": full_answer})

                elif stream_res.status_code == 404:
                    st.error("No relevant context found. Please ensure the document is uploaded.")
                elif stream_res.status_code == 401:
                    st.error("Session expired. Please log out and log back in.")
                else:
                    err_msg = get_error_message(stream_res)
                    st.error(f"Error: {err_msg}")

            except requests.exceptions.RequestException as e:
                st.error(f"Streaming error: {e}")