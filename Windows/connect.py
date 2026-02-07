# PyPass - Password Manager
# Copyright (C) 2026 Lif28
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

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
        raise FileNotFoundError('Insert the USB key!!!')
    
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
    except:
        return -1
    try:
        decrypted = fernet.decrypt(encrypted)
        with open(output_path, 'wb') as f:
            f.write(decrypted)
    except:
        return -2
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


def get_passwd():
    if os.path.exists('client_secrets.enc'):
        result = decryptfile('client_secrets.enc', 'client_secrets.json')
        if result == 0:
            with open('client_secrets.json', 'r') as file:
                data = json.load(file)
        elif result == -2:
            return -2
        else: 
            with open('logs.txt', 'a') as log:
                log.write('[ERR] get_passwd')
                return -1
        
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
        return -3
    
result = get_passwd()

if type(result) == int:
    if result == -3:
        with open('logs.txt', 'a') as file:
            file.write('\n[ERR] get_passwd: client_secrets missing!\n')
    elif result == -2:
        with open('logs.txt', 'a') as file:
            file.write('[WARNING] get_passwd: Token changed!')
    else:
        with open('logs.txt', 'a') as file:
            file.write('[ERR] get_passwd: generic error')

else:
    username = result[0]
    password = result[1]
    options = {
        'webdav_hostname': 'https://kai.nl.tab.digital/remote.php/webdav/',
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
            logs.write(f'\n[ERR] Download: {e}\n')
        return -2

