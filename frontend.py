
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
    except ValueError:
        return response.text


def get_auth_headers():
    """Return the authentication header for the current user."""
    token = st.session_state.get("access_token")
    return {"Authorization": f"Bearer {token}"}


# Verify the current session.
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
            st.warning("Your session has expired. Please log in again.")

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


# Show login and registration when the user is not authenticated.
if not st.session_state.get("access_token"):

    st.title("🛡️ CyberTalk")
    st.subheader("Welcome to CyberTalk")

    login_tab, register_tab = st.tabs(
        ["Sign In", "Create Account"]
    )

    with login_tab:
        st.write("Sign in to access your CyberTalk workspace.")

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
                st.error("Please enter your username/email and password.")

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
                            f"Login failed: {get_api_error(login_response)}"
                        )

                except requests.exceptions.RequestException as exc:
                    st.error(f"Could not connect to the API: {exc}")

                except (ValueError, KeyError):
                    st.error("The API returned an invalid login response.")

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
                st.error("Please complete all registration fields.")

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
                    st.error(f"Could not connect to the API: {exc}")

                except ValueError:
                    st.error("The API returned an invalid response.")

    # Do not display the application until login succeeds.
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

if st.sidebar.button("Log Out", use_container_width=True):
    st.session_state["access_token"] = None
    st.session_state.pop("qa_result", None)
    st.session_state.pop("cybertalk_result", None)
    st.rerun()

# -----------------------------
# Page heading
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
            with st.spinner("Checking your question and generating an answer..."):
                qa_response = requests.post(
                    f"{API_URL}/ask",
                    json={"question": question.strip()},
                    timeout=360,
                )

                if not qa_response.ok:
                    try:
                        detail = qa_response.json().get(
                            "detail",
                            qa_response.text,
                        )
                    except ValueError:
                        detail = qa_response.text

                    st.error(
                        f"The CyberTalk API returned "
                        f"HTTP {qa_response.status_code}: {detail}"
                    )
                else:
                    qa_result = qa_response.json()
                    st.session_state["qa_result"] = qa_result

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
            st.error("The API returned an invalid JSON response.")

qa_result = st.session_state.get("qa_result")

if qa_result:
    st.subheader("Answer")
    st.write(qa_result.get("answer", "No answer was returned."))

# -----------------------------
# User input
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
# Validate and call the API
# -----------------------------

if submitted:
    errors = []

    if len(topic.strip()) < 3:
        errors.append("Enter a topic containing at least 3 characters.")

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
        errors.append("Please provide two different stakeholders.")

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
                    try:
                        detail = response.json().get(
                            "detail",
                            response.text,
                        )
                    except ValueError:
                        detail = response.text

                    st.error(
                        f"The CyberTalk API returned "
                        f"HTTP {response.status_code}: {detail}"
                    )
                    st.stop()

                result = response.json()

            # Keep the complete result available during reruns.
            st.session_state["cybertalk_result"] = result

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
            st.error("The API returned an invalid JSON response.")


# -----------------------------
# Display the generated result
# -----------------------------

result = st.session_state.get("cybertalk_result")

if result:
    st.divider()

    st.header("Discussion Results")

    st.markdown(f"**Topic:** {result.get('topic', 'Not provided')}")

    stakeholders = result.get("stakeholders", [])
    if stakeholders:
        names = [
            item.get("name", "Unknown stakeholder")
            for item in stakeholders
        ]
        st.markdown("**Stakeholders:** " + " and ".join(names))

    st.markdown(
        f"**Discussion rounds:** {result.get('rounds', 'Unknown')}"
    )

    st.caption(
        "The final two statements are closing statements, "
        "in addition to the requested discussion rounds."
    )

    # Display the alternating discussion.
    st.subheader("Stakeholder Dialogue")

    dialogue = result.get("dialogue", [])

    if not dialogue:
        st.warning("The API returned no dialogue entries.")

    for entry in dialogue:
        turn_number = entry.get("turn", "?")
        speaker = entry.get("speaker", "Unknown stakeholder")
        message = entry.get("message", "")

        with st.chat_message("assistant"):
            st.markdown(
                f"**Turn {turn_number} — {speaker}**"
            )
            st.write(message)

    # Display the agreement evaluation.
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

    unresolved = agreement.get("unresolved_disagreements", [])

    st.markdown("**Unresolved disagreements**")
    if unresolved:
        for disagreement in unresolved:
            st.write(f"- {disagreement}")
    else:
        st.write("No unresolved disagreements were reported.")

    next_actions = agreement.get("next_actions", [])

    st.markdown("**Next actions**")
    if next_actions:
        for action in next_actions:
            st.write(f"- {action}")
    else:
        st.write("No next actions were reported.")
