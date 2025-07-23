from nicegui import ui, app
import threading
import json
import os
from cryptography.fernet import Fernet
import random
import signal
import string
import pyperclip
import os
from connect import *

def generate_password(length=16):
    characters = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(random.SystemRandom().choice(characters) for _ in range(length))
    return str(password)

def find():
    global FILE
    for i in string.ascii_uppercase:
        if os.path.exists(fr"{i}:\masterkey.key"):
            FILE = i

def kill():
    ui.navigate.to("/")

def copy_password(password):
    ui.notify('Password copied!', type="positive")
    pyperclip.copy(password)

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

def show_personal():
    ui.navigate.to('/personal')

def show_add_password():
    ui.navigate.to('/personal/add_login')

def encrypt_password(password: str) -> str:
    fernet = Fernet(open(fr"{FILE}:\masterkey.key", "rb").read())
    return fernet.encrypt(password.encode()).decode()

def decrypt_password(encrypted: str) -> str:
    fernet = Fernet(open(fr"{FILE}:\masterkey.key", "rb").read())
    return fernet.decrypt(encrypted.encode()).decode()

def killall():
    os.kill(os.getpid(), signal.SIGTERM)

def shutdown():
    os.remove('logins.json')
    ui.run_javascript('window.close()')
    killall()

FILE = None
ui.dark_mode(value=True)

# === Home Page ===
@ui.page('/')
def home_page(): 
    ui.dark_mode().enable()
    with ui.header(elevated=True).style('background-color: #1976d2; text-align: center; justify-content: center'):
        ui.label('PyPass - 1.0').style('font-size: 1.5rem; font-weight: bold; color: white;')
    with ui.column().classes('w-full max-w-md mx-auto mt-10 gap-4'):
        with ui.card().classes('items-center justify-center w-full p-6'):
            ui.label('Password Manager').classes('text-3xl font-bold text-center mb-8')
            if os.path.exists(rf"{FILE}:\masterkey.key"):
                with ui.column().classes('gap-4'):
                    ui.button(
                        'Personal',
                        on_click=show_personal,
                        icon='person'
                    ).classes('w-full h-12 text-lg').props('color=primary size=lg')
                    
                    ui.button(
                        'Add Password',
                        on_click=show_add_password,
                        icon='add'
                    ).classes('w-full h-12 text-lg').props('color=secondary size=lg')
                    ui.button(                        
                        'Quit',
                        on_click=shutdown,
                    ).classes('w-full h-12 text-lg').props('color= size=lg')
            else:
                ui.notify("Please insert the USB  key", type="negative")



# === Personal Page ===
@ui.page('/personal')

def personal_page():
    ui.dark_mode().enable()
    with ui.header(elevated=True).style('background-color: #1976d2; text-align: center; justify-content: center'):
        ui.label('Your Passwords').style('font-size: 1.5rem; font-weight: bold; color: white;')

    with ui.column().classes('w-full max-w-md mx-auto mt-10 gap-4 items-center justify-center'):
        # logins.json
        if os.path.exists('logins.json'):
            with open('logins.json', 'r') as file:
                data = json.load(file)

            if data:
                for item in data:
                    if 'comment' not in item:
                        with ui.card().classes('w-full items-center justify-center'):
                            with ui.expansion(item['service']).classes('w-full items-center justify-center text-lg font-semibold text-primary'):
                                with ui.row().style('color: white'):
                                    ui.label(f"Username:")
                                    ui.label(f"{decrypt_password(item['username'])}").style('font-weight: normal;')
                                with ui.row().style('color: white'):
                                    ui.label("Password:")
                                    ui.label(f"{'•' * 8}").style('font-weight: normal;')  
                                with ui.row().classes('gap-2 justify-center').style('width: 100%;'):
                                    ui.button('Edit', on_click=lambda item=item: edit_passwd(item))
                                    ui.button('Remove', on_click=lambda item=item: rem_passwd(item['service']))
                                    ui.button('Show', on_click=lambda item=item: show_passwd(item['password']))
            else:
                ui.label('Nothing to see here!')
        else:
            try: 
                Download()
                decrypt_file('logins.enc', 'login.json')
            except: pass
        ui.button('Back', on_click=lambda: ui.navigate.to("/"))

