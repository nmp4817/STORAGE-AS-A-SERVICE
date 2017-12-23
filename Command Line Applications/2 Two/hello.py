import swiftclient
from hashlib import md5
from Crypto.Cipher import AES
from Crypto import Random
import os,sys
import config_local
from os import listdir
from os.path import isfile, join

encrypt_filename = "encrypt.txt"
decrypt_filename = "decrypt.txt"
encrypt_decrypt_password = 'xyz'

# config_local is py file with authentication info 
password = config_local.password
auth_url = config_local.auth_url
project_id = config_local.project_id
user_id = config_local.user_id
region_name = config_local.region_name

conn = swiftclient.Connection(key=password, authurl=auth_url, auth_version='3', os_options={"project_id": project_id, "user_id": user_id, "region_name": region_name})

cont_name = "CSE-6331 test"
# conn.put_container(cont_name)


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


def exit():
	sys.exit()

def list_files():
	files = [f for f in os.listdir('.') if os.path.isfile(f)]
	for f in files:
		print f
def enter_encryption_key():
	global encrypt_decrypt_password
	encrypt_decrypt_password = str(input("Please enter 4 digits: "))

def file_to_encrypt():
	global encrypt_decrypt_password
	global encrypt_filename
	if encrypt_decrypt_password == '':
		encrypt_decrypt_password = str(input("Please enter 4 digits encryption key: "))
	file = input("Enter name of file to encrypt: ")
	with open(file, 'rb') as src_file, open(encrypt_filename,'wb') as encrypt_file:
	    encrypt(src_file, encrypt_file, encrypt_decrypt_password)

def decrypt_file():
	global encrypt_decrypt_password
	global decrypt_filename
	if encrypt_decrypt_password == '':
		encrypt_decrypt_password = str(input("Please enter 4 digits encryption key: "))
	encrypt_filename = input("Enter name of file to decrypt: ")
	with open(encrypt_filename, 'rb') as encrypt_file, open(decrypt_filename,'wb') as decrypt_file:
		decrypt(encrypt_file, decrypt_file, encrypt_decrypt_password)

def create_container():
	cont_name = input("Enter name of container: ")
def upload_file_to_cloud():
	global conn
	for container in conn.get_account()[1]:
		print container['name']
	cont_name = input("Enter name of container: ")
	filename = input("Enter name of file: ")
	with open(filename,'rb') as src_file:
		conn.put_object(cont_name, "test.txt", contents= src_file.read())

def delete_file_from_cloud():
	global conn
	for container in conn.get_account()[1]:
		print container['name']
	cont_name = input("Enter name of container: ")
	filename = input("Enter name of file: ")
	conn.delete_object(cont_name, file_name)

def list_files_from_cloud():
	for container in conn.get_account()[1]:
		print container['name']
	cont_name = input("Enter name of container: ")
	for container in conn.get_account()[1]:
		if container['name'] == cont_name:
			for data in conn.get_container(container['name'])[1]:
				print 'object: {0} \t size: {1} \t date: {2}'.format(data['name'], data['bytes'], data['last_modified'])

def download_file_from_cloud():
	global conn
	global encrypt_filename
	for container in conn.get_account()[1]:
		print container['name']
	cont_name = input("Enter name of container: ")
	filename = input("Enter name of file: ")
	obj = conn.get_object(cont_name, "test.txt")
	with open(encrypt_filename, 'wb') as encrypt_file:
		encrypt_file.write(obj[1])

def delete_file_localy():
	filename = input("Enter name of file to delete: ")
	os.remove(filename)

def delte_more_than_size():
	global conn
	
	cont_name = input("Enter name of container: ")
	size = input("Enter size in bytes")
	for container in conn.get_account()[1]:
		if container['name'] == cont_name:
			for data in conn.get_container(container['name'])[1]:
				if data['bytes'] > size:
					conn.delete_object(cont_name, data['name'])
def delete_container():
	for container in conn.get_account()[1]:
		print container['name']
	cont_name = input("Enter name of container: ")
	conn.delete_container(cont_name)
	
options = {0 : exit,
   1 : list_files,
   2 : enter_encryption_key,
   3 : file_to_encrypt,
   4 : decrypt_file,
   5 : create_container,
   6 : upload_file_to_cloud,
   7 : delete_file_from_cloud,
   8 : list_files_from_cloud,
   9 : download_file_from_cloud,
   10 : delete_file_localy,
   11 : delte_more_than_size,
   12 : delete_container
}

print "Menu:\n 0. Exit \n 1. List Files \n 2. Enter encryption key \n 3. Enter name of file to encrypt \n 4. Enter name of file to decrypt \n 5. Create container  \n 6. Upload file to cloud \n 7. Delete file from cloud \n 8. List cloud files \n 9. Download file from cloud \n 10. Delete file from local \n 11. Delete more than specific size \n 12. Delete container from cloud"

while(1):
	n = input("Select one option: ")
	options[n]()
