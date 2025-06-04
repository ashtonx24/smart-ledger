# main.py

from utils.db_setup import initialize_database
from ui.tkinter_ui import launch_entry_window
from utils.config import DB_PATH

def main():
    print("Smart Ledger is booting up...")
    
    # Step 1: Initialize the database
    initialize_database(DB_PATH)
    print("Database ready.")

    # Step 2: Launch the UI
    launch_entry_window()
    print("UI launched. You can now add transactions.")

if __name__ == "__main__":
    main()