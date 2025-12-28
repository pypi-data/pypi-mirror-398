# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Native subscription authentication client for Claude Pro/Max plans"""


import asyncio
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional

import aiohttp


class AnthropicSubscriptionClient:
    """Native OAuth 2.0 PKCE client for Anthropic subscription authentication"""

    # Anthropic OAuth endpoints (based on research)
    AUTHORIZATION_SERVER = "https://auth.anthropic.com"
    DISCOVERY_ENDPOINT = f"{AUTHORIZATION_SERVER}/.well-known/oauth-authorization-server"
    REGISTER_ENDPOINT = f"{AUTHORIZATION_SERVER}/oauth/register"
    AUTHORIZE_ENDPOINT = f"{AUTHORIZATION_SERVER}/oauth/authorize"
    TOKEN_ENDPOINT = f"{AUTHORIZATION_SERVER}/oauth/token"

    # aii OAuth client configuration
    CLIENT_NAME = "aii CLI"
    CLIENT_URI = "https://github.com/ailabs/aii"
    REDIRECT_URI = "http://localhost:8080/oauth/callback"
    SCOPES = ["claude:subscription", "claude:api"]

    def __init__(self, config_dir: Path):
        """Initialize OAuth client"""
        self.config_dir = config_dir
        self.auth_dir = config_dir / "auth"
        self.auth_dir.mkdir(parents=True, exist_ok=True)

        self.credentials_file = self.auth_dir / "oauth_credentials.json"
        self.client_file = self.auth_dir / "oauth_client.json"

        # OAuth state
        self.client_id: Optional[str] = None
        self.client_secret: Optional[str] = None
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.expires_at: Optional[datetime] = None

    async def authenticate(self) -> bool:
        """Complete OAuth authentication flow"""
        try:
            # Step 1: Discover OAuth endpoints
            print("🔍 Discovering OAuth endpoints...")
            if not await self._discover_endpoints():
                print("❌ Failed to discover OAuth endpoints")
                return False

            # Step 2: Register dynamic client (if needed)
            print("📝 Registering OAuth client...")
            if not await self._register_client():
                print("❌ Failed to register OAuth client")
                return False

            # Step 3: Start OAuth flow
            print("🔐 Starting OAuth authentication flow...")
            if not await self._start_oauth_flow():
                print("❌ OAuth authentication failed")
                return False

            print("✅ Subscription authentication successful!")
            return True

        except Exception as e:
            print(f"❌ Authentication failed: {e}")
            return False

    async def _discover_endpoints(self) -> bool:
        """Discover OAuth endpoints from .well-known"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.DISCOVERY_ENDPOINT) as response:
                    if response.status == 200:
                        discovery = await response.json()
                        # Update endpoints from discovery
                        self.AUTHORIZE_ENDPOINT = discovery.get("authorization_endpoint", self.AUTHORIZE_ENDPOINT)
                        self.TOKEN_ENDPOINT = discovery.get("token_endpoint", self.TOKEN_ENDPOINT)
                        self.REGISTER_ENDPOINT = discovery.get("registration_endpoint", self.REGISTER_ENDPOINT)
                        return True
                    return False
        except Exception:
            # Fallback to hardcoded endpoints
            return True

    async def _register_client(self) -> bool:
        """Register dynamic OAuth client with Anthropic"""
        # Check if client is already registered
        if self.client_file.exists():
            with open(self.client_file, 'r') as f:
                client_data = json.load(f)
                self.client_id = client_data.get("client_id")
                self.client_secret = client_data.get("client_secret")
                if self.client_id and self.client_secret:
                    return True

        # Register new client using Dynamic Client Registration (DCR)
        registration_data = {
            "client_name": self.CLIENT_NAME,
            "client_uri": self.CLIENT_URI,
            "redirect_uris": [self.REDIRECT_URI],
            "grant_types": ["authorization_code", "refresh_token"],
            "response_types": ["code"],
            "scope": " ".join(self.SCOPES),
            "token_endpoint_auth_method": "client_secret_basic",
            "application_type": "native"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.REGISTER_ENDPOINT,
                    json=registration_data,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 201:
                        client_data = await response.json()
                        self.client_id = client_data["client_id"]
                        self.client_secret = client_data["client_secret"]

                        # Save client credentials
                        with open(self.client_file, 'w') as f:
                            json.dump({
                                "client_id": self.client_id,
                                "client_secret": self.client_secret,
                                "registration_data": client_data
                            }, f, indent=2)

                        # Set secure permissions
                        os.chmod(self.client_file, 0o600)
                        return True
                    else:
                        print(f"❌ Client registration failed: {response.status}")
                        return False
        except Exception as e:
            print(f"❌ Client registration error: {e}")
            return False

    async def _start_oauth_flow(self) -> bool:
        """Start OAuth 2.0 PKCE authorization flow"""
        # Generate PKCE parameters
        code_verifier = self._generate_code_verifier()
        code_challenge = self._generate_code_challenge(code_verifier)
        state = secrets.token_urlsafe(32)

        # Build authorization URL
        auth_params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.REDIRECT_URI,
            "scope": " ".join(self.SCOPES),
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256"
        }

        auth_url = f"{self.AUTHORIZE_ENDPOINT}?{urllib.parse.urlencode(auth_params)}"

        # Start local callback server
        app = web.Application()
        callback_result = {"success": False, "code": None, "state": None}

        async def oauth_callback(request):
            """Handle OAuth callback"""
            query = request.query
            callback_result["code"] = query.get("code")
            callback_result["state"] = query.get("state")
            callback_result["success"] = bool(query.get("code"))

            if callback_result["success"]:
                return web.Response(
                    text="✅ Authentication successful! You can close this window and return to your terminal.",
                    content_type="text/html"
                )
            else:
                error = query.get("error", "unknown_error")
                return web.Response(
                    text=f"❌ Authentication failed: {error}. Please try again.",
                    content_type="text/html"
                )

        app.router.add_get("/oauth/callback", oauth_callback)

        # Start server
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, 'localhost', 8080)
        await site.start()

        try:
            # Open browser for user authentication
            print(f"🌐 Opening browser for authentication...")
            print(f"If browser doesn't open, visit: {auth_url}")
            webbrowser.open(auth_url)

            # Wait for callback (with timeout)
            timeout = 300  # 5 minutes
            start_time = asyncio.get_event_loop().time()

            while not callback_result["success"]:
                if asyncio.get_event_loop().time() - start_time > timeout:
                    print("❌ Authentication timeout. Please try again.")
                    return False
                await asyncio.sleep(1)

            # Verify state parameter
            if callback_result["state"] != state:
                print("❌ Invalid state parameter. Possible CSRF attack.")
                return False

            # Exchange authorization code for tokens
            return await self._exchange_code_for_tokens(
                callback_result["code"],
                code_verifier
            )

        finally:
            await runner.cleanup()

    async def _exchange_code_for_tokens(self, auth_code: str, code_verifier: str) -> bool:
        """Exchange authorization code for access and refresh tokens"""
        token_data = {
            "grant_type": "authorization_code",
            "code": auth_code,
            "redirect_uri": self.REDIRECT_URI,
            "client_id": self.client_id,
            "code_verifier": code_verifier
        }

        # Basic auth with client credentials
        auth = aiohttp.BasicAuth(self.client_id, self.client_secret)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.TOKEN_ENDPOINT,
                    data=token_data,
                    auth=auth,
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                ) as response:
                    if response.status == 200:
                        tokens = await response.json()

                        self.access_token = tokens["access_token"]
                        self.refresh_token = tokens.get("refresh_token")

                        # Calculate expiration
                        expires_in = tokens.get("expires_in", 3600)
                        self.expires_at = datetime.now() + timedelta(seconds=expires_in)

                        # Save credentials
                        await self._save_credentials()
                        return True
                    else:
                        error_text = await response.text()
                        print(f"❌ Token exchange failed: {response.status} - {error_text}")
                        return False
        except Exception as e:
            print(f"❌ Token exchange error: {e}")
            return False

    async def _save_credentials(self):
        """Save OAuth credentials securely"""
        credentials = {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "client_id": self.client_id,
            "updated_at": datetime.now().isoformat()
        }

        with open(self.credentials_file, 'w') as f:
            json.dump(credentials, f, indent=2)

        # Set secure permissions
        os.chmod(self.credentials_file, 0o600)

    async def load_credentials(self) -> bool:
        """Load saved OAuth credentials"""
        if not self.credentials_file.exists():
            return False

        try:
            with open(self.credentials_file, 'r') as f:
                credentials = json.load(f)

            self.access_token = credentials.get("access_token")
            self.refresh_token = credentials.get("refresh_token")
            self.client_id = credentials.get("client_id")

            expires_at_str = credentials.get("expires_at")
            if expires_at_str:
                self.expires_at = datetime.fromisoformat(expires_at_str)

            return bool(self.access_token)
        except Exception:
            return False

    async def get_valid_token(self) -> Optional[str]:
        """Get valid access token (refresh if needed)"""
        # Load existing credentials
        if not await self.load_credentials():
            return None

        # Check if token is expired
        if self.expires_at and datetime.now() >= self.expires_at:
            # Try to refresh token
            if not await self._refresh_access_token():
                return None

        return self.access_token

    async def _refresh_access_token(self) -> bool:
        """Refresh expired access token"""
        if not self.refresh_token:
            return False

        # Load client credentials
        if not self.client_file.exists():
            return False

        with open(self.client_file, 'r') as f:
            client_data = json.load(f)
            self.client_id = client_data.get("client_id")
            self.client_secret = client_data.get("client_secret")

        refresh_data = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
            "client_id": self.client_id
        }

        auth = aiohttp.BasicAuth(self.client_id, self.client_secret)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.TOKEN_ENDPOINT,
                    data=refresh_data,
                    auth=auth,
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                ) as response:
                    if response.status == 200:
                        tokens = await response.json()

                        self.access_token = tokens["access_token"]
                        if "refresh_token" in tokens:
                            self.refresh_token = tokens["refresh_token"]

                        # Calculate expiration
                        expires_in = tokens.get("expires_in", 3600)
                        self.expires_at = datetime.now() + timedelta(seconds=expires_in)

                        # Save updated credentials
                        await self._save_credentials()
                        return True
                    else:
                        return False
        except Exception:
            return False

    def _generate_code_verifier(self) -> str:
        """Generate PKCE code verifier"""
        return base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')

    def _generate_code_challenge(self, code_verifier: str) -> str:
        """Generate PKCE code challenge"""
        code_sha = hashlib.sha256(code_verifier.encode('utf-8')).digest()
        return base64.urlsafe_b64encode(code_sha).decode('utf-8').rstrip('=')

    async def logout(self) -> bool:
        """Logout and clear credentials"""
        try:
            # Remove credential files
            if self.credentials_file.exists():
                self.credentials_file.unlink()
            if self.client_file.exists():
                self.client_file.unlink()

            # Clear memory
            self.access_token = None
            self.refresh_token = None
            self.expires_at = None
            self.client_id = None
            self.client_secret = None

            return True
        except Exception:
            return False

    def is_authenticated(self) -> bool:
        """Check if user is currently authenticated"""
        return bool(self.access_token and (
            not self.expires_at or datetime.now() < self.expires_at
        ))
