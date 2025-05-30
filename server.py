import socket
import os
import time
import ssl

HOST = '127.0.0.1'
CONTROL_PORT = 21
DATA_PORT = 2021
BASE_DIR = os.getcwd()

users = {
    "u1": {"pass":"123","read_access":True, "write_access":False,"delete_access":True,"create_access":False},
    "u2": {"pass":"456","read_access":False,"write_access":False,"delete_access":True,"create_access":True},
    "u3": {"pass":"789","read_access":True, "write_access":True, "delete_access":True,"create_access":True},
}

class FTPServer:
    def __init__(self, host, control_port, data_port):
        self.host = host
        self.control_port = control_port
        self.data_port = data_port
        self.current_dir = BASE_DIR
        self.user_authenticated = False

    def start(self):
        
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        context.load_cert_chain(certfile="server.crt", keyfile="server.key")
        
        control_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        control_socket.bind((self.host, self.control_port))
        control_socket.listen(1)
        print(f"Server started on {self.host} Port:{self.control_port}")
        control_socket = context.wrap_socket(control_socket, server_side=True)
        
        data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        data_socket.bind((self.host, self.data_port))
        data_socket.listen(1)
        print(f"Data connection on {self.host} Port:{self.data_port}")
        data_socket = context.wrap_socket(data_socket, server_side=True)
        
        while True:
            control_conn, addr = control_socket.accept()
            print(f"Control connection established with {addr}")
            data_conn, _ = data_socket.accept()
            print("Data connection established.")

            self.handle_client(control_conn, data_conn)

    def handle_client(self, control_conn, data_conn):
        
        control_conn.send(b"** Welcome to FTP Server **\r\n")
        username = None
        
        while True:
            command = control_conn.recv(1024).decode().strip()
            if not command:
                break

            print(f"Received command: {command}")
            cmd, *args = command.split()
            arg = " ".join(args)

            if cmd.upper() == "USER":
                if arg in users:
                    username = arg
                    control_conn.send(b"    *331* Username accepted enter password.\r\n")
                else:
                    control_conn.send(b"    *530* Invalid username.\r\n")

            elif cmd.upper() == "PASS":
                if username and users[username]["pass"] == arg:
                    self.user_authenticated = True
                    control_conn.send(b"    *230* Login successful.\r\n")
                else:
                    control_conn.send(b"    *530* Invalid password.\r\n")

            elif cmd.upper() == "LIST":
                if not self.user_authenticated:
                    control_conn.send(b"    *530* Please login first.\r\n")
                elif not users[username]["read_access"]:
                    control_conn.send(b"    *530* You do not have read access.\r\n")
                else:
                    path = arg if arg else self.current_dir
                    try:
                        control_conn.send(b"    *125* Opening data connection.\r\n")
                        files = os.listdir(path)
                        file_info_list = []
                        for file in files:
                          file_path = os.path.join(path, file)
                          size = os.path.getsize(file_path)
                          mtime = time.ctime(os.path.getmtime(file_path))  
                          file_info_list.append(f"{mtime} | {file} | {size} bytes ")
        
                        file_list = "\n".join(file_info_list)
                        control_conn.sendall(file_list.encode())
                        control_conn.send(b"\n    *226* Transfer complete.\r\n")
                    except FileNotFoundError:
                        control_conn.send(b"    *550* Path not found.\r\n")

            elif cmd.upper() == "RETR":
                if not self.user_authenticated:
                    control_conn.send(b"    *530* Please login first.\r\n")
                elif not users[username]["read_access"]:
                    control_conn.send(b"    *530* You do not have read access.\r\n")    
                else:
                    try:
                        with open(arg, "rb") as file:
                            control_conn.send(b"    *150* Opening data connection.\r\n")
                            data_conn.send(file.read())
                            control_conn.send(b"    *226* Transfer complete.\r\n")
                    except FileNotFoundError:
                        control_conn.send(b"    *550* File not found.\r\n")

            elif cmd.upper() == "STOR":
                if not self.user_authenticated:
                    control_conn.send(b"    *530* Please login first.\r\n")
                elif not users[username]["write_access"]:
                    control_conn.send(b"    *530* You do not have write access.\r\n")    
                else:
                    try:
                        control_conn.send(b"    *150* Ready to receive file.\r\n")
                        with open(arg, "wb") as file:
                             data = data_conn.recv(1024*1024*10)
                             file.write(data)
                        control_conn.send(b"    *226* Transfer complete.\r\n")
                    except Exception:
                        control_conn.send(b"    *550* Error saving file.\r\n")

            elif cmd.upper() == "DELE":
                if not self.user_authenticated:
                    control_conn.send(b"    *530* Please login first.\r\n")
                elif not users[username]["delete_access"]:
                    control_conn.send(b"    *530* You do not have delete access.\r\n")    
                else:
                    try:
                        os.remove(arg)
                        control_conn.send(b"    *250* File deleted successfully.\r\n")
                    except FileNotFoundError:
                        control_conn.send(b"    *550* File not found.\r\n")
                        
            elif cmd.upper() == "MKD":
                if not self.user_authenticated:
                    control_conn.send(b"    *530* Please login first.\r\n")
                elif not users[username]["create_access"]:
                    control_conn.send(b"    *530* You do not have create access.\r\n")    
                else:
                    try:
                        os.makedirs(arg)
                        control_conn.send(f"    *257* \"{arg}\" directory created.\r\n".encode())
                    except Exception as e:
                        control_conn.send(f"    *550* Failed to create directory: {e}\r\n".encode())

            elif cmd.upper() == "RMD":
                if not self.user_authenticated:
                    control_conn.send(b"    *530* Please login first.\r\n")
                elif not users[username]["delete_access"]:
                    control_conn.send(b"    *530* You do not have delete access.\r\n")    
                else:
                    try:
                        os.rmdir(arg)
                        control_conn.send(f"    *250* Directory \"{arg}\" removed successfully.\r\n".encode())
                    except Exception as e:
                        control_conn.send(f"    *550* Failed to remove directory: {e}\r\n".encode())

            elif cmd.upper() == "PWD":
                if not self.user_authenticated:
                    control_conn.send(b"    *530* Please login first.\r\n")
                elif not users[username]["read_access"]:
                    control_conn.send(b"    *530* You do not have read access.\r\n")    
                else:
                    control_conn.send(f"    *257* \"{self.current_dir}\"\r\n".encode())

            elif cmd.upper() == "CWD":
                if not self.user_authenticated:
                    control_conn.send(b"    *530* Please login first.\r\n")
                elif not users[username]["write_access"]:
                    control_conn.send(b"    *530* You do not have write access.\r\n")        
                else:
                    try:
                        os.chdir(arg)
                        self.current_dir = os.getcwd()
                        control_conn.send(b"    *250* Directory changed.\r\n")
                    except FileNotFoundError:
                        control_conn.send(b"    *550* Directory not found.\r\n")
            elif cmd.upper() == "CDUP":
                if not self.user_authenticated:
                    control_conn.send(b"    *530* Please login first.\r\n")
                elif not users[username]["write_access"]:
                    control_conn.send(b"    *530* You do not have write access.\r\n")        
                else:
                    try:
                        parent_dir = os.path.dirname(self.current_dir)
                        os.chdir(parent_dir)
                        self.current_dir = os.getcwd()
                        control_conn.send(b"    *250* Directory changed to parent.\r\n")
                    except Exception as e:
                        control_conn.send(f"    *550* Failed to change directory: {e}\r\n".encode())

            elif cmd.upper() == "QUIT":
                control_conn.send(b"    *221* Goodbye.\r\n")
                break

            else:
                control_conn.send(b"    *502* Command not implemented.\r\n")

        control_conn.close()
        data_conn.close()

if __name__ == "__main__":
    server = FTPServer(HOST, CONTROL_PORT, DATA_PORT)
    server.start()
    file_info_list = []
        
    