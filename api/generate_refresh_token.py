#!/usr/bin/env python3
"""
Generate Google OAuth2 refresh token for Livinin Bintaro Drive sync.
Simple version: prints URL, you authorize in browser, paste code back.
"""

import json
import requests

CREDENTIALS_FILE = "/root/.secrets/livininbintaro-google.json"
TOKEN_FILE = "/var/www/livininbintaro/api/.google_token.json"

SCOPES = [
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/spreadsheets.readonly"
]

# Load credentials
with open(CREDENTIALS_FILE) as f:
    creds = json.load(f)["installed"]

CLIENT_ID = creds["client_id"]
CLIENT_SECRET = creds["client_secret"]
REDIRECT_URI = "http://localhost"  # Will just show code in URL

def main():
    print("="*70)
    print("Google OAuth2 - Generate Refresh Token for Livinin Bintaro")
    print("="*70)

    # Step 1: Generate authorization URL
    scope_str = " ".join(SCOPES)
    auth_url = (
        f"https://accounts.google.com/o/oauth2/auth"
        f"?client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&scope={scope_str}"
        f"&response_type=code"
        f"&access_type=offline"
        f"&prompt=consent"
    )

    print("\nStep 1: Authorize the application")
    print("-" * 70)
    print("\nOpen this URL in your browser:")
    print(f"\n{auth_url}\n")
    print("-" * 70)
    print("\nAfter authorizing:")
    print("1. You'll be redirected to localhost (page won't load - that's OK)")
    print("2. Look at the URL in your browser address bar")
    print("3. Copy the 'code' parameter from the URL")
    print("   Example: http://localhost/?code=4/0AY... <- copy everything after 'code='")
    print()

    # Step 2: Get authorization code from user
    auth_code = input("Paste the authorization code here: ").strip()

    if not auth_code:
        print("[ERROR] No code provided!")
        return

    # Clean up code (remove any URL parts if user pasted full URL)
    if "code=" in auth_code:
        auth_code = auth_code.split("code=")[1].split("&")[0]

    print("\n[INFO] Exchanging code for refresh token...")

    # Step 3: Exchange code for tokens
    try:
        token_resp = requests.post("https://oauth2.googleapis.com/token", data={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "code": auth_code,
            "redirect_uri": REDIRECT_URI,
            "grant_type": "authorization_code",
        })

        if token_resp.status_code != 200:
            print(f"[ERROR] Token exchange failed!")
            print(f"Response: {token_resp.text}")
            return

        tokens = token_resp.json()

        if "refresh_token" not in tokens:
            print("[ERROR] No refresh_token in response!")
            print("This can happen if you've already authorized this app before.")
            print("\nSolutions:")
            print("1. Revoke access: https://myaccount.google.com/permissions")
            print("2. Find 'Livinin Bintaro' or the app name and remove it")
            print("3. Run this script again")
            return

        # Step 4: Save tokens
        print(f"\n[OK] Refresh token obtained!")
        print(f"[INFO] Saving to {TOKEN_FILE}...")

        with open(TOKEN_FILE, "w") as f:
            json.dump(tokens, f, indent=2)

        print("\n" + "="*70)
        print("SUCCESS! Token saved.")
        print("="*70)
        print(f"\nToken file: {TOKEN_FILE}")
        print(f"Refresh token: {tokens['refresh_token'][:40]}...")
        print(f"\nYou can now run: python3 sync_images_new.py")
        print("="*70)

    except Exception as e:
        print(f"[ERROR] {e}")
        return

if __name__ == "__main__":
    main()
