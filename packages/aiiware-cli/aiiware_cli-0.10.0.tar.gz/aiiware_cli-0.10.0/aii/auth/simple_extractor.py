# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Simple Claude token extraction guide"""


import json
import os
from pathlib import Path


def guide_user_extraction():
    """Guide user through token extraction with clear steps"""
    print("\n🔐 Claude Session Token Extraction Guide")
    print("=" * 50)
    print("\nWe'll extract your Claude session token in 3 simple steps:")
    print("This works with Chrome, Firefox, Safari, and Edge.\n")

    print("📋 Step 1: Open Claude and DevTools")
    print("1. Go to https://claude.ai and make sure you're logged in")
    print("2. Press F12 (or Cmd+Option+I on Mac) to open Developer Tools")
    print("3. Click on the 'Console' tab")

    print("\n📋 Step 2: Extract Your Session Token")
    print("4. In the console, type this command and press Enter:")
    print("   localStorage.getItem('sessionKey')")
    print("\n   OR try these alternatives if the first doesn't work:")
    print("   localStorage.getItem('authToken')")
    print("   localStorage.getItem('auth_token')")
    print("   localStorage.getItem('claude_session')")

    print("\n📋 Step 3: Copy and Paste")
    print("5. Copy the value that appears (it should be a long string)")
    print("6. Paste it below (don't include the quotes)")

    print("\n" + "─" * 50)

    # Interactive token input
    while True:
        token = input("Paste your session token here: ").strip()

        if not token:
            print("❌ No token entered. Please try again.")
            continue

        # Clean up the token
        token = token.strip('"\'')

        if len(token) < 10:
            print("❌ Token seems too short. Please check and try again.")
            continue

        # Basic validation
        if token.lower() in ['null', 'undefined', 'none']:
            print("❌ Token is null/undefined. Try the alternative commands above.")
            continue

        return token


def save_token_to_config(token: str) -> bool:
    """Save token to aii configuration"""
    try:
        config_dir = Path.home() / ".aii" / "auth"
        config_dir.mkdir(parents=True, exist_ok=True)

        session_file = config_dir / "claude_session.json"

        from datetime import datetime, timedelta

        session_data = {
            "session_key": token,
            "plan_type": "pro",  # Default assumption
            "expires_at": (datetime.now() + timedelta(days=30)).isoformat(),
            "updated_at": datetime.now().isoformat(),
            "extraction_method": "manual"
        }

        with open(session_file, 'w') as f:
            json.dump(session_data, f, indent=2)

        # Set secure permissions
        os.chmod(session_file, 0o600)

        return True

    except Exception as e:
        print(f"❌ Error saving token: {e}")
        return False


def main():
    """Main extraction flow"""
    try:
        # Guide user through extraction
        token = guide_user_extraction()

        if token:
            print(f"\n✅ Token received: {token[:20]}...")

            # Validate token format
            if len(token) < 20:
                print("⚠️  Warning: Token seems short. Please double-check.")

            # Save to config
            print("💾 Saving token to aii configuration...")
            if save_token_to_config(token):
                print("✅ Token saved successfully!")

                # Update main config
                config_file = Path.home() / ".aii" / "config.yaml"
                if config_file.exists():
                    try:
                        import yaml
                        with open(config_file, 'r') as f:
                            config = yaml.safe_load(f) or {}

                        config.setdefault('llm', {})
                        config['llm']['provider'] = 'anthropic'
                        config['llm']['use_subscription'] = True

                        with open(config_file, 'w') as f:
                            yaml.dump(config, f, default_flow_style=False, indent=2)

                        print("✅ Configuration updated to use subscription mode")
                    except Exception:
                        print("⚠️  Could not update main config, but token is saved")

                print("\n🎉 Setup Complete!")
                print("You can now test with: uv run aii config oauth status")

            else:
                print("❌ Failed to save token")
                print(f"💾 You can manually set it with:")
                print(f"export CLAUDE_SESSION_KEY='{token}'")

        else:
            print("❌ No token provided")

    except KeyboardInterrupt:
        print("\n\n⚠️  Setup cancelled by user")
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")


if __name__ == "__main__":
    main()
