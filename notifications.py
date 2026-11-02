import logging
import os
import time
from dotenv import load_dotenv
load_dotenv()

log = logging.getLogger("notifications")

MAX_ATTEMPTS = int(os.getenv("EMAIL_MAX_ATTEMPTS", "3"))
BACKOFF = float(os.getenv("EMAIL_BACKOFF_SECONDS", "1"))

def send_email(to: str, subject: str, body: str) -> None:
    if os.getenv("EMAIL_FORCE_FAIL", "false").lower() == "true":
        raise RuntimeError("forced email failure")
    log.info("EMAIL to=%s subject=%s", to, subject)

def send_confirmation(submission_id: int, to:str, widget_title: str)-> None:
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            send_email(
                to=to,
                subject=f"Thanks for contacting {widget_title}",
                body="We received your submission.",
            )

            return
        except Exception as e:
            log.warning("Email attempt %d/%d for submission %s failed: %s", attempt, MAX_ATTEMPTS, submission_id, str(e))
            if attempt < MAX_ATTEMPTS:
                time.sleep(BACKOFF * (2 ** (attempt - 1)))
    log.error("ALERT: confirmation email for submission %s failed after %d attempts", submission_id, MAX_ATTEMPTS)