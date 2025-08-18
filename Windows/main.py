import os
from nicegui import ui, app
import qrcode
import base64
from io import BytesIO
import threading
import time
import json
from cryptography.fernet import Fernet
import random
import signal
import string
import pyperclip
from connect import *
import ctypes

FILE = None
logins = 'logins.json'
en_logins = 'logins.enc'

def generate_qr_base64(text: str) -> str:
    img = qrcode.make(text)
    buf = BytesIO()
    img.save(buf, format='PNG')
    base64_img = base64.b64encode(buf.getvalue()).decode('utf-8')
    return f'data:image/png;base64,{base64_img}'

def secure_erase(s):
    if isinstance(s, str):
        buf = ctypes.create_string_buffer(s.encode())
        ctypes.memset(ctypes.addressof(buf), 0, len(buf))
    return ""

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
    
def generate_password(length=16):
    characters = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(random.SystemRandom().choice(characters) for _ in range(length))
    return str(password)

def encrypt_file(input_path: str, output_path: str, file=None):
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

def decrypt_file(input_path: str, output_path: str, file=None):
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

def kill():
    ui.navigate.to("/")

def copy_password(password):
    ui.notify('Password copied!', type="positive")
    pyperclip.copy(password)
    password = secure_erase(password)

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
        file = fr"{FILE}:\PyPass\masterkey.key"
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
        file = fr"{FILE}:\PyPass\masterkey.key"
    fernet = Fernet(open(file, "rb").read())
    return fernet.decrypt(encrypted.encode()).decode()

def killall():
    os.kill(os.getpid(), signal.SIGTERM)

def shutdown():
    try:
        if os.path.exists(logins):
            os.remove(logins)
        if os.path.exists(en_logins):
            os.remove(en_logins)
        ui.run_javascript('window.close()')
        time.sleep(0.5)
        app.shutdown()
    except:
        time.sleep(1)
        shutdown()
    

def check_network():
    if os.path.exists('logs.txt'):
        with open('logs.txt', 'r') as logs:
            data = logs.read()
        if 'No connection' in data:
            return -1
    else:
        return 0
#ui.dark_mode(value=True)

# === Home Page ===
@ui.page('/')
def home_page(): 
    #ui.dark_mode().enable()
    with ui.header(elevated=True).style('background-color: #1976d2; text-align: center; justify-content: center'):
        ui.label('PyPass - 1.0').style('font-size: 1.5rem; font-weight: bold; color: white;')

    if os.path.exists('logs.txt'):
        with open('logs.txt', 'r') as logs:
            data = logs.read()
        if 'client_secrets.json' or 'client_secrets.enc' in data:
            ui.notify('[WARNING] Missing client_secrets file', type='warning')

    def warning():
        with ui.dialog() as dialog, ui.card().classes('w-[600px] max-w-[90vw] items-center justify-center '):
            ui.label("Warning: Changing the token is very unsafe without a backup (USB). Do not change the token before updating it on all your devices.").style('font-size: 1rem; font-weight: bold;')
            with ui.row().classes('gap-4 justify-end'):
                ui.button('Proceed', on_click= lambda: ui.navigate.to('/new-token')).props('color=negative')
                ui.button('Cancel', on_click= kill)
        dialog.open()

    with ui.column().classes('w-full max-w-md mx-auto mt-10 gap-4'):
        with ui.card().classes('items-center justify-center w-full p-6').style("background-color: #EFEFEF"):
            ui.label('Password Manager').classes('text-3xl font-bold text-center mb-8')
            if os.path.exists(rf"{FILE}:\PyPass\masterkey.key"):
                with ui.column().classes('gap-4'):
                    if not os.path.exists(logins) or os.path.getsize(logins) <= 1:
                        ui.button('Personal', on_click=show_personal, icon='person').classes('w-full h-12 text-lg').props('color=primary size=lg').disable()
                        find()
                        if FILE != None:
                            try:
                                threading.Thread(target=Download).start()
                                decrypt_file(en_logins, logins) # Used if we changed token and went back to /
                            except Exception as e: 
                                ui.notify(f"[ERR] {e}", type='negative')
                    else:
                        ui.button('Personal', on_click=show_personal, icon='person').classes('w-full h-12 text-lg').props('color=primary size=lg')
                        # Enable all the other buttons if the user was offline
                        if os.path.exists('logs.txt'):
                            os.remove('logs.txt')

                    if check_network() == -1:
                        ui.button('Add Password', on_click=show_add_password, icon='add').classes('w-full h-12 text-lg').props('color=primary size=lg').disable()
                        ui.button('New Token', on_click= warning, icon='generating_tokens').classes('w-full h-12 text-lg').props('color="primary" size=lg').disable()
                    else:
                        ui.button('Add Password', on_click=show_add_password, icon='add').classes('w-full h-12 text-lg').props('color=primary size=lg')
                        ui.button('New Token', on_click= warning, icon='generating_tokens').classes('w-full h-12 text-lg').props('color="primary" size=lg')
                    ui.button('Quit', on_click=shutdown, icon='highlight_off', color='#C0392B').classes('w-full h-12 text-lg text-white')
            else:
                ui.notify("Please insert the USB  key", type="negative")
                find()
                if FILE != None:
                    try:
                        Download()
                        decrypt_file(en_logins)
                    except: 
                        ui.notify("You're Offline")