@ui.page('/personal/add_login')
def add_login():  
    ui.dark_mode().enable()
    login = {"service": "", "username": "", "password": ""}
    with ui.dialog() as dialog, ui.card().classes('w-[600px] max-w-[90vw] items-center justify-center'):

        service = ui.input('Service', value=login.get('service', ''))
        username = ui.input('Username', value=login.get('username', ''))
        password = ui.input('Password', password=False, value=generate_password())
        
        def save():
            if all(i != "" for i in [service.value, username.value, password.value]):
                login =  {"service": f"{service.value}", "username":f"{encrypt_password(username.value)}", "password": f"{encrypt_password(password.value)}"}
                # Writes
                if os.path.exists('logins.json'):
                    with open('logins.json', 'r') as f:
                        try:
                            data = json.load(f)
                            for i in data:
                                if i['service'] == service.value:
                                    ui.notify("Service is already been used.", type="warning")
                                    return
                        except json.JSONDecodeError:
                            data = []
                else: data = []

                # Append new login
                data.append(login)

                # Write back to file
                with open('logins.json', 'w') as f:
                    json.dump(data, f, indent=4)

                # Google Drive

                threading.Thread(target=Upload).start()
                kill()
            else:
                ui.notify("Please fill in all the fields", type="negative")
                return
        with ui.row().classes('gap-4 justify-end'):
            ui.button('Save', on_click=save).props('color=primary')
            ui.button('Cancel', on_click=kill)
    dialog.open()


def edit_passwd(item):
    with ui.dialog() as dialog, ui.card().classes('w-[600px] max-w-[90vw] items-center justify-center'):

        service = ui.input('Service', value=item.get('service', ''))
        try:
            username = ui.input('Username', value=decrypt_password(item.get('username', '')))
            password = ui.input('Password', password=False, value=decrypt_password(item.get('password', '')))
        except FileNotFoundError:
            ui.notify("Please insert the USB key", type="negative")
        except Exception:
            ui.notify(f"Error: Password is not encrypted or the key is wrong!")
        
        def save():
            if all(i != "" for i in [service.value, username.value, password.value]):
                # hole file
                with open('logins.json', 'r') as f:
                    data = json.load(f)
                # Check
                count = 0
                for i in data:
                    if i.get('service') == service.value:
                        count += 1
                if count > 1:
                    print(count)
                    ui.notify("Service is already been used.", type="warning")
                    count = 1
                    return
                    
                for entry in data:
                    if entry == item:
                        entry['service'] = service.value
                        entry['username'] = encrypt_password(username.value)
                        entry['password'] = encrypt_password(password.value)
                        break

                # Writes
                with open('logins.json', 'w') as f:
                    json.dump(data, f, indent=4)

                threading.Thread(target=Upload).start()

                dialog.close()
                ui.navigate.to('/personal') 
            else:
                ui.notify("Please fill in all the fields", type="negative")
                return
        with ui.row().classes('gap-4 justify-end'):
            ui.button('Save', on_click= save).props('color=primary')
            ui.button('Cancel', on_click=dialog.close)
    dialog.open()

def remove_passwd(service, dialog):
    if os.path.exists(fr"{FILE}:\masterkey.key"):
        with open('logins.json', 'r') as f:
            data = json.load(f)

        data = [entry for entry in data if entry.get('service') != service]
        with open('logins.json', 'w') as f:
            json.dump(data, f, indent=4)

        threading.Thread(target=Upload).start()
        dialog.close()
        ui.notify("Login removed!", type="positive")
    else:
        ui.notify("Please insert the USB key", type="negative")

def rem_passwd(service):
    with ui.dialog() as dialog, ui.card().classes('w-[600px] max-w-[90vw] items-center justify-center '):
        ui.label("Confirm deletion: Do you really want to remove this login?").style('font-size: 1rem; font-weight: bold;')
        with ui.row().classes('gap-4 justify-end'):
            ui.button('Yes', on_click=lambda: remove_passwd(service, dialog)).props('color=negative')
            ui.button('No', on_click=dialog.close)
    dialog.open()
    
def show_passwd(passwd):
    try:
        password = decrypt_password(passwd)
    except FileNotFoundError:
        ui.notify("Please insert the USB key", type="negative")
    except Exception:
        ui.notify(f"Error: Password is not encrypted or the key is wrong!")

    with ui.dialog() as dialog, ui.card().classes('w-[600px] max-w-[90vw] items-center justify-center'):
        ui.label("Password:").style('font-size: 1rem; font-weight: bold;')
        ui.label(f"{password}")
        with ui.row().classes('gap-4 justify-end'):
            ui.button('Copy', on_click=lambda: copy_password(password)).props('color=secondary')
            ui.button('Close', on_click=dialog.close)
    dialog.open()

# === Start ===
if __name__ in {"__main__", "__mp_main__"}:
    find()
    threading.Thread(target=Download).start()
    ui.run(
            title='Password Manager',
            port=5000,
            show=True,
            favicon='🔐'
        )


