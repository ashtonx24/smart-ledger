# main.py

from utils.db_setup import initialize_database
from ui.tkinter_ui import launch_ui
from utils.config import DB_PATH

def main():
    print("Smart Ledger is booting up...")
    
    # Step 1: Initialize the database
    initialize_database(DB_PATH)
    print("Database ready.")

    # Step 2: Launch the UI
    launch_ui()

if __name__ == "__main__":
    main()