import json
import getpass
import os
from .crypto import store_password_meta
from .db import init_db

def main():
    # Prompt for a new password (twice for confirmation)
    while True:
        pwd1 = getpass.getpass('Set a password for the app: ')
        pwd2 = getpass.getpass('Confirm password: ')
        if pwd1 != pwd2:
            print('Passwords do not match. Try again.')
            continue
        if not pwd1:
            print('Password cannot be empty.')
            continue
        break
    meta = store_password_meta(pwd1)
    # Save meta JSON next to the db (in src folder)
    meta_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app_meta.json')
    with open(meta_path, 'w') as f:
        json.dump(meta, f, indent=2)
    # Initialize DB tables
    init_db()
    print('Application initialized. Database and auth metadata created.')

if __name__ == '__main__':
    main()
