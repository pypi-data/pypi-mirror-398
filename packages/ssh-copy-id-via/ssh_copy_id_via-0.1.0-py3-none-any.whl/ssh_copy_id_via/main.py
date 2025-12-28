#!/usr/bin/env python3
"""ssh-copy-id-via - Copy SSH keys to passwordless users via another user"""

import os
import sys
import argparse
import subprocess
import tempfile
import shlex
from pathlib import Path

def copy_id_via(via_user_host, target_user, key_file=None):
    """Copy SSH key to target user via another user"""
    
    if key_file is None:
        key_file = Path.home() / ".ssh" / "id_rsa.pub"
    else:
        key_file = Path(key_file)
    
    if not key_file.exists():
        print(f"Error: Key file {key_file} not found")
        print("Generate one with: ssh-keygen -t rsa")
        sys.exit(1)
    
    # Read the public key
    with open(key_file) as f:
        public_key = f.read().strip()
    
    print(f"Copying key to {target_user} via {via_user_host}...")
    
    # Properly quote the target_user to prevent shell injection
    quoted_target_user = shlex.quote(target_user)
    quoted_public_key = shlex.quote(public_key)
    
    # Create the remote commands to set up SSH key with proper quoting
    setup_commands = f'''
set -e
sudo mkdir -p /home/{quoted_target_user}/.ssh
echo {quoted_public_key} | sudo tee /home/{quoted_target_user}/.ssh/authorized_keys > /dev/null
sudo chown -R {quoted_target_user}:{quoted_target_user} /home/{quoted_target_user}/.ssh
sudo chmod 700 /home/{quoted_target_user}/.ssh
sudo chmod 600 /home/{quoted_target_user}/.ssh/authorized_keys
echo "✓ SSH key installed for {quoted_target_user}"
    '''.strip()
    
    # Execute via SSH with pseudo-terminal
    try:
        result = subprocess.run([
            "ssh", "-t", via_user_host, setup_commands
        ], check=True)
        
        # Extract hostname for testing
        if '@' in via_user_host:
            hostname = via_user_host.split('@')[1]
        else:
            hostname = via_user_host
            
        print(f"✓ Key copied successfully!")
        print(f"Test with: ssh {target_user}@{hostname}")
        
    except subprocess.CalledProcessError as e:
        print(f"Error: Failed to copy key via {via_user_host}")
        print("Make sure you can sudo on the remote system")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nAborted")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(
        description="Copy SSH keys to passwordless users via another user",
        epilog="Example: ssh-copy-id-via user@server git"
    )
    parser.add_argument("via", help="User@host to SSH through (must have sudo)")
    parser.add_argument("target_user", help="Target user to copy key to")
    parser.add_argument("-i", "--identity", help="SSH key file (default: ~/.ssh/id_rsa.pub)")
    
    args = parser.parse_args()
    copy_id_via(args.via, args.target_user, args.identity)

if __name__ == "__main__":
    main()