@ui.page('/new-token')
def alert():
    def generate_new_key():
        find()

        # Logins 
        with open(logins, 'r') as file:
            data = json.load(file)
        for i in data:
            i['username'] = decrypt_password(i['username'])
            i['password'] = decrypt_password(i['password'])
        with open(logins, 'w') as new:
            json.dump(data, new, indent=4)

        if decrypt_file('client_secrets.enc', 'client_secrets.json') == -1:
            with open('logs.txt', 'a') as logs:
                logs.write(f"\n[ERR] generate_new_key: {e}")
                return ui.notify(f"[ERR] stupido ", type='negative')
        try:
            if os.path.exists(en_logins):
                os.remove(logins)
            if os.path.exists(fr'{FILE}:\PyPass\masterkey_old_old.key'):
                os.remove(fr'{FILE}:\PyPass\masterkey_old_old.key')
            if os.path.exists(fr'{FILE}:\PyPass\masterkey_old.key'):
                os.rename(fr'{FILE}:\PyPass\masterkey_old.key', fr'{FILE}:\PyPass\masterkey_old_old.key')

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
            os.rename(fr'{FILE}:\PyPass\masterkey.key', fr'{FILE}:\PyPass\masterkey_old.key')
        except Exception as e:
            with open('logs.txt', 'a') as logs:
                logs.write(f"\n[ERR] generate_new_key: {e}")
                return ui.notify(f"[ERR] {e} ", type='negative')

        key_path = fr"{FILE}:\PyPass\masterkey.key"
        key = Fernet.generate_key()
        with open(key_path, "wb") as file:
            file.write(key)

    def update_key():
        find()
        Download()
        if check_network() == 0:
            generate_new_key()
            with open(logins, 'r') as file:
                data = json.load(file)
            try:
                for i in data:
                    i['username'] = encrypt_password(i['username'])
                    i['password'] = encrypt_password(i['password'])

                with open(logins, 'w') as new:
                    json.dump(data, new, indent=4)

                encrypt_file('client_secrets.json', 'client_secrets.enc')
            except Exception as e:
                with open('logs.txt', 'a') as logs:
                    logs.write(f"\n[ERR] generate_new_key: {e}")
                    return ui.notify(f"[ERR] {e} ", type='negative')
                
            files = {logins:en_logins}
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
                os.remove(logins)
                os.remove('client_secrets.json')
                # new token created
                
            except Exception as e:
                with open('logs.txt', 'a') as logs:
                    logs.write(f"\n[ERR] generate_new_key 2: {e}")
                    return ui.notify(f"[ERR] {e} ", type='negative')

                
            return ui.notify("Token updated!", type='positive'), dialog.close()
        else:
            return ui.notify("Check your internet connection!", type='warning')
    # UI
    with ui.dialog() as dialog, ui.card().classes('w-[600px] max-w-[90vw] items-center justify-center '):
        ui.label("Do you want to create a new Token? The old one will no longer work.").style('font-size: 1rem; font-weight: bold;')
        with ui.row().classes('gap-4 justify-end'):
            ui.button('Yes', on_click= update_key, color='#C0392B').classes('text-white')
            ui.button('No', on_click= kill)
        
    dialog.open()



