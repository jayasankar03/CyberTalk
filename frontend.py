
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

    about_tab, login_tab, register_tab = st.tabs(
        ["About CyberTalk", "Sign In", "Create Account"]
    )

    # -------------------------
    # About CyberTalk
    # -------------------------

    with about_tab:

        st.title("🛡️ CyberTalk")

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
# Logout
# -----------------------------

if st.sidebar.button(
    "Log Out",
    use_container_width=True,
):

    st.session_state["access_token"] = None

    st.session_state.pop("qa_result", None)
    st.session_state.pop("cybertalk_result", None)

    st.rerun()


# -----------------------------
# Chat History Sidebar
# -----------------------------

st.sidebar.divider()
st.sidebar.subheader("📚 My Chat History")

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

            for record in history_records:

                history_id = record["id"]
                conversation_type = record["conversation_type"]
                title = record["title"]

                with st.sidebar.expander(
                    title,
                    expanded=False,
                ):

                    st.caption(
                        f"Type: {conversation_type.upper()}"
                    )

                    st.caption(
                        f"Saved: {record['created_at']}"
                    )

                    # Open saved conversation.
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

                    # Delete saved conversation.
                    if st.button(
                        "Delete Conversation",
                        key=f"delete_history_{history_id}",
                        use_container_width=True,
                    ):

                        try:

                            delete_response = delete_chat_history(
                                history_id
                            )

                            if delete_response.ok:

                                st.sidebar.success(
                                    "Conversation deleted successfully."
                                )

                                st.rerun()

                            else:

                                st.sidebar.error(
                                    "Could not delete conversation: "
                                    f"{get_api_error(delete_response)}"
                                )

                        except requests.exceptions.RequestException:

                            st.sidebar.error(
                                "Could not connect to the API."
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

st.title("🛡️ CyberTalk")
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
