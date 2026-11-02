import os
import smtplib
import ssl
from email.message import EmailMessage
from urllib.parse import urlencode, urlsplit, urlunsplit, parse_qsl


def send_password_reset_email(
    recipient_email: str,
    reset_token: str,
) -> None:
    """Send a password-reset link using the configured SMTP server."""

    smtp_host = os.getenv("CYBERTALK_SMTP_HOST")
    smtp_port = int(os.getenv("CYBERTALK_SMTP_PORT", "587"))
    smtp_username = os.getenv("CYBERTALK_SMTP_USERNAME")
    smtp_password = os.getenv("CYBERTALK_SMTP_PASSWORD")
    sender_email = os.getenv("CYBERTALK_SMTP_FROM_EMAIL")
    reset_url = os.getenv(
        "CYBERTALK_PASSWORD_RESET_URL",
        "http://localhost:8501/",
    )

    required_settings = {
        "CYBERTALK_SMTP_HOST": smtp_host,
        "CYBERTALK_SMTP_USERNAME": smtp_username,
        "CYBERTALK_SMTP_PASSWORD": smtp_password,
        "CYBERTALK_SMTP_FROM_EMAIL": sender_email,
    }

    missing_settings = [
        name for name, value in required_settings.items() if not value
    ]

    if missing_settings:
        raise RuntimeError(
            "Password-reset email settings are incomplete."
        )

    if not 1 <= smtp_port <= 65535:
        raise RuntimeError("Invalid SMTP port configuration.")

    # Add the token and recipient to the configured reset page URL.
    parsed_url = urlsplit(reset_url)
    query_parameters = dict(parse_qsl(parsed_url.query))
    query_parameters.update({
        "token": reset_token,
        "email": recipient_email,
    })

    password_reset_link = urlunsplit((
        parsed_url.scheme,
        parsed_url.netloc,
        parsed_url.path,
        urlencode(query_parameters),
        parsed_url.fragment,
    ))

    message = EmailMessage()
    message["Subject"] = "CyberTalk password reset"
    message["From"] = sender_email
    message["To"] = recipient_email
    message.set_content(
        "We received a request to reset your CyberTalk password.\n\n"
        f"Use this link to continue:\n{password_reset_link}\n\n"
        "This link expires in 30 minutes. If you did not request "
        "a password reset, you can ignore this email."
    )

    tls_context = ssl.create_default_context()

    if smtp_port == 465:
        with smtplib.SMTP_SSL(
            smtp_host,
            smtp_port,
            context=tls_context,
            timeout=20,
        ) as server:
            server.login(smtp_username, smtp_password)
            server.send_message(message)
    else:
        with smtplib.SMTP(
            smtp_host,
            smtp_port,
            timeout=20,
        ) as server:
            server.ehlo()
            server.starttls(context=tls_context)
            server.ehlo()
            server.login(smtp_username, smtp_password)
            server.send_message(message)