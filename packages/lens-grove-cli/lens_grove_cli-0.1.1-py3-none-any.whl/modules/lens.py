from modules import db
import randomname

def add_lens_account(address: str, name: str | None = None):
    """Stores a Lens Account address with an optional friendly name."""
    config = db.get_config()
    
    # Check if address already exists
    for existing in config.get('lens_accs', []):
        if existing['addr'].lower() == address.lower():
            print(f"Error: This address is already saved as '{existing['name']}'.")
            return

    # Handle name generation if blank
    if not name:
        name = f"lens-{randomname.get_name()}"
    
    # Ensure name uniqueness
    all_names = [l['name'] for l in config.get('lens_accs', [])]
    while name in all_names:
        name = f"lens-{randomname.get_name()}"

    new_lens_data = {
        "name": name,
        "addr": address
    }

    config['lens_accs'].append(new_lens_data)
    db.save_config(config)
    
    print(f"Lens Account added!")
    print(f"Name: {name}")
    print(f"Address: {address}")

def list_lens_accounts():
    config = db.get_config()
    accounts = config.get('lens_accs', [])

    if not accounts:
        print("No Lens Accounts found.")
        return

    print("Saved Lens Accounts:")
    for i, acc in enumerate(accounts, start=1):
        # Using the same truncation logic for consistency
        short_addr = f"{acc['addr'][:6]}...{acc['addr'][-4:]}"
        print(f"{i}: {acc['name']} ({short_addr})")

def remove_lens_account(identifier: str):
    # Use the resolver you already built!
    resolved_addr = db.resolve_identity("lens", identifier)
    
    if not resolved_addr:
        print(f"Could not find a Lens Account matching '{identifier}'.")
        return

    config = db.get_config()
    # Filter out the matching address
    config['lens_accs'] = [l for l in config['lens_accs'] if l['addr'] != resolved_addr]
    
    db.save_config(config)
    print(f"Lens Account '{identifier}' removed from local database.")
    
def get_lens_account(name: str):
    config = db.get_config()
    
    found = False
    
    # Looking through the lens_accs list
    for acc in config.get('lens_accs', []):
        if acc['name'] == name:
            print("Lens Account found!")
            print(f"Name: {acc['name']}")
            print(f"Address: {acc['addr']}")
            found = True
            break
    
    if not found:
        print("We couldn't find that Lens Account. Try \"grove-cli lensacc list\".")