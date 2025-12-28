# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Browser session token extractor for Claude Pro/Max authentication"""


import json
import os
import sqlite3
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    from Crypto.Cipher import AES
    from Crypto.Protocol.KDF import PBKDF2
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False


class ChromeSessionExtractor:
    """Extract Claude session tokens from Chrome browser"""

    def __init__(self):
        self.claude_domains = [
            "claude.ai",
            ".claude.ai",
            "api.claude.ai"
        ]

    def get_chrome_paths(self) -> Dict[str, Path]:
        """Get Chrome data paths for different operating systems"""
        home = Path.home()

        # macOS paths
        if os.name == 'posix' and os.uname().sysname == 'Darwin':
            return {
                'cookies': home / 'Library' / 'Application Support' / 'Google' / 'Chrome' / 'Default' / 'Cookies',
                'local_storage': home / 'Library' / 'Application Support' / 'Google' / 'Chrome' / 'Default' / 'Local Storage' / 'leveldb',
                'session_storage': home / 'Library' / 'Application Support' / 'Google' / 'Chrome' / 'Default' / 'Session Storage',
                'preferences': home / 'Library' / 'Application Support' / 'Google' / 'Chrome' / 'Default' / 'Preferences'
            }

        # Linux paths
        elif os.name == 'posix':
            return {
                'cookies': home / '.config' / 'google-chrome' / 'Default' / 'Cookies',
                'local_storage': home / '.config' / 'google-chrome' / 'Default' / 'Local Storage' / 'leveldb',
                'session_storage': home / '.config' / 'google-chrome' / 'Default' / 'Session Storage',
                'preferences': home / '.config' / 'google-chrome' / 'Default' / 'Preferences'
            }

        # Windows paths
        else:
            appdata = Path(os.environ.get('LOCALAPPDATA', ''))
            return {
                'cookies': appdata / 'Google' / 'Chrome' / 'User Data' / 'Default' / 'Cookies',
                'local_storage': appdata / 'Google' / 'Chrome' / 'User Data' / 'Default' / 'Local Storage' / 'leveldb',
                'session_storage': appdata / 'Google' / 'Chrome' / 'User Data' / 'Default' / 'Session Storage',
                'preferences': appdata / 'Google' / 'Chrome' / 'User Data' / 'Default' / 'Preferences'
            }

    def extract_claude_cookies(self) -> List[Dict]:
        """Extract Claude-related cookies from Chrome"""
        paths = self.get_chrome_paths()
        cookies_path = paths['cookies']

        if not cookies_path.exists():
            print(f"❌ Chrome cookies database not found at: {cookies_path}")
            return []

        try:
            # Copy cookies database to temporary location (Chrome locks the original)
            import tempfile
            import shutil

            with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_file:
                shutil.copy2(cookies_path, temp_file.name)
                temp_db_path = temp_file.name

            # Connect to cookies database
            conn = sqlite3.connect(temp_db_path)
            cursor = conn.cursor()

            # Query for Claude cookies
            query = """
            SELECT name, value, host_key, path, expires_utc, is_secure, is_httponly, creation_utc
            FROM cookies
            WHERE host_key LIKE '%claude.ai%' OR host_key LIKE '%.claude.ai%'
            ORDER BY creation_utc DESC
            """

            cursor.execute(query)
            cookies = []

            for row in cursor.fetchall():
                cookies.append({
                    'name': row[0],
                    'value': row[1],
                    'domain': row[2],
                    'path': row[3],
                    'expires': row[4],
                    'secure': bool(row[5]),
                    'httponly': bool(row[6]),
                    'created': row[7]
                })

            conn.close()
            os.unlink(temp_db_path)  # Clean up temp file

            return cookies

        except Exception as e:
            print(f"❌ Error extracting cookies: {e}")
            return []

    def extract_claude_tokens_from_network(self) -> List[str]:
        """Extract tokens using Chrome debugging protocol"""
        try:
            # Check if Chrome is running with debugging enabled
            debug_port = 9222

            # Try to connect to Chrome debugging port
            import requests
            try:
                response = requests.get(f'http://localhost:{debug_port}/json/list', timeout=2)
                tabs = response.json()
            except:
                print("🔧 Chrome debugging not available. Let me help you enable it...")
                print("Please follow these steps:")
                print("1. Close all Chrome windows")
                print("2. Run Chrome with debugging enabled:")

                if os.name == 'posix' and os.uname().sysname == 'Darwin':  # macOS
                    print("   /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port=9222")
                elif os.name == 'posix':  # Linux
                    print("   google-chrome --remote-debugging-port=9222")
                else:  # Windows
                    print("   chrome.exe --remote-debugging-port=9222")

                print("3. Open claude.ai and login")
                print("4. Run this command again")
                return []

            # Find Claude tabs
            claude_tabs = [tab for tab in tabs if 'claude.ai' in tab.get('url', '')]

            if not claude_tabs:
                print("❌ No Claude.ai tabs found. Please open claude.ai in Chrome.")
                return []

            tokens = []
            for tab in claude_tabs:
                try:
                    # Connect to tab's debugging session
                    import websocket
                    ws_url = tab['webSocketDebuggerUrl']

                    # This is a simplified approach - in practice, you'd need more complex WebSocket handling
                    print(f"🔍 Found Claude tab: {tab['title']}")

                except Exception as e:
                    print(f"⚠️  Could not extract from tab: {e}")

            return tokens

        except Exception as e:
            print(f"❌ Network extraction failed: {e}")
            return []

    def get_session_from_chrome_storage(self) -> Optional[str]:
        """Extract session key from Chrome's local storage"""
        paths = self.get_chrome_paths()

        # Try to find Local Storage files for claude.ai
        local_storage_path = paths['local_storage']

        if not local_storage_path.exists():
            print(f"❌ Chrome Local Storage not found at: {local_storage_path}")
            return None

        try:
            # Look for claude.ai storage files
            claude_storage_files = []
            for file_path in local_storage_path.glob('*'):
                if file_path.is_file():
                    try:
                        with open(file_path, 'rb') as f:
                            content = f.read()
                            if b'claude.ai' in content or b'sessionKey' in content:
                                claude_storage_files.append(file_path)
                    except:
                        continue

            # Parse storage files for session keys
            for storage_file in claude_storage_files:
                try:
                    with open(storage_file, 'rb') as f:
                        content = f.read().decode('utf-8', errors='ignore')

                        # Look for sessionKey patterns
                        import re
                        session_patterns = [
                            r'"sessionKey"[:\s]*"([^"]+)"',
                            r'sessionKey[:\s]*"([^"]+)"',
                            r'"session"[:\s]*"([^"]+)"'
                        ]

                        for pattern in session_patterns:
                            matches = re.findall(pattern, content)
                            if matches:
                                return matches[0]

                except Exception as e:
                    continue

        except Exception as e:
            print(f"❌ Local storage extraction failed: {e}")

        return None

    def extract_using_applescript(self) -> Optional[str]:
        """Extract session using AppleScript (macOS only)"""
        if os.name != 'posix' or os.uname().sysname != 'Darwin':
            return None

        applescript = '''
        tell application "Google Chrome"
            repeat with w in windows
                repeat with t in tabs of w
                    if URL of t contains "claude.ai" then
                        try
                            set sessionKey to execute t javascript "localStorage.getItem('sessionKey')"
                            if sessionKey is not null then
                                return sessionKey
                            end if
                        end try

                        try
                            set authToken to execute t javascript "document.cookie.match(/auth[^;]*/) && document.cookie.match(/auth[^;]*/)[0].split('=')[1]"
                            if authToken is not null then
                                return authToken
                            end if
                        end try
                    end if
                end repeat
            end repeat
        end tell
        '''

        try:
            result = subprocess.run(['osascript', '-e', applescript],
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        except Exception as e:
            print(f"⚠️  AppleScript extraction failed: {e}")

        return None

    def guided_manual_extraction(self) -> Optional[str]:
        """Guide user through manual token extraction with specific instructions"""
        print("\n🔍 Let's extract your Claude session token step by step:")
        print("=" * 60)

        print("\n📋 Method 1: Using Browser Console (Easiest)")
        print("1. Make sure you're logged into claude.ai")
        print("2. Press F12 or Cmd+Option+I to open DevTools")
        print("3. Go to the 'Console' tab")
        print("4. Type this command and press Enter:")
        print("   localStorage.getItem('sessionKey')")
        print("5. Copy the value (including quotes)")

        session_key = input("\nPaste the sessionKey value here (or press Enter to try another method): ").strip()
        if session_key and session_key != 'null':
            # Clean up the session key
            session_key = session_key.strip('"\'')
            if session_key:
                return session_key

        print("\n📋 Method 2: Using Network Tab")
        print("1. Open DevTools (F12 or Cmd+Option+I)")
        print("2. Go to the 'Network' tab")
        print("3. Send a message to Claude")
        print("4. Look for requests to 'api/organizations' or 'conversations'")
        print("5. Click on one of these requests")
        print("6. In the Headers section, find 'Cookie:'")
        print("7. Copy the entire Cookie header value")

        cookie_header = input("\nPaste the Cookie header here (or press Enter to try another method): ").strip()
        if cookie_header:
            # Try to extract session from cookies
            import re
            patterns = [
                r'sessionKey=([^;]+)',
                r'auth_token=([^;]+)',
                r'claude_session=([^;]+)'
            ]

            for pattern in patterns:
                match = re.search(pattern, cookie_header)
                if match:
                    return match.group(1)

        print("\n📋 Method 3: Using Application Tab")
        print("1. Open DevTools (F12 or Cmd+Option+I)")
        print("2. Go to the 'Application' tab (or 'Storage' in Firefox)")
        print("3. In the left sidebar, expand 'Local Storage'")
        print("4. Click on 'https://claude.ai'")
        print("5. Look for a key named 'sessionKey' or similar")
        print("6. Copy its value")

        storage_key = input("\nPaste the storage value here: ").strip()
        if storage_key:
            return storage_key.strip('"\'')

        return None

    def extract_token(self) -> Optional[str]:
        """Main method to extract Claude authentication token"""
        print("🔍 Extracting Claude authentication token from Chrome...")

        # Method 1: Try AppleScript on macOS
        if os.name == 'posix' and os.uname().sysname == 'Darwin':
            print("📱 Trying AppleScript extraction...")
            token = self.extract_using_applescript()
            if token and token != 'null':
                print("✅ Token extracted using AppleScript!")
                return token

        # Method 2: Try Chrome Local Storage
        print("💾 Checking Chrome Local Storage...")
        token = self.get_session_from_chrome_storage()
        if token:
            print("✅ Token found in Local Storage!")
            return token

        # Method 3: Try cookies
        print("🍪 Checking Chrome cookies...")
        cookies = self.extract_claude_cookies()
        for cookie in cookies:
            if 'session' in cookie['name'].lower() or 'auth' in cookie['name'].lower():
                if cookie['value'] and len(cookie['value']) > 10:
                    print(f"✅ Found potential token in cookie: {cookie['name']}")
                    return cookie['value']

        # Method 4: Guided manual extraction
        print("\n⚠️  Automatic extraction failed. Let's try manual extraction...")
        return self.guided_manual_extraction()


def extract_claude_token() -> Optional[str]:
    """Convenience function to extract Claude token"""
    extractor = ChromeSessionExtractor()
    return extractor.extract_token()


if __name__ == "__main__":
    token = extract_claude_token()
    if token:
        print(f"\n✅ Success! Token extracted: {token[:20]}...")
    else:
        print("\n❌ Could not extract token. Please try manual method.")
