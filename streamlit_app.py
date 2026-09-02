import streamlit as st
import requests

# 1. Page Configuration
st.set_page_config(page_title="OmniDoc", page_icon="📄", layout="wide")
st.title("📄 OmniDoc Dashboard")
st.write("Upload multi-PDF documents and ask questions with low-latency hierarchical RAG.")

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
def get_error_message(res, default_msg="An error occurred"):
    if res is None:
        return default_msg
    try:
        data = res.json()
        detail = data.get("detail", default_msg)
        if isinstance(detail, list):
            return "Please ensure all fields are filled out correctly."
        return str(detail)
    except Exception:
        return f"{default_msg} (Server returned HTTP {res.status_code})"

# 2. Sidebar Setup
with st.sidebar:
    st.header("Authentication")
    
    if st.session_state.auth_token:
        st.success("✅ You are securely logged in.")
        if st.button("Logout"):
            st.session_state.auth_token = None
            st.session_state.session_id = None
            st.session_state.suggested_questions = []
            st.session_state.messages = []
            st.rerun()
            
    else:
        auth_mode = st.radio("Select Action", ["Log In", "Register", "Manual Token"])
        
        if auth_mode == "Log In":
            with st.form("login_form"):
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                submit_login = st.form_submit_button("Log In")
                
                if submit_login:
                    if not email or not password:
                        st.error("⚠️ Please enter both your email and password.")
                    else:
                        with st.spinner("Logging in..."):
                            try:
                                login_res = requests.post(
                                    f"{API_URL}/login", 
                                    data={"username": email, "password": password},
                                    timeout=60
                                )
                                if login_res.status_code in [200, 201]:
                                    data = login_res.json()
                                    st.session_state.auth_token = data.get("access_token")
                                    st.success("Logged in successfully!")
                                    st.rerun()
                                else:
                                    err_msg = get_error_message(login_res, "Invalid credentials")
                                    st.error(f"Login failed: {err_msg}")
                            except Exception as e:
                                st.error(f"Connection Error: {e}")
                            
        elif auth_mode == "Register":
            with st.form("register_form"):
                reg_email = st.text_input("Email")
                reg_password = st.text_input("Password", type="password")
                submit_register = st.form_submit_button("Register")
                
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
                                    timeout=60
                                )
                                if reg_res.status_code == 201:
                                    st.success("✅ Account created! Please select 'Log In' above to authenticate.")
                                else:
                                    err_msg = get_error_message(reg_res, "Registration failed")
                                    st.error(f"Registration failed: {err_msg}")
                            except Exception as e:
                                st.error(f"Connection Error: {e}")
                            
        elif auth_mode == "Manual Token":
            manual_token = st.text_input("Access Token / JWT", type="password")
            if st.button("Set Token"):
                if manual_token:
                    st.session_state.auth_token = manual_token
                    st.success("Token set!")
                    st.rerun()
                else:
                    st.warning("Please enter a token.")

    st.divider()
    
    if st.session_state.session_id:
        st.header("Active Session")
        st.info(f"📁 Session ID: `{st.session_state.session_id[:8]}...`")
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
        "Choose PDF files to index into PGVector",
        type=["pdf"],
        accept_multiple_files=True
    )
    
    upload_btn = st.button("🚀 Process & Index Documents", type="primary")

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

                    # ✅ Points to /upload on live backend
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
                        st.success("✅ Documents Processed and Indexed Successfully!")
                        st.rerun()

                    elif response.status_code == 401:
                        st.error("🔒 Unauthorized (401): Invalid or expired access token. Please log out and log back in.")
                    else:
                        err_msg = get_error_message(response, "Upload failed")
                        st.error(f"🚨 Error: {err_msg}")

                except requests.exceptions.Timeout:
                    st.error("The request timed out. Document processing took longer than expected.")
                except requests.exceptions.RequestException as e:
                    st.error(f"Failed to connect to the backend: {e}")

else:
    st.subheader("💬 Step 2: Chat with Your Documents")

    if st.session_state.suggested_questions:
        st.write("💡 **AI Suggested Questions:**")
        cols = st.columns(len(st.session_state.suggested_questions[:3]))
        for i, question_text in enumerate(st.session_state.suggested_questions[:3]):
            if cols[i].button(f"🔍 {question_text}", key=f"sug_q_{i}", use_container_width=True):
                st.session_state.messages.append({"role": "user", "content": question_text})
                st.rerun()

    st.divider()

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_query = st.chat_input("Ask a question about your uploaded documents...")

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

                # ✅ Points to /chat/{session_id} on live backend
                stream_res = requests.post(
                    f"{API_URL}/chat/{st.session_state.session_id}",
                    headers=headers,
                    json={"question": query_to_send},
                    stream=True,
                    timeout=90
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
                    st.error("Unauthorized. Please log out and log back in.")
                else:
                    err_msg = get_error_message(stream_res, "Streaming request failed")
                    st.error(f"Error: {err_msg}")

            except requests.exceptions.RequestException as e:
                st.error(f"Streaming error: {e}")