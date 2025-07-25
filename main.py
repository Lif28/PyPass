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

FILE = None

def find():
    global FILE
    for i in string.ascii_uppercase:
        if os.path.exists(fr"{i}:\masterkey.key"):
            FILE = i
def ensure_file():
    global FILE
    if FILE is None:
        find()
    if FILE is None:
        raise  FileNotFoundError('USB key???')
    
def generate_password(length=16):
    characters = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(random.SystemRandom().choice(characters) for _ in range(length))
    return str(password)

def encrypt_file(input_path: str, output_path: str, file=None):
    # Important for ensure the program doesn't blow up
    if file is None:
        ensure_file()
        file = fr"{FILE}:\masterkey.key"

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

def decrypt_file(input_path: str, output_path: str, file=None):
    # Important for ensure the program doesn't blow up
    if file is None:
        ensure_file()
        file = fr"{FILE}:\masterkey.key"
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

def kill():
    ui.navigate.to("/")

def copy_password(password):
    ui.notify('Password copied!', type="positive")
    pyperclip.copy(password)

def show_personal():
    ui.navigate.to('/personal')

def show_add_password():
    ui.navigate.to('/personal/add_login')

def encrypt_password(password: str, file=None) -> str:
    if file is None:
        find()
        try:
            ensure_file()
        except FileNotFoundError as e:
            ui.notify(str(e), type='negative')
            return
            #raise FileNotFoundError("USB key with masterkey.key not found.")
        file = fr"{FILE}:\masterkey.key"
    fernet = Fernet(open(file, "rb").read())
    return fernet.encrypt(password.encode()).decode()

def decrypt_password(encrypted: str, file=None) -> str:
    if file is None:
        find()
        try:
            ensure_file()
        except FileNotFoundError as e:
            ui.notify(str(e), type='negative')
            return
            #raise FileNotFoundError("USB key with masterkey.key not found.")
        file = fr"{FILE}:\masterkey.key"
    fernet = Fernet(open(file, "rb").read())
    return fernet.decrypt(encrypted.encode()).decode()

def killall():
    os.kill(os.getpid(), signal.SIGTERM)

def shutdown():
    if os.path.exists('logins.json'):
        os.remove('logins.json')
    ui.run_javascript('window.close()')
    app.shutdown()

def encrypt_with_new_token():
# Encripts and delete useless files
        find()
        with open('logins.json', 'r') as file:
            data = json.load(file)
        try:
            for i in data:
                i['username'] = encrypt_password(i['username'])
                i['password'] = encrypt_password(i['password'])
            with open('logins.json', 'w') as new:
                json.dump(data, new, indent=4)
        except Exception as e:
            with open('logs.txt', 'a') as logs:
                logs.write(f"\n[ERR] check_old_token 3: {e}")
                return e
        files = {'logins.json':'logins.enc', 'token.json':'token.enc', 'client_secrets.json':'client_secrets.enc'}
        try:
            for i in files.keys():
                if encrypt_file(i, files.get(i)) == -1:
                    return -1
        except Exception as e:
            with open('logs.txt', 'a') as logs:
                logs.write(f"\n[ERR] check_old_token 4: {e}")
                return e
        try:
            os.remove('logins.json')
            os.remove('token.json')
            os.remove('client_secrets.json')
            with open('.token_migrated', 'w') as f:
                f.write('ok')
            return 0
            
        except Exception as e:
            with open('logs.txt', 'a') as logs:
                logs.write(f"\n[ERR] check_old_token 5: {e}")
                return e
        
        
def migrate_from_old_token():
    global FILE
    find()
    print('ok')
    try:
        key_path = fr'{FILE}:\masterkey_old.key'

        if not os.path.exists('token.json'):
            if decrypt_file('token.enc', 'token.json', file=key_path) == -1:
                return -3
        if not os.path.exists('client_secrets.json'):
            if decrypt_file('client_secrets.enc', 'client_secrets.json', file=key_path) == -1:
                return -3

        # Auth and download
        auth_result = authenticate()
        with open('logs.txt', 'a') as logs:
            logs.write(f'\n[INFO] auth_result: {auth_result}, drive: {drive}\n')
        if auth_result == -1 or drive is None:
            with open('logs.txt', 'a') as logs:
                logs.write('\n[ERR] Authentication failed or drive not initialized\n')
            return -1

        Download()
        encrypt_with_new_token()
        return 0

    except Exception as e:
        with open('logs.txt', 'a') as logs:
            logs.write(f'\n[ERR] migrate_from_old_token: {e}\n')
        return -1

