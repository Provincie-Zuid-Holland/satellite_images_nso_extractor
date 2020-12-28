from cryptography.fernet import Fernet
import os
"""
    Class to encrypt a string to avoid hard coding.

    author: Michael de Winter

"""

def generate_key(path):
    """
    Generates a key and save it into a file
    """
    key = Fernet.generate_key()
    with open(path+'/secret.key', "wb") as key_file:
        key_file.write(key)

def load_key(path):
    """
    Loads the key named `secret.key` from the current directory.
    """
    #return open(path+'/secret.key', "rb").read()
    return "r12by_tRKvtXxCLoskLzj6v8UgBWwnjHWXmf9nnmjIc="


def encrypt_message(message, path):
    """
    Encrypts a message
    """
    key = load_key(path)
    encoded_message = message.encode()
    f = Fernet(key)
    encrypted_message = f.encrypt(encoded_message)

    print(encrypted_message)


def decrypt_message(encrypted_message):
    """
    Decrypts an encrypted message
    """
    key = load_key(os.path.dirname(os.path.realpath(__file__)).replace('\\','/'))
    f = Fernet(key)
    decrypted_message = f.decrypt(encrypted_message)

    return(decrypted_message.decode())

def get_nso_credentials():
     """
        Automatically get the NSO credentials.

        TODO: Strings need to be replaced for login credentials.
     """

     user = decrypt_message(b'gAAAAABfcu0jGodTmtcPP2zl-VmEa6eIij1aenI2HDVqgdPVwTL_Au7g2bq8CPNEAoHwJJlXiRK34fEbq52LU0peFPqn5UsZ_Q==')   
     password = decrypt_message(b'gAAAAABfcu2eMNKRjxyrae6duxPC9YJpvFtdBywHE6klqtvUlZFu6HnKI0_BlCpi7-2_n0L0WGzkKttaXYqiYEy04mow-vOFLBZ-COtnA0El5V4myK-lVaQ=')

     return user,password