#!/usr/bin/env python3
# Configure ELTEX SW-PLG01 WiFi smart plug.
# Usage example:
#    plgreg.py --ssid MySSID --password MyPassword --mqtt-broker 192.168.100.60:1883 --mqtt-login mqttdevice --mqtt-password mqttdevice_pass --node-id swplg01_01 --host 10.24.83.55
# Run on laptop connected to smart plug WiFi network. Use WiFi gateway address for --host parameter.
# MQTT over TLS is not supported for custom MQTT broker because CA certificate is hardcoded to FW and verification is enabled.
# Notes: Protocol messages format based on ProtoBuf
# (C) Kerd 2025
import socket
import struct
import sys
import argparse
import time

def varint_decode(data, offset=0):
    result = 0
    shift = 0
    while offset < len(data):
        b = data[offset]
        result |= (b & 0x7F) << shift
        offset += 1
        if not (b & 0x80):
            return result, offset
        shift += 7
        if shift > 63:
            raise ValueError("Varint too long")
    raise ValueError("Truncated varint")

def varint_encode(value):
    out = []
    while value > 0x7F:
        out.append((value & 0x7F) | 0x80)
        value >>= 7
    out.append(value & 0x7F)
    return bytes(out)

def recv_exactly(sock, n):
    data = b''
    while len(data) < n:
        chunk = sock.recv(n - len(data))
        if not chunk:
            raise ConnectionError("Connection closed")
        data += chunk
    return data

def recv_message(sock):
    """
    Receive one framed message.
    Returns (msg_type, payload_bytes or None, full_protobuf)
    """
    len_bytes = recv_exactly(sock, 4)
    msg_len = struct.unpack('!I', len_bytes)[0]
    protobuf = recv_exactly(sock, msg_len)
    if protobuf is not None:
        print(f"[+] Received message ({msg_len} bytes): {protobuf.hex()}")

    # Parse outer message: look for field 1 (type)
    offset = 0
    msg_type = None
    payload = None

    while offset < len(protobuf):
        key, offset = varint_decode(protobuf, offset)
        field = key >> 3
        wire = key & 0x7

        if field == 1 and wire == 0:  # varint
            # Read varint value (assume it fits in 1 byte for simplicity)
            # For robustness, we should decode full varint:
            val, offset = varint_decode(protobuf, offset)
            msg_type = val
        elif field in (2, 3) and wire == 2:  # length-delimited payload
            length, offset = varint_decode(protobuf, offset)
            payload = protobuf[offset:offset + length]
            offset += length
        else:
            # Skip unknown field
            if wire == 0:      # varint
                _, offset = varint_decode(protobuf, offset)
            elif wire == 1:    # 64-bit
                offset += 8
            elif wire == 2:    # length-delimited
                length, offset = varint_decode(protobuf, offset)
                offset += length
            elif wire == 5:    # 32-bit
                offset += 4
            else:
                raise ValueError(f"Unknown wire type {wire}")

    if msg_type is None:
        raise ValueError("Message type (field 1) not found")

    return msg_type, payload, protobuf

def parse_hello(payload):
    """Parse HelloMessage from payload (fields 1,2,3)"""
    fields = {}
    offset = 0
    while offset < len(payload):
        key, offset = varint_decode(payload, offset)
        field = key >> 3
        wire = key & 0x7
        if wire == 2:
            length, offset = varint_decode(payload, offset)
            value = payload[offset:offset + length]
            offset += length
            fields[field] = value.decode('utf-8')
        else:
            # Skip
            if wire == 0:
                _, offset = varint_decode(payload, offset)
            else:
                raise ValueError("Unexpected wire in Hello")
    return fields