def check_old_token():
    global FILE
    try:
        ensure_file()
    except FileNotFoundError as e:
        return -2
    
    #Checks if we have new tokens to use
    try:
        if decrypt_file('token.enc', 'token.json') != -1:
            # Token is up to date!
            os.remove('token.json')
            if os.path.exists('.token_migrated'):
                with open('.token_migrated', 'w') as file:
                    file.write('ok')
            return
        if os.path.exists('.token_migrated'):
            os.remove('.token_migrated')
        
        if os.path.exists(fr'{FILE}:\masterkey_old.key'):
            return migrate_from_old_token()
        
        return -4
            
    except Exception as e:
        with open('logs.txt', 'a') as logs:
            logs.write(f'\n[ERR] check_old_token 0: {e}\n')
        return -1


#ui.dark_mode(value=True)

# === Home Page ===
@ui.page('/')
def home_page(): 
    #ui.dark_mode().enable()
    with ui.header(elevated=True).style('background-color: #1976d2; text-align: center; justify-content: center'):
        ui.label('PyPass - 1.0').style('font-size: 1.5rem; font-weight: bold; color: white;')

    #Checks for new tokens
    def threaded_check_old_token():
        result = check_old_token()
        if result == 0:
            return ui.notify("Old token migrated!", type="positive")
        elif result == -1:
            return ui.notify('Error during the process, please contact the developer or try again later... ', type='negative')
        elif result ==-2:
            return ui.notify('Please insert the USB key', type="negative")
        elif result == -3:
            return ui.notify('Old token not found!', type='negative')

    threaded_check_old_token()

    with ui.column().classes('w-full max-w-md mx-auto mt-10 gap-4'):
        with ui.card().classes('items-center justify-center w-full p-6').style("background-color: #EFEFEF"):
            ui.label('Password Manager').classes('text-3xl font-bold text-center mb-8')
            if os.path.exists(rf"{FILE}:\masterkey.key"):
                with ui.column().classes('gap-4'):
                    if not os.path.exists("logins.json") or os.path.getsize('logins.json') <= 2:
                        ui.button('Personal', on_click=show_personal, icon='person').classes('w-full h-12 text-lg').props('color=primary size=lg').disable()
                        find()
                        if FILE != None:
                            try:
                                threading.Thread(target=Download).start()
                                decrypt_file('logins.enc', 'logins.json')
                            except Exception as e: 
                                ui.notify(f"[ERR] {e}", type='negative')
                    else:
                        ui.button('Personal', on_click=show_personal, icon='person').classes('w-full h-12 text-lg').props('color=primary size=lg')

                    ui.button('Add Password', on_click=show_add_password, icon='add').classes('w-full h-12 text-lg').props('color=secondary size=lg')
                    ui.button('New Token', on_click=lambda: ui.navigate.to('/new-token')).classes('w-full h-12 text-lg').props('color="primary" size=lg')
                    ui.button('Quit',on_click=shutdown).classes('w-full h-12 text-lg').props('color="red"')
            else:
                ui.notify("Please insert the USB  key", type="negative")
                find()
                if FILE != None:
                    try:
                        authenticate()
                        Download()
                        decrypt_file('logins.enc', 'logins.json')
                    except: 
                        ui.notify("You're Offline")



