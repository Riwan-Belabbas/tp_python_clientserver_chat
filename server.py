import socket
import sys  # utilisé pour sortir du programme
import time
from clientthread import ClientListener


class Server():
    """Le serveur de chat : il accepte les clients et diffuse leurs messages à tous."""

    def __init__(self, port):
        # Création d'un socket TCP (SOCK_STREAM) en IPv4 (AF_INET) : la "prise réseau" du serveur
        self.listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # On attache le socket au port donné ('' = toutes les interfaces réseau de la machine)
        self.listener.bind(('', port))
        # Le serveur se met en écoute (1 = taille de la file d'attente des connexions)
        self.listener.listen(1)
        print("Listening on port", port)
        # Liste des sockets de tous les clients connectés (sert à diffuser les messages)
        self.clients_sockets = []

    def run(self):
        """Boucle principale : accepte les nouveaux clients, un thread par client."""
        while True:
            print("listening new customers")
            try:
                # accept() BLOQUE jusqu'à ce qu'un client se connecte.
                # Il renvoie le socket dédié à ce client et son adresse (IP, port).
                (client_socket, client_adress) = self.listener.accept()
            except socket.error:
                sys.exit("Cannot connect clients")
            # On mémorise le client pour pouvoir lui envoyer les messages plus tard
            self.clients_sockets.append(client_socket)
            print("Start the thread for client:", client_adress)
            # Un thread par client : il écoute ce client pendant que run() continue
            # d'accepter les suivants
            client_thread = ClientListener(self, client_socket, client_adress)
            client_thread.start()
            time.sleep(0.1)

    def remove_socket(self, socket):
        """Retire un client de la liste (appelé quand il quitte)."""
        self.clients_sockets.remove(socket)

    def echo(self, data):
        """Envoie le message 'data' à TOUS les clients connectés."""
        print("echoing:", data)
        for sock in self.clients_sockets:
            try:
                # Le réseau transporte des octets : on encode le texte en UTF-8
                sock.sendall(data.encode("UTF-8"))
            except socket.error:
                # Si un client est injoignable, on continue avec les autres
                print("Cannot send the message")


# Ce bloc ne s'exécute que si on lance ce fichier directement (py server.py)
if __name__ == "__main__":
    server = Server(59001)
    server.run()
