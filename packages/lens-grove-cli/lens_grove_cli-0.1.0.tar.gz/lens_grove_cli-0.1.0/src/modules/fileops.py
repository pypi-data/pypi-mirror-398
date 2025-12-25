from web3 import Web3
from pathlib import Path
from modules import db
from modules import filesdb
import requests
import json
import os
import mimetypes

def upload_file(path:str, aclmode:str="immutable", aclidentity:str|None=None, chain:str="testnet", name:str|None=None):
    fileToUpload = Path(path).expanduser()
    if not fileToUpload.exists():
        print(f"Error: File '{path}' not found.")
        return

    # Pre-stage 1: Get a Chain ID
    chainId = 37111 if chain == "testnet" else 232
    
    # Pre-stage 2: Define the ACL
    acl = {"chain_id": chainId}
    owner_addr = None

    if aclmode == "immutable":
        acl["template"] = "immutable"
    
    elif aclmode == "wallet":
        acl["template"] = "wallet_address"
        if Web3().is_address(aclidentity):
            owner_addr = aclidentity
        else:
            res = db.resolve_identity("wallet", aclidentity)
            if res: owner_addr = res['addr']
        
        if not owner_addr:
            print("Error: Could not resolve wallet identity.")
            return
        acl["wallet_address"] = owner_addr

    elif aclmode == "lens-account":
        # Note: Check Grove docs if the template name is 'lens_account' vs 'wallet_address'
        acl["template"] = "lens_account" 
        if Web3().is_address(aclidentity):
            owner_addr = aclidentity
        else:
            owner_addr = db.resolve_identity("lens", aclidentity)
        
        if not owner_addr:
            print("Error: Could not resolve Lens identity.")
            return
        acl["lens_account"] = owner_addr
                
    # Stage 1: Get a Storage Key
    try:
        newkey_response = requests.post("https://api.grove.storage/link/new")
        newkey_response.raise_for_status()
        storage_key = newkey_response.json()[0]['storage_key']
    except (requests.RequestException, KeyError, IndexError) as e:
        print(f"Failed to initialize upload key: {e}")
        return
    
    # Stage 2: Start file upload
    with open(fileToUpload, "rb") as f:
        files = {
            storage_key: (
                os.path.basename(fileToUpload), 
                f, 
                mimetypes.guess_type(fileToUpload)[0] or "application/octet-stream"
            ),
            "lens-acl.json": (
                "acl.json", 
                json.dumps(acl), 
                "application/json"
            )
        }
        
        try:
            upload_url = f"https://api.grove.storage/{storage_key}"
            response = requests.post(upload_url, files=files)
            response.raise_for_status()
            
            data = response.json()
            print("\nSuccess! Your file was uploaded.")
            if not chainId==232:
                print("WARNING: Your file was uploaded using testnet retention policy and may not be permanent!")
            print(f"Gateway URL: {data[0].get('gateway_url')}")
        except requests.exceptions.RequestException as e:
            print(f"Upload failed: {e}")
            return
        
        filesdb.add_file_to_db(name if name else fileToUpload.parts[-1], storage_key, chain, None if aclmode=="immutable" else aclmode, owner_addr)
        
