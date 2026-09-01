import socket

server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server.bind(('0.0.0.0', 514))

print("Слушаю syslog на порту 514...")
while True:
    data, addr = server.recvfrom(1024)
    print(f"[{addr[0]}] {data.decode('utf-8', errors='ignore')}")