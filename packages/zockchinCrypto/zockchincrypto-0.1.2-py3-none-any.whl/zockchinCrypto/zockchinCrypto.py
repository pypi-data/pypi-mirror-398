import random
import base64
import os
from cryptography.fernet import Fernet


def VigEncryption(text, _key):
    msg = text
    key = _key
    len_key = len(key)
    encrypted = ""
    for i, ch in enumerate(msg):
        if ch.isalpha():
            start = ord('a') if ch.islower() else ord('A')
            shift = ord(key[i % len_key].lower()) - ord('a')
            encrypted += chr((ord(ch) - start + shift) % 26 + start)
        else:
            encrypted += ch
    return encrypted

def VigDeciphering(text, _key):
    msg = text
    key = _key
    len_key = len(key)
    encrypted = ""
    for i, ch in enumerate(msg):
        if ch.isalpha():
            start = ord('a') if ch.islower() else ord('A')
            shift = ord(key[i % len_key].lower()) - ord('a')
            encrypted += chr((ord(ch) - start - shift) % 26 + start)
        else:
            encrypted += ch
    return encrypted

def ReplacementEncryption(_list, text, key):
    list_ = list(_list)
    key_list = list(key) 
    cipher_text = ""
    for char in text:
        if char in list_:
            index_in_list = list_.index(char)
            cipher_text += key_list[index_in_list]
        else:
            cipher_text += char 
    return cipher_text

def ReplacementDecryption(_list, cipher_text, key):
    list_ = list(_list)
    key_list = list(key)
    plain_text = ""
    for char in cipher_text:
        if char in key_list:
            index_in_key = key_list.index(char)
            plain_text += list_[index_in_key]
        else:
            plain_text += char
    return plain_text

def CaesarEncryption(text, key, _list):
    alphabet = list(_list)
    msg = text
    shift = key
    encrypted = ""
    for ch in msg:
        if ch in alphabet:
            index = alphabet.index(ch)      
            new_index = (index + shift) % 26 
            encrypted += alphabet[new_index] 
        else:
            encrypted += ch
    return encrypted

def CaesarDecryption(text, key, _list):
    alphabet = list(_list)
    msg = text
    shift = key
    encrypted = ""
    for ch in msg:
        if ch in alphabet:
            index = alphabet.index(ch)      
            new_index = (index - shift) % 26 
            encrypted += alphabet[new_index] 
        else:
            encrypted += ch
    return encrypted

def ferentTextEncryption(text):
    msg = text.encode()
    fileKEYname = 'ftext_key.pem'
    key = Fernet.generate_key()
    if not os.path.exists(fileKEYname):
        with open(fileKEYname, "wb") as f:
            f.write(key)
    with open(fileKEYname, 'rb') as f:
        keyFromfile = f.read()
    cipher = Fernet(keyFromfile)
    Etext = cipher.encrypt(msg)
    return Etext.decode()

def ferentTextDecryption(encrypted_text):
    fileKEYname = 'ftext_key.pem'
    if not os.path.exists(fileKEYname):
        return "Key file not found."
    with open(fileKEYname, 'rb') as f:
        keyFromfile = f.read()
    cipher = Fernet(keyFromfile)
    try:
        decrypted_bytes = cipher.decrypt(encrypted_text.encode())
        return decrypted_bytes.decode()
    except Exception as e:
        return f"Decryption failed: {e}"

def ferentFileEncryption(_path, extension):
    fileKEYname = 'ffile_key.pem'
    key = Fernet.generate_key()
    if not os.path.exists(fileKEYname):
        with open(fileKEYname, "wb") as f:
            f.write(key)
    with open(fileKEYname, 'rb') as f:
        keyFromfile = f.read()
    cipher = Fernet(keyFromfile)
    with open(f'{_path}.{extension}', 'rb') as f:
        fileText = f.read()
    encrypte = cipher.encrypt(fileText)
    with open(f'encrypted_file.{extension}', 'wb') as f:
        f.write(encrypte)

def ferentFileDecryption(_path, extension):
    fileKEYname = 'ffile_key.pem'
    with open(fileKEYname, 'rb') as f:
        keyFromfile = f.read()
    cipher = Fernet(keyFromfile)
    with open(f'{_path}.{extension}', 'rb') as f:
        encrypted_fileText = f.read()
    decrypted = cipher.decrypt(encrypted_fileText)
    with open(f'decrypted_file.{extension}', 'wb') as f:
        f.write(decrypted)