def edit_file(fileid:str, ownerid:str, path:str):
    fileToUpload = Path(path).expanduser()
    w3 = Web3()
    
    # Pre-Stage 1: Resolve Wallet
    owner_res = db.resolve_identity("wallet", ownerid)
    if not owner_res:
        print(f"Error: Wallet '{ownerid}' not found in local database.")
        return
    acc = w3.eth.account.from_key(owner_res['key'])
    
    # Pre-Stage 2: Get file metadata
    file_key = filesdb.get_key_for_file(fileid)
    if not file_key:
        print("Could not find the file's metadata locally.")
        return
    
    # Find the specific entry to get the ACL data
    file_data = None
    for f in db.get_config()['files']:
        if f['key'] == file_key:
            file_data = f
            break
            
    # Pre-Stage 3: Redefine ACL
    acl = {"chain_id": 232 if file_data.get('chain') == "mainnet" else 37111}
    
    # Note: Using underscores to match your filesdb module
    o_type = file_data.get('owner_type')
    o_addr = file_data.get('owner_addr')

    if not o_type:
        print("This file is immutable and cannot be edited.")
        return
    
    if o_type == "wallet":
        acl['template'] = "wallet_address"
        acl['wallet_address'] = o_addr
    elif o_type == "lens-account":
        acl['template'] = "lens_account"
        acl['lens_account'] = o_addr
            
    # Stage 1: Get a challenge
    challenge_request_input = {"storage_key": file_key, "action": "edit"}
    try:
        challenge_req = requests.post("https://api.grove.storage/challenge/new", json=challenge_request_input)
        challenge_req.raise_for_status()
        challenge_data = challenge_req.json()
    except Exception as e:
        print(f"Could not get a challenge: {e}")
        return
        
    # Stage 2 & 3: Sign and get CID
    from eth_account.messages import encode_defunct
    encoded_message = encode_defunct(text=challenge_data['message'])
    signed_message = w3.eth.account.sign_message(encoded_message, acc.key)
    challenge_data['signature'] = signed_message.signature.to_0x_hex()
    
    try:
        cid_req = requests.post("https://api.grove.storage/challenge/sign", json=challenge_data)
        cid_req.raise_for_status()
        challenge_cid = cid_req.json()['challenge_cid']
    except Exception as e:
        print(f"Challenge signing failed: {e}")
        return
        
    # Stage 4: Final Upload
    with open(fileToUpload, "rb") as f:
        files = {
            file_key: (os.path.basename(fileToUpload), f, mimetypes.guess_type(path)[0] or "application/octet-stream"),
            "lens-acl.json": ("acl.json", json.dumps(acl), "application/json")
        }
        
        try:
            # Fixed: using file_key instead of storage_key
            upload_url = f"https://api.grove.storage/{file_key}"
            params = {"challenge_cid": challenge_cid, "secret_random": challenge_data['secret_random']}
            response = requests.post(upload_url, files=files, params=params)
            response.raise_for_status()
            
            print("\nSuccess! The storage key now points to the new file.")
        except requests.exceptions.RequestException as e:
            print(f"Edit failed: {e}")
            
def delete_file(fileid: str, ownerid: str):
    w3 = Web3()
    
    # 1. Resolve Identity
    owner_res = db.resolve_identity("wallet", ownerid)
    if not owner_res:
        print(f"Error: Wallet '{ownerid}' not found.")
        return
    acc = w3.eth.account.from_key(owner_res['key'])
    
    # 2. Resolve File Key
    file_key = filesdb.get_key_for_file(fileid)
    if not file_key:
        print("Could not find file metadata locally.")
        return

    # Stage 1: Get Challenge
    challenge_input = {
        "storage_key": file_key,
        "action": "delete"  # As specified in Grove docs
    }
    
    try:
        c_req = requests.post("https://api.grove.storage/challenge/new", json=challenge_input)
        c_req.raise_for_status()
        challenge_data = c_req.json()
    except Exception as e:
        print(f"Challenge request failed: {e}")
        return

    # Stage 2: Sign Challenge
    from eth_account.messages import encode_defunct
    encoded = encode_defunct(text=challenge_data['message'])
    signed = w3.eth.account.sign_message(encoded, acc.key)
    challenge_data['signature'] = signed.signature.to_0x_hex()

    # Stage 3: Get Challenge CID
    try:
        cid_req = requests.post("https://api.grove.storage/challenge/sign", json=challenge_data)
        cid_req.raise_for_status()
        challenge_cid = cid_req.json()['challenge_cid']
    except Exception as e:
        print(f"Challenge signing failed: {e}")
        return

    # Stage 4: Send DELETE request
    try:
        delete_url = f"https://api.grove.storage/{file_key}"
        params = {
            "challenge_cid": challenge_cid, 
            "secret_random": challenge_data['secret_random']
        }
        
        # Note: No 'files' or 'json' body needed for a standard Grove delete
        response = requests.delete(delete_url, params=params)
        response.raise_for_status()
        
        print(f"\nSuccess! File {file_key} has been deleted from the network.")
        
        # Clean up local database
        filesdb.delete_file_from_db(fileid)
        
    except requests.exceptions.RequestException as e:
        print(f"Delete request failed: {e}")