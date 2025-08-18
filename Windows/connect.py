from webdav3.client import Client
from cryptography.fernet import Fernet
import string
import os
import json

FILE = None

def find():
    global FILE
    for i in string.ascii_uppercase:
        if os.path.exists(fr"{i}:\PyPass\masterkey.key"):
            FILE = i

def ensure_file():
    global FILE
    if FILE is None:
        find()
    if FILE is None:
        raise  FileNotFoundError('USB key???')
    
def encryptfile(input_path: str, output_path: str, file=None):
    # Important for ensure the program doesn't blow up
    if file is None:
        ensure_file()
        file = fr"{FILE}:\PyPass\masterkey.key"

    try:
        fernet = Fernet(open(file, "rb").read())
    except Exception as e:
        with open('logs.txt', 'a') as logs:
            logs.write(f"\n[ERR] encrypt_file: {e}")
            return -1
    with open(input_path, 'rb') as f:
        data = f.read()
    encrypted = fernet.encrypt(data)
    with open(output_path, 'wb') as f:
        f.write(encrypted)
    return

def decryptfile(input_path: str, output_path: str, file=None):
    # Important for ensure the program doesn't blow up
    if file is None:
        ensure_file()
        file = fr"{FILE}:\PyPass\masterkey.key"
    try:
        fernet = Fernet(open(file, "rb").read())
    except:
        return -1
    try:
        with open(input_path, 'rb') as f:
            encrypted = f.read()
        decrypted = fernet.decrypt(encrypted)
        with open(output_path, 'wb') as f:
            f.write(decrypted)
    except:
        return -1
    return 0

def encrypt_pass(password: str, file=None) -> str:
    if file is None:
        find()
        try:
            ensure_file()
        except FileNotFoundError as e:
            return
            #raise FileNotFoundError("USB key with masterkey.key not found.")
        file = fr"{FILE}:\PyPass\masterkey.key"
    fernet = Fernet(open(file, "rb").read())
    return fernet.encrypt(password.encode()).decode()

def decrypt_pass(encrypted: str, file=None) -> str:
    if file is None:
        find()
        try:
            ensure_file()
        except FileNotFoundError as e:
            return
            #raise FileNotFoundError("USB key with masterkey.key not found.")
        file = fr"{FILE}:\PyPass\masterkey.key"
    fernet = Fernet(open(file, "rb").read())
    return fernet.decrypt(encrypted.encode()).decode()

def check_old_token():
    global FILE
    try:
        ensure_file()
    except FileNotFoundError as e:
        return -2
    
    #Checks if we have new tokens to use
    try:
        if os.path.exists(fr'{FILE}:\PyPass\masterkey_old.key'):
            find()
            if decryptfile('client_secrets.enc','client_secrets.json', file=fr'{FILE}:\PyPass\masterkey_old.key') != -1:
                return 0
            else:
                return
            
    except Exception as e:
        with open('logs.txt', 'a') as logs:
            logs.write(f'\n[ERR] check_old_token 0: {e}\n')
        return -1

def get_passwd():
    if os.path.exists('client_secrets.enc'):
        if decryptfile('client_secrets.enc', 'client_secrets.json') != -1:
            with open('client_secrets.json', 'r') as file:
                data = json.load(file)
        else:
            if check_old_token() == 0:
                with open('client_secrets.json', 'r') as file:
                    data = json.load(file)
            else: 
                with open('logs.txt', 'a') as log:
                    log.write('[ERR] get_passwd')
        
        
        username = data['username']
        password = data['password']
        os.remove('client_secrets.json')
        return username, password
        
    elif os.path.exists('client_secrets.json'):
        with open('client_secrets.json', 'r') as file:
            data = json.load(file)

        username = data['username']
        password = data['password']
        encryptfile('client_secrets.json', 'client_secrets.enc')
        os.remove('client_secrets.json')
        return username, password
    else:
        return -2
    
username, password = get_passwd()

if username == -2:
    with open('logs.txt', 'a') as file:
        file.write('[ERR] get_passwd: client_secrets missing!')

options = {
    'webdav_hostname': 'https://leo.it.tab.digital/remote.php/webdav/',
    'webdav_login': username,
    'webdav_password': password,
}

client = Client(options)
file = 'logins.enc'
file_ = '/logins.enc'

def Upload():
    # Connection
    encryptfile('logins.json', 'logins.enc')
    try:
        if client.check():
            local_file = file
            remote_file = file_  
            client.upload_sync(remote_path=remote_file, local_path=local_file)
            if os.path.exists('logins.enc'):
                os.remove('logins.enc')
            return 0
        else:
            return -1
    except Exception as e:
        with open('logs.txt', 'a') as logs:
            logs.write(f'\n[ERR] Upload: {e}\n')
        return -2

def Download():
    try:
        if client.check():
            remote_file = file_       
            local_file = file  
            client.download_sync(remote_path=remote_file, local_path=local_file)
            decryptfile('logins.enc', 'logins.json')
            if os.path.exists('logins.enc'):
                os.remove('logins.enc')
            return 0
        else:
            return -1
    except Exception as e:
        with open('logs.txt', 'a') as logs:
            logs.write(f'\n[ERR] Upload: {e}\n')
        return -2
