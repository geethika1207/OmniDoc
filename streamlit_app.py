import streamlit as st
import requests

# 1. Page Configuration
st.set_page_config(page_title="OmniDoc", page_icon="📄", layout="wide")
st.title("📄 OmniDoc Dashboard")
st.write("Upload multi-PDF documents and ask questions with low-latency hierarchical RAG.")

st.info(
    "👋 **Welcome to OmniDoc!**\n\n"
    "Upload one or more PDF documents to generate hierarchical parent-child embeddings with PGVector, "
    "get AI-suggested starter questions, and chat with your documents in real-time."
)

# Live Render backend URL
API_URL = "https://omnidoc-fiak.onrender.com"

# --- INIT SESSION STATE ---
# This keeps the user logged in and tracks session across button clicks
if "auth_token" not in st.session_state:
    st.session_state.auth_token = None
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "suggested_questions" not in st.session_state:
    st.session_state.suggested_questions = []
if "messages" not in st.session_state:
    st.session_state.messages = []

# 2. Sidebar Setup
with st.sidebar:
    st.header("Authentication")
    
    # If the user is already logged in, show a success message and a Logout button
    if st.session_state.auth_token:
        st.success("✅ You are securely logged in.")
        if st.button("Logout"):
            st.session_state.auth_token = None
            st.session_state.session_id = None
            st.session_state.suggested_questions = []
            st.session_state.messages = []
            st.rerun()  # Refresh the app to clear state
            
    # If the user is NOT logged in, show the Login/Register UI
    else:
        auth_mode = st.radio("Select Action", ["Log In", "Register", "Manual Token"])
        
        if auth_mode == "Log In":
            with st.form("login_form"):
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                submit_login = st.form_submit_button("Log In")
                
                if submit_login:
                    # FRONTEND VALIDATION: Check for empty fields
                    if not email or not password:
                        st.error("⚠️ Please enter both your email and password.")
                    else:
                        with st.spinner("Logging in..."):
                            # OAuth2PasswordRequestForm expects 'username' and 'password' as form data
                            login_res = requests.post(
                                f"{API_URL}/login", 
                                data={"username": email, "password": password}
                            )
                            if login_res.status_code in [200, 201]:
                                # Save the token to session state
                                st.session_state.auth_token = login_res.json().get("access_token")
                                st.success("Logged in successfully!")
                                st.rerun()  # Refresh the UI to hide the login form
                            else:
                                # CLEAN ERROR HANDLING: Catch Pydantic 422 lists safely
                                error_detail = login_res.json().get("detail", "Invalid credentials")
                                if isinstance(error_detail, list):
                                    st.error("⚠️ Please ensure all fields are filled out correctly.")
                                else:
                                    st.error(f"Login failed: {error_detail}")
                            
        elif auth_mode == "Register":
            with st.form("register_form"):
                reg_email = st.text_input("Email")
                reg_password = st.text_input("Password", type="password")
                submit_register = st.form_submit_button("Register")
                
                if submit_register:
                    # FRONTEND VALIDATION: Prevent empty strings and short passwords
                    if not reg_email or not reg_password:
                        st.error("⚠️ Please enter both an email and a password.")
                    elif len(reg_password) < 4:
                        st.warning("⚠️ Password must be at least 4 characters long.")
                    else:
                        with st.spinner("Creating account..."):
                            # Registration expects standard JSON
                            reg_res = requests.post(
                                f"{API_URL}/user", 
                                json={"email": reg_email, "password": reg_password}
                            )
                            if reg_res.status_code == 201:
                                st.success("✅ Account created! Please select 'Log In' above to authenticate.")
                            else:
                                # CLEAN ERROR HANDLING
                                error_detail = reg_res.json().get("detail", "Error creating account")
                                if isinstance(error_detail, list):
                                    st.error("⚠️ Invalid email format or missing fields.")
                                else:
                                    st.error(f"Registration failed: {error_detail}")
                            
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
    
    # Session Reset in Sidebar
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

# Document Upload Step
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
                "Extracting PDF text, chunking into parent-child blocks, generating Cohere embeddings, "
                "and indexing into PGVector...\n\n"
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
                        f"{API_URL}/api/upload",
                        headers=headers,
                        files=files_payload,
                        timeout=120
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
                        st.error(f"🚨 Error {response.status_code}: {response.text}")

                except requests.exceptions.Timeout:
                    st.error("The request timed out. Document processing took longer than expected.")
                except requests.exceptions.RequestException as e:
                    st.error(f"Failed to connect to the backend: {e}")

# Chat Step (When documents are indexed)
else:
    st.subheader("💬 Step 2: Chat with Your Documents")

    # Display AI Suggested Questions as Clickable Buttons
    if st.session_state.suggested_questions:
        st.write("💡 **AI Suggested Questions:**")
        cols = st.columns(len(st.session_state.suggested_questions[:3]))
        for i, question_text in enumerate(st.session_state.suggested_questions[:3]):
            if cols[i].button(f"🔍 {question_text}", key=f"sug_q_{i}", use_container_width=True):
                st.session_state.messages.append({"role": "user", "content": question_text})
                st.rerun()

    st.divider()

    # Display Chat History
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat Input Bar
    user_query = st.chat_input("Ask a question about your uploaded documents...")

    # Check if a suggested question was clicked or user typed in chat input
    needs_response = False
    query_to_send = ""

    if user_query:
        query_to_send = user_query
        st.session_state.messages.append({"role": "user", "content": query_to_send})
        with st.chat_message("user"):
            st.markdown(query_to_send)
        needs_response = True

    elif st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
        # Handle case where user clicked a suggested question button
        if len(st.session_state.messages) % 2 == 1:
            query_to_send = st.session_state.messages[-1]["content"]
            needs_response = True

    # Stream the Assistant Response
    if needs_response:
        with st.chat_message("assistant"):
            try:
                headers = {
                    "Authorization": f"Bearer {st.session_state.auth_token}",
                    "Content-Type": "application/json"
                }

                stream_res = requests.post(
                    f"{API_URL}/api/chat/{st.session_state.session_id}",
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
                    st.error("Unauthorized. Please log out and log back in.")
                else:
                    st.error(f"Error {stream_res.status_code}: {stream_res.text}")

            except requests.exceptions.RequestException as e:
                st.error(f"Streaming error: {e}")