from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from cryptography.fernet import Fernet
import os
import string
import time

def find_key():
    global FILE
    for i in string.ascii_uppercase:
        if os.path.exists(fr"{i}:\masterkey.key"):
            FILE = i

def encrypt_file(input_path: str, output_path: str):
    try:
        fernet = Fernet(open(fr"{FILE}:\masterkey.key", "rb").read())
    except:
        return -1
    with open(input_path, 'rb') as f:
        data = f.read()
    encrypted = fernet.encrypt(data)
    with open(output_path, 'wb') as f:
        f.write(encrypted)
    return

def decrypt_file(input_path: str, output_path: str):
    try:
        fernet = Fernet(open(fr"{FILE}:\masterkey.key", "rb").read())
    except:
        return -1
    with open(input_path, 'rb') as f:
        encrypted = f.read()
    decrypted = fernet.decrypt(encrypted)
    with open(output_path, 'wb') as f:
        f.write(decrypted)
    return

# === AUTH ===
gauth = None
drive = None

def authenticate():
    global gauth, drive

    if gauth and drive: return
    gauth = GoogleAuth()
    gauth.LoadClientConfigFile("client_secrets.json")
    if os.path.exists(r"token.enc"):
        if decrypt_file("token.enc", "token.json") == -1:
            return -2

        try:
            gauth.LoadCredentialsFile("token.json")
            # New Token
            if gauth.credentials is None or gauth.access_token_expired:
                gauth.Refresh()
        except Exception as e:
            print("Error", e)
            gauth.LocalWebserverAuth()  
    else:
        gauth.LocalWebserverAuth()  
        
    gauth.SaveCredentialsFile("token.json")
    encrypt_file("token.json", "token.enc")
    os.remove("token.json")
    drive = GoogleDrive(gauth)

def Upload():
    if authenticate() == -2:
        return -2

    if encrypt_file("logins.json", "logins.enc") == -1:
        return -2
    try:
        ID = None
        if os.path.exists(r"ID.txt"):
            with open("ID.txt", "r") as file:
                ID = file.read().strip()

        if ID:
            # Update 
            file_drive = drive.CreateFile({'id': ID})
        else:
            # Create new file
            file_drive = drive.CreateFile({'title': 'logins.enc'})

        file_drive.SetContentFile("logins.enc")
        file_drive.Upload()

        # Save/Update ID
        with open("ID.txt", "w") as file:
            file.write(file_drive['id'])

        return 0

    except Exception as e:
        print("Upload error:", e)
        return -1
    
def Download():
    find_key()
    time.sleep(0.5)
    if authenticate() == -2:
        return -2
    try: 
        with open(r"ID.txt", "r") as file:
            ID = file.read().strip()

        file_drive = drive.CreateFile(({'id': ID}))
        file_drive.GetContentFile('logins.enc')
        if decrypt_file("logins.enc", "logins.json") == -1:
            return -2
        
        os.remove("logins.enc")
        return 0
    
    except Exception as e:
        print(e)
        return -1
    
