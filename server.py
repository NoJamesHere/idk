import socket
import threading
import json

port = 8888
clients = []
i = 0
clients_usernames = {}

list_of_commands = "List of commands\n/help: Print this list.\n/ping: Get ping from server.\n/list: Get list of users connected.\n/msg <user> <your message>: DM another user.\n/nick <new_nick>: Change your nickname.\n/quit: Disconnect from server and exit.\nEnd of List."
def send_pong(sock):
    sock.sendall("[Server]: Pong!".encode())

def send_list(sock):
    sock.sendall(f"[Server]: {list_of_commands}".encode())

def change_username(sock, new_username):
    clients_usernames[sock]["username"] = new_username
    print(f"A user has changed their username: {new_username}")
    sock.sendall("ok.".encode())
    print(clients_usernames[sock]["username"])
    
def send_clients(sock):
    listing = "Users:\n"
    for socketthingy, info in clients_usernames.items():
        listing += f"{info['username']}\n"
    sock.sendall(f"[Server]: {listing}".encode())

def user_exists(username):
    for socketthingy, info in clients_usernames.items():
        if info["username"] == username:
            return True, socketthingy
    return False, None

def message_user(current_user, socket_of_user, message):
    formatted = f"(DM)[{current_user}]: {message}"

    socket_of_user.sendall(formatted.encode())


def disconnect_user(sock):
    try:
        disconnect_message = f"{clients_usernames[sock]['username']} has disconnected."

        print(f"A user has disconnected: {clients_usernames[sock]}")

        sock.sendall("[Server]: Disconnecting you..".encode())
        clients.remove(sock)
        clients_usernames.pop(sock, None)
        sock.close()
        for client in clients:
            client.sendall(disconnect_message.encode())
    except Exception as e:
        print(f"Something happened: {e}")
        pass

def broadcast(message, sender=None):
    for client in clients:
        if client != sender:
            try:
                client.sendall(message.encode())
            except:
                clients.remove(client)
                print(clients)


def chitchat(sock):
    while True:
        try:
            data = sock.recv(5012).decode()
            if not data:
                disconnect_user(sock)
                break
            message = json.loads(data)
            print(message)
            if(message["message"] == "REGISTER"):
                clients_usernames[sock]["username"] = message["username"]
                broadcast(f"[Server]: {message['username']} has joined", sock)
                continue
            if(message["message"] == "GET_PING"):
                send_pong(sock)
                continue
            if(message["message"] == "GET_LIST"):
                send_list(sock)
                continue
            if(message["message"] == "CLIENT_DISCONNECT"):
                disconnect_user(sock)
                break
            if(message["message"] == "CHANGE_USERNAME"):
                new_user = message["other"]
                print(clients)
                print("\n", clients_usernames)
                change_username(sock, new_user)
                broadcast(f"[Server]: A user has changed their username to {new_user}.", sock)
                continue
            if(message["message"] == "GET_CLIENTS"):
                send_clients(sock)
                continue
            if(message["message"] == "MESSAGE_USER"):
                wanted_user = message["another"]
                message_to_user = message["other"]
                boolean_of_user_existing, socket_of_user = user_exists(wanted_user)
                if boolean_of_user_existing:
                    message_user(clients_usernames[sock]["username"], socket_of_user, message_to_user)
                else:
                    sock.sendall("[Server]: User does not exist.".encode())
                continue
            elif(message["message"].startswith("/")):
                sock.sendall("[Server]: Command does not exist. Type /help to get all commands.".encode())
                continue
            username = message["username"]
            line = message["message"]
            formatted = f"[{username}]: {line}"
            print(formatted)
            broadcast(formatted, sender=sock)
        except Exception as e:
            print(f"Error: {e}")
            disconnect_user(sock)

errorcount = 0

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(("0.0.0.0", port))
print("Binded. Server is going to start listening momentarily..")
server.settimeout(0.2)

while True:
    try:
        server.listen()
        connection, address = server.accept()

        clients.append(connection)

        client = f"Client_{i}"
        clients_usernames[connection] = {"username": client}
        i += 1
        newThreader = threading.Thread(target=chitchat, args=(connection,), daemon=True)
        newThreader.start()
        print(f"Connected: {address}")
        print(clients_usernames)
    except KeyboardInterrupt:
        print("Shutting down..")
        for client in clients:
            client.close()
        server.close()
        exit()
    except socket.timeout:
        continue
    except Exception as e:
        errorcount += 1
        print(f"Error: {e}")

        if(errorcount > 5):
            print(f"Error: {e}\nShutting down..")

            for client in clients:
                try:
                    client.shutdown(socket.SHUT_RDWR,)
                except:
                    pass
                client.close()
            server.close()
            server.shutdown(socket.SHUT_RDWR,)
            exit()
        else:
            print(f"Continuing.. Error count: {errorcount}")
            continue