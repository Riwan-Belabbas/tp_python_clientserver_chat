import queue
import socket
import time
import tkinter as tk
from tkinter import scrolledtext

from client import Client  # on réutilise la classe Client du terminal (connexion, envoi, écoute)

# Port UDP des serveurs pour la découverte automatique (le même que dans server.py)
DISCOVERY_PORT = 59002


def discover_servers(timeout=1.5):
    """Cherche les serveurs du réseau local.
    Envoie "/name" en UDP (broadcast + adresse locale), puis collecte les réponses
    pendant 'timeout' secondes. Renvoie une liste de (nom, ip, port)."""
    found = {}
    udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)  # autorise le broadcast
    udp.settimeout(0.3)  # recvfrom() ne bloque pas plus de 0,3 s à chaque tour
    try:
        # 255.255.255.255 = "tout le réseau local" ; 127.0.0.1 = cette machine (sécurité pour la démo)
        for target in ("255.255.255.255", "127.0.0.1"):
            try:
                udp.sendto(b"/name", (target, DISCOVERY_PORT))
            except OSError:
                pass
        end = time.time() + timeout
        while time.time() < end:
            try:
                data, address = udp.recvfrom(1024)
            except socket.timeout:
                continue
            except ConnectionResetError:
                continue  # Windows : signale qu'aucun serveur n'écoutait sur une des adresses
            except OSError:
                break
            try:
                name, port = data.decode("UTF-8").rsplit(";", 1)
                found[(name, int(port))] = address[0]  # même serveur vu deux fois = une seule entrée
            except ValueError:
                pass  # réponse mal formée : on l'ignore
    finally:
        udp.close()
    return [(name, ip, port) for (name, port), ip in found.items()]


class GuiClient(Client):
    """Le Client du terminal, mais les messages reçus sont mis dans une file
    d'attente au lieu d'être affichés avec print()."""

    def __init__(self, username, server, port, incoming):
        self.incoming = incoming  # la file d'attente partagée avec la fenêtre
        super().__init__(username, server, port)

    def handle_msg(self, data):
        # Appelée dans le THREAD d'écoute à chaque message reçu du serveur
        if data == "QUIT" or data == "":
            self.tidy_up()
            self.incoming.put("*** Connexion au serveur perdue ***")
        else:
            self.incoming.put(data)


