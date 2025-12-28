# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Claude Pro/Max subscription authentication client"""


import asyncio
import json
import os
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional

import aiohttp


class ClaudeSubscriptionClient:
    """Authentication client for Claude Pro/Max subscription plans"""

    # Claude web interface endpoints
    CLAUDE_WEB_API = "https://claude.ai/api"
    CLAUDE_CHAT_API = f"{CLAUDE_WEB_API}/conversations"
    CLAUDE_AUTH_URL = "https://claude.ai/login"

    def __init__(self, config_dir: Path):
        """Initialize subscription client"""
        self.config_dir = config_dir
        self.auth_dir = config_dir / "auth"
        self.auth_dir.mkdir(parents=True, exist_ok=True)

        self.session_file = self.auth_dir / "claude_session.json"

        # Session state
        self.session_key: Optional[str] = None
        self.organization_id: Optional[str] = None
        self.user_id: Optional[str] = None
        self.expires_at: Optional[datetime] = None
        self.plan_type: Optional[str] = None

    async def authenticate_interactive(self) -> bool:
        """Interactive authentication flow for Claude Pro/Max"""
        # Use simple extractor for guided manual extraction
        try:
            from .simple_extractor import guide_user_extraction

            token = guide_user_extraction()

            if token:
                success = await self._validate_session_key(token)
                if success:
                    print("✅ Token validated successfully!")
                    return True
                else:
                    print("❌ Token validation failed.")
                    print("The token might be expired or invalid.")
                    print("Please try logging out and back into claude.ai")

        except KeyboardInterrupt:
            print("\n⚠️  Setup cancelled by user")
        except Exception as e:
            print(f"❌ Authentication failed: {e}")

        print("\n❌ Authentication setup incomplete.")
        print("For help, visit: https://docs.claude.com/")
        return False

    async def _validate_session_key(self, session_key: str) -> bool:
        """Validate session key by making a test request"""
        try:
            headers = {
                "Authorization": f"Bearer {session_key}",
                "Content-Type": "application/json",
                "User-Agent": "aii-cli/1.0"
            }

            async with aiohttp.ClientSession() as session:
                # Try to get user info or make a simple request
                async with session.get(
                    f"{self.CLAUDE_WEB_API}/organizations",
                    headers=headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()

                        # Extract session info
                        self.session_key = session_key
                        self.expires_at = datetime.now() + timedelta(days=30)

                        if isinstance(data, list) and len(data) > 0:
                            org = data[0]
                            self.organization_id = org.get("uuid")
                            # Try to determine plan type
                            capabilities = org.get("capabilities", [])
                            if "claude_3_5_sonnet" in capabilities:
                                self.plan_type = "pro"
                            elif "claude_3_opus" in capabilities:
                                self.plan_type = "max"

                        await self._save_session()
                        return True

                    return False

        except Exception as e:
            print(f"Session validation error: {e}")
            return False

    async def _parse_cookie_header(self, cookie_header: str) -> bool:
        """Parse cookie header and extract session information"""
        try:
            # Clean up cookie header
            if cookie_header.startswith("Cookie: "):
                cookie_header = cookie_header[8:]

            # Parse cookies
            cookies = {}
            for cookie in cookie_header.split(";"):
                if "=" in cookie:
                    key, value = cookie.strip().split("=", 1)
                    cookies[key] = value

            # Look for Claude session cookies
            session_key = None
            for key in ["sessionKey", "claude_session", "auth_token", "_session"]:
                if key in cookies:
                    session_key = cookies[key]
                    break

            if session_key:
                return await self._validate_session_key(session_key)

            print("❌ No valid session key found in cookies")
            return False

        except Exception as e:
            print(f"Cookie parsing error: {e}")
            return False

    async def get_valid_session(self) -> Optional[str]:
        """Get valid session key (load if needed)"""
        if not await self.load_session():
            return None

        # Check if session is expired
        if self.expires_at and datetime.now() >= self.expires_at:
            print("⚠️  Session expired. Please re-authenticate with 'aii config oauth login'")
            return None

        return self.session_key

    async def load_session(self) -> bool:
        """Load saved session data"""
        if not self.session_file.exists():
            return False

        try:
            with open(self.session_file, 'r') as f:
                session_data = json.load(f)

            self.session_key = session_data.get("session_key")
            self.organization_id = session_data.get("organization_id")
            self.user_id = session_data.get("user_id")
            self.plan_type = session_data.get("plan_type")

            expires_str = session_data.get("expires_at")
            if expires_str:
                self.expires_at = datetime.fromisoformat(expires_str)

            return bool(self.session_key)

        except Exception:
            return False

    async def _save_session(self):
        """Save session data securely"""
        session_data = {
            "session_key": self.session_key,
            "organization_id": self.organization_id,
            "user_id": self.user_id,
            "plan_type": self.plan_type,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "updated_at": datetime.now().isoformat()
        }

        with open(self.session_file, 'w') as f:
            json.dump(session_data, f, indent=2)

        # Set secure permissions
        os.chmod(self.session_file, 0o600)

    async def logout(self) -> bool:
        """Clear session data"""
        try:
            if self.session_file.exists():
                self.session_file.unlink()

            # Clear memory
            self.session_key = None
            self.organization_id = None
            self.user_id = None
            self.expires_at = None
            self.plan_type = None

            return True
        except Exception:
            return False

    def is_authenticated(self) -> bool:
        """Check if user has valid session"""
        return bool(
            self.session_key and
            (not self.expires_at or datetime.now() < self.expires_at)
        )

    async def test_api_access(self) -> bool:
        """Test if session provides API access"""
        if not self.session_key:
            return False

        try:
            headers = {
                "Authorization": f"Bearer {self.session_key}",
                "Content-Type": "application/json"
            }

            async with aiohttp.ClientSession() as session:
                # Test with a simple conversation request
                test_payload = {
                    "prompt": "Hello",
                    "model": "claude-3-sonnet-20240229"
                }

                async with session.post(
                    f"{self.CLAUDE_CHAT_API}",
                    headers=headers,
                    json=test_payload
                ) as response:
                    return response.status == 200

        except Exception:
            return False

    def get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for API requests"""
        if not self.session_key:
            return {}

        return {
            "Authorization": f"Bearer {self.session_key}",
            "Content-Type": "application/json",
            "User-Agent": "aii-cli/1.0"
        }

    def get_status_info(self) -> Dict:
        """Get authentication status information"""
        return {
            "authenticated": self.is_authenticated(),
            "session_key": self.session_key[:10] + "..." if self.session_key else None,
            "plan_type": self.plan_type,
            "organization_id": self.organization_id,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None
        }
