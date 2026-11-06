import queue
import socket
import tkinter as tk
from tkinter import scrolledtext

from client import Client  # on réutilise la classe Client du terminal (connexion, envoi, écoute)


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
        self.incoming = queue.Queue()  # les messages reçus attendent ici d'être affichés
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)  # clic sur la croix
        self.build_login()

    # ---------- Écran de connexion ----------

    def build_login(self):
        self.login_frame = tk.Frame(self.window)
        self.login_frame.pack(padx=20, pady=20)

        tk.Label(self.login_frame, text="Pseudo :").grid(row=0, column=0, sticky="e")
        self.username_entry = tk.Entry(self.login_frame)
        self.username_entry.grid(row=0, column=1, pady=3)

        tk.Label(self.login_frame, text="Serveur :").grid(row=1, column=0, sticky="e")
        self.server_entry = tk.Entry(self.login_frame)
        self.server_entry.insert(0, "localhost")  # valeur par défaut
        self.server_entry.grid(row=1, column=1, pady=3)

        tk.Label(self.login_frame, text="Port :").grid(row=2, column=0, sticky="e")
        self.port_entry = tk.Entry(self.login_frame)
        self.port_entry.insert(0, "59001")  # valeur par défaut
        self.port_entry.grid(row=2, column=1, pady=3)

        # Étiquette rouge pour afficher les erreurs de connexion
        self.error_label = tk.Label(self.login_frame, fg="red", wraplength=250)
        self.error_label.grid(row=3, column=0, columnspan=2)

        tk.Button(self.login_frame, text="Se connecter", command=self.connect).grid(
            row=4, column=0, columnspan=2, pady=5)
        self.username_entry.focus()
        self.window.bind("<Return>", lambda event: self.connect() if self.client is None else None)

    def connect(self):
        username = self.username_entry.get().strip()
        server = self.server_entry.get().strip() or "localhost"
        port_text = self.port_entry.get().strip() or "59001"

        if not username:
            self.error_label.config(text="Erreur : choisis un pseudo.")
            return
        try:
            port = int(port_text)
        except ValueError:
            self.error_label.config(text="Erreur : le port doit être un nombre.")
            return
        try:
            self.client = GuiClient(username, server, port, self.incoming)
        except socket.error:
            self.error_label.config(
                text="Erreur : impossible de se connecter à {0}:{1}. Le serveur est-il lancé ?".format(server, port))
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
