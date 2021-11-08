import os, shutil, stat, sys, random, logging
from subprocess import call
from cryptography.fernet import Fernet
from tqdm import tqdm
from datetime import datetime

# Warnings: Rollback and Backup features have not been done,
# There is a possibility of decrypting with the wrong key and 
# overwriting the formerly encrpted files, that can be disastrous

class Timelock():

    def __init__(self, dir, date, email, force_write=False):

        self.is_futurepy_module_installed()

        self.email = email
        self.dir = dir
        self.date = datetime.strptime(date, "%d-%m-%Y")
        self.force_write = force_write
        self.message_key = Fernet.generate_key()
        self.encryption_key = Fernet.generate_key()
        self.num_of_files = self.get_num_of_files()
        self.pbar = None

        logging.basicConfig(filename=self.log_dir(), format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')

    def is_futurepy_module_installed(self):
        if os.path.exists(rf'{sys.exec_prefix}\Scripts\futurepy.exe'):
            pass
        else:
            print('[Error] You might not have futurepy module installed\nhint: pip install futurepy')
            sys.exit(1)

    # adds time component to date and validates the date
    def is_valid_date(self):
            datenow = datetime.now()
            self.date = datetime.combine(self.date.date(), datenow.time())
            if self.date > datenow:
                if (self.date - datenow).days >= 7:
                    return True
            return False

    def save_message_key(self):
        if os.path.isfile(self.dir):
            save_dir = os.path.dirname(self.dir)
        else:
            save_dir = self.dir
        with open(rf'{save_dir}/timelock.key', 'wb') as file:
            file.write(self.message_key)

    def send_key_to_the_future(self, destroy_key=True):
        fernet = Fernet(self.message_key)
        date = datetime.strftime(self.date, '%Y%m%d')
        subject = f"Timelock Encrypted Message ({datetime.strftime(self.date, '%d-%m-%Y')})"
        message = fernet.encrypt(self.encryption_key).decode(encoding='utf-8')

        try:
            # Workaround to access modules(futurepy) from subprocess in virtual environments
            #
            # Weird issue causes space in front of parameters after argument has been parsed, 
            # workaround is removing space beforehand
            with open('send this message to the future.txt', 'w') as file:
                file.write(message)
            """
            returncode = call([rf'{sys.exec_prefix}\Scripts\futurepy.exe', "--debug", f"-s'{subject}'", f"-b'{message}'", f"-d{date}", f"-e{self.email}", "-c"])
            print(returncode)
            input()
            if returncode  != 0:
                raise 
            """
        except Exception as e:
            self.pbar.close()
            print(e, '--> An unknown error has occurred\nRolling back changes')
            rollback = False
            if rollback:
                print('Rollback completed sucessfully')
            else:
                name = f'encryption-{random.getrandbits(30)}.key'
                with open(name, 'wb') as file:
                    file.write(self.encryption_key)
                print(f"Unable to complete rollback, stored the encryption key in './{name}'")
                print(f"hint: with open('./{name}', 'rb') as file:")
                print('      \tencryption_key = file.read()')                
                print('      \tTimelock.unlock(encryption_key=encryption_key)')
                sys.exit(1)
            return
        
        if destroy_key:
            self.encryption_key = None

    def get_num_of_files(self): 
        # count = sum([len(files) for r, d, files in os.walk(self.dir)])
        count = list()
        for r, d, files in os.walk(self.dir):
            # Skipping failed files
            try:                
                if os.path.samefile(r, f'{self.root_dir()}/timelock-fails/encryption') or os.path.samefile(r, f'{self.root_dir()}/timelock-fails/decryption'): 
                    continue
            except:
                pass
            count.append(len(files))
        count = sum(count)
        
        # Remove file from count since it's not being encrypted
        if os.path.exists(self.get_timelock_dir()):
            count = count - 1
        if os.path.exists(self.log_dir()):
            count = count - 1
        return count

    def root_dir(self):
        if os.path.isfile(self.dir):
            dir = os.path.dirname(self.dir)
        else:
            dir = self.dir
        return dir

    def get_timelock_dir(self):    
        return f'{self.root_dir()}/timelock.key'
    
    def log_dir(self):
        return f'{self.root_dir()}/timelock.log'

    def lock(self):
        if self.is_valid_date():
            pass
        else:
            print(f"[InvalidDate Error] '{self.date.strftime('%d-%m-%Y')}' --> a valid date should be at least 7 days from now")
            sys.exit(1)  

        print(f'Timelocking files at {self.date}...')
        fernet = Fernet(self.encryption_key)

        self.pbar = tqdm(total=self.num_of_files, desc='Encrypting files')

        # Encrypting files
        for root, dirs, files in os.walk(self.dir):
            # Skipping failed files
            try:
                if os.path.samefile(root, f'{self.root_dir()}/timelock-fails/encryption') or os.path.samefile(root, f'{self.root_dir()}/timelock-fails/decryption'): 
                    continue
            except:
                pass 
            for file in files: 
                dir = os.path.join(root, file)
                
                # Skipping timelock.key and timelock.log file
                try:
                    if os.path.samefile(dir, self.get_timelock_dir()) or os.path.samefile(dir, self.log_dir()): continue
                except:
                    pass

                if self.force_write:
                    os.chmod(dir, stat.S_IWRITE)  # Change file permissions to writable

                try:
                    with open(dir, 'rb') as file:
                        data = file.read()

                    data_encrypted = fernet.encrypt(data)

                    with open(dir, 'wb') as file:
                        file.write(data_encrypted)
                except Exception as e:
                    fails = self.root_dir()+'/timelock-fails/encryption'

                    if not os.path.exists(fails):
                        os.makedirs(fails)

                    try:
                        shutil.move(dir, fails)
                    except Exception as err:
                        logging.error(f'{err} --> {file}')
                        pass
                    logging.error(f'{e} --> {file}')
                    continue
                finally:    
                    self.pbar.update(1) 

        self.pbar.set_description('Sending encryption key to the future')
        self.send_key_to_the_future(destroy_key=True)
        self.save_message_key()

        self.pbar.set_description('Completed Encryption')
        self.pbar.close()

    def unlock(self, **kwargs):
        self.pbar = tqdm(total=self.num_of_files, desc="Opening message key file --> 'timelock.key'")

        if 'email_message' in kwargs and 'encryption_key' in kwargs:
            self.pbar.close()
            print("You cannot set parameters for both 'email_message' and 'encryption_key'")
            sys.exit(1)
        elif 'email_message' in kwargs:
            email_message = kwargs['email_message']
            try:
                with open(f'{self.get_timelock_dir()}', 'rb') as file:
                    message_key = file.read()
            except Exception as e:
                print(e, "--> Make sure Key: 'timelock.key' is in root directory of encrypted files")

            self.pbar.set_description('Decrypting email message containing encryption key')

            # Decrypting message containing encryption key
            fernet = Fernet(message_key)
            encryption_key = fernet.decrypt(email_message.encode())
            fernet = Fernet(encryption_key)
        elif 'encryption_key' in kwargs:
            encryption_key = kwargs['encryption_key']
            fernet = Fernet(encryption_key)
        
        self.pbar.set_description('Decrypting files')

        # Decrypting files
        for root, dirs, files in os.walk(self.dir):
            # Skipping failed files
            try:
                if os.path.samefile(root, f'{self.root_dir()}/timelock-fails/encryption') or os.path.samefile(root, f'{self.root_dir()}/timelock-fails/decryption'): 
                    continue
            except:
                pass 
            for file in files: 
                dir = os.path.join(root, file)

                # Skipping timelock.key and timelock.log file
                if os.path.samefile(dir, self.get_timelock_dir()) or os.path.samefile(dir, self.log_dir()): continue

                if self.force_write:
                    os.chmod(dir, stat.S_IWRITE)  # Change file permissions to writable

                try:
                    with open(dir, 'rb') as file:
                        data = file.read()

                    data_decrypted = fernet.decrypt(data)

                    with open(dir, 'wb') as file:
                        file.write(data_decrypted)
                except Exception as e:
                    fails = self.root_dir()+'/timelock-fails/decryption'

                    if not os.path.exists(fails):
                        os.makedirs(fails)

                    try:
                        shutil.move(dir, fails)
                    except Exception as err:
                        logging.error(f'{err} --> {file}')
                        pass
                    logging.error(f'{e} --> {file}')
                    continue
                finally:
                    self.pbar.update(1) 

        self.pbar.set_description('Completed Decryption')         
        self.pbar.close()
