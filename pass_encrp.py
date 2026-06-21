import json
from urllib.parse import urlparse
from getpass import getpass
import random
import string
from cryptography.fernet import Fernet

FILE_NAME = "vault.json"

def load_data():
    try:
        with open(FILE_NAME, "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    
#----------------------------------------------------------------------------------------------------

def save_data(vault):
    with open(FILE_NAME, "w") as file:
        json.dump(vault, file, indent=4)

#----------------------------------------------------------------------------------------------------

def valid_url(url):
    result = urlparse(url)
    return all([result.scheme, result.netloc])   # all() returns True only if all values are truthy.

#----------------------------------------------------------------------------------------------------

def load_key():
    with open("key.key", "rb") as file:
        return file.read()

key = load_key()
cipher = Fernet(key)

#----------------------------------------------------------------------------------------------------

def add_password(vault):
    website = input("Website: ").lower()
    website_url = input("Website URL: ")

    if not valid_url(website_url):
        print("Invalid URL!")
        return
    
    if website in vault:
        print("Website already exists!")
        return
    
    username = input("Username: ")
    print("1.Enter password manually \n2.Generate Password")

    try:
        ch = int(input('Enter Choice: '))
    except ValueError:
        print('Invalid Input !')    
        return
    
    if ch == 1:
        password = getpass("Password: ")
    
    elif ch == 2:

        password = generate_password()
        print(f"\nGenerated Password: {password}")

        confirm = input("Use this password? (y/n): ").lower()
        if confirm == 'n':
            print("Operation cancelled.")
            return

    else:
        print("Invalid choice!")
        return

    encrypted_password = cipher.encrypt(password.encode()).decode()   
    
    vault[website] = {
        "username": username,
        "password": encrypted_password,
        "url":website_url
    }

    save_data(vault)
    print("Password saved successfully!")

#----------------------------------------------------------------------------------------------------

def view_password(vault):
    
    print(f"\n" + "=" *50)
    print("All Passwords".center(50))    
    print(f"=" *50)

    print(f"\n{'No':5}{'Website':<15}{'username':<25}{'password':<20}\n")

    for idx, web in enumerate(vault, 1):
        url = vault[web]["url"]
        username = vault[web]['username']

        encrypted_password = vault[web]["password"]
        password = cipher.decrypt(encrypted_password.encode()).decode()

        print(f"{idx:<5}{web:<15}{username:<25}{password:<20}")
        print(f"     URL: {url}\n")
        
    print(f"-" * 50)    

#----------------------------------------------------------------------------------------------------

def search_password(vault):
    website = input("Enter website name: ").lower()

    if website in vault:

        encrypted_password = vault[website]["password"]
        password = cipher.decrypt(encrypted_password.encode()).decode()

        print("\nWebsite: ", website)
        print("Username: ", vault[website]["username"])
        print("Password: ", password)
    else:
        print("Website not found!")

#----------------------------------------------------------------------------------------------------

def update_passwords(vault):

    view_password(vault)

    website = input("Enter Website :").lower()

    if website in vault:

        new_username = input("New Username (Enter to keep old): ")
        new_password = getpass("New Password (Enter to keep old): ")

        if new_username:
            vault[website]["username"] = new_username
        
        if new_password:
            encrypted_password = cipher.encrypt(new_password.encode()).decode()
            vault[website]["password"] = encrypted_password

        save_data(vault)
        print("Updated Successfully")

    else:
        print("Web  site not found in stored websites !")   

#----------------------------------------------------------------------------------------------------

def generate_password(length=8):

    chars = string.ascii_letters + string.digits + "!@#$%^&*"

    password = "".join(
        random.choice(chars)
        for _ in range(length)
    )

    return password
           
#----------------------------------------------------------------------------------------------------

def delete_password(vault):
    website = input("Enter website to delete: ").lower()

    if website in vault:
        del vault[website]
        save_data(vault)
        print("Password deleted successfully!")

    else:
        print("Website not found!")        

#----------------------------------------------------------------------------------------------------

def chk_masterpass():

    for _ in range(3):
        masterpass = getpass("Enter Master Password to View all passowrds :")

        if masterpass == "Aryan9911":
            return True
        else:
            print("Incorrect Password !")

    print("Access denied !")
    return False

#----------------------------------------------------------------------------------------------------

vault = load_data()

def main():

    login = chk_masterpass()

    if login:

        while True:

            print("\n1. Add Pass")
            print("2. Show Pass")
            print("3. Search Pass")
            print("4. Delete Pass")
            print("5. Update Password")
            print("6. Exit")

            choice = input("Enter your choice: ")

            if choice == '1':
                add_password(vault)

            elif choice == '2':
                view_password(vault)

            elif choice == '3':
                search_password(vault)

            elif choice == '4':
                delete_password(vault)

            elif choice == '5':
                update_passwords(vault)  
                
            elif choice == '6':
                print("Goodbye!")
                break

            else:
                print("Invalid choice!")

if __name__ == "__main__":
    main()

#-----------------------------Understanding---------------------------------------

'''
*  encrypted_password = cipher.encrypt(password.encode()).decode()  *
    
passowrd = hello123

hello123 -> password.encode() -> b'hello123' (Because Fernet encrypts bytes, not strings.

cipher.encrypt(b'hello123') -> b'gAAAAABoXYZabc123...'   (Fernet encrypts the bytes.

(Notice the b.This means the encrypted result is still bytes.)
(JSON cannot store bytes directly.)

decodes() -> b'gAAAAABoXYZabc123...' -> 'gAAAAABoXYZabc123...' (which is a normal Python string.)
(Now it can be saved in JSON.)

'''


'''
* password = cipher.decrypt(encrypted_password.encode()).decode() *

encrypted_password = 'gAAAAABoXYZabc123...'

'gAAAAABoXYZabc123...' -> encode() -> b'gAAAAABoXYZabc123...'

(Fernet decrypts bytes, not strings.)

b'gAAAAABoXYZabc123...' -> cipher.decrypt() -> b'hello123'

(The encrypted bytes are decrypted.)

b'hello123' -> .decode() -> 'hello123'

(decode() converts bytes -> string)

Got back the original password.
'''
