#!/usr/bin/env python3
"""
Re-authenticate Google OAuth to get a new refresh token.
Run this script, visit the printed URL in a browser, authorize with dhunney@gmail.com,
then paste the authorization code when prompted.
"""
import json
import os
import requests
import urllib.parse
import http.server
import threading

CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
REDIRECT_URI = "http://localhost:3000/auth/callback"
TOKEN_FILE = "/var/www/livininbintaro/api/.google_token.json"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]

# Build authorization URL
auth_params = {
    "client_id": CLIENT_ID,
    "redirect_uri": REDIRECT_URI,
    "response_type": "code",
    "scope": " ".join(SCOPES),
    "access_type": "offline",
    "prompt": "consent",  # Force consent to get new refresh token
}
auth_url = f"https://accounts.google.com/o/oauth2/auth?{urllib.parse.urlencode(auth_params)}"

print("=" * 70)
print("GOOGLE OAUTH RE-AUTHENTICATION")
print("=" * 70)
print()
print("1. Open this URL in your browser:")
print()
print(auth_url)
print()
print("2. Sign in with: dhunney@gmail.com")
print("3. Authorize access to Google Sheets and Drive")
print()

# Try to capture the code via local HTTP server
auth_code = [None]

class CallbackHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        if "code" in params:
            auth_code[0] = params["code"][0]
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"<h1>Authorization successful!</h1><p>You can close this tab.</p>")
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"No code received")
    def log_message(self, format, *args):
        pass  # Suppress logs

# Start local server in background
server = http.server.HTTPServer(("0.0.0.0", 3000), CallbackHandler)
server_thread = threading.Thread(target=server.handle_request)
server_thread.daemon = True
server_thread.start()

print("Waiting for callback on port 3000...")
print("(If the redirect doesn't work, paste the full redirect URL or just the code below)")
print()

# Wait for either callback or manual input
import select, sys
server_thread.join(timeout=300)  # Wait up to 5 minutes

if not auth_code[0]:
    code_input = input("Paste the authorization code (or full redirect URL): ").strip()
    if "code=" in code_input:
        # Extract code from URL
        parsed = urllib.parse.urlparse(code_input)
        params = urllib.parse.parse_qs(parsed.query)
        auth_code[0] = params.get("code", [code_input])[0]
    else:
        auth_code[0] = code_input

server.server_close()

if not auth_code[0]:
    print("[ERROR] No authorization code received!")
    sys.exit(1)

print(f"[OK] Got authorization code: {auth_code[0][:20]}...")

# Exchange code for tokens
print("Exchanging code for tokens...")
resp = requests.post("https://oauth2.googleapis.com/token", data={
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "code": auth_code[0],
    "redirect_uri": REDIRECT_URI,
    "grant_type": "authorization_code",
})

if resp.status_code != 200:
    print(f"[ERROR] Token exchange failed: {resp.status_code}")
    print(resp.text)
    sys.exit(1)

token_data = resp.json()
print(f"[OK] Access token: {token_data.get('access_token', '')[:30]}...")
print(f"[OK] Refresh token: {'YES' if token_data.get('refresh_token') else 'NO'}")

# Save to token file
save_data = {
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "refresh_token": token_data.get("refresh_token", ""),
    "access_token": token_data.get("access_token", ""),
    "token_type": token_data.get("token_type", "Bearer"),
    "expires_in": token_data.get("expires_in", 3599),
}

with open(TOKEN_FILE, "w") as f:
    json.dump(save_data, f, indent=2)
print(f"[OK] Saved to {TOKEN_FILE}")

# Also update hardcoded refresh token in sync_images.py
if token_data.get("refresh_token"):
    new_rt = token_data["refresh_token"]
    with open("/var/www/livininbintaro/api/sync_images.py") as f:
        content = f.read()
    import re
    content = re.sub(
        r'REFRESH_TOKEN = ".*?"',
        f'REFRESH_TOKEN = "{new_rt}"',
        content
    )
    with open("/var/www/livininbintaro/api/sync_images.py", "w") as f:
        f.write(content)
    print("[OK] Updated REFRESH_TOKEN in sync_images.py")

# Test connectivity
print()
print("Testing Google Sheets API...")
headers = {"Authorization": f"Bearer {token_data['access_token']}"}
test_resp = requests.get(
    "https://sheets.googleapis.com/v4/spreadsheets/1Qgq7HorUj-fJGeIaER1xxycQc45I8oK8L4AP1v1UY68?fields=properties.title",
    headers=headers
)
if test_resp.status_code == 200:
    print(f"[OK] Sheets API works! Spreadsheet: {test_resp.json()['properties']['title']}")
else:
    print(f"[WARN] Sheets API returned {test_resp.status_code}: {test_resp.text[:200]}")

print("Testing Google Drive API...")
drive_resp = requests.get(
    "https://www.googleapis.com/drive/v3/about?fields=user",
    headers=headers
)
if drive_resp.status_code == 200:
    user = drive_resp.json().get("user", {})
    print(f"[OK] Drive API works! User: {user.get('displayName')} ({user.get('emailAddress')})")
else:
    print(f"[WARN] Drive API returned {drive_resp.status_code}: {drive_resp.text[:200]}")

print()
print("=" * 70)
print("RE-AUTHENTICATION COMPLETE")
print("=" * 70)
