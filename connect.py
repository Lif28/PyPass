from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from cryptography.fernet import Fernet
import os
import string

logs = 'logs.txt'
FILE = None
def find_key():
    global FILE
    for i in string.ascii_uppercase:
        if os.path.exists(fr"{i}:\masterkey.key"):
            FILE = i

def encrypt(input_path: str, output_path: str, file=None):
    # Important for ensure the program doesn't blow up
    if file is None:
        find_key()
        file = fr"{FILE}:\masterkey.key"

    try:
        fernet = Fernet(open(file, "rb").read())
    except Exception as e:
        with open('logs.txt', 'a') as logs:
            logs.write(f"[ERR] generate_new_key: {e}")
            return -1
    with open(input_path, 'rb') as f:
        data = f.read()
    encrypted = fernet.encrypt(data)
    with open(output_path, 'wb') as f:
        f.write(encrypted)
    return

def decrypt(input_path: str, output_path: str, file=None):
    # Important for ensure the program doesn't blow up
    if file is None:
        find_key()
        file = fr"{FILE}:\masterkey.key"
    try:
        fernet = Fernet(open(file, "rb").read())
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
    find_key()

    # Ensure we have client secrets
    if not os.path.exists('client_secrets.json'):
        if not os.path.exists('client_secrets.enc'):
            with open(logs, 'a') as log:
                log.write("\n[ERR] Missing both client_secrets files\n")
            return -1
        if decrypt('client_secrets.enc', 'client_secrets.json') == -1:
            return -1

    if gauth and drive: return 0
    gauth = GoogleAuth()
    gauth.LoadClientConfigFile("client_secrets.json")

    if os.path.exists("token.enc") and not os.path.exists('token.json'):
        if decrypt("token.enc", "token.json") == -1:
            return -1
        try:
            gauth.LoadCredentialsFile("token.json")
            # New Token
            if gauth.credentials is None or gauth.access_token_expired:
                gauth.Refresh()

        except Exception as e:
            with open('logs.txt', 'a') as logs:
                logs.write(f'\n[ERR] Authentication: {e}')
            gauth.LocalWebserverAuth() 
        
    elif os.path.exists('token.json'):
        # Token not encrypted --> old token has been used to decrypt token.enc and we'll use token.json directly.
        try:
            gauth.LoadCredentialsFile("token.json")
            # New Token
            if gauth.credentials is None or gauth.access_token_expired:
                gauth.Refresh()

        except Exception as e:
            with open('logs.txt', 'a') as logs:
                logs.write(f'\n[ERR] Authentication: {e}')
            gauth.LocalWebserverAuth() 

    else:
        gauth.LocalWebserverAuth()  
        
    gauth.SaveCredentialsFile("token.json")
    encrypt("token.json", "token.enc")
    encrypt("client_secrets.json", "client_secrets.enc")
    os.remove("token.json")
    os.remove("client_secrets.json")
    drive = GoogleDrive(gauth)

def Upload():
        
    # Error 2
    if encrypt("logins.json", "logins.enc") == -1:
        with open('logs.txt', 'a') as logs:
            logs.write('\n[ERR] Insert the USB key\n')
            return   
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

    except Exception as e:
        with open('logs.txt', 'a') as logs:
            logs.write(f'\n[ERR] Upload: {e}\n')
            return
    
def Download():
    find_key()
    #Error 1
    try: 
        with open(r"ID.txt", "r") as file:
            ID = file.read().strip()
        
        if os.path.exists("logins.enc"):
            os.remove("logins.enc")

        file_drive = drive.CreateFile(({'id': ID}))
        file_drive.GetContentFile('logins.enc')

        #Error 2
        if decrypt("logins.enc", "logins.json") == -1:
            with open('logs.txt', 'a') as logs:
                logs.write('\n[ERR] Insert the USB key\n')

        os.remove("logins.enc")

    except Exception as e:
        with open('logs.txt', 'a') as logs:
            logs.write(f'\n[ERR] Download: {e}\n')
            return -1
