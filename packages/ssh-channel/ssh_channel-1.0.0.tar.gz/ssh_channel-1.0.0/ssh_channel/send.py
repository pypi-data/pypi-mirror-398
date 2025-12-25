#!/usr/bin/env python3
"""
ssh-channel-send
Send named messages via OSC 52 escape sequences
"""

import sys
import base64
import argparse

def send_named_message(name, data):
    """Send named message via OSC 52"""
    # Format: name:data
    message = f"{name}:{data}"
    
    # Encode as base64 for OSC 52
    b64_data = base64.b64encode(message.encode('utf-8')).decode('ascii')
    
    # Send OSC 52 sequence: ESC ] 52 ; c ; base64_data BEL
    osc_sequence = f"\033]52;c;{b64_data}\007"
    sys.stdout.write(osc_sequence)
    sys.stdout.flush()

def main():
    parser = argparse.ArgumentParser(description='Send named messages via OSC 52')
    parser.add_argument('name', help='Message name (notification, log, clipboard, etc.)')
    parser.add_argument('data', nargs='*', help='Message data (or read from stdin)')
    
    args = parser.parse_args()
    
    # Get data from arguments or stdin
    if args.data:
        data = ' '.join(args.data)
    else:
        data = sys.stdin.read().strip()
    
    if not data:
        print("No data to send", file=sys.stderr)
        sys.exit(1)
    
    # Send named message
    send_named_message(args.name, data)
    
    print(f"Sent '{args.name}' message: {data[:50]}{'...' if len(data) > 50 else ''}", file=sys.stderr)

if __name__ == '__main__':
    main()