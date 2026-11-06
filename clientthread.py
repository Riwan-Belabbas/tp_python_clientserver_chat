import socket
import threading
import re
import time


class ClientListener(threading.Thread):
    """Un thread par client connecté : il écoute les messages de CE client
    et les transmet au serveur pour diffusion."""

    def __init__(self, server, socket, address):
        # Initialise la partie "thread" de la classe (obligatoire)
        super(ClientListener, self).__init__()
        self.server = server        # le serveur (pour appeler echo / remove_socket)
        self.socket = socket        # la ligne dédiée à ce client
        self.address = address      # adresse (IP, port) du client
        self.listening = True       # interrupteur : False = le thread s'arrête
        self.username = "No username"  # pseudo par défaut, avant réception du vrai

    def run(self):
        """Boucle d'écoute : exécutée automatiquement par start()."""
        while self.listening:
            data = ""
            try:
                # recv() BLOQUE jusqu'à réception de données (1024 octets max)
                # decode() transforme les octets reçus en texte
                data = self.socket.recv(1024).decode('UTF-8')
            except socket.error:
                print("Connexion perdue avec", self.address)
            self.handle_msg(data)
            time.sleep(0.1)
        print("Ending client thread for", self.address)

    def quit(self):
        """Ferme proprement la connexion de ce client."""
        self.listening = False                 # arrête la boucle run()
        self.socket.close()                    # ferme la connexion
        self.server.remove_socket(self.socket)  # retire le client de la liste
        self.server.echo("{0} has quit\n".format(self.username))  # prévient les autres

    def handle_msg(self, data):
        """Décide quoi faire d'un message reçu."""
        print(self.address, "sent :", data)
        # Expression régulière : le message commence-t-il par "USERNAME " ?
        username_result = re.search('^USERNAME (.*)$', data)
        if username_result:
            # Cas 1 : annonce du pseudo -> on l'enregistre et on prévient tout le monde
            self.username = username_result.group(1)
            self.server.echo("{0} has joined.\n".format(self.username))
        elif data == "/name":
            # Commande spéciale : le serveur répond avec son nom, UNIQUEMENT à ce client
            try:
                self.socket.sendall("Serveur : {0}\n".format(self.server.name).encode("UTF-8"))
            except socket.error:
                print("Cannot send the server name")
        elif data == "QUIT":
            # Le client demande à partir
            self.quit()
        elif data == "":
            # Message vide = le client a fermé sa connexion
            self.quit()
        else:
            # Message de chat normal -> diffusé à tous
            self.server.echo(data)
