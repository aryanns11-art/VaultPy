import json

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

def add_password(vault):
    website = input("Website: ")
    username = input("Username: ")
    password = input("Password: ")

    vault[website] = {
        "username": username,
        "password": password
    }

    save_data(vault)
    print("Password saved successfully!")

#----------------------------------------------------------------------------------------------------

def view_password(vault):
    
    print(f"\n" + "=" *50)
    print("All Passwords".center(50))    
    print(f"=" *50)

    print(f"\n{'No':5}{'Website':<10}{'username':<25}{'password':<20}")

    for idx, web in enumerate(vault, 1):
        username = vault[web]['username']
        password = vault[web]['password']

        print(f"{idx:<5}{web:<10}{username:<25}{password:<20}")
    print(f"\n" + "-" * 50)    

#----------------------------------------------------------------------------------------------------

def search_password(vault):
    website = input("Enter website name: ")

    if website in vault:
        print("\nWebsite :", website)
        print("Username:", vault[website]["username"])
        print("Password:", vault[website]["password"])
    else:
        print("Website not found!")

#----------------------------------------------------------------------------------------------------

def delete_password(vault):
    website = input("Enter website to delete: ")

    if website in vault:
        del vault[website]
        save_data(vault)
        print("Password deleted successfully!")

    else:
        print("Website not found!")        

#----------------------------------------------------------------------------------------------------

vault = load_data()

def main():

    while True:

        print("\n1. Add Pass")
        print("2. Show Pass")
        print("3. Search Pass")
        print("4. Delete Pass")
        print("5. Exit")

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
            print("Goodbye!")
            break

        else:
            print("Invalid choice!")

if __name__ == "__main__":
    main()