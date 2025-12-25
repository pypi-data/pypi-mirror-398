# modules/wallet.py
from web3 import Web3
import randomname
from modules import db
import getpass

def create_new_wallet(name: str = ""):
    w3 = Web3()
    
    # 1. Handle name generation
    if not name:
        name = randomname.get_name()
    
    # 2. Generate the keys
    account = w3.eth.account.create()
    
    # 3. Load and update DB
    config = db.get_config()
    
    # Check for collisions
    for existing in config['wallets']:
        if existing['name'] == name:
            # Simple fix: append a few random digits or tell the user
            name = randomname.get_name()
    
    new_wallet_data = {
        "name": name,
        "addr": account.address,
        "key": w3.to_hex(account.key)
    }
    
    config['wallets'].append(new_wallet_data)
    db.save_config(config)
    
    print("New wallet created!")
    print(f"Name: {name}")
    print(f"Address: {account.address}")
    
def import_wallet():
    print("WARNING: It's not recommended to use an important wallet here since private keys are stored in plaintext!")
    print("If you want to set a Lens Account as a storage key's owner, you can add a CLI wallet's address as a Manager (without token access) on said Lens Account.")
    print("If the CLI wallet is ever lost or compromised, it's easy to revoke a Manager's access.")
    print()
    
    answer = input("Do you want to continue? (y/n) ")
    if not answer.lower() == "y": return
    
    key = getpass.getpass("Paste the wallet's private key here (input will be masked): ", echo_char="*")
    name = input("Give the wallet a name (leave blank for a random name): ")
    
    if not name: name = randomname.get_name()
    
    w3 = Web3()
    
    account = w3.eth.account.from_key(key)
    config = db.get_config()

    # 1. Check if the address is already imported
    for existing in config['wallets']:
        if existing['addr'].lower() == account.address.lower():
            print(f"Error: This wallet is already imported as '{existing['name']}'.")
            return

    # 2. Robust Name Collision Check
    # Ensure the name is unique, even if we have to generate a few random ones
    all_names = [w['name'] for w in config['wallets']]
    while name in all_names:
        name = randomname.get_name()
    
    new_wallet_data = {
        "name": name,
        "addr": account.address,
        "key": w3.to_hex(account.key)
    }
    
    config['wallets'].append(new_wallet_data)
    db.save_config(config)
    
    print("Wallet imported!")
    print(f"Name: {name}")
    print(f"Address: {account.address}")

def list_wallets():
    config = db.get_config()
    wallets = config.get('wallets', [])

    if not wallets:
        print("No wallets found.")
        return

    print("Stored Wallets:")
    for i, wallet in enumerate(wallets, start=1):
        name = wallet.get('name', 'Unnamed')
        addr = wallet.get('addr', '0x000...')
        
        # Shorten address to 0x12AB...34CD
        # First 6 chars + ... + last 4 chars
        short_addr = f"{addr[:6]}...{addr[-4:]}"
        
        print(f"{i}: {name} ({short_addr})")
        
def get_wallet(name:str):
    config = db.get_config()
    
    found = False
    
    for wallet in config['wallets']:
        if wallet['name'] == name:
            print("Wallet found!")
            print(f"Name: {wallet['name']}")
            print(f"Address: {wallet['addr']}")
            found = True
            break
    
    if not found:
        print("We couldn't find that wallet. Try \"grove-cli wallet list\".")
        
def delete_wallet(identifier:str):
    resolved_id = db.resolve_identity("wallet", identifier)
    
    if resolved_id:
        print("A wallet was found in the database with that name or address.")
        print("Deleting a wallet is a potentially destructive action.")
        print("MAKE SURE THE PRIVATE KEY IS BACKED UP SOMEWHERE IF YOU THINK YOU MIGHT NEED THIS WALLET AGAIN!")
        print()
        if not input("Really delete the wallet? (y/n) ").lower() == "y": return
        
        config = db.get_config()
        for i, wallet in enumerate(config['wallets']):
            if wallet['addr'] == resolved_id['addr']:
                config['wallets'].pop(i)
                break
        
        db.save_config(config)
        
        print("Wallet deleted.")