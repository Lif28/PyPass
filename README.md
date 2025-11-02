# PyPass Manager

**PyPass Manager** is an open-source password manager that implements **end-to-end encryption (E2EE)** and **two-factor authentication (2FA)** to ensure the highest security for your sensitive data. This tool is designed to provide a secure, reliable, and easy-to-use solution for password management.

---

## 🔒 Security

### End-to-End Encryption (E2EE)
PyPass Manager uses the `cryptography.fernet` library to encrypt data locally before it is saved or synchronized. This means:
- **Only you** can access your data, as encryption happens on your device.
- Data is protected even during synchronization via WebDAV.

### Master Key
- The **master key** is stored on an external USB drive, ensuring that only someone with physical access to the USB can access the encrypted data.
- The master key is required to encrypt and decrypt data, adding an extra layer of security.

### Two-Factor Authentication (2FA)
- **Mandatory**: PyPass Manager requires two-factor authentication to access its main features.
- You can use an authentication app like **Google Authenticator** or **Authy** to generate 2FA codes.
- This adds an additional layer of security, ensuring that even if someone gets your password, they cannot access your data without the second authentication factor.

### Secure Password Generation
- Generated passwords include a combination of uppercase letters, lowercase letters, numbers, and symbols.
- Password generation happens locally on your device, ensuring that passwords are never transmitted in plaintext.

---

## 📋 Features

- **Secure Password Generation**: Generates complex and secure passwords.
- **End-to-End Encryption**: All passwords are encrypted before being saved or synchronized.
- **WebDAV Synchronization**: Syncs encrypted data with a WebDAV server.
- **Two-Factor Authentication (2FA)**: Additional protection for accessing main features.
- **Key Management**: Uses a master key stored on a USB drive.
- **QR Codes**: Generates QR codes for secure sharing of information.
- **Intuitive User Interface**: Developed with `nicegui` for a simple and modern user experience.

---

## 📦 Libraries Used

- `nicegui`: Framework for creating interactive web user interfaces.
- `qrcode`: Library for generating QR codes.
- `cryptography`: Library for encrypting and decrypting data, using secure algorithms like **Fernet** (AES in CBC mode with HMAC).
- `webdav3`: Client for synchronizing with WebDAV servers.
- `pyperclip`: Library for managing the system clipboard.
- `os`, `json`, `base64`, `string`, `random`, `ctypes`: System libraries for file management, random data generation, and secure memory manipulation.

---

## ✨ Strengths

- **Advanced Security**: Implementation of **end-to-end encryption** and **two-factor authentication (2FA)**.
- **Portability**: Ability to synchronize encrypted data via WebDAV.
- **Intuitive User Interface**: Uses `nicegui` for a simple and modern user experience.
- **Robust Password Generation**: Generates secure and complex passwords that comply with security standards.

---

## 🔧 How to use PyPass (Windows Only)

### STEP 1 - Installing the dependencies:
- Install python from the official website: https://www.python.org/downloads/
- Install the libraries: `pip install nicegui qrcode cryptography webdav3 pyperclip`
- Install pyinstaller: `pip install pyinstaller`


### STEP 2 - Installing PyPass: 
- Clone the repository: `git clone https://github.com/Lif28/PyPass.git`
- Open a terminal inside the folder PyPass.
- Type `pyinstaller --noconfirm --onedir --windowed --icon "PyPass.ico" --name "PyPass" --clean --add-data "####\site-packages\nicegui;nicegui/" --add-data "connect.py;." --exclude-module "PyQt6" --exclude-module "PySide6"  "main.py"`
  (replace #### with the directory of nicegui)

### STEP 3 - Using PyPass:
1) #### Open PyPass.

<div align="center">
  <br>
  <img width="283" height="163" alt="image" src="https://github.com/user-attachments/assets/fdb1ceae-775e-4118-8ba0-fb59f6fa82ca" align="middle" />
  <br>
</div>

2) #### Enter your nextcloud credentials.

<div align="center">
  <br>
  <img width="1919" height="851" alt="image" src="https://github.com/user-attachments/assets/a063999e-5805-4bb6-bd26-a9e260578e7b" />
  <br>
</div>

3) #### Start adding your logins (you can adjust the lenght of the password).

<div align="center">
  <br>
  <img width="497" height="417" alt="image" src="https://github.com/user-attachments/assets/568994fc-62dd-4dd9-afae-87095f0c4709" />
  <br>
</div>

4) #### See your logins by clicking the Personal button.

<div align="center">
  <br>
  <img width="1919" height="907" alt="image" src="https://github.com/user-attachments/assets/74c26ef6-7369-43c3-9962-db853b5d6237" />
  <br>
</div>







---

## 📂 Project Structure

