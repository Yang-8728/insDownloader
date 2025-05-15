import glob
import platform
import sqlite3
import os
from os.path import expanduser
from instaloader import Instaloader, ConnectionException
from dotenv import set_key

def get_cookiefile():
    default_cookiefile = {
        "Windows": "~/AppData/Roaming/Mozilla/Firefox/Profiles/*/cookies.sqlite",
        "Darwin": "~/Library/Application Support/Firefox/Profiles/*/cookies.sqlite",
        "Linux": "~/.mozilla/firefox/*/cookies.sqlite",
    }.get(platform.system(), "~/.mozilla/firefox/*/cookies.sqlite")
    cookiefiles = glob.glob(expanduser(default_cookiefile))
    if not cookiefiles:
        raise SystemExit("No Firefox cookies.sqlite file found. Please log in to Instagram in Firefox.")
    return cookiefiles[0]

def import_session(cookiefile, username):
    print(f"Using cookies from: {cookiefile}")
    conn = sqlite3.connect(f"file:{cookiefile}?immutable=1", uri=True)
    try:
        cookie_data = conn.execute(
            "SELECT name, value FROM moz_cookies WHERE baseDomain='instagram.com'"
        )
    except sqlite3.OperationalError:
        cookie_data = conn.execute(
            "SELECT name, value FROM moz_cookies WHERE host LIKE '%instagram.com'"
        )
    loader = Instaloader(max_connection_attempts=1)
    loader.context._session.cookies.update(cookie_data)
    loader.context.username = username
    print(f"Verifying login for: {username}")
    if not loader.test_login():
        raise SystemExit("Login failed. Are you logged in successfully on Firefox?")
    session_path = expanduser(f"~/.config/instaloader/session-{username}")
    loader.save_session_to_file(session_path)
    print(f"Session saved to: {session_path}")
    dotenv_path = os.path.join(os.getcwd(), ".env")
    if not os.path.exists(dotenv_path):
        open(dotenv_path, 'a').close()
    set_key(dotenv_path, "IG_USERNAME", username)

if __name__ == "__main__":
    print("Please login to your Instagram account in Firefox first.")
    username = input("Enter your Instagram username: ").strip()
    try:
        cookiefile = get_cookiefile()
        import_session(cookiefile, username)
    except (ConnectionException, sqlite3.OperationalError) as e:
        raise SystemExit(f"Cookie import failed: {e}")