@ui.page('/new-token')
def alert():
    def generate_new_key():
        # Logins 
        with open('logins.json', 'r') as file:
            data = json.load(file)
        for i in data:
            i['username'] = decrypt_password(i['username'])
            i['password'] = decrypt_password(i['password'])
        with open('logins.json', 'w') as new:
            json.dump(data, new, indent=4)

        #print("DATA", data)
        decrypt_file('token.enc', 'token.json')
        decrypt_file('client_secrets.enc', 'client_secrets.json')
        try:
            if os.path.exists('logins.enc'):
                os.remove('logins.enc')
            if os.path.exists(fr'{FILE}:\masterkey_old_old.key'):
                os.remove(fr'{FILE}:\masterkey_old_old.key')
            if os.path.exists(fr'{FILE}:\masterkey_old.key'):
                os.rename(fr'{FILE}:\masterkey_old.key', fr'{FILE}:\masterkey_old_old.key')
                #print("\nREMOVED\n")
            os.remove('token.enc')
            os.remove('client_secrets.enc')
        except Exception as e:
            with open('logs.txt', 'a') as logs:
                logs.write(f"\n[ERR] generate_new_key: {e}")
                return ui.notify(f"[ERR] {e} ", type='negative')
        try:
            ensure_file()
        except FileNotFoundError as e:
            ui.notify(str(e), type='negative')
            return
        try:
            os.rename(fr'{FILE}:\masterkey.key', fr'{FILE}:\masterkey_old.key')
        except Exception as e:
            with open('logs.txt', 'a') as logs:
                logs.write(f"\n[ERR] generate_new_key: {e}")
                return ui.notify(f"[ERR] {e} ", type='negative')

        key_path = fr"{FILE}:\masterkey.key"
        key = Fernet.generate_key()
        with open(key_path, "wb") as file:
            file.write(key)

    def update_key():
        generate_new_key()
        with open('logins.json', 'r') as file:
            data = json.load(file)
        try:
            for i in data:
                i['username'] = encrypt_password(i['username'])
                i['password'] = encrypt_password(i['password'])
            #print(data)
            with open('logins.json', 'w') as new:
                json.dump(data, new, indent=4)
        except Exception as e:
            with open('logs.txt', 'a') as logs:
                logs.write(f"\n[ERR] generate_new_key: {e}")
                return ui.notify(f"[ERR] {e} ", type='negative')
            
        files = {'logins.json':'logins.enc', 'token.json':'token.enc', 'client_secrets.json':'client_secrets.enc'}
        try:
            for i in files.keys():
                if encrypt_file(i, files.get(i)) == -1:
                    return ui.notify("[ERR] Token broke!", type='negative')
        except Exception as e:
            with open('logs.txt', 'a') as logs:
                logs.write(f"\n[ERR] generate_new_key: {e}")
                return ui.notify(f"[ERR] {e} ", type='negative')
        try:
            Upload()
        except Exception as e:
            with open('logs.txt', 'a') as logs:
                logs.write(f"\n[ERR] generate_new_key 1: {e}")
                return ui.notify(f"[ERR] {e} ", type='negative')

        try:
            os.remove('logins.json')
            os.remove('token.json')
            os.remove('client_secrets.json')
            with open('.token_migrated', 'w') as file:
                file.write('ok')
            return ui.notify(f"Token updated!", type='positive'), dialog.close()
            
        except Exception as e:
            with open('logs.txt', 'a') as logs:
                logs.write(f"\n[ERR] generate_new_key 2: {e}")
                return ui.notify(f"[ERR] {e} ", type='negative')
            
    # UI
    with ui.dialog() as dialog, ui.card().classes('w-[600px] max-w-[90vw] items-center justify-center '):
        ui.label("Do you want to create a new Token? The old one will no longer work.").style('font-size: 1rem; font-weight: bold;')
        with ui.row().classes('gap-4 justify-end'):
            ui.button('Yes', on_click= update_key).props('color=negative')
            ui.button('No', on_click= kill)
        
    dialog.open()



# === Personal Page ===
@ui.page('/personal')

