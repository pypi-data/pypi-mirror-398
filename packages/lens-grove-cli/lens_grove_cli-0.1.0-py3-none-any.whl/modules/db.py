import yaml
import os
from pathlib import Path

# Using Path makes cross-platform (Windows/Mac/Linux) path handling much easier
DB_PATH = Path("~/.littlebitstudios/grove_cli/database.yaml").expanduser()

def ensure_db_exists():
    """Creates the directory and database file with a default structure if they don't exist."""
    if not DB_PATH.parent.exists():
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    if not DB_PATH.exists():
        default_schema = {
            "wallets": [],
            "lens_accs": [],
            "files": []
        }
        save_config(default_schema)

def save_config(config: dict):
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    temp_file = DB_PATH.with_suffix(".tmp")
    try:
        with open(temp_file, "w") as f:
            yaml.safe_dump(config, f, sort_keys=False)
        
        # This operation is "atomic" on most systems—it either succeeds 
        # completely or doesn't happen at all.
        os.replace(temp_file, DB_PATH)
    except Exception as e:
        if temp_file.exists():
            os.remove(temp_file)
        raise e

def get_config() -> dict:
    ensure_db_exists()
    try:
        with open(DB_PATH, "r") as f:
            data = yaml.safe_load(f)
            # Handle cases where the file exists but is totally empty
            return data if data is not None else {}
    except Exception as e:
        print(f"Error loading database: {e}")
        return {"wallets": [], "lens_accs": [], "files": []}
    
# modules/db.py

def resolve_identity(mode:str, identifier:str) -> dict | str | None:
    """
    Finds a wallet key and address from an identifier 
    (which could be a friendly name or a raw address).
    """
    config = get_config()
    
    # Check Wallets
    if mode == "wallet":
        for w in config.get('wallets', []):
            if identifier.lower() in [w['name'].lower(), w['addr'].lower()]:
                return w # Returns the dict with 'key' and 'addr'
    if mode == "lens":
        for l in config.get('lens_accs', []):
            if identifier.lower() in [l['name'].lower(), l['addr'].lower()]:
                return l['addr']

    return None