def build_config_message(ssid, password, mqtt_broker, mqtt_login, mqtt_password, node_id):
    config = b''
    # Field 1: ssid
    b_ssid = ssid.encode('utf-8')
    config += b'\x0a' + varint_encode(len(b_ssid)) + b_ssid
    # Field 3: password (optional)
    if password is not None:
        b_pwd = password.encode('utf-8')
        config += b'\x1a' + varint_encode(len(b_pwd)) + b_pwd
    # Field 4: mqtt_broker
    b_broker = mqtt_broker.encode('utf-8')
    config += b'\x22' + varint_encode(len(b_broker)) + b_broker
    # Field 5: mqtt_login
    b_login = mqtt_login.encode('utf-8')
    config += b'\x2a' + varint_encode(len(b_login)) + b_login
    # Field 6: mqtt_password
    b_pass = mqtt_password.encode('utf-8')
    config += b'\x32' + varint_encode(len(b_pass)) + b_pass
    # Field 7: node_id
    b_node = node_id.encode('utf-8')
    config += b'\x3a' + varint_encode(len(b_node)) + b_node
    return config

def build_outer_message(msg_type, payload=None):
    """Build OuterMessage: type=field1, payload=field3"""
    outer = b'\x08' + varint_encode(msg_type)
    if payload is not None:
        outer += b'\x1a' + varint_encode(len(payload)) + payload
    return outer

def main():
    parser = argparse.ArgumentParser(description="ELTEX Config Client (with message loop)")
    parser.add_argument("--ssid", required=True, help="Wi-Fi SSID")
    parser.add_argument("--password", help="Wi-Fi password (omit for open network)")
    parser.add_argument("--mqtt-broker", default="eltexhome.ru:8883", help="MQTT broker URL")
    parser.add_argument("--mqtt-login", required=True, help="MQTT login (UUID)")
    parser.add_argument("--mqtt-password", required=True, help="MQTT password (base64)")
    parser.add_argument("--node-id", required=True, help="Node ID (UUID)")
    parser.add_argument("--host", default="127.0.0.1", help="Server host")
    parser.add_argument("--port", type=int, default=56684, help="Server port")
    parser.add_argument("--timeout", type=int, default=10, help="Timeout for GOODBYE (seconds)")

    args = parser.parse_args()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(args.timeout)
        s.connect((args.host, args.port))
        print(f"[+] Connected to {args.host}:{args.port}")

        config_sent = False
        goodbye_received = False

        while not goodbye_received:
            try:
                msg_type, payload, raw = recv_message(s)
                print(f"[+] Received message: type={msg_type}, payload_size={len(payload) if payload else 0}")
                if msg_type == 0:  # HELLO
                    if payload:
                        hello = parse_hello(payload)
                        print(f"    → HELLO: magic='{hello.get(1)}', mac='{hello.get(2)}', device='{hello.get(3)}'")
                    else:
                        print("    → HELLO with empty payload")

                    # Send config in response to HELLO
                    if not config_sent:
                        print("[+] Sending config...")
                        config_inner = build_config_message(
                            ssid=args.ssid,
                            password=args.password,
                            mqtt_broker=args.mqtt_broker,
                            mqtt_login=args.mqtt_login,
                            mqtt_password=args.mqtt_password,
                            node_id=args.node_id
                        )
                        outer_msg = build_outer_message(1, config_inner)
                        packet = struct.pack('!I', len(outer_msg)) + outer_msg
                        s.sendall(packet)
                        config_sent = True
                        print(f"    → Sent config ({len(outer_msg)} bytes)")

                elif msg_type == 2:  # GOODBYE
                    print("[+] GOODBYE received — configuration accepted")
                    goodbye_received = True
                    # Optionally parse payload if needed later
                    if payload:
                        print(f"    → GOODBYE payload: {payload.hex()}")
                    break

                else:
                    print(f"    → Unknown message type {msg_type}, ignored")

            except socket.timeout:
                print("[!] Timeout waiting for server message")
                break
            except ConnectionError as e:
                print(f"[!] Connection error: {e}")
                break

        if not goodbye_received:
            print("[!] Did not receive GOODBYE confirmation")
            sys.exit(1)
        else:
            print("[+] Success: configuration acknowledged")

if __name__ == '__main__':
    main()
