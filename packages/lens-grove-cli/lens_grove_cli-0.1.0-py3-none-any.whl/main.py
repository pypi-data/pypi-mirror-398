import argparse

def main():
    parser = argparse.ArgumentParser(
        prog="lens-grove-cli", 
        description="A command line interface for the Lens Grove storage network"
    )
    
    # 1. Added 'dest' so you can identify which sub-command was called in your code
    # 2. Added 'required=True' (optional) to force a sub-command selection
    subparsers = parser.add_subparsers(dest="command")
    
    # --- Wallets ---
    wallet_parser = subparsers.add_parser("wallet", help="Manage wallets held by the local database")
    wallet_subparsers = wallet_parser.add_subparsers(dest="wallet_action", help="Wallet actions")
    
    wallet_new = wallet_subparsers.add_parser("new", help="Create a new wallet")
    wallet_new.add_argument("--name", type=str, help="Optional name for the wallet")
    
    wallet_import = wallet_subparsers.add_parser("import", help="Import a wallet using its private key")
    
    wallet_remove = wallet_subparsers.add_parser("remove", help="Delete a wallet from this device's database")
    wallet_remove.add_argument("target", metavar="[wallet friendly name or 0x12AB...]", help="The friendly name or wallet address to delete")
    
    wallet_get = wallet_subparsers.add_parser("get", help="Get information for a wallet by its friendly name.")
    wallet_get.add_argument("name", metavar="[wallet friendly name]", help="The name of the wallet to get information for.")
    
    wallet_list = wallet_subparsers.add_parser("list", help="List wallets held by the local database")
    # ---------------
    
    # --- Lens Accounts ---
    lens_parser = subparsers.add_parser("lensacc", help="Manage known Lens Accounts")
    lens_subparsers = lens_parser.add_subparsers(dest="lens_action", help="Lens Account actions")
    
    lens_add = lens_subparsers.add_parser("add", help="Store a Lens Account address for future use")
    lens_add.add_argument("address", metavar="0x12AB...", help="The Lens Account address to store")
    lens_add.add_argument("-n", "--name", help="Optional friendly name for this Lens Account in the local database")
    
    lens_list = lens_subparsers.add_parser("list", help="List known Lens Accounts")
    
    lens_remove = lens_subparsers.add_parser("remove", help="Forget a known Lens Account")
    lens_remove.add_argument("target", metavar="[lensacc friendly name or 0x12AB...]")
    # ---------------------

    # --- Known Files ---
    files_parser = subparsers.add_parser("files", help="Manage known uploaded files")
    files_subparsers = files_parser.add_subparsers(dest="files_action", help="Known file actions")
    
    files_recall = files_subparsers.add_parser("recall", help="Recall a known file by its friendly name or key")
    files_recall.add_argument("name", metavar="[file friendly name or 12AB...]")
    
    files_list = files_subparsers.add_parser("list", help="List all known files")
    
    files_remove = files_subparsers.add_parser("remove", help="Forget a known file")
    files_remove.add_argument("name", metavar="[file friendly name]", help="The friendly name of the file you want to forget")
    # -------------------

    # upload command
    upload_parser = subparsers.add_parser("upload", help="Upload files to Grove. Interactive input is used by default for option selection.")
    upload_parser.add_argument("file", help="The file name to upload")
    upload_parser.add_argument("-a", "--acl-mode", help="Specify an ACL mode (default immutable)", choices=["immutable", "wallet", "lens-account"])
    upload_parser.add_argument("-i", "--identity", help="The wallet or Lens Account that will own this file, for relevant ACL modes.", metavar="[wallet/lensacc friendly name or 0x12AB...]")
    upload_parser.add_argument("-c", "--chain", help="Specify a chain (default testnet)", choices=["mainnet", "testnet"])
    upload_parser.add_argument("-n", "--name", help="A friendly name for the file in this machine's database")
    
    # edit command
    edit_parser = subparsers.add_parser("edit", help="Replace the file under a storage key. The key must have been made with a non-immutable ACL.")
    edit_parser.add_argument("key", metavar="[file friendly name or 12AB...]", help="The storage key (or local friendly name) of the file to replace.")
    edit_parser.add_argument("identity", metavar="[wallet friendly name or 0x12AB]", help="The wallet that will be used to sign for the edit. This wallet must have authority over the key (either by direct ownership or Lens Account relationship).")
    edit_parser.add_argument("file", metavar="/path/to/replacement/file", help="The path to the file that will replace the key's current file.")
    
    # delete command
    delete_parser = subparsers.add_parser("delete", help="Delete the storage key. The key must have been made with a non-immutable ACL.")
    delete_parser.add_argument("key", metavar="[file friendly name or 12AB...]", help="The key that you want to delete.")
    delete_parser.add_argument("identity", metavar="[wallet friendly name or 0x12AB...]", help="The wallet that will be used to sign for the deletion. This wallet must have authority over the key (either by direct ownership or Lens Account relationship).")

    # Parse and test
    args = parser.parse_args()
    
    # Handle Wallets
    if args.command == "wallet":
        from modules import wallet
        if args.wallet_action == "new":
            wallet.create_new_wallet(args.name)
        elif args.wallet_action == "import":
            wallet.import_wallet()
        elif args.wallet_action == "list":
            wallet.list_wallets()
        elif args.wallet_action == "get":
            wallet.get_wallet(args.name)
        elif args.wallet_action == "remove":
            wallet.delete_wallet(args.target)
        else:
            wallet_parser.print_help()

    # Handle Lens Accounts
    elif args.command == "lensacc":
        from modules import lens
        if args.lens_action == "add":
            lens.add_lens_account(args.address, args.name or None)
        elif args.lens_action == "list":
            lens.list_lens_accounts()
        elif args.lens_action == "remove":
            lens.remove_lens_account(args.target)
        else:
            lens_parser.print_help()

    # Handle Local File Database (Known Files)
    elif args.command == "files":
        from modules import filesdb
        if args.files_action == "list":
            filesdb.list_files()
        elif args.files_action == "recall":
            # You'll need to add a recall function to filesdb 
            # or just call get_file to show the info
            filesdb.get_file(args.name)
        elif args.files_action == "remove":
            filesdb.delete_file_from_db(args.name)
        else:
            files_parser.print_help()

    # Handle Network Operations (FileOps)
    elif args.command == "upload":
        from modules import fileops
        fileops.upload_file(
            path=args.file,
            aclmode=args.acl_mode or "immutable",
            aclidentity=args.identity,
            chain=args.chain or "testnet",
            name=args.name
        )

    elif args.command == "edit":
        from modules import fileops
        fileops.edit_file(
            fileid=args.key,
            ownerid=args.identity,
            path=args.file
        )

    elif args.command == "delete":
        from modules import fileops
        fileops.delete_file(
            fileid=args.key,
            ownerid=args.identity
        )

    else:
        parser.print_help()

if __name__ == "__main__":
    main()