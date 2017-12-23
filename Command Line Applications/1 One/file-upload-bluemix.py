import swiftclient
import sys
import config_local
from hashlib import md5
from Crypto.Cipher import AES
from Crypto import Random

# config_local is py file with authentication info 
password = config_local.password
auth_url = config_local.auth_url
project_id = config_local.project_id
user_id = config_local.user_id
region_name = config_local.region_name

filename = "test.txt"
encrypt_filename = "encrypt.txt"
decrypt_filename = "decrypt.txt"
encrypt_decrypt_password = "xyz"

cont_name = "CSE-6331 test"

conn = swiftclient.Connection(key=password, authurl=auth_url, auth_version='3', os_options={"project_id": project_id, "user_id": user_id, "region_name": region_name})

def derive_key_and_iv(password, salt, key_length, iv_length):
    d = d_i = ''
    while len(d) < key_length + iv_length:
        d_i = md5(d_i + password + salt).digest()
        d += d_i
    return d[:key_length], d[key_length:key_length+iv_length]

def encrypt(in_file, out_file, password, key_length=32):
    bs = AES.block_size
    salt = Random.new().read(bs - len('Salted__'))
    key, iv = derive_key_and_iv(password, salt, key_length, bs)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    out_file.write('Salted__' + salt)
    finished = False
    while not finished:
        chunk = in_file.read(1024 * bs)
        if len(chunk) == 0 or len(chunk) % bs != 0:
            padding_length = (bs - len(chunk) % bs) or bs
            chunk += padding_length * chr(padding_length)
            finished = True
        out_file.write(cipher.encrypt(chunk))

def decrypt(in_file, out_file, password, key_length=32):
    bs = AES.block_size
    salt = in_file.read(bs)[len('Salted__'):]
    key, iv = derive_key_and_iv(password, salt, key_length, bs)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    next_chunk = ''
    finished = False
    while not finished:
        chunk, next_chunk = next_chunk, cipher.decrypt(in_file.read(1024 * bs))
        if len(next_chunk) == 0:
            padding_length = ord(chunk[-1])
            chunk = chunk[:-padding_length]
            finished = True
        out_file.write(chunk)

# conn.put_container(cont_name)
def upload():
    print "\nEncryption started for file: "+filename
    
    with open(filename, 'rb') as src_file, open(encrypt_filename,'wb') as encrypt_file:
        encrypt(src_file, encrypt_file, encrypt_decrypt_password)

    print "\nEncryption done stored in file: "+encrypt_filename

    print "\nUploading the encrypted file in bluemix container: "+cont_name

    with open(encrypt_filename,'rb') as encrypt_file:
        conn.put_object(cont_name, filename, contents= encrypt_file.read())

    print "\nFile successfully uploaded: "+filename+" in bluemix container: "+cont_name

def download():
    print "\nReading encrypted file: "+filename+" from bluemix container: "+cont_name    

    obj = conn.get_object(cont_name, filename)

    print "\nWriting content of file: "+filename+" to file: "+encrypt_filename

    with open(encrypt_filename, 'wb') as encrypt_file:
        encrypt_file.write(obj[1])

    print "\nDecryption started for file: "+encrypt_filename

    with open(encrypt_filename, 'rb') as encrypt_file, open(decrypt_filename,'wb') as decrypt_file:
        decrypt(encrypt_file, decrypt_file, encrypt_decrypt_password)

    print "\nDecryption done stored in file: "+decrypt_filename

def delete():
    print "\nDeleting file:"+filename+" from bluemix container: "+cont_name

    conn.delete_object(cont_name, filename)

    print "\nSuccessfully deleted file:"+filename+" from bluemix container: "+cont_name

if __name__ == "__main__":
    print "\nStarting upload................."
    upload()
    print "\nStartring downlaod.............."
    download()
    print "\nDeleting From container........."
    delete()