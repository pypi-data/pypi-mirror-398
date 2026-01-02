"""GitHub Device Flow authentication for vmux."""

import time
import webbrowser

import httpx

from .ui import console

# vmux's GitHub OAuth App credentials (public - not secret)
# Users authorize via Device Flow, no client_secret needed
GITHUB_CLIENT_ID = "Ov23lifqVB48MUK3nJz3"


def device_flow_login() -> dict:
    """Authenticate user via GitHub Device Flow.

    Returns dict with: access_token, github_username, github_id
    """
    # Step 1: Request device code
    resp = httpx.post(
        "https://github.com/login/device/code",
        data={"client_id": GITHUB_CLIENT_ID, "scope": "read:user"},
        headers={"Accept": "application/json"},
    )
    resp.raise_for_status()
    data = resp.json()

    device_code = data["device_code"]
    user_code = data["user_code"]
    verification_uri = data["verification_uri"]
    interval = data.get("interval", 5)

    # Step 2: Show user the code
    console.print()
    console.print("  [bold cyan]Login to vmux with GitHub[/bold cyan]")
    console.print()
    console.print(f"  1. Go to: [yellow]{verification_uri}[/yellow]")
    console.print(f"  2. Enter code: [bold green]{user_code}[/bold green]")
    console.print()

    # Try to open browser
    try:
        webbrowser.open(verification_uri)
        console.print("  [dim](Opened browser for you)[/dim]")
    except Exception:
        pass

    console.print()
    console.print("  Waiting for authorization...", end="")

    # Step 3: Poll for token
    while True:
        time.sleep(interval)

        resp = httpx.post(
            "https://github.com/login/oauth/access_token",
            data={
                "client_id": GITHUB_CLIENT_ID,
                "device_code": device_code,
                "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            },
            headers={"Accept": "application/json"},
        )

        token_data = resp.json()

        if "access_token" in token_data:
            console.print(" [green]done![/green]")
            access_token = token_data["access_token"]
            break
        elif token_data.get("error") == "authorization_pending":
            console.print(".", end="")
            continue
        elif token_data.get("error") == "slow_down":
            interval += 5
            continue
        elif token_data.get("error") == "expired_token":
            raise ValueError("Login timed out. Please try again.")
        elif token_data.get("error") == "access_denied":
            raise ValueError("Login was denied.")
        else:
            raise ValueError(f"Login failed: {token_data.get('error_description', 'Unknown error')}")

    # Step 4: Get user info
    user_resp = httpx.get(
        "https://api.github.com/user",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    user_resp.raise_for_status()
    user = user_resp.json()

    console.print()
    console.print(f"  [bold green]Logged in as {user['login']}[/bold green]")
    console.print()

    return {
        "access_token": access_token,
        "github_username": user["login"],
        "github_id": user["id"],
    }