def personal_page():
    #ui.dark_mode().enable()
    with ui.header(elevated=True).style('background-color: #1976d2; text-align: center; justify-content: center'):
        ui.label('Your Passwords').style('font-size: 1.5rem; font-weight: bold; color: white;')

    with ui.column().classes('w-full max-w-md mx-auto mt-10 gap-4 items-center justify-center'):
        # logins.json
        if os.path.exists('logins.json') and os.path.exists(fr"{FILE}:\masterkey.key"):
            with open('logins.json', 'r') as file:
                data = json.load(file)

            if data:
                for item in data:
                    if 'comment' not in item:
                        with ui.card().classes('w-full items-center justify-center').style("background-color: #EFEFEF"):
                            with ui.expansion(item['service']).classes('w-full items-center justify-center text-lg font-semibold text-primary'):
                                with ui.row().style('color: black'):
                                    ui.label(f"Username:")
                                    ui.label(f"{decrypt_password(item['username'])}").style('font-weight: normal;')
                                with ui.row().style('color: black'):
                                    ui.label("Password:")
                                    ui.label(f"{'•' * 8}").style('font-weight: normal;')  
                                with ui.row().classes('gap-2 justify-center').style('width: 100%;'):
                                    ui.button('Edit', on_click=lambda item=item: edit_passwd(item))
                                    ui.button('Remove', on_click=lambda item=item: rem_passwd(item['service']))
                                    ui.button('Show', on_click=lambda item=item: show_passwd(item['password']))
            else:
                ui.label('Nothing to see here!')
        else:
            ui.notify('Please insert the USB key', type="negative")
            find()
            if FILE != None:
                try:
                    Download()
                    decrypt_file('logins.enc', 'logins.json')
                except: 
                    ui.notify("You're Offline")
        ui.button('Back', on_click=lambda: ui.navigate.to("/"))

@ui.page('/personal/add_login')
def add_login():  
    #ui.dark_mode().enable()
    login = {"service": "", "username": "", "password": ""}
    with ui.dialog() as dialog, ui.card().classes('w-[400px] max-w-[90vw] items-center justify-center'):

        service = ui.input('Service', value=login.get('service', '')).style("width: 200px")
        username = ui.input('Username', value=login.get('username', '')).style("width: 200px")
        with ui.row().style("padding-top:20px;"):
            slider = ui.slider(min=10, max=40, value=15, step=5).style("width: 200px;")
            ui.label().bind_text_from(slider, 'value')
        password = ui.input('Password', password=False, value=generate_password(slider.value)).style("width: 200px")
        
        # New password for slider 
        def on_slider_move(e):
            new_length = e.args
            password.value = generate_password(new_length)

        slider.on('update:model-value', on_slider_move, throttle=0.05, leading_events=True)

        def save(check = 1):
            def perform():
                # Append new login
                data.append(login)

                # Write back to file
                with open('logins.json', 'w') as f:
                    json.dump(data, f, indent=4)

                # Google Drive

                threading.Thread(target=Upload).start()
                kill()

            if all(i != "" for i in [service.value, username.value, password.value]):
                if os.path.exists(fr"{FILE}:\masterkey.key"):
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

                    if len(password.value) < 15 and check == 1:
                        with ui.dialog() as dialog, ui.card().classes('w-[600px] max-w-[90vw] items-center justify-center '):
                            ui.label("The password entered is not secure.\n Are you sure you want to save this login?").style('font-size: 1rem; font-weight: bold;')
                            with ui.row().classes('gap-4 justify-end'):
                                ui.button('Yes', on_click=lambda: save(check = 0)).props('color=negative')
                                ui.button('No', on_click=dialog.close)
                        dialog.open()
                        return
                    elif check == 0:
                        perform()
                    else:
                        perform()
                else:
                    ui.notify("Please insert the USB key", type="negative")
                    return
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

    if os.path.exists('logs.txt'):
        os.remove("logs.txt")
    try:
        if authenticate() == -1:
            with open('logs.txt', 'a') as logs:
                logs.write('\n[ERR] Authentication\n')
        else:
            if os.path.exists("token.enc"):
                threading.Thread(target=Download).start() 
            else:
                Download()
    except:
        # This means we have a new token to use ...
        pass
    ui.run(
            title='Password Manager',
            port=5000,
            show=True,
            favicon='🔐'
        )


