# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

#!/usr/bin/env python3
"""Standalone Claude token extractor tool"""


import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from browser_extractor import extract_claude_token


def main():
    """Main function for standalone token extraction"""
    print("🔍 Claude Token Extractor")
    print("=" * 40)
    print("This tool will help you extract your Claude session token")
    print("from your Chrome browser for use with aii.\n")

    token = extract_claude_token()

    if token:
        print(f"\n✅ Success! Your Claude session token is:")
        print(f"📋 {token}")
        print(f"\n🔧 To use this token with aii, run:")
        print(f"export CLAUDE_SESSION_KEY='{token}'")
        print(f"uv run aii config oauth status")

        # Optionally save to environment file
        save_choice = input("\nWould you like to save this to your shell profile? (y/N): ").strip().lower()
        if save_choice in ['y', 'yes']:
            save_to_profile(token)
    else:
        print("\n❌ Could not extract token.")
        print("Please ensure you're logged into claude.ai in Chrome")
        print("and try the manual extraction steps.")


def save_to_profile(token: str):
    """Save token to shell profile"""
    from pathlib import Path
    import os

    # Determine shell profile file
    shell = os.environ.get('SHELL', '').split('/')[-1]
    home = Path.home()

    profile_files = {
        'bash': [home / '.bashrc', home / '.bash_profile'],
        'zsh': [home / '.zshrc'],
        'fish': [home / '.config' / 'fish' / 'config.fish']
    }

    profile_file = None
    if shell in profile_files:
        for candidate in profile_files[shell]:
            if candidate.exists():
                profile_file = candidate
                break
        # If no existing profile file, create the first one
        if not profile_file:
            profile_file = profile_files[shell][0]

    if not profile_file:
        profile_file = home / '.profile'

    try:
        # Add export line to profile
        export_line = f"export CLAUDE_SESSION_KEY='{token}'"

        # Check if already exists
        if profile_file.exists():
            with open(profile_file, 'r') as f:
                content = f.read()
                if 'CLAUDE_SESSION_KEY' in content:
                    print(f"⚠️  CLAUDE_SESSION_KEY already exists in {profile_file}")
                    return

        # Append to profile
        with open(profile_file, 'a') as f:
            f.write(f"\n# Claude session key for aii\n{export_line}\n")

        print(f"✅ Token saved to {profile_file}")
        print(f"🔄 Run 'source {profile_file}' or restart your terminal to use it")

    except Exception as e:
        print(f"❌ Could not save to profile: {e}")


if __name__ == "__main__":
    main()
