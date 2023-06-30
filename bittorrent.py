import hashlib
import os
import socket
import struct
import threading
import time
import torrent_parser
import bencodepy
import random
import string
from enum import Enum


class MessageType(Enum):
    REQUEST = 6
    PIECE = 7

class BitTorrent:
    def __init__(self, torrent_file):
        self.torrent = torrent_parser.parse_torrent_file(torrent_file)
        self.tracker_url = self.torrent["announce"]
        self.peer_id = self.generate_peer_id()
        self.port = 6881  # Port number for communication
        self.peer_list = []
        self.bitfield = []  # Bitfield to track downloaded pieces
        self.connected_peers = []
        
    def start(self):
        self.connect_to_tracker()
        self.download_file()
        self.upload_file()
    
    def connect_to_tracker(self):
        # Create a socket and connect to the tracker
        tracker_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        tracker_socket.connect((self.tracker_url, 80))

        # Create the initial connection message
        connection_id = 0x41727101980  # Initial connection ID for UDP tracker
        transaction_id = 0x12345678  # Random transaction ID
        connect_msg = struct.pack("!QII", connection_id, 0, transaction_id)

        # Send the connection message to the tracker
        tracker_socket.send(connect_msg)

        # Receive and parse the tracker response
        response = tracker_socket.recv(2048)
        action, transaction_id, connection_id = struct.unpack("!IIQ", response)

        # Close the socket
        tracker_socket.close()

        # Parse the response and retrieve peer information
        # Update the peer list with the received information
        peer_list = self.parse_tracker_response(response)
        self.peer_list = peer_list
    
    def download_file(self):
        for peer in self.peer_list:
            peer_socket = self.connect_to_peer(peer)
            if peer_socket:
                # Send handshake message to establish connection
                self.send_handshake_message(peer_socket)
                
                # Receive and validate handshake message from the peer
                if self.receive_handshake_message(peer_socket):
                    # Send bitfield message to request the availability of pieces
                    self.send_bitfield_message(peer_socket)
                    
                    # Receive and process bitfield message from the peer
                    self.receive_bitfield_message(peer_socket)
                    
                    # Request pieces from the peer
                    self.request_pieces(peer_socket)
                    
                    # Start receiving and verifying pieces
                    self.receive_and_verify_pieces(peer_socket)
                    
                    # Close the connection with the peer
                    peer_socket.close()
    
    def upload_file(self):
        # Start listening for incoming connections from other peers
        listen_thread = threading.Thread(target=self.listen_for_connections)
        listen_thread.start()
        
        # Connect to other peers and send necessary messages
        for peer in self.peer_list:
            peer_socket = self.connect_to_peer(peer)
            if peer_socket:
                # Send handshake message to establish connection
                self.send_handshake_message(peer_socket)
                
                # Receive and validate handshake message from the peer
                if self.receive_handshake_message(peer_socket):
                    # Send bitfield message to inform the availability of pieces
                    self.send_bitfield_message(peer_socket)
                    
                    # Start sending pieces to the peer
                    self.send_pieces(peer_socket)
                    
                    # Close the connection with the peer
                    peer_socket.close()


    def handle_peer_connection(self, peer_info):
        # Handle a connection with a peer
        peer_socket = self.connect_to_peer(peer_info)
        if peer_socket:
            # Send handshake message to establish connection
            self.send_handshake_message(peer_socket)
            
            # Receive and validate handshake message from the peer
            if self.receive_handshake_message(peer_socket):
                # Send bitfield message to request the availability of pieces
                self.send_bitfield_message(peer_socket)
                
                # Receive and process bitfield message from the peer
                self.receive_bitfield_message(peer_socket)
                
                # Handle the communication with the peer
                self.handle_peer_communication(peer_socket)
                
                # Close the connection with the peer
                peer_socket.close()
    
    def handle_piece_request(self, peer_socket):
    # Handle a piece request from a peer
        request_message = self.receive_message(peer_socket)
        if request_message and request_message["type"] == "request":
            piece_index = request_message["piece_index"]
            offset = request_message["offset"]
            length = request_message["length"]
            
            # Check if the requested piece is available
            if self.bitfield[piece_index] == 1:
                # Read the requested piece from the file
                piece_data = self.read_piece(piece_index, offset, length)
                
                # Create and send the piece message
                piece_message = self.create_piece_message(piece_index, offset, piece_data)
                self.send_message(peer_socket, piece_message)
        else:
            # Handle invalid request message
            error_message = self.create_error_message("Invalid request message")
            self.send_message(peer_socket, error_message)

    
    def send_piece(self, peer_socket, piece_index):
        # Send a piece to a peer
        piece_data = self.read_piece(piece_index)
        if piece_data:
            offset = 0
            length = len(piece_data)
            
            # Create and send the request message
            request_message = self.create_request_message(piece_index, offset, length)
            self.send_message(peer_socket, request_message)
    
    def receive_piece(self, peer_socket):
        # Receive a piece from a peer
        piece_message = self.receive_message(peer_socket)
        if piece_message and piece_message["type"] == "piece":
            piece_index = piece_message["piece_index"]
            offset = piece_message["offset"]
            piece_data = piece_message["data"]
            
            # Write the received piece to the file
            self.write_piece(piece_index, offset, piece_data)
            
            # Update the bitfield with the received piece
            self.update_bitfield(piece_index)
        else:
            # Handle invalid piece message
            pass
    
    def verify_piece(self, piece_index):
        # Verify the integrity of a downloaded piece
        piece_path = self.get_piece_path(piece_index)
        piece_data = self.read_piece(piece_path)
        expected_hash = self.torrent["info"]["pieces"][piece_index * 20:(piece_index + 1) * 20]
        calculated_hash = hashlib.sha1(piece_data).digest()
        if calculated_hash == expected_hash:
            print(f"Piece {piece_index} is verified successfully.")
            return True
        else:
            print(f"Piece {piece_index} verification failed.")
            return False
    
    def update_bitfield(self, piece_index):
        # Update the bitfield with the downloaded piece
        self.bitfield[piece_index] = 1
    
    def create_request_message(self, piece_index, offset, length):
        # Create a request message for a piece
        message = struct.pack("!IBIII", 13, 6, piece_index, offset, length)
        return message
    
    def create_piece_message(self, piece_index, offset, data):
        # Create a piece message with the requested piece data
        message_length = len(data) + 9
        message = struct.pack("!IBII", message_length, 7, piece_index, offset) + data
        return message
    
    def create_bitfield_message(self):
        # Create a bitfield message with the current bitfield status
        bitfield_data = self.serialize_bitfield()
        message_length = len(bitfield_data) + 1
        message = struct.pack("!IB", message_length, 5) + bitfield_data
        return message
    
    def create_handshake_message(self):
        # Create a handshake message to establish a connection with a peer
        protocol_name = "BitTorrent protocol"
        protocol_name_length = len(protocol_name)
        reserved_bytes = b"\x00" * 8
        handshake = struct.pack("!B{}s8s20s20s".format(protocol_name_length), protocol_name_length, protocol_name.encode(), reserved_bytes, self.torrent["info_hash"], self.peer_id.encode())
        return handshake
    
    
    def generate_peer_id(self):
        peer_id_prefix = "-PY0001-"  # Replace with your desired prefix
        random_chars = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
        peer_id = peer_id_prefix + random_chars
        return peer_id
    
    def parse_tracker_response(self, response):
        tracker_data = bencodepy.decode(response)

        if "failure reason" in tracker_data:
            # Handle failure response from the tracker
            failure_reason = tracker_data["failure reason"]
            print(f"Tracker response failure: {failure_reason}")
            return None

        # Extract peer information from the response
        peers = []
        if "peers" in tracker_data:
            raw_peers = tracker_data["peers"]
            if isinstance(raw_peers, list):
                # For compact response format
                for i in range(0, len(raw_peers), 6):
                    ip = '.'.join(str(b) for b in raw_peers[i:i + 4])
                    port = (raw_peers[i + 4] << 8) + raw_peers[i + 5]
                    peers.append((ip, port))
            elif isinstance(raw_peers, bytes):
                # For non-compact response format
                for i in range(0, len(raw_peers), 6):
                    ip = '.'.join(str(raw_peers[i + j]) for j in range(4))
                    port = (raw_peers[i + 4] << 8) + raw_peers[i + 5]
                    peers.append((ip, port))
        
        return peers


    

    def connect_to_peer(self, peer):
        # Logic for connecting to a peer
        peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            peer_socket.connect((peer[0], peer[1]))  # peer is a tuple (ip, port)
            self.send_handshake_message(peer_socket)
            self.receive_handshake_message(peer_socket)
            if self.validate_handshake_message(peer_socket):
                self.handle_peer_connection(peer_socket)
            else:
                # Handle invalid handshake message
                self.handle_invalid_handshake_message(peer_socket)
        except ConnectionRefusedError:
            # Handle connection error
            self.handle_connection_error(peer[0], peer[1])  # peer is a tuple (ip, port)
        finally:
            peer_socket.close()

    def send_handshake_message(self, peer_socket):
        # Logic for sending the handshake message to the peer
        handshake = self.create_handshake_message()
        peer_socket.send(handshake)

    def receive_handshake_message(self, peer_socket):
        # Logic for receiving and validating the handshake message from the peer
        handshake = peer_socket.recv(68)
        if len(handshake) == 68 and handshake[:20] == self.handshake_header:
            peer_id = handshake[48:]
            # Validate the received handshake message
            if self.validate_handshake_message(handshake):
                # Perform further actions with the validated peer
                pass
            else:
                # Handle invalid handshake message
                self.handle_invalid_handshake_message(peer_socket)
        else:
            # Handle invalid handshake message
            self.handle_invalid_handshake_message(peer_socket)

    def validate_handshake_message(self, handshake):
        # Logic for validating the received handshake message
        return handshake[28:48] == self.info_hash and handshake[48:] != self.peer_id

    def create_handshake_message(self):
        # Logic for creating a handshake message to establish a connection with a peer
        pstrlen = struct.pack("B", 19)
        pstr = b"BitTorrent protocol"
        reserved = struct.pack("Q", 0)
        handshake = pstrlen + pstr + reserved + self.info_hash + self.peer_id.encode()
        return handshake

    def handle_invalid_handshake_message(self, peer_socket):
        # Logic for handling an invalid handshake message
        # Close the connection with the peer
        peer_socket.close()
        # Perform any necessary cleanup or error handling
        # For example, you may want to remove the peer from your peer list or mark it as invalid
        self.remove_invalid_peer(peer_socket.getpeername())
        pass

        
    def send_bitfield_message(self, peer_socket):
        # Logic for sending the bitfield message to the peer
        bitfield_message = self.create_bitfield_message()
        peer_socket.send(bitfield_message)

    def receive_bitfield_message(self, peer_socket):
        # Logic for receiving and processing the bitfield message from the peer
        bitfield_message = peer_socket.recv(4096)
        # Process the received bitfield message
        self.process_bitfield_message(bitfield_message)

    def handle_peer_communication(self, peer_socket):
        # Logic for handling the communication with the peer
        while True:
            message = self.receive_message(peer_socket)
            if message is None:
                # Handle disconnection from the peer
                break
            # Process the received message
            self.process_message(message)

    def receive_message(self, peer_socket):
        # Logic for receiving a message from the peer
        try:
            message_length = struct.unpack('>I', peer_socket.recv(4))[0]
            message = peer_socket.recv(message_length)
            return message
        except (ConnectionResetError, ConnectionAbortedError):
        # Handle disconnection from the peer
            self.handle_peer_disconnection(peer_socket)
            return None


    
    def read_piece(self, piece_index, offset, length):
    # Logic for reading a piece from the file
        with open(self.file_path, 'rb') as file:
            file.seek(piece_index * self.piece_length + offset)
            piece_data = file.read(length)
        return piece_data

    def create_piece_message(self, piece_index, offset, data):
        # Logic for creating a piece message with the requested piece data
        message = struct.pack('>IBII', len(data) + 9, MessageType.PIECE.value, piece_index, offset) + data
        return message

    def send_message(self, peer_socket, message):
        # Logic for sending a message to the peer
        peer_socket.send(message)

    def receive_message(self, peer_socket):
        # Logic for receiving a message from the peer
        try:
            message_length = struct.unpack('>I', peer_socket.recv(4))[0]
            message = peer_socket.recv(message_length)
            return message
        except (ConnectionResetError, ConnectionAbortedError):
            # Handle disconnection from the peer
            self.handle_peer_disconnection(peer_socket)
            return None

    def write_piece(self, piece_index, offset, data):
        # Logic for writing a received piece to the file
        with open(self.file_path, 'r+b') as file:
            file.seek(piece_index * self.piece_length + offset)
            file.write(data)
    
    def update_bitfield(self, piece_index):
    # Logic for updating the bitfield with the received piece
        self.bitfield[piece_index] = 1

    def read_piece(self, piece_index):
        # Logic for reading a piece from the file
        with open(self.file_path, 'rb') as file:
            file.seek(piece_index * self.piece_length)
            piece_data = file.read(self.piece_length)
        return piece_data

    def create_request_message(self, piece_index, offset, length):
        # Logic for creating a request message for a piece
        message = struct.pack('>IBIII', 13, MessageType.REQUEST.value, piece_index, offset, length)
        return message

    def send_message(self, peer_socket, message):
        # Logic for sending a message to the peer
        peer_socket.send(message)

    def process_bitfield_message(self, peer_socket, bitfield_message):
        # Logic for processing a bitfield message received from a peer
        # Your implementation goes here
        # For example, you can print the bitfield message received
        print("Received bitfield message:", bitfield_message)
        # You can add more custom logic based on your requirements

    def handle_peer_disconnection(self, peer_socket):
        # Logic for handling a peer disconnection
        # Your implementation goes here
        # For example, you can remove the peer from the connected_peers list
        if peer_socket in self.connected_peers:
            self.connected_peers.remove(peer_socket)
        # You can add more custom logic based on your requirements

    def remove_invalid_peer(self, peer_socket):
        # Logic for removing an invalid peer from the peer list
        # Your implementation goes here
        # For example, you can remove the peer from the peer_list
        if peer_socket in self.peer_list:
            self.peer_list.remove(peer_socket)
        # You can add more custom logic based on your requirements

    def handle_peer_disconnection(self, peer_socket):
        if peer_socket in self.connected_peers:
            # Peer is currently connected
            # Perform cleanup or error handling
            self.connected_peers.remove(peer_socket)
            print("Peer disconnected: ", peer_socket)
        else:
            # Peer was not found in the connected peers list
            print("Error: Peer not found!")

    def main_logic(self):
        # Example usage of handle_peer_disconnection
        peer1 = "Peer1"
        peer2 = "Peer2"

        # Simulating peer connections
        self.connected_peers.append(peer1)
        self.connected_peers.append(peer2)
        print("Connected peers:", self.connected_peers)

        # Simulating disconnection of peer2
        self.handle_peer_disconnection(peer2)

        # Check the updated connected peers list
        print("Connected peers:", self.connected_peers)

# Create an instance of the BitTorrent class
bt = BitTorrent()

# Execute the main logic
bt.main_logic()