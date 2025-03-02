#!/usr/bin/env python3
import argparse
import sys
from app import send_message, load_phone_numbers, logger

def main():
    """Command-line tool to send test messages."""
    parser = argparse.ArgumentParser(description="Send a test SMS message")
    
    # Add subparsers for different commands
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Add a command to send a message to a specific number
    send_parser = subparsers.add_parser("send", help="Send a message to a specific number")
    send_parser.add_argument("number", help="Phone number to send the message to")
    send_parser.add_argument("message", help="Message content")
    
    # Add a command to send a test message to all numbers
    send_all_parser = subparsers.add_parser("send-all", help="Send a test message to all non-opted-out numbers")
    send_all_parser.add_argument("message", help="Message content")
    
    # Parse the arguments
    args = parser.parse_args()
    
    # If no command is provided, show help
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Execute the appropriate command
    if args.command == "send":
        # Send a message to a specific number
        success = send_message(args.number, args.message)
        if success:
            print(f"Message sent successfully to {args.number}")
        else:
            print(f"Failed to send message to {args.number}")
            sys.exit(1)
    
    elif args.command == "send-all":
        # Send a message to all non-opted-out numbers
        phone_numbers = load_phone_numbers()
        sent_count = 0
        skipped_count = 0
        
        for number, data in phone_numbers.items():
            if data.get("opted_out", False):
                print(f"Skipping {number} (opted out)")
                skipped_count += 1
                continue
                
            if send_message(number, args.message):
                print(f"Message sent successfully to {number}")
                sent_count += 1
            else:
                print(f"Failed to send message to {number}")
        
        print(f"Summary: {sent_count} messages sent, {skipped_count} numbers skipped")
    
if __name__ == "__main__":
    main() 