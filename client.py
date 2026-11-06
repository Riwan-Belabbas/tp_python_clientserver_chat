import threading
import socket
import time
import re
import sys


class Client():
    """Le client de chat : il envoie ce que tu tapes et affiche ce que le serveur renvoie."""

    def __init__(self, username, server, port):
        # Création d'un socket TCP (la prise réseau du client)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Connexion au serveur (adresse + port)
        self.socket.connect((server, port))
        self.username = username
        # Dès la connexion, on annonce notre pseudo au serveur
        self.send("USERNAME {0}".format(username))
        self.listening = True  # interrupteur de la boucle d'écoute

    def listener(self):
        """Boucle d'écoute : attend les messages du serveur et les affiche."""
        while self.listening:
            data = ""
            try:
                # recv() bloque jusqu'à réception de données ; decode() octets -> texte
                data = self.socket.recv(1024).decode('UTF-8')
            except socket.error:
                print("Unable to receive data")
            self.handle_msg(data)
            time.sleep(0.1)

    def listen(self):
        """Lance listener() dans un thread séparé, pour écouter en arrière-plan
        pendant que le programme principal attend ce que l'utilisateur tape."""
        self.listen_thread = threading.Thread(target=self.listener)
        # daemon = True : le thread s'arrête quand le programme principal se termine
        self.listen_thread.daemon = True
        self.listen_thread.start()

    def send(self, message):
        """Envoie un message au serveur."""
        try:
            # Le message est-il l'annonce du pseudo ("USERNAME ...") ?
            username_result = re.search('^USERNAME (.*)$', message)
            if not username_result:
                # Message normal : on ajoute le pseudo devant ("riwan: hello")
                message = "{0}: {1}".format(self.username, message)
            # Encode le texte en octets (UTF-8) puis l'envoie
            self.socket.sendall(message.encode("UTF-8"))
        except socket.error:
            print("unable to send message")

    def tidy_up(self):
        """Arrête l'écoute et ferme la connexion."""
        self.listening = False
        self.socket.close()

    def handle_msg(self, data):
        """Traite un message reçu du serveur."""
        if data == "QUIT":
            self.tidy_up()
        elif data == "":
            # Message vide = connexion coupée par le serveur
            self.tidy_up()
        else:
            # Message normal : on l'affiche
            print(data)


# Ce bloc ne s'exécute que si on lance ce fichier directement (py client.py)
if __name__ == "__main__":
    username = input("Pseudo : ")
    # "ou" : si l'utilisateur appuie sur Entrée, on prend la valeur par défaut
    server = input("Adresse du serveur (Entrée = localhost) : ") or "localhost"
    port_text = input("Port (Entrée = 59001) : ") or "59001"
    try:
        port = int(port_text)
    except ValueError:
        # int() échoue si on tape autre chose qu'un nombre
        print("Erreur : le port doit être un nombre.")
        sys.exit(1)
    try:
        client = Client(username, server, port)
    except socket.error:
        # La connexion échoue si le serveur est éteint ou si l'adresse/le port est faux
        print("Erreur : impossible de se connecter à {0}:{1}. Le serveur est-il lancé ?".format(server, port))
        sys.exit(1)
    client.listen()
    message = ""
    while message != "QUIT":
        message = input()
        client.send(message)
