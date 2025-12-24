# zockchinCrypto 🔐

A lightweight and easy-to-use Python library for text and file encryption. It supports modern encryption standards like **Fernet (AES)** and classic algorithms like the **Caesar Cipher**.

## Features
- **Text Encryption:** Secure your strings using Fernet symmetric encryption.
- **File Encryption:** Encrypt any file type (images, PDFs, ZIP files, etc.).
- **Automatic Key Management:** Automatically generates and manages secure keys in `.pem` files.
- **Caesar Cipher:** Includes the classic Caesar shift cipher for educational purposes.
- **Robust:** Built on top of the industry-standard `cryptography` library.

## Installation

Install the library using `pip`:

```bash
pip install zockchinCrypto




#How to use the Vigenere Cipher
import zockchinCrypto

# Encryption using Vigenère (Verna)
Encryption = zockchinCrypto.VigEncryption('egypt is frist', 'key')
print(Encryption)  # Output: okwzx sw pvgcx

# Decryption using Vigenère (Verna)
Deciphering = zockchinCrypto.VigDeciphering('okwzx sw pvgcx', 'key')
print(Deciphering)  # Output: egypt is frist





#How to use the Replacement Cipher
st = string.ascii_letters + string.digits + string.punctuation
key = list(st)
random.shuffle(key)
print(key)
Replacement  = zockchinCrypto.ReplacementEncryption(st , 'zockchin',key)
print(Replacement)

#Add here the previous list you obtained during encryption
Replacement  = zockchinCrypto.ReplacementDecryption(st , '8TlKl"I<',['z', '/', 'l', 'A', 'x', 'G', ':', '"', 'I', '=', 'K', '5', 'C', '<', 'T', '`', 'F', '{', 't', 'p', '?', "'", 'O', 'Z', 'W', '8', ',', ';', '}', 'y', 'g', 'D', 'r', 'h', 'a', 'L', '@', 'N', 'H', 's', 'v', 'j', '^', 'i', ']', 'X', '!', 'E', '-', '#', 'e', 'V', 'Q', 'u', '0', 'Y', 'P', 'B', ')', 'n', '>', 'k', '[', '3', 'M', 'c', '(', 'd', 'q', 'J', '%', '6', 'w', '_', 'R', 'U', '|', '9', '1', 'f', 'b', 'o', '4', '\\', '+', '$', '2', '.', 'S', '*', 'm', '7', '~', '&'])

print(Replacement)




#How to use Caesar cipher
a = zockchinCrypto.CaesarEncryption('zockchin',3,'abcdefghijklmnopqrstuvwxyz')
print('caesar  ',a)

a = zockchinCrypto.CaesarDecryption('cbdg',3,'abcdefghijklmnopqrstuvwxyz')
print('caesar  ',a)




#Method of encrypting and decrypting text using the Ferent code

Encryption = zockchinCrypto.ferentTextEncryption('zockchin')
print(Encryption)

Decryption = zockchinCrypto.ferentTextDecryption('gAAAAABpRzfC7t_hQ26YHtb949YUi5UvwxWT7lelqSwt2gKPeUP5_H-AynkIZW7XGjFej-popoB6AO_erkYOO66SCPkARt7u5Q==')
print(Decryption)



#Method of encrypting and decrypting file using the Ferent code

FileEncryption = zockchinCrypto.ferentFileEncryption('test','rar')

FileDecryption = zockchinCrypto.ferentFileDecryption('encrypted_file','rar')

