import os
import sys

# Ensure src is in path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.integration.calendar_connector import CalendarConnector

def main():
    print("=== Google Calendar Authentication ===")
    print("This script will open your browser to log in to Google.")
    print("Ensure 'credentials.json' is in the project root.")
    
    if not os.path.exists("credentials.json"):
        print("ERROR: credentials.json not found!")
        return

    try:
        # This triggers the auth flow
        connector = CalendarConnector()
        if connector.service:
            print("\nSUCCESS! Authenticated successfully.")
            print("token.json has been created.")
        else:
            print("\nFAILED. Could not authenticate.")
    except Exception as e:
        print(f"\nERROR: {e}")

if __name__ == "__main__":
    main()
