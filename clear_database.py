#!/usr/bin/env python3
import os
import sys
import sqlite3
from pathlib import Path

DB_PATH = 'conversation_state.db'

def clear_all():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"✅ Deleted {DB_PATH}")
        print("The database will be recreated when you restart the server.")
    else:
        print(f"ℹ️  {DB_PATH} does not exist. Nothing to clear.")

def clear_messages_only():
    if not os.path.exists(DB_PATH):
        print(f"ℹ️  {DB_PATH} does not exist. Nothing to clear.")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM messages")
    conn.commit()
    
    count = cursor.rowcount
    conn.close()
    
    print(f"✅ Deleted {count} messages from the database")
    print("Processing state (last processed row ID) has been preserved.")

def reset_processing_state():
    if not os.path.exists(DB_PATH):
        print(f"ℹ️  {DB_PATH} does not exist. Nothing to reset.")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("UPDATE processing_state SET last_processed_row_id = 0 WHERE id = 1")
    conn.commit()
    conn.close()
    
    print("✅ Reset processing state to 0")
    print("⚠️  WARNING: This will cause the server to reprocess ALL historical messages!")
    print("Make sure this is what you want before restarting the server.")

def show_stats():
    if not os.path.exists(DB_PATH):
        print(f"ℹ️  {DB_PATH} does not exist.")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM messages")
    total_messages = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(DISTINCT sender_id) FROM messages")
    unique_senders = cursor.fetchone()[0]
    
    cursor.execute("SELECT last_processed_row_id FROM processing_state WHERE id = 1")
    last_processed = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM messages WHERE is_from_user = 1")
    user_messages = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM messages WHERE is_from_user = 0")
    ai_messages = cursor.fetchone()[0]
    
    conn.close()
    
    print("\n📊 Database Statistics:")
    print(f"   Total messages: {total_messages}")
    print(f"   User messages: {user_messages}")
    print(f"   AI responses: {ai_messages}")
    print(f"   Unique conversations: {unique_senders}")
    print(f"   Last processed Messages DB row ID: {last_processed}")
    print()

def show_menu():
    print("\n" + "="*50)
    print("  Database Management Utility")
    print("="*50)
    print("\n1. Show database statistics")
    print("2. Clear all messages (keep processing state)")
    print("3. Reset processing state to 0")
    print("4. Delete entire database")
    print("5. Exit")
    print()

def main():
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        if command == 'clear-all' or command == '--clear-all':
            clear_all()
        elif command == 'clear-messages' or command == '--clear-messages':
            clear_messages_only()
        elif command == 'reset-state' or command == '--reset-state':
            reset_processing_state()
        elif command == 'stats' or command == '--stats':
            show_stats()
        else:
            print("Usage:")
            print("  python3 clear_database.py                  # Interactive menu")
            print("  python3 clear_database.py stats            # Show statistics")
            print("  python3 clear_database.py clear-all        # Delete entire database")
            print("  python3 clear_database.py clear-messages   # Clear messages only")
            print("  python3 clear_database.py reset-state      # Reset processing state")
        return
    
    while True:
        show_menu()
        choice = input("Enter your choice (1-5): ").strip()
        
        if choice == '1':
            show_stats()
        elif choice == '2':
            confirm = input("Are you sure you want to clear all messages? (yes/no): ").strip().lower()
            if confirm == 'yes':
                clear_messages_only()
            else:
                print("Cancelled.")
        elif choice == '3':
            confirm = input("Are you sure you want to reset processing state? (yes/no): ").strip().lower()
            if confirm == 'yes':
                reset_processing_state()
            else:
                print("Cancelled.")
        elif choice == '4':
            confirm = input("Are you sure you want to DELETE the entire database? (yes/no): ").strip().lower()
            if confirm == 'yes':
                clear_all()
            else:
                print("Cancelled.")
        elif choice == '5':
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please enter 1-5.")
        
        input("\nPress Enter to continue...")

if __name__ == '__main__':
    main()

