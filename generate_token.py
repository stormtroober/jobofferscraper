import os
import sys

# Ensure the current directory is in the path so we can import utils
sys.path.append(os.getcwd())

from utils.sheet_manager import SheetManager

TOKEN_FILE = "token.json"

def main():
    print("--- Google API Token Regenerator ---")
    
    if os.path.exists(TOKEN_FILE):
        print(f"Removing existing '{TOKEN_FILE}' to force re-authentication...")
        os.remove(TOKEN_FILE)
    else:
        print(f"'{TOKEN_FILE}' not found. Proceeding with generation...")

    print("\nInitializing SheetManager to trigger OAuth flow...")
    print("A browser window will open shortly. Please log in with your Google account.")
    print("Make sure to approve the permissions.")
    
    try:
        # Initializing SheetManager triggers _authenticate()
        SheetManager() 
        
        if os.path.exists(TOKEN_FILE):
            print(f"\nSUCCESS: New '{TOKEN_FILE}' has been generated!")
        else:
            print(f"\nWARNING: Authentication finished but '{TOKEN_FILE}' was not found.")
            
    except Exception as e:
        print(f"\nERROR during authentication: {e}")
        print("Please ensure 'credentials.json' is present and valid.")

if __name__ == "__main__":
    main()