# === Personal Page ===
@ui.page('/personal')

def personal_page():
    password = ""
    if password:
        password = secure_erase(password)
    #ui.dark_mode().enable()
    with ui.header(elevated=True).style('background-color: #1976d2; text-align: center; justify-content: center'):
        ui.label('Your Passwords').style('font-size: 1.5rem; font-weight: bold; color: white;')

    with ui.column().classes('w-full max-w-md mx-auto mt-10 gap-4 items-center justify-center'):
        # logins.json
        if os.path.exists(logins) and os.path.exists(fr"{FILE}:\PyPass\masterkey.key"):
            with open(logins, 'r') as file:
                data = json.load(file)

            if data:
                for item in data:
                    if 'comment' not in item:
                        with ui.card().classes('w-full items-center justify-center').style("background-color: #EFEFEF; width: 500px"):
                            with ui.expansion(item['service']).classes('w-full items-center justify-center text-lg font-semibold text-primary'):
                                with ui.row().style('color: black'):
                                    ui.label(f"Username:")
                                    ui.label(f"{decrypt_password(item['username'])}").style('font-weight: normal;')
                                with ui.row().style('color: black'):
                                    ui.label("Password:")
                                    ui.label(f"{'•' * 8}").style('font-weight: normal;')  
                                with ui.row().classes('gap-2 justify-center').style('width: 100%;'):
                                    ui.button('Edit', on_click=lambda item=item: edit_passwd(item), icon='edit')
                                    ui.button('Remove', on_click=lambda item=item: rem_passwd(item['service']), icon='delete')
                                    ui.button('Show', on_click=lambda item=item: show_passwd(item['password']), icon='remove_red_eye')
            else:
                ui.label('Nothing to see here!')
        else:
            ui.notify('Please insert the USB key', type="negative")
            find()
            if FILE != None:
                try:
                    Download()
                    decrypt_file(en_logins, logins)
                except: 
                    ui.notify("You're Offline")
        ui.button('Back', on_click=lambda: ui.navigate.to("/"), icon='keyboard_arrow_left')

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
                with open(logins, 'w') as f:
                    json.dump(data, f, indent=4)

                # Google Drive

                threading.Thread(target=Upload).start()
                if check_network() == -1:
                    return ui.notify('Check your internet connection!', type='warning')
                kill()

            if all(i != "" for i in [service.value, username.value, password.value]):
                if os.path.exists(fr"{FILE}:\PyPass\masterkey.key"):
                    login =  {"service": f"{service.value}", "username":f"{encrypt_password(username.value)}", "password": f"{encrypt_password(password.value)}"}
                    # Writes
                    if os.path.exists(logins):
                        with open(logins, 'r') as f:
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
                                ui.button('Yes', on_click=lambda: save(check = 0), color='#C0392B').classes('text-white')
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
            if password: 
                secure_erase(password)
            with open('logs.txt', 'a') as file:
                file.write(f'[ERR] Edit_password: {e}')
            return ui.notify("Please insert the USB key", type="negative")
        except Exception as e:
            if password: 
                secure_erase(password)
            with open('logs.txt', 'a') as file:
                file.write(f'[ERR] Edit_password: {e}')
            return ui.notify(f"Error: Password is not encrypted or the key is wrong!")
            
        
        def save():
            if all(i != "" for i in [service.value, username.value, password.value]):
                # hole file
                with open(logins, 'r') as f:
                    data = json.load(f)
                # Check
                count = 0
                for i in data:
                    if i.get('service') == service.value:
                        count += 1
                if count > 1:

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
                with open(logins, 'w') as f:
                    json.dump(data, f, indent=4)

                threading.Thread(target=Upload).start()

                if check_network() == -1: return ui.notify('Check your internet connection!', type='warning')

                # Clear password in memory
                dialog.close()
                return ui.notify('Login updated!', type='positive'), ui.navigate.to('/personal') 
            
            else:
                ui.notify("Please fill in all the fields", type="negative")
                return
        with ui.row().classes('gap-4 justify-end'):
            ui.button('Save', on_click= save).props('color=primary')
            ui.button('Cancel', on_click=dialog.close)
    dialog.open()

