#!/usr/bin/env python3
"""
QuickBooks Online token refresh script.
Run via cron every 30 minutes to refresh access tokens before expiry.
"""
import os
import json
import sys
import base64
import requests
from pathlib import Path

def main():
    print("QuickBooks token refresh starting...")
    
    # Load credentials
    client_id = os.environ.get("QBO_CLIENT_ID")
    client_secret = os.environ.get("QBO_CLIENT_SECRET")
    token_file = Path.home() / ".hermes" / "qbo_tokens.json"
    
    if not all([client_id, client_secret]):
        print("ERROR: Missing QBO_CLIENT_ID or QBO_CLIENT_SECRET")
        return 1
    
    if not token_file.exists():
        print("ERROR: Token file not found. Run initial OAuth flow first.")
        return 1
    
    with open(token_file) as f:
        tokens = json.load(f)
    
    refresh_token = tokens.get("refresh_token")
    if not refresh_token:
        print("ERROR: No refresh token found")
        return 1
    
    # Refresh token
    auth_header = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    
    response = requests.post(
        "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer",
        headers={
            "Authorization": f"Basic {auth_header}",
            "Content-Type": "application/x-www-form-urlencoded"
        },
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token
        },
        timeout=30
    )
    
    if response.status_code != 200:
        print(f"ERROR: Token refresh failed: {response.status_code}")
        print(response.text)
        # If invalid_grant, token is expired - need re-auth
        if response.json().get("error") == "invalid_grant":
            print("Refresh token expired. Manual re-auth required.")
            # TODO: Notify owners via Telegram
        return 1
    
    new_tokens = response.json()
    
    # Update token file
    tokens.update({
        "access_token": new_tokens["access_token"],
        "refresh_token": new_tokens["refresh_token"],
        "access_expires_at": "TODO: calculate from expires_in"
    })
    
    with open(token_file, "w") as f:
        json.dump(tokens, f, indent=2)
    
    print("Token refresh successful")
    return 0

if __name__ == "__main__":
    sys.exit(main())