class ChatApp():
    """La fenêtre : un écran de connexion, puis l'écran de chat."""

    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Chat")
        self.client = None
        self.found_servers = []  # résultats de la dernière recherche
        self.incoming = queue.Queue()  # les messages reçus attendent ici d'être affichés
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)  # clic sur la croix
        self.build_login()

    # ---------- Écran de connexion ----------

    def build_login(self):
        self.login_frame = tk.Frame(self.window)
        self.login_frame.pack(padx=20, pady=20)

        tk.Label(self.login_frame, text="Pseudo :").grid(row=0, column=0, sticky="e")
        self.username_entry = tk.Entry(self.login_frame, width=28)
        self.username_entry.grid(row=0, column=1, pady=3)

        tk.Label(self.login_frame, text="Serveur :").grid(row=1, column=0, sticky="e")
        self.server_entry = tk.Entry(self.login_frame, width=28)
        self.server_entry.insert(0, "localhost")  # valeur par défaut
        self.server_entry.grid(row=1, column=1, pady=3)

        tk.Label(self.login_frame, text="Port :").grid(row=2, column=0, sticky="e")
        self.port_entry = tk.Entry(self.login_frame, width=28)
        self.port_entry.insert(0, "59001")  # valeur par défaut
        self.port_entry.grid(row=2, column=1, pady=3)

        # Découverte automatique : bouton + liste des serveurs trouvés
        tk.Button(self.login_frame, text="Rechercher des serveurs", command=self.search_servers).grid(
            row=3, column=0, columnspan=2, pady=(10, 3))
        self.server_list = tk.Listbox(self.login_frame, height=4, width=45)
        self.server_list.grid(row=4, column=0, columnspan=2)
        self.server_list.bind("<<ListboxSelect>>", self.on_server_selected)  # un clic remplit les champs
        self.server_list.bind("<Double-Button-1>", lambda event: self.connect())  # double-clic = connexion

        # Étiquette de statut (rouge pour une erreur)
        self.status_label = tk.Label(self.login_frame, wraplength=300)
        self.status_label.grid(row=5, column=0, columnspan=2, pady=3)

        tk.Button(self.login_frame, text="Se connecter", command=self.connect).grid(
            row=6, column=0, columnspan=2, pady=5)
        self.username_entry.focus()
        self.window.bind("<Return>", lambda event: self.connect() if self.client is None else None)

    def set_status(self, text, error=False):
        self.status_label.config(text=text, fg="red" if error else "black")

    def search_servers(self):
        """Lance la découverte automatique et remplit la liste."""
        self.set_status("Recherche en cours...")
        self.window.update()  # force l'affichage du message avant la recherche (≈ 1,5 s)
        self.found_servers = discover_servers()
        self.server_list.delete(0, "end")
        for name, ip, port in self.found_servers:
            self.server_list.insert("end", "{0}  ({1}:{2})".format(name, ip, port))
        if self.found_servers:
            self.set_status("{0} serveur(s) trouvé(s). Clique sur l'un d'eux.".format(len(self.found_servers)))
        else:
            self.set_status("Aucun serveur trouvé.", error=True)

    def on_server_selected(self, event=None):
        """Quand on clique sur un serveur de la liste, on remplit l'adresse et le port."""
        selection = self.server_list.curselection()
        if selection:
            name, ip, port = self.found_servers[selection[0]]
            self.server_entry.delete(0, "end")
            self.server_entry.insert(0, ip)
            self.port_entry.delete(0, "end")
            self.port_entry.insert(0, str(port))

    def connect(self):
        username = self.username_entry.get().strip()
        server = self.server_entry.get().strip() or "localhost"
        port_text = self.port_entry.get().strip() or "59001"

        if not username:
            self.set_status("Erreur : choisis un pseudo.", error=True)
            return
        try:
            port = int(port_text)
        except ValueError:
            self.set_status("Erreur : le port doit être un nombre.", error=True)
            return
        try:
            self.client = GuiClient(username, server, port, self.incoming)
        except socket.error:
            self.set_status(
                "Erreur : impossible de se connecter à {0}:{1}. Le serveur est-il lancé ?".format(server, port),
                error=True)
            return

        self.client.listen()          # lance l'écoute du serveur dans un thread séparé
        self.login_frame.destroy()    # on enlève l'écran de connexion
        self.window.unbind("<Return>")
        self.build_chat()             # on affiche l'écran de chat
        self.check_incoming()         # on commence à vérifier les messages reçus

    # ---------- Écran de chat ----------

    def build_chat(self):
        self.window.title("Chat - " + self.client.username)

        # Zone d'affichage (verrouillée : seul le programme y écrit)
        self.display = scrolledtext.ScrolledText(self.window, width=50, height=20, state="disabled")
        self.display.pack(padx=10, pady=10)

        # Champ de saisie + bouton Envoyer
        self.entry = tk.Entry(self.window, width=40)
        self.entry.pack(side="left", padx=10, pady=(0, 10))
        self.entry.bind("<Return>", self.send_message)  # touche Entrée = envoyer
        self.entry.focus()

        self.button = tk.Button(self.window, text="Envoyer", command=self.send_message)
        self.button.pack(side="left", padx=(0, 10), pady=(0, 10))

    def show_message(self, text):
        """Ajoute une ligne dans la zone d'affichage."""
        self.display.config(state="normal")
        self.display.insert("end", text.rstrip("\n") + "\n")
        self.display.config(state="disabled")
        self.display.see("end")

    def send_message(self, event=None):
        text = self.entry.get()
        if text:
            # Le client ajoute le pseudo et envoie au serveur.
            # Pas d'affichage local : le serveur nous renvoie notre message comme aux autres.
            self.client.send(text)
            self.entry.delete(0, "end")

    def check_incoming(self):
        """Toutes les 100 ms, affiche les messages arrivés dans la file d'attente.
        On passe par une file car Tkinter ne doit être modifié que par le thread de la fenêtre,
        pas par le thread d'écoute du réseau."""
        while not self.incoming.empty():
            self.show_message(self.incoming.get())
        self.window.after(100, self.check_incoming)  # se re-planifie dans 100 ms

    # ---------- Fermeture ----------

    def on_close(self):
        if self.client is not None:
            self.client.tidy_up()  # ferme proprement la connexion
        self.window.destroy()

    def run(self):
        self.window.mainloop()


if __name__ == "__main__":
    ChatApp().run()
