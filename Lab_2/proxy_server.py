#!/usr/bin/env python3
import socket, sys
import time
from multiprocessing import Process
import os

def create_tcp_socket():
    print('Creating socket...')
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except (socket.error, msg):
        print(f'Failed to create socket. Error code: {str(msg[0])} , Error message : {msg[1]}')
        sys.exit()
    print('Socket created successfully')
    return s

def get_remote_ip(host):
    print(f'Getting IP for {host}...')
    try:
        remote_ip = socket.gethostbyname( host )
    except socket.gaierror:
        print ('Hostname could not be resolved. Exiting')
        sys.exit()

    print (f'Ip address of {host} is {remote_ip}')
    return remote_ip

def send_data(serversocket, payload):
    print("Sending payload...")    
    try:
        # data from proxy client already encoded dont need to encode
        serversocket.sendall(payload)
    except socket.error:
        print ('Send failed')
        sys.exit()
    print("Payload sent successfully")

def send_to_internet(payload):
    try:
        PS_HOST = 'www.google.com'
        PS_PORT = 80
        buffer_size = 4096

        # make the socket, get the ip, and connect
        s = create_tcp_socket()
        remote_ip = get_remote_ip(PS_HOST)
        s.connect((remote_ip , PS_PORT))
        print(f'Proxy server connected to {PS_HOST} on ip {remote_ip}')
        
        # send the data and shutdown
        s.sendall(payload)
        s.shutdown(socket.SHUT_WR)
        print(f'Data sent to {PS_HOST}')

        return_data = s.recv(buffer_size)
        return return_data

    except Exception as e:
        print(e)

    finally:
        s.close()

def mp_handler(pc_conn, addr):
    print('parent process:', os.getppid(), '| process id:', os.getpid())

    pc_full_data = pc_conn.recv(PC_BUFFER_SIZE)
    if pc_full_data: print('Data received from proxy client')
    #time.sleep(2)
        
    # sends pc data to server and get data to return back to pc
    ps_return_data = send_to_internet(pc_full_data)
    if ps_return_data: print('Data received from remote connection')
    #time.sleep(2)

    # sends data back to pc
    print('Sending data back to client')
    pc_conn.sendall(ps_return_data)
    pc_conn.close()
    
# global variables
PC_HOST = ""            # any client can connect
PC_PORT = 8001          # listening to this port 
PC_BUFFER_SIZE = 4096   #1024
pc_full_data = b''

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        print(f'Proxy server started, listening to port {PC_PORT}')
        # connects to client and bind
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((PC_HOST, PC_PORT))
        s.listen(2)
        
        # continuously listen for connections
        while True:
            # instance of socket, IP of client
            pc_conn, addr = s.accept()
            print("Proxy server connected by", addr)
            
            # multiprocessing to handle more than one proxy client
            p = Process(target=mp_handler, args=(pc_conn, addr))
            p.daemon = True
            p.start()
            pc_conn.close()            

if __name__ == "__main__":
    main()