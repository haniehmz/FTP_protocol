import os
import time
import socket
import ssl

def ftp_client():
    host = '127.0.0.1'
    control_port = 21
    data_port = 2021

    context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    context.check_hostname = False
    context.verify_mode = ssl.CERT_REQUIRED
    context.load_verify_locations(f'F:\python\CN project\cnproject2\cnproject2\server.crt')  
    control_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    control_socket.connect((host, control_port))
    control_socket = context.wrap_socket(control_socket, server_hostname=host)

    data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    data_socket.connect((host, data_port))
    data_socket = context.wrap_socket(data_socket, server_hostname=host)

    def send_command(command):

        control_socket.send(f"{command}\r\n".encode())
        response = control_socket.recv(1024).decode()
        print(response)
        return response
    
    print(control_socket.recv(1024).decode()) 

    while True:
        command = input("Enter FTP command: ")
      
        if command.upper() == "QUIT":
            send_command(command)
            break
        elif command.upper().startswith("RETR"):
           response = send_command(command)  
           if response.startswith('    *150*'): 
             filename = command.split()[1]
             with open(filename, "wb") as file:
                 time.sleep(0.1)
                 data = data_socket.recv(1024*1024*10)  
                 file.write(data)  
             print(control_socket.recv(1024).decode()) 
             
        elif command.upper().startswith("STOR"):
           response = send_command(command)  
           if response.startswith('    *150*'):
               filename = command.split()[1]
               with open(filename, "rb") as file:
                       data_socket.send(file.read())
               print(control_socket.recv(1024).decode())        
                    
        else:
            send_command(command)

    control_socket.close()
    data_socket.close()

if __name__ == "__main__":
    ftp_client()