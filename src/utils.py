from dotenv import set_key
from src.config import ALLOWED_USER_IDS, BASE_DIR

def add_allowed_user(user_id: int) -> bool:
    """
    Adds a user ID to the allowed list in memory and persists it to the .env file.
    """
    if user_id in ALLOWED_USER_IDS:
        return False
    
    # Update in-memory list
    ALLOWED_USER_IDS.append(user_id)
    
    # Update .env file
    env_path = BASE_DIR / ".env"
    
    # Reconstruct the string
    new_value = ",".join(map(str, ALLOWED_USER_IDS))
    
    # Update .env using dotenv's set_key which handles quoting/parsing safely
    # Note: set_key creates the file if it doesn't exist, but we expect it to exist.
    set_key(str(env_path), "ALLOWED_USER_IDS", new_value)
    
    return True
