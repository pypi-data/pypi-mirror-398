# Language file for user-facing strings

LANGUAGES = {
    "en": {
        "sleep_message": "Sleep is important.",
        "future_thanks": "Tomorrow you will be glad.",
        "go_to_sleep": "Go to sleep, your future self will thank you.",
        "window_title": "Time to Sleep!",
        "shutdown_now": "Shutdown now",
        "later": "Later",
        "shutdown_failed": "Shutdown failed:",
    },
    "de": {
        "sleep_message": "Schlaf ist wichtig.",
        "future_thanks": "Morgen wirst du froh sein.",
        "go_to_sleep": "Geh schlafen, Zukunftsdu dankt dir.",
        "window_title": "Zeit zum Schlafen!",
        "shutdown_now": "Jetzt herunterfahren",
        "later": "Später",
        "shutdown_failed": "Shutdown fehlgeschlagen:",
    }
}

# Default language
CURRENT_LANGUAGE = "de"

def get_string(key):
    return LANGUAGES[CURRENT_LANGUAGE].get(key, key)


def set_language(lang_code):
    global CURRENT_LANGUAGE
    if lang_code in LANGUAGES:
        CURRENT_LANGUAGE = lang_code
    else:
        raise ValueError(f"Language '{lang_code}' not supported. Only {list(LANGUAGES.keys())} are available.")
