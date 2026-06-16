import json
from urllib.parse import urlparse
from getpass import getpass
import random
import string

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
    password = getpass("Password: ")

    vault[website] = {
        "username": username,
        "password": password,
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
        password = vault[web]['password']

        print(f"{idx:<5}{web:<15}{username:<25}{password:<20}")
        print(f"     URL: {url}\n")
        
    print(f"-" * 50)    

#----------------------------------------------------------------------------------------------------

def search_password(vault):
    website = input("Enter website name: ").lower()

    if website in vault:
        print("\nWebsite :", website)
        print("Username:", vault[website]["username"])
        print("Password:", vault[website]["password"])
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
            vault[website]["password"] = new_password

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

    masterpass = getpass("Enter Master Password to View all passowrds :")

    if masterpass == "Aryan9911":
        return True
    else:
        print("Incorrect Password ! Access denied !")
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
            print("6. Genearte Password")
            print("7. Exit")

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
                generate_password()

            elif choice == '7':
                print("Goodbye!")
                break

            else:
                print("Invalid choice!")

if __name__ == "__main__":
    main()