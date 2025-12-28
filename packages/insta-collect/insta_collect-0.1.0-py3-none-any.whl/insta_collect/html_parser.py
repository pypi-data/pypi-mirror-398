from bs4 import BeautifulSoup
import os
import re

def parse_instagram_html(file_path, min_len=10):
    with open(file_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    results = []
    current_user = None
    caption_done = False

    UI_TEXTS = {
    "Instagram Lite",
    "Log in",
    "Sign up",
    "Open in app",
    "Reply",
    "Like",
    "See translation",
    "View all replies",
    "View replies",
    "More",
    "Follow",
    "Suggested for you"
              }


    def is_username(text):
        return (
            text.islower()
            and " " not in text
            and 3 <= len(text) <= 30
        )

    def is_timestamp(text):
        return re.match(r"^\d+[smhdw]$", text) is not None

    for span in soup.find_all("span"):
        text = span.get_text(strip=True)

        if not text or text in UI_TEXTS:
            continue

        if is_username(text) and not is_timestamp(text):
            current_user = text
            continue

        if current_user and len(text) >= min_len:
            entry_type = "caption" if not caption_done else "comment"
            caption_done = True

            text = re.sub(r"Verified\d+[smhdw]", "", text)

            results.append({
                "username": current_user,
                "text": text,
                "type": entry_type,
                "char_len": len(text)
            })

            current_user = None

    return results