def remove_passwd(service, dialog):
    if os.path.exists(fr"{FILE}:\PyPass\masterkey.key"):
        with open(logins, 'r') as f:
            data = json.load(f)
        if check_network() == 0:
            data = [entry for entry in data if entry.get('service') != service]
            with open(logins, 'w') as f:
                json.dump(data, f, indent=4)
            
            threading.Thread(target=Upload).start()
            dialog.close()
            ui.notify("Login removed!", type="positive")
        else:
            ui.notify('Check your internet connection!', type='warning')
            return
    else:
        ui.notify("Please insert the USB key", type="negative")

def rem_passwd(service):
    with ui.dialog() as dialog, ui.card().classes('w-[600px] max-w-[90vw] items-center justify-center '):
        ui.label("Confirm deletion: Do you really want to remove this login?").style('font-size: 1rem; font-weight: bold;')
        with ui.row().classes('gap-4 justify-end'):
            ui.button('Yes', on_click=lambda: remove_passwd(service, dialog), color='#C0392B').classes('text-white')
            ui.button('No', on_click=dialog.close)
    dialog.open()

def share_passwd(passwd):
    try:
        password = passwd
        qr_data_url = generate_qr_base64(password)
        with ui.dialog() as dialog:
            ui.image(qr_data_url).style("max-width: 25%")
        dialog.open()
    except FileNotFoundError:
        ui.notify("Please insert the USB key", type="negative")
    except Exception:
        ui.notify(f"Error: Password is not encrypted or the key is wrong!")
    finally:
        if password: 
            secure_erase(password)

def show_passwd(passwd):
    def erase_and_close(password):
        password = secure_erase(password)
        return dialog.close()
    try:
        password = decrypt_password(passwd)
    except FileNotFoundError:
        ui.notify("Please insert the USB key", type="negative")
    except Exception:
        ui.notify(f"Error: Password is not encrypted or the key is wrong!")
    finally:
        if password: 
            secure_erase(password)
    with ui.dialog() as dialog, ui.card().classes('w-[600px] max-w-[90vw] items-center justify-center'):
        ui.label("Password:").style('font-size: 1rem; font-weight: bold;')
        ui.label(f"{password}")
        with ui.row().classes('gap-4 justify-end'):
            ui.button('Copy', on_click=lambda: copy_password(password), icon='content_copy').props('color=secondary')
            ui.button('Share', on_click=lambda: share_passwd(password), icon='share')
            ui.button('Close', on_click=lambda: erase_and_close(password), icon='close')
    dialog.open()


# === Start ===
if __name__ in {"__main__", "__mp_main__"}:
    find()
    import sys
    class DummyStream:
        def write(self, msg):
            pass
        def flush(self):
            pass
        def isatty(self):
            return False
    
    # "Disable" logs 
    sys.stderr = DummyStream()
    sys.stdout = DummyStream()

    if os.path.exists('logs.txt'):
        os.remove("logs.txt")

    threading.Thread(target=Download()).start()

    ui.run(
            title='Password Manager',
            favicon='🔐',
            port=5000,
            reload = False,
            show=True
        )
