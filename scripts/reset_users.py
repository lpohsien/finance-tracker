import sys
import os

# Add the project root to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from api.db import SessionLocal
from api.models import User

def reset_users():
    db = SessionLocal()
    try:
        # Fetch all users to ensure ORM cascades are triggered locally
        users = db.query(User).all()
        count = len(users)
        
        if count == 0:
            print("No users found to delete.")
            return

        print(f"Found {count} users. Deleting...")
        for user in users:
            print(f"Deleting user: {user.username} (ID: {user.id})")
            db.delete(user)
        
        db.commit()
        print(f"Successfully deleted {count} users and their associated data (transactions, configurations).")
    except Exception as e:
        print(f"Error deleting users: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("WARNING: This will delete ALL users and their data from the database.")
    confirmation = input("Are you sure you want to proceed? (y/N): ")
    if confirmation.lower() == 'y':
        reset_users()
    else:
        print("Operation cancelled.")
