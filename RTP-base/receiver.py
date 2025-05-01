import argparse
import socket
import sys

from utils import PacketHeader, compute_checksum


def receiver(receiver_ip, receiver_port, window_size):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind((receiver_ip, receiver_port))

    expected_seq = 1
    connected = False
    data = {}

    while True:
        msg, addr = s.recvfrom(2048)  # buffer lớn hơn packet
        header = PacketHeader(msg[:16])
        body = msg[16:]
        # Verify checksum
        pkt_checksum = header.checksum
        header.checksum = 0
        calc_checksum = compute_checksum(header/body)

        if calc_checksum != pkt_checksum:
            ack_header = PacketHeader(type=3, seq_num=expected_seq)
            ack_header.checksum = compute_checksum(bytes(ack_header))
            s.sendto(bytes(ack_header), addr)
            continue  # Ignore corrupted packets

        # Handle Start Packet
        if header.type == 0 and not connected:
            if header.seq_num == 0:
                print("Received START packet")
                ack_header = PacketHeader(type=3, seq_num=1)
                ack_header.checksum = compute_checksum(bytes(ack_header))
                s.sendto(bytes(ack_header), addr)
                connected = True
                continue

        # Handle Data Packet
        elif header.type == 2 and connected:
            if header.seq_num >= expected_seq+window_size:
                ack_header = PacketHeader(type=3, seq_num=expected_seq)
                ack_header.checksum = compute_checksum(bytes(ack_header))
                s.sendto(bytes(ack_header), addr)
                continue

            if header.seq_num not in data:
                data[header.seq_num] = body

            while expected_seq in data:
                sys.stdout.buffer.write(data[expected_seq])
                sys.stdout.buffer.flush()
                expected_seq += 1
            # Always send cumulative ACK
            ack_header = PacketHeader(type=3, seq_num=expected_seq)
            ack_header.checksum = compute_checksum(bytes(ack_header))
            s.sendto(bytes(ack_header), addr)

        # Handle END Packet
        elif header.type == 1 and connected:
            print("Received END packet")
            ack_header = PacketHeader(type=3, seq_num=header.seq_num)
            ack_header.checksum = compute_checksum(bytes(ack_header))
            s.sendto(bytes(ack_header), addr)
            print("Connection closed.")
            break

    s.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "receiver_ip", help="The IP address of the host that receiver is running on"
    )
    parser.add_argument(
        "receiver_port", type=int, help="The port number on which receiver is listening"
    )
    parser.add_argument(
        "window_size", type=int, help="Maximum number of outstanding packets"
    )
    args = parser.parse_args()

    receiver(args.receiver_ip, args.receiver_port, args.window_size)


if __name__ == "__main__":
    main()
