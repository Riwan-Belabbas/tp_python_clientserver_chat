# tp_python_clientserver_chat

TP final Python (CFA INSTA) : application de chat client/serveur en Python, avec interface graphique Tkinter et découverte automatique des serveurs.

Auteur : Riwan Belabbas

## Fonctionnalités

- Un serveur accepte plusieurs clients en même temps (un thread par client) et diffuse chaque message à tous.
- Un client en ligne de commande (`client.py`) et un client avec **interface graphique Tkinter** (`client_gui.py`).
- **Messages d'erreur clairs** : serveur injoignable, port invalide, connexion perdue.
- **Valeurs par défaut** à la connexion (adresse `localhost`, port `59001`).
- **Nom du serveur** : le serveur a un nom, renvoyé avec la commande `/name`.
- **Découverte automatique** : le client cherche les serveurs du réseau local et les affiche dans une liste, avec leur nom.

## Prérequis

- Python 3 (Tkinter est inclus avec l'installation standard de Python sur Windows).
- Aucune bibliothèque externe.

Sous Windows, si la commande `python` n'est pas reconnue, utiliser `py` à la place.

## Lancer le projet

### 1. Le serveur

```
py server.py
```

Le programme demande un nom pour le serveur (Entrée = « Serveur de chat »), puis écoute sur le port TCP `59001`. Il répond aussi aux appels de découverte sur le port UDP `59002`.

### 2. Un client avec interface graphique

```
py client_gui.py
```

- Saisir un pseudo.
- Cliquer sur **Rechercher des serveurs** : les serveurs trouvés s'affichent dans la liste. Un clic remplit l'adresse et le port, un double-clic se connecte.
- Ou saisir l'adresse et le port à la main, puis cliquer sur **Se connecter**.

Lancer `client_gui.py` plusieurs fois (avec des pseudos différents) pour discuter entre plusieurs clients.

### 3. Un client en ligne de commande (facultatif)

```
py client.py
```

## Commandes

| Commande | Effet |
|---|---|
| `/name` | Le serveur répond avec son nom (uniquement au demandeur) |
| `QUIT` | Quitte le chat (client en ligne de commande) |

## Organisation du code

| Fichier | Rôle |
|---|---|
| `server.py` | Serveur TCP : accepte les clients, diffuse les messages, répond aux appels de découverte UDP |
| `clientthread.py` | Un thread par client connecté : lit ses messages, gère le pseudo, `/name` et le départ |
| `client.py` | Client en ligne de commande : connexion, envoi, écoute dans un thread séparé |
| `client_gui.py` | Client graphique Tkinter, qui réutilise la classe `Client` |

## Comment ça marche

- **Chat** : chaque client est connecté en TCP au serveur. Quand un client envoie un message, le serveur le renvoie à tous les clients connectés.
- **Interface graphique** : l'écoute du réseau tourne dans un thread séparé et dépose les messages dans une file d'attente (`queue`). La fenêtre vérifie cette file toutes les 100 ms, ce qui évite qu'elle se fige.
- **Découverte automatique** : le client envoie la commande `/name` en UDP (broadcast sur le réseau local, et vers la machine locale). Chaque serveur répond avec `nom;port`, et le client affiche les réponses reçues pendant 1,5 seconde.

## Améliorations apportées au code de base

- Commentaires ajoutés dans tous les fichiers.
- Correction du `except socket.error` dans `clientthread.py` (le module `socket` était importé de façon incorrecte, ce qui faisait planter le thread lors d'une coupure brutale).
- Messages d'erreur lisibles et valeurs par défaut dans `client.py`.
- Interface graphique Tkinter avec écran de connexion.
- Nom du serveur et commande `/name`.
- Découverte automatique des serveurs.

## Limites

- Le broadcast UDP ne traverse pas les routeurs : la découverte ne fonctionne qu'entre machines du même réseau local, et certains réseaux peuvent la bloquer. Sur une même machine, la recherche trouve toujours le serveur local.
- Les pseudos ne sont pas vérifiés (deux clients peuvent porter le même).
