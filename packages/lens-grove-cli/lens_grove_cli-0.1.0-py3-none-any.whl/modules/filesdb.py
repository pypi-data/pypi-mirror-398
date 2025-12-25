from modules import db
import datetime

def add_file_to_db(name: str, storage_key: str, chain: str, owner_type: str | None = None, owner_addr: str | None = None):
    """
    Saves a successfully uploaded file's metadata to the local database.
    Now includes 'chain' (testnet/mainnet) for future ACL redefinition.
    """
    config = db.get_config()
    
    # 1. Handle name collisions
    all_names = [f['name'] for f in config.get('files', [])]
    original_name = name
    counter = 1
    while name in all_names:
        name = f"{original_name}-{counter}"
        counter += 1

    # 2. Build the entry
    new_file_data = {
        "name": name,
        "key": storage_key,
        "chain": chain, # 'testnet' or 'mainnet'
        "date_added": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    # 3. Only add ownership if provided
    if owner_type:
        new_file_data["owner_type"] = owner_type
    if owner_addr:
        new_file_data["owner_addr"] = owner_addr

    config['files'].append(new_file_data)
    db.save_config(config)
    
    print(f"File metadata saved locally as '{name}'.")

def list_files():
    config = db.get_config()
    files = config.get('files', [])

    if not files:
        print("No known files in the local database.")
        return

    # Adjusted header to include Network
    print(f"{'#':<3} {'Name':<18} {'Key':<15} {'Network':<10} {'Owner':<15}")
    print("-" * 75)
    
    for i, f in enumerate(files, start=1):
        short_key = f"{f['key'][:6]}...{f['key'][-4:]}"
        network = f.get('chain', 'testnet') # Default to testnet if missing
        
        if f.get('owner_addr'):
            addr = f['owner_addr']
            owner_display = f"{addr[:6]}...{addr[-4:]}"
        else:
            owner_display = "Immutable"
        
        print(f"{i:<3} {f['name']:<18} {short_key:<15} {network:<10} {owner_display:<15}")

def get_file(name: str):
    config = db.get_config()
    
    for f in config.get('files', []):
        if f['name'].lower() == name.lower():
            print("--- File Metadata ---")
            print(f"Name:         {f['name']}")
            print(f"Storage Key:  {f['key']}")
            print(f"Network:      {f.get('chain', 'testnet').upper()}")
            print(f"Uploaded On:  {f.get('date_added', 'Unknown')}")
            
            if f.get('owner_type'):
                print(f"Owner Type:   {f['owner_type']}")
            if f.get('owner_addr'):
                print(f"Owner Addr:   {f['owner_addr']}")
            else:
                print("Permissions:  Immutable (No Owner)")
            return f
            
    print(f"Could not find a file named '{name}' in the local database.")
    return None

def get_key_for_file(identifier: str):
    """Returns the storage key if found by name or by the key itself."""
    config = db.get_config()
    
    for f in config.get('files', []):
        # Allow searching by friendly name OR the actual key
        if f['name'].lower() == identifier.lower() or f['key'] == identifier:
            return f['key']
        
    return None

def delete_file_from_db(identifier: str):
    """
    Removes a file's metadata from the local database.
    Can be identified by name or by the storage key.
    """
    config = db.get_config()
    files = config.get('files', [])
    
    initial_count = len(files)
    
    # Filter out the file that matches either the name or the key
    config['files'] = [
        f for f in files 
        if f['name'].lower() != identifier.lower() and f['key'] != identifier
    ]
    
    if len(config['files']) < initial_count:
        db.save_config(config)
        print(f"Metadata for '{identifier}' removed from local database.")
        return True
    else:
        print(f"Warning: No local metadata found for '{identifier}'.")
        return False