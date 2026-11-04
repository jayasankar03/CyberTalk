
import json
import os

import requests
import streamlit as st


# -----------------------------
# Page configuration
# -----------------------------

st.set_page_config(
    page_title="CyberTalk",
    page_icon="🛡️",
    layout="wide",
)
# -----------------------------
# CyberTalk Custom UI Theme
# -----------------------------

st.markdown(
    """
    <style>

    /* Main application background */
    .stApp {
        background: linear-gradient(
            135deg,
            #071426 0%,
            #10243d 50%,
            #091a2e 100%
        );
        color: #eaf2ff;
    }

    /* Main content area */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1400px;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(
            180deg,
            #0b192c,
            #10243d
        );
        border-right: 1px solid #263e5c;
    }

    /* Headings */
    h1, h2, h3 {
        color: #eaf2ff !important;
        font-weight: 700 !important;
    }

    /* Paragraphs */
    p, label, .stMarkdown {
        color: #d1deef;
    }

    /* Buttons */
    .stButton > button,
    .stFormSubmitButton > button {
        background: linear-gradient(
            90deg,
            #0878d1,
            #13a5d9
        );
        color: white;
        border: none;
        border-radius: 9px;
        font-weight: 600;
        transition: 0.2s ease;
    }

    .stButton > button:hover,
    .stFormSubmitButton > button:hover {
        background: linear-gradient(
            90deg,
            #0965ad,
            #087fc0
        );
        color: white;
        border: none;
    }

    /* Input fields */
    .stTextInput input,
    .stTextArea textarea {
        background-color: #142a43;
        color: white;
        border: 1px solid #34516f;
        border-radius: 8px;
    }

    /* Dividers */
    hr {
        border-color: #34516f;
    }

    /* Expanders */
    [data-testid="stExpander"] {
        background-color: #10243b;
        border: 1px solid #294663;
        border-radius: 10px;
    }

    /* Metrics */
    [data-testid="stMetric"] {
        background-color: #122a44;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #294663;
    }
    /* Minimal three-dot conversation menu button */
    [class*="st-key-history_menu_icon_wrapper_"] .stButton > button {
        background: transparent !important;
        background-image: none !important;
        color: #d1deef !important;
        border: none !important;
        box-shadow: none !important;
        border-radius: 8px !important;
        min-height: 40px !important;
        height: 40px !important;
        padding: 0 !important;
        font-size: 25px !important;
        font-weight: 700 !important;
        line-height: 1 !important;
    }

    [class*="st-key-history_menu_icon_wrapper_"] .stButton > button:hover {
        background: #203b58 !important;
        color: #19c9f4 !important;
        border: none !important;
        box-shadow: none !important;
    }

    /* Centered delete confirmation dialog */
    [data-testid="stDialog"] {
        background: #10243d;
        border: 1px solid #34516f;
        border-radius: 14px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)
# -----------------------------
# CyberTalk Brand Logo
# -----------------------------


def render_cybertalk_logo():
    """Render a professional CyberTalk shield and wordmark."""

    logo_col, title_col = st.columns(
        [0.7, 7],
        gap="small",
        vertical_alignment="center",
    )

    with logo_col:
        st.components.v1.html(
            """
            <svg width="76" height="84" viewBox="0 0 100 110"
                 xmlns="http://www.w3.org/2000/svg">
                <path d="M50 5 L91 22 L85 67 Q76 91 50 104
                         Q24 91 15 67 L9 22 Z"
                      fill="#102F4B"
                      stroke="#19C9F4"
                      stroke-width="4"/>
                <path d="M50 16 L79 29 L74 65 Q67 83 50 94
                         Q33 83 26 65 L21 29 Z"
                      fill="#0878D1"
                      fill-opacity="0.35"/>
                <path d="M32 42 H68 M32 68 H68"
                      stroke="#16D9F5" stroke-width="2"/>
                <text x="50" y="62" fill="#FFFFFF"
                      font-size="25" font-weight="bold"
                      text-anchor="middle">CT</text>
            </svg>
            """,
            height=120,
            scrolling=False,
        )

    with title_col:
        st.title("CyberTalk", anchor=False)

API_URL = os.getenv(
    "CYBERTALK_API_URL",
    "http://127.0.0.1:8000",
).rstrip("/")


# -----------------------------
# Authentication
# -----------------------------

st.session_state.setdefault("access_token", None)


def get_api_error(response):
    """Extract a readable error message from an API response."""
    try:
        return response.json().get("detail", response.text)
    except (ValueError, AttributeError):
        return response.text


def get_auth_headers():
    """Return the authentication header for the current user."""
    token = st.session_state.get("access_token")
    return {"Authorization": f"Bearer {token}"}


# -----------------------------
# Chat history helper functions
# -----------------------------

def save_chat_history(conversation_type, title, content):
    """Save a conversation for the authenticated user."""

    response = requests.post(
        f"{API_URL}/history",
        headers=get_auth_headers(),
        json={
            "conversation_type": conversation_type,
            "title": title,
            "content": json.dumps(content, ensure_ascii=False),
        },
        timeout=30,
    )

    return response


def fetch_chat_history():
    """Retrieve the authenticated user's conversations."""

    return requests.get(
        f"{API_URL}/history",
        headers=get_auth_headers(),
        timeout=15,
    )


def fetch_single_chat_history(history_id):
    """Retrieve one saved conversation."""

    return requests.get(
        f"{API_URL}/history/{history_id}",
        headers=get_auth_headers(),
        timeout=15,
    )


def delete_chat_history(history_id):
    """Delete one conversation belonging to the current user."""

    return requests.delete(
        f"{API_URL}/history/{history_id}",
        headers=get_auth_headers(),
        timeout=15,
    )

def delete_all_chat_history():
    """Delete all conversations belonging to the current user."""

    return requests.delete(
        f"{API_URL}/history",
        headers=get_auth_headers(),
        timeout=30,
    )


@st.dialog("Delete all conversations?")
def show_delete_all_confirmation():
    """Confirm and delete all conversations for the current user."""

    st.warning(
        "You are about to permanently delete all your saved conversations."
    )

    st.caption(
        "This action cannot be undone. Other users' conversations "
        "will not be affected."
    )

    confirm_col, cancel_col = st.columns(2)

    with confirm_col:
        if st.button(
            "Delete All",
            key="confirm_delete_all_chats",
            type="primary",
            use_container_width=True,
        ):
            try:
                response = delete_all_chat_history()

                if response.ok:
                    result = response.json()
                    deleted_count = result.get("deleted_count", 0)

                    st.session_state["delete_all_success"] = (
                        deleted_count
                    )

                    # Clear any conversation currently displayed.
                    st.session_state.pop("qa_result", None)
                    st.session_state.pop("cybertalk_result", None)

                    # Clear history-related UI state.
                    for key in list(st.session_state.keys()):
                        if (
                            key.startswith("show_history_menu_")
                            or key.startswith("show_history_details_")
                        ):
                            st.session_state.pop(key, None)

                    st.rerun()

                else:
                    st.error(get_api_error(response))

            except requests.exceptions.RequestException:
                st.error("Could not connect to the API. Please try again.")

    with cancel_col:
        if st.button(
            "Cancel",
            key="cancel_delete_all_chats",
            use_container_width=True,
        ):
            st.rerun()

def rename_chat_history(history_id, new_title):
    """Rename one conversation belonging to the current user."""

    return requests.put(
        f"{API_URL}/history/{history_id}",
        headers=get_auth_headers(),
        json={"title": new_title},
        timeout=15,
    )

def create_share_link(history_id, expires_in_days=None):
    """Create a shareable link for an owned conversation."""

    payload = {}

    if expires_in_days is not None:
        payload["expires_in_days"] = expires_in_days

    return requests.post(
        f"{API_URL}/history/{history_id}/share",
        headers=get_auth_headers(),
        json=payload,
        timeout=15,
    )


def revoke_share_link(history_id, share_id):
    """Revoke a shareable link for an owned conversation."""

    return requests.delete(
        f"{API_URL}/history/{history_id}/share/{share_id}",
        headers=get_auth_headers(),
        timeout=15,
    )


# -----------------------------
# Verify current user session
# -----------------------------

current_user = None

if st.session_state.get("access_token"):

    try:
        profile_response = requests.get(
            f"{API_URL}/users/me",
            headers=get_auth_headers(),
            timeout=15,
        )

        if profile_response.status_code == 401:
            st.session_state["access_token"] = None

            st.session_state.pop("qa_result", None)
            st.session_state.pop("cybertalk_result", None)

            st.warning(
                "Your session has expired. Please log in again."
            )

        elif not profile_response.ok:
            st.error(
                "Could not verify your account: "
                f"{get_api_error(profile_response)}"
            )
            st.stop()

        else:
            current_user = profile_response.json()

    except requests.exceptions.RequestException:
        st.error(
            "Could not connect to the CyberTalk API. "
            f"Make sure FastAPI is running at {API_URL}."
        )
        st.stop()


# -----------------------------
# Login and registration
# -----------------------------

if not st.session_state.get("access_token"):

    # -------------------------
    # Password reset confirmation
    # -------------------------

    reset_token = st.query_params.get("token", "")

    if reset_token:

        st.title("Reset Your Password")

        st.write(
            "Enter your new password to regain access to CyberTalk."
        )

        with st.form("password_reset_confirm_form"):

            new_reset_password = st.text_input(
                "New Password",
                type="password",
                max_chars=128,
            )

            confirm_reset_password = st.text_input(
                "Confirm New Password",
                type="password",
                max_chars=128,
            )

            reset_submitted = st.form_submit_button(
                "Reset Password",
                type="primary",
                use_container_width=True,
            )

        if reset_submitted:

            if not new_reset_password or not confirm_reset_password:

                st.error("Please complete both password fields.")

            elif len(new_reset_password) < 8:

                st.error(
                    "Password must contain at least 8 characters."
                )

            elif new_reset_password != confirm_reset_password:

                st.error("Passwords do not match.")

            else:

                try:
                    with st.spinner("Updating your password..."):

                        reset_response = requests.post(
                            f"{API_URL}/password-reset/confirm",
                            json={
                                "token": reset_token,
                                "new_password": new_reset_password,
                            },
                            timeout=30,
                        )

                    if reset_response.ok:

                        st.query_params.clear()

                        st.success(
                            "Password reset successful! "
                            "You can now sign in with your new password."
                        )

                    else:

                        st.error(
                            "Password reset failed: "
                            f"{get_api_error(reset_response)}"
                        )

                except requests.exceptions.RequestException as exc:

                    st.error(
                        f"Could not connect to the API: {exc}"
                    )

        st.stop()

    # -------------------------
    # Authentication tabs
    # -------------------------

    about_tab, login_tab, register_tab, forgot_tab = st.tabs(
        [
            "About CyberTalk",
            "Sign In",
            "Create Account",
            "Forgot Password",
        ]
    )

    # -------------------------
    # About CyberTalk
    # -------------------------

    with about_tab:

        render_cybertalk_logo()

        st.subheader("Two Chatbots, One Agreement")

        st.write(
            "CyberTalk is a Generative AI application that brings "
            "two cybersecurity stakeholders together to discuss "
            "important security topics and reach informed decisions."
        )

        st.divider()

        st.header("🎯 Project Objective")

        st.write(
            "The objective of CyberTalk is to demonstrate how "
            "Generative AI can facilitate structured cybersecurity "
            "discussions between professionals with different "
            "responsibilities and perspectives."
        )

        st.header("🚀 Key Features")

        feature_col1, feature_col2 = st.columns(2)

        with feature_col1:

            st.markdown("#### 💬 Stakeholder Dialogue")

            st.write(
                "Create discussions between any two stakeholders "
                "using custom professional roles."
            )

            st.markdown("#### 🤖 Cybersecurity Q&A")

            st.write(
                "Ask cybersecurity-related questions and receive "
                "AI-generated answers."
            )

            st.markdown("#### 📚 Chat History")

            st.write(
                "Save, revisit, and delete your previous conversations."
            )

        with feature_col2:

            st.markdown("#### ⚖️ Agreement Evaluation")

            st.write(
                "Evaluate whether stakeholders reach an agreement, "
                "partially agree, or disagree."
            )

            st.markdown("#### 🔄 Configurable Discussions")

            st.write(
                "Choose between one and five discussion rounds."
            )

            st.markdown("#### 🔐 User Authentication")

            st.write(
                "Register an account and securely access your "
                "personal CyberTalk workspace."
            )

        st.divider()

        st.header("⚙️ How CyberTalk Works")

        st.markdown(
            """
            1. Enter a cybersecurity discussion topic.
            2. Define two different stakeholder roles.
            3. Select the number of discussion rounds.
            4. Let the AI generate an alternating discussion.
            5. Review closing statements and the final agreement.
            6. Explore shared decisions, disagreements, and next actions.
            """
        )

        st.header("🛠️ Technology Stack")

        st.write(
            "Python · FastAPI · Streamlit · Ollama · "
            "Llama 3.2 · SQLAlchemy · SQLite · Pydantic"
        )

        st.divider()

        st.info(
            "Ready to explore CyberTalk? Select the Sign In tab "
            "to access your workspace or Create Account to register."
        )

        st.caption(
            "CyberTalk — Two Chatbots, One Agreement | "
            "Generative AI Cybersecurity Project"
        )

    # -------------------------
    # Login
    # -------------------------

    with login_tab:

        st.write(
            "Sign in to access your CyberTalk workspace."
        )

        with st.form("login_form"):

            identifier = st.text_input(
                "Username or Email",
                max_chars=255,
            )

            login_password = st.text_input(
                "Password",
                type="password",
            )

            login_submitted = st.form_submit_button(
                "Sign In",
                type="primary",
                use_container_width=True,
            )

        if login_submitted:

            if not identifier.strip() or not login_password:

                st.error(
                    "Please enter your username/email and password."
                )

            else:

                try:
                    with st.spinner("Signing you in..."):

                        login_response = requests.post(
                            f"{API_URL}/login",
                            json={
                                "identifier": identifier.strip(),
                                "password": login_password,
                            },
                            timeout=30,
                        )

                    if login_response.ok:

                        login_data = login_response.json()

                        st.session_state["access_token"] = (
                            login_data["access_token"]
                        )

                        st.success("Login successful!")
                        st.rerun()

                    else:

                        st.error(
                            f"Login failed: "
                            f"{get_api_error(login_response)}"
                        )

                except requests.exceptions.RequestException as exc:

                    st.error(
                        f"Could not connect to the API: {exc}"
                    )

                except (ValueError, KeyError):

                    st.error(
                        "The API returned an invalid login response."
                    )

    # -------------------------
    # Registration
    # -------------------------

    with register_tab:

        st.write("Create a new CyberTalk account.")

        with st.form("registration_form"):

            new_username = st.text_input(
                "Username",
                max_chars=50,
            )

            new_email = st.text_input(
                "Email",
                max_chars=255,
            )

            new_password = st.text_input(
                "Password",
                type="password",
            )

            confirm_password = st.text_input(
                "Confirm Password",
                type="password",
            )

            register_submitted = st.form_submit_button(
                "Create Account",
                use_container_width=True,
            )

        if register_submitted:

            if not all([
                new_username.strip(),
                new_email.strip(),
                new_password,
                confirm_password,
            ]):

                st.error(
                    "Please complete all registration fields."
                )

            elif new_password != confirm_password:

                st.error("Passwords do not match.")

            else:

                try:
                    with st.spinner("Creating your account..."):

                        register_response = requests.post(
                            f"{API_URL}/register",
                            json={
                                "username": new_username.strip(),
                                "email": new_email.strip(),
                                "password": new_password,
                            },
                            timeout=30,
                        )

                    if register_response.status_code == 201:

                        st.success(
                            "Account created successfully! "
                            "Please sign in using the Sign In tab."
                        )

                    else:

                        st.error(
                            "Registration failed: "
                            f"{get_api_error(register_response)}"
                        )

                except requests.exceptions.RequestException as exc:

                    st.error(
                        f"Could not connect to the API: {exc}"
                    )

                except ValueError:

                    st.error(
                        "The API returned an invalid response."
                    )

    # -------------------------
    # Forgot Password
    # -------------------------

    with forgot_tab:

        st.write(
            "Enter your registered email address. "
            "We'll send you a password-reset link."
        )

        with st.form("password_reset_request_form"):

            reset_email = st.text_input(
                "Registered Email",
                max_chars=255,
            )

            request_reset_submitted = st.form_submit_button(
                "Send Reset Link",
                type="primary",
                use_container_width=True,
            )

        if request_reset_submitted:

            if not reset_email.strip():

                st.error(
                    "Please enter your registered email address."
                )

            else:

                try:
                    with st.spinner("Sending password-reset email..."):

                        request_reset_response = requests.post(
                            f"{API_URL}/password-reset/request",
                            json={
                                "email": reset_email.strip()
                            },
                            timeout=30,
                        )

                    if request_reset_response.ok:

                        st.success(
                            request_reset_response.json().get(
                                "message",
                                "If an account exists for that email, "
                                "a password-reset link has been sent."
                            )
                        )

                    else:

                        st.error(
                            "Could not process the request: "
                            f"{get_api_error(request_reset_response)}"
                        )

                except requests.exceptions.RequestException as exc:

                    st.error(
                        f"Could not connect to the API: {exc}"
                    )

    st.stop()



# -----------------------------
# Authenticated user controls
# -----------------------------

st.sidebar.success(
    f"Signed in as {current_user.get('username', 'User')}"
)

st.sidebar.caption(
    f"Role: {current_user.get('role', 'user')}"
)



# -----------------------------
# Top-right Profile Icon
# -----------------------------

st.session_state.setdefault("show_profile", False)

top_spacer, profile_column = st.columns([12, 1])

with profile_column:

    if st.button(
        "👤",
        key="profile_menu_button",
        help="My Profile",
        use_container_width=True,
    ):

        st.session_state["show_profile"] = (
            not st.session_state["show_profile"]
        )

        st.rerun()


# -----------------------------
# My Profile Page
# -----------------------------

if st.session_state["show_profile"]:
    if st.button(
        "← Back to Chat",
        key="back_to_chat",
    ):
        st.session_state["show_profile"] = False
        st.rerun()

    st.title("My Profile")

    st.write(
        "View your CyberTalk account information."
    )

    st.divider()
    st.subheader("Edit Profile")

    with st.form("update_profile_form"):

        updated_username = st.text_input(
            "Username",
            value=current_user.get("username", ""),
            max_chars=50,
        )

        updated_email = st.text_input(
            "Email Address",
            value=current_user.get("email", ""),
            max_chars=255,
        )

        save_profile = st.form_submit_button(
            "Save Changes",
            use_container_width=True,
        )

        if save_profile:
            username = updated_username.strip()
            email = updated_email.strip().lower()

            if len(username) < 3:
                st.error("Username must contain at least 3 characters.")

            elif (
                "@" not in email
                or "." not in email.split("@")[-1]
            ):
                st.error("Please provide a valid email address.")

            elif (
                username == current_user.get("username")
                and email == current_user.get("email", "").lower()
            ):
                st.info("No profile changes were made.")

            else:
                try:
                    update_response = requests.put(
                        f"{API_URL}/users/me",
                        headers=get_auth_headers(),
                        json={
                            "username": username,
                            "email": email,
                        },
                        timeout=15,
                    )

                    if update_response.status_code == 200:
                        st.success(
                            "Your profile was updated successfully."
                        )
                        st.rerun()

                    elif update_response.status_code == 401:
                        st.error(
                            "Your session has expired. Please log in again."
                        )
                        st.session_state["access_token"] = None
                        st.rerun()

                    else:
                        st.error(get_api_error(update_response))

                except requests.RequestException:
                    st.error(
                        "Unable to update your profile. "
                        "Please check your connection and try again."
                    )

    st.divider()
    st.subheader("Change Password")
    st.caption("Update your account password securely.")

    with st.form("change_password_form"):
        current_password = st.text_input(
            "Current Password",
            type="password",
        )

        new_password = st.text_input(
            "New Password",
            type="password",
            help="Must contain at least 8 characters.",
        )

        confirm_new_password = st.text_input(
            "Confirm New Password",
            type="password",
        )

        change_password_submitted = st.form_submit_button(
            "Change Password",
            use_container_width=True,
        )

    if change_password_submitted:
        if not current_password or not new_password or not confirm_new_password:
            st.error("Please fill in all password fields.")

        elif len(new_password) < 8:
            st.error("New password must contain at least 8 characters.")

        elif new_password != confirm_new_password:
            st.error("New passwords do not match.")

        elif new_password == current_password:
            st.error("New password must be different from the current password.")

        else:
            try:
                response = requests.post(
                    f"{API_URL}/change-password",
                    headers=get_auth_headers(),
                    json={
                        "current_password": current_password,
                        "new_password": new_password,
                        "confirm_new_password": confirm_new_password,
                    },
                    timeout=15,
                )

                if response.status_code == 200:
                    st.success("Password changed successfully!")

                elif response.status_code == 401:
                    st.session_state["access_token"] = None
                    st.error(
                        "Your session has expired. Please log in again."
                    )
                    st.rerun()

                else:
                    st.error(get_api_error(response))

            except requests.RequestException:
                st.error(
                    "Unable to connect to the CyberTalk server. "
                    "Please try again."
                )

    st.divider()
    st.subheader("Account Information")

    profile_col1, profile_col2 = st.columns(2)

    with profile_col1:
        st.metric(
            "User ID",
            current_user.get("id", "N/A"),
        )

        st.metric(
            "Username",
            current_user.get("username", "N/A"),
        )

    with profile_col2:
        st.metric(
            "Account Role",
            current_user.get("role", "user").title(),
        )

        st.metric(
            "Email Address",
            current_user.get("email", "N/A"),
        )

    st.divider()
    st.subheader("Account Details")

    created_at = current_user.get(
        "created_at",
        "Not available",
    )

    st.write(f"**Registration Date:** {created_at}")

    st.caption(
        "Your profile information is retrieved securely "
        "from your authenticated CyberTalk account."
    )

    st.divider()

    if st.button(
        "Log Out",
        use_container_width=True,
        key="profile_logout",
    ):
        st.session_state["access_token"] = None
        st.session_state["show_profile"] = False

        st.session_state.pop("qa_result", None)
        st.session_state.pop("cybertalk_result", None)

        st.rerun()

    st.stop()
@st.dialog("Delete conversation?")
def confirm_delete_conversation(history_id):
    """Delete a conversation after explicit user confirmation."""

    try:
        response = delete_chat_history(history_id)

        if response.ok:
            st.session_state[f"delete_success_{history_id}"] = True
        else:
            st.session_state[f"delete_error_{history_id}"] = (
                get_api_error(response)
            )

    except requests.exceptions.RequestException:
        st.session_state[f"delete_error_{history_id}"] = (
            "Could not connect to the API."
        )


@st.dialog("Delete conversation?")
def show_delete_confirmation(history_id, title):
    st.write(
        f'Are you sure you want to permanently delete "{title}"?'
    )
    st.caption("This action cannot be undone.")

    success_key = f"delete_success_{history_id}"
    error_key = f"delete_error_{history_id}"

    if st.session_state.get(success_key):
        st.session_state.pop(success_key, None)
        st.rerun()

    if st.session_state.get(error_key):
        st.error(st.session_state.pop(error_key))

    confirm_col, cancel_col = st.columns(2)

    with confirm_col:
        if st.button(
            "Delete",
            key=f"confirm_delete_{history_id}",
            type="primary",
            use_container_width=True,
            on_click=confirm_delete_conversation,
            args=(history_id,),
        ):
            if st.session_state.get(success_key):
                st.session_state.pop(success_key, None)
                st.rerun()

    with cancel_col:
        if st.button(
            "Cancel",
            key=f"cancel_delete_{history_id}",
            use_container_width=True,
        ):
            st.rerun()

# -----------------------------
# Chat History Sidebar
# -----------------------------

st.sidebar.divider()
st.sidebar.subheader("📚 My Chat History")
if "delete_all_success" in st.session_state:
    deleted_count = st.session_state.pop("delete_all_success")

    st.sidebar.success(
        f"Successfully deleted {deleted_count} conversation(s)."
    )
try:
    history_response = fetch_chat_history()

    if history_response.status_code == 401:
        st.sidebar.warning(
            "Your session has expired. Please log in again."
        )

    elif history_response.ok:
        history_records = history_response.json()

        if not isinstance(history_records, list):
            st.sidebar.warning(
                "The API returned an invalid history response."
            )

        elif not history_records:
            st.sidebar.caption(
                "No saved conversations yet."
            )

        else:
            st.sidebar.caption(
            f"{len(history_records)} saved conversation(s)"
            )

            if st.sidebar.button(
                "🗑️ Delete All Chats",
                key="delete_all_chats_button",
                use_container_width=True,
            ):
                show_delete_all_confirmation()

            for record in history_records:
                history_id = record["id"]
                conversation_type = record["conversation_type"]
                title = record["title"]

                menu_key = f"show_history_menu_{history_id}"
                details_key = f"show_history_details_{history_id}"
                confirm_delete_key = (
                    f"confirm_delete_history_{history_id}"
                )

                # Conversation title and three-dot menu.
                title_col, menu_col = st.sidebar.columns(
                    [0.88, 0.12]
                )

                with title_col:
                    if st.button(
                        title,
                        key=f"history_title_{history_id}",
                        use_container_width=True,
                    ):
                        st.session_state[details_key] = not (
                            st.session_state.get(details_key, False)
                        )
                        st.rerun()

                with menu_col:
                    with st.container(
                        key=f"history_menu_icon_wrapper_{history_id}"
                    ):
                        if st.button(
                            "⋮",
                            key=f"history_menu_button_{history_id}",
                            help="Conversation actions",
                            use_container_width=True,
                        ):
                            st.session_state[menu_key] = not (
                                st.session_state.get(menu_key, False)
                            )
                            st.rerun()
                # Expanded conversation details.
                if st.session_state.get(details_key, False):
                    with st.sidebar.container():
                        st.caption(
                            f"Type: {conversation_type.upper()}"
                        )
                        st.caption(
                            f"Saved: {record['created_at']}"
                        )

                        if st.button(
                            "Open Conversation",
                            key=f"open_history_{history_id}",
                            use_container_width=True,
                        ):
                            try:
                                detail_response = (
                                    fetch_single_chat_history(history_id)
                                )

                                if detail_response.ok:
                                    saved_record = detail_response.json()
                                    saved_content = json.loads(
                                        saved_record["content"]
                                    )

                                    if (
                                        saved_record["conversation_type"]
                                        == "qa"
                                    ):
                                        if not isinstance(
                                            saved_content, dict
                                        ):
                                            raise ValueError(
                                                "Invalid saved Q&A data."
                                            )

                                        st.session_state["qa_result"] = (
                                            saved_content
                                        )
                                        st.session_state.pop(
                                            "cybertalk_result",
                                            None,
                                        )

                                    elif (
                                        saved_record["conversation_type"]
                                        == "dialogue"
                                    ):
                                        if not isinstance(
                                            saved_content, dict
                                        ):
                                            raise ValueError(
                                                "Invalid saved dialogue data."
                                            )

                                        st.session_state[
                                            "cybertalk_result"
                                        ] = saved_content
                                        st.session_state.pop(
                                            "qa_result",
                                            None,
                                        )

                                    st.rerun()

                                else:
                                    st.sidebar.error(
                                        "Could not open this conversation: "
                                        f"{get_api_error(detail_response)}"
                                    )

                            except (
                                requests.exceptions.RequestException,
                                ValueError,
                                KeyError,
                            ):
                                st.sidebar.error(
                                    "Could not load the saved conversation."
                                )

                # Three-dot menu actions.
                if st.session_state.get(menu_key, False):
                    with st.sidebar.container(border=True):
                        st.caption("Conversation actions")

                        with st.form(
                            key=f"rename_history_form_{history_id}"
                        ):
                            new_title = st.text_input(
                                "Conversation title",
                                value=title,
                                max_chars=500,
                                key=f"rename_title_{history_id}",
                            )

                            rename_submitted = st.form_submit_button(
                                "Rename",
                                use_container_width=True,
                            )

                            if rename_submitted:
                                if not new_title.strip():
                                    st.sidebar.warning(
                                        "Conversation title cannot be empty."
                                    )

                                elif new_title.strip() == title:
                                    st.sidebar.info(
                                        "The conversation title has not changed."
                                    )

                                else:
                                    try:
                                        rename_response = rename_chat_history(
                                            history_id,
                                            new_title.strip(),
                                        )

                                        if rename_response.ok:
                                            st.session_state[menu_key] = False
                                            st.rerun()

                                        else:
                                            st.sidebar.error(
                                                "Could not rename conversation: "
                                                f"{get_api_error(rename_response)}"
                                            )

                                    except requests.exceptions.RequestException:
                                        st.sidebar.error(
                                            "Could not connect to the API."
                                        )

                        st.divider()

                        st.caption("Share or export conversation")

                        share_state_key = f"share_link_data_{history_id}"
                        revoked_state_key = f"share_revoked_{history_id}"

                        if st.session_state.pop(revoked_state_key, False):
                            st.sidebar.success("Share link revoked successfully.")

                        with st.form(key=f"share_form_{history_id}"):
                            expiry_label = st.selectbox(
                                "Link expiration",
                                options=[
                                    "Never",
                                    "1 day",
                                    "7 days",
                                    "30 days",
                                    "90 days",
                                    "365 days",
                                ],
                                key=f"share_expiry_{history_id}",
                            )

                            generate_share = st.form_submit_button(
                                "Generate Shareable Link",
                                use_container_width=True,
                                disabled=bool(st.session_state.get(share_state_key)),
                            )

                        if generate_share:
                            expiry_days = {
                                "Never": None,
                                "1 day": 1,
                                "7 days": 7,
                                "30 days": 30,
                                "90 days": 90,
                                "365 days": 365,
                            }

                            try:
                                share_response = create_share_link(
                                    history_id,
                                    expiry_days[expiry_label],
                                )

                                if share_response.ok:
                                    st.session_state[share_state_key] = (
                                        share_response.json()
                                    )
                                    st.rerun()

                                else:
                                    st.sidebar.error(
                                        "Could not create share link: "
                                        f"{get_api_error(share_response)}"
                                    )

                            except requests.exceptions.RequestException:
                                st.sidebar.error(
                                    "Could not connect to the API."
                                )

                        share_data = st.session_state.get(share_state_key)

                        if share_data:
                            st.caption("Your read-only sharing link")

                            # Streamlit code blocks provide a copy-to-clipboard control.
                            st.code(share_data["share_url"])

                            if share_data.get("expires_at"):
                                st.caption(
                                    f"Expires: {share_data['expires_at']}"
                                )
                            else:
                                st.caption("This link does not expire.")

                            if st.button(
                                "Revoke Share Link",
                                key=f"revoke_share_{history_id}",
                                use_container_width=True,
                                type="secondary",
                            ):
                                try:
                                    revoke_response = revoke_share_link(
                                        history_id,
                                        share_data["share_id"],
                                    )

                                    if revoke_response.ok:
                                        st.session_state.pop(share_state_key, None)
                                        st.session_state[revoked_state_key] = True
                                        st.rerun()

                                    else:
                                        st.sidebar.error(
                                            "Could not revoke share link: "
                                            f"{get_api_error(revoke_response)}"
                                        )

                                except requests.exceptions.RequestException:
                                    st.sidebar.error(
                                        "Could not connect to the API."
                                    )

                        st.button(
                            "📥 Download Conversation",
                            key=f"download_history_{history_id}",
                            disabled=True,
                            use_container_width=True,
                            help="Conversation downloads will be available soon.",
                        )
                        if st.button(
                            "Delete",
                            key=f"delete_history_{history_id}",
                            use_container_width=True,
                            type="secondary",
                        ):
                            show_delete_confirmation(
                                history_id,
                                title,
                            )

    else:
        st.sidebar.warning(
            "Could not load your chat history."
        )

except requests.exceptions.RequestException:
    st.sidebar.warning(
        "Chat history is currently unavailable."
    )


# -----------------------------
# Main page heading
# -----------------------------

render_cybertalk_logo()
st.subheader("Two Chatbots, One Agreement")

st.write(
    "Bring two cybersecurity stakeholders together to discuss a topic, "
    "explore different perspectives, and identify a shared decision."
)

st.info(
    "Enter your own stakeholder roles. CyberTalk does not restrict "
    "you to predefined personas."
)


# -----------------------------
# Cybersecurity Q&A
# -----------------------------

st.divider()

st.header("💬 Ask a Cybersecurity Question")

st.write(
    "Ask a cybersecurity-related question and get a direct answer "
    "from the AI assistant. This mode does not generate a stakeholder "
    "dialogue."
)

with st.form("qa_form"):

    question = st.text_input(
        "Your question",
        placeholder=(
            "Example: How can I protect my organization from phishing?"
        ),
        max_chars=2000,
    )

    qa_submitted = st.form_submit_button(
        "Ask CyberTalk",
        use_container_width=True,
    )


if qa_submitted:

    if not question.strip():

        st.error("Please enter a question.")

    else:

        try:

            with st.spinner(
                "Checking your question and generating an answer..."
            ):

                qa_response = requests.post(
                    f"{API_URL}/ask",
                    json={
                        "question": question.strip()
                    },
                    timeout=360,
                )

            if not qa_response.ok:

                st.error(
                    f"The CyberTalk API returned "
                    f"HTTP {qa_response.status_code}: "
                    f"{get_api_error(qa_response)}"
                )

            else:

                qa_result = qa_response.json()

                st.session_state["qa_result"] = qa_result

                # Automatically save Q&A history.
                try:

                    history_response = save_chat_history(
                        conversation_type="qa",
                        title=question.strip()[:500],
                        content={
                            "question": question.strip(),
                            "answer": qa_result.get("answer", ""),
                        },
                    )

                    if history_response.status_code == 201:

                        st.success(
                            "Your conversation was saved to chat history."
                        )

                    else:

                        st.warning(
                            "Your answer was generated, but could not "
                            "be saved to chat history."
                        )

                except requests.exceptions.RequestException:

                    st.warning(
                        "Your answer was generated, but chat history "
                        "could not be reached."
                    )

        except requests.exceptions.Timeout:

            st.error(
                "The request timed out. Please try again."
            )

        except requests.exceptions.ConnectionError:

            st.error(
                "Could not connect to the CyberTalk API. "
                f"Make sure FastAPI is running at {API_URL}."
            )

        except requests.exceptions.RequestException as exc:

            st.error(f"Request failed: {exc}")

        except ValueError:

            st.error(
                "The API returned an invalid JSON response."
            )


# -----------------------------
# Display Q&A result
# -----------------------------

qa_result = st.session_state.get("qa_result")

if qa_result:

    st.subheader("Answer")

    st.write(
        qa_result.get(
            "answer",
            "No answer was returned.",
        )
    )


# -----------------------------
# Stakeholder dialogue input
# -----------------------------

with st.form("dialogue_form"):

    topic = st.text_area(
        "Cybersecurity topic",
        placeholder=(
            "Example: Should our organization require "
            "multi-factor authentication for all employees?"
        ),
        max_chars=500,
        help="Enter a topic containing at least 3 characters.",
    )

    col1, col2 = st.columns(2)

    with col1:

        stakeholder_1 = st.text_input(
            "Stakeholder 1",
            placeholder="Example: Chief Information Security Officer",
            max_chars=100,
        )

    with col2:

        stakeholder_2 = st.text_input(
            "Stakeholder 2",
            placeholder="Example: IT Operations Manager",
            max_chars=100,
        )

    rounds = st.number_input(
        "Number of discussion rounds",
        min_value=1,
        max_value=5,
        value=2,
        step=1,
        help=(
            "Each round includes one response from each stakeholder. "
            "Two additional closing statements are generated afterward."
        ),
    )

    submitted = st.form_submit_button(
        "Generate CyberTalk Dialogue",
        type="primary",
        use_container_width=True,
    )


# -----------------------------
# Validate and call dialogue API
# -----------------------------

if submitted:

    errors = []

    if len(topic.strip()) < 3:

        errors.append(
            "Enter a topic containing at least 3 characters."
        )

    if len(stakeholder_1.strip()) < 2:

        errors.append(
            "Stakeholder 1 must contain at least 2 characters."
        )

    if len(stakeholder_2.strip()) < 2:

        errors.append(
            "Stakeholder 2 must contain at least 2 characters."
        )

    if (
        stakeholder_1.strip().casefold()
        == stakeholder_2.strip().casefold()
    ):

        errors.append(
            "Please provide two different stakeholders."
        )

    if errors:

        for error in errors:
            st.error(error)

    else:

        payload = {
            "topic": topic.strip(),
            "stakeholder_1": stakeholder_1.strip(),
            "stakeholder_2": stakeholder_2.strip(),
            "rounds": int(rounds),
        }

        try:

            with st.spinner(
                "Generating the discussion and evaluating agreement. "
                "This may take several minutes..."
            ):

                response = requests.post(
                    f"{API_URL}/dialogue",
                    json=payload,
                    timeout=900,
                )

            if not response.ok:

                st.error(
                    f"The CyberTalk API returned "
                    f"HTTP {response.status_code}: "
                    f"{get_api_error(response)}"
                )

            else:

                result = response.json()

                # Keep the complete result available during reruns.
                st.session_state["cybertalk_result"] = result

                # Automatically save dialogue history.
                try:

                    history_response = save_chat_history(
                        conversation_type="dialogue",
                        title=result.get(
                            "topic",
                            "CyberTalk Discussion",
                        )[:500],
                        content=result,
                    )

                    if history_response.status_code == 201:

                        st.success(
                            "Your dialogue was saved to chat history."
                        )

                    else:

                        st.warning(
                            "The dialogue was generated, but could not "
                            "be saved to chat history."
                        )

                except requests.exceptions.RequestException:

                    st.warning(
                        "The dialogue was generated, but chat history "
                        "could not be reached."
                    )

        except requests.exceptions.Timeout:

            st.error(
                "The request timed out. The local AI model may need "
                "more time. Please try again."
            )

        except requests.exceptions.ConnectionError:

            st.error(
                "Could not connect to the CyberTalk API. Make sure "
                "FastAPI is running at "
                f"{API_URL}."
            )

        except requests.exceptions.RequestException as exc:

            st.error(f"Request failed: {exc}")

        except ValueError:

            st.error(
                "The API returned an invalid JSON response."
            )


# -----------------------------
# Display stakeholder dialogue
# -----------------------------

result = st.session_state.get("cybertalk_result")

if result:

    st.divider()

    st.header("Discussion Results")

    st.markdown(
        f"**Topic:** {result.get('topic', 'Not provided')}"
    )

    stakeholders = result.get("stakeholders", [])

    if stakeholders:

        names = [
            item.get("name", "Unknown stakeholder")
            for item in stakeholders
        ]

        st.markdown(
            "**Stakeholders:** " + " and ".join(names)
        )

    st.markdown(
        f"**Discussion rounds:** "
        f"{result.get('rounds', 'Unknown')}"
    )
    # Display AI performance metrics.
    performance = result.get("performance", {})

    if isinstance(performance, dict) and performance:

        st.divider()
        st.subheader("⏱️ AI Performance")

        perf_col1, perf_col2, perf_col3 = st.columns(3)

        perf_col1.metric(
            "Dialogue generation",
            f"{performance.get('generation_seconds', 0):.2f} s",
        )

        perf_col2.metric(
            "Agreement evaluation",
            f"{performance.get('evaluation_seconds', 0):.2f} s",
        )

        perf_col3.metric(
            "Total processing time",
            f"{performance.get('total_seconds', 0):.2f} s",
        )

        st.caption(
            "Dialogue entries generated: "
            f"{performance.get('dialogue_entries', 0)}"
        )
    st.caption(
        "The final two statements are closing statements, "
        "in addition to the requested discussion rounds."
    )

    # Display alternating discussion.
    st.subheader("Stakeholder Dialogue")

    dialogue = result.get("dialogue", [])

    if not dialogue:

        st.warning(
            "The API returned no dialogue entries."
        )

    for entry in dialogue:

        turn_number = entry.get("turn", "?")
        speaker = entry.get("speaker", "Unknown stakeholder")
        message = entry.get("message", "")

        with st.chat_message("assistant"):

            st.markdown(
                f"**Turn {turn_number} — {speaker}**"
            )

            st.write(message)

    # Display agreement evaluation.
    st.divider()

    st.subheader("Final Agreement Evaluation")

    agreement = result.get("agreement", {})

    status = agreement.get("status", "unknown")

    explanation = agreement.get(
        "explanation",
        "No explanation was provided.",
    )

    status_labels = {
        "agreement_reached": "Agreement reached",
        "partial_agreement": "Partial agreement",
        "no_agreement": "No agreement",
    }

    st.markdown(
        f"**Status:** {status_labels.get(status, status)}"
    )

    st.write(explanation)

    shared_decision = agreement.get("shared_decision")

    st.markdown("**Shared decision**")

    if shared_decision:

        st.success(shared_decision)

    else:

        st.warning(
            "The evaluator did not identify a confirmed shared decision."
        )

    unresolved = agreement.get(
        "unresolved_disagreements",
        [],
    )

    st.markdown("**Unresolved disagreements**")

    if unresolved:

        for disagreement in unresolved:
            st.write(f"- {disagreement}")

    else:

        st.write(
            "No unresolved disagreements were reported."
        )

    next_actions = agreement.get("next_actions", [])

    st.markdown("**Next actions**")

    if next_actions:

        for action in next_actions:
            st.write(f"- {action}")

    else:

        st.write(
            "No next actions were reported."
        )
