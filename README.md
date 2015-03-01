# ovh-dynhost
Script permettant d'update un champ A ou AAAA (non dynhost) avec l'api d'OVH en python 3.x


## Installation

Ce script nécessite python ainsi que requests.
Vous pouvez, si nécessaire, créer un virtualenv.

```Bash
cd ~
virtualenv --python=python3 env
source env/bin/activate
git clone https://github.com/steven-martins/ovh-dynhost.git
cd ovh-dynhost
pip install -r requirements.txt
```

(Si vous ne souhaitez pas de virtualenv, omettez les 3 premières commandes)

## Configuration

Voici un exemple de fichier de configuration (dynhost.conf):
```
[credentials]
application_key = n39F1dvkdSiVzFrl
application_secret = DOcqGCL4SPfXNyCtO4xYl3tUOm1qhuTW

[zone]
domain = stevenmartins.fr
subdomain = golgafrincham
```

Vous devez juste spécifier le nom de domaine ainsi que le sous-domaine que vous souhaitez utiliser en tant que dyndns.
Le sous-domaine sera automatiquement créé s'il n'existe pas.

Pour tester le script:
```Bash
python script.py
```
Exemple d'output:
```
(env)steven@Andy ~/ovh-dynhost $ python script.py
2015-03-01 23:12:37,426:INFO:MainThread: Starting new HTTPS connection (1): nsupdate.info
2015-03-01 23:12:37,852:WARNING:MainThread: local: Unable to load file .myip : [Errno 2] No such file or directory: '/home/steven/.myip'
2015-03-01 23:12:37,856:INFO:MainThread: Your ip changed to 1.1.1.1
2015-03-01 23:12:37,891:INFO:MainThread: Starting new HTTPS connection (1): eu.api.ovh.com
Update OK
(env)steven@Andy ~/ovh-dynhost $ python script.py
2015-03-01 23:12:55,800:INFO:MainThread: Starting new HTTPS connection (1): nsupdate.info
2015-03-01 23:12:56,235:INFO:MainThread: Your ip is the same since last check. Nothing to do.
```

## Lancement automatique

Le plus simple consiste à ajouter une règle crontab pour que le script puisse s'exécuter à intervalle régulier.

```Bash
crontab -e
```

Voici un exemple:
```
# m h  dom mon dow   command
*/15 * * * * bash -c "source ~/env/bin/activate && cd ~/ovh-dynhost && python ~/ovh-dynhost/script.py" 2>&1 > ~/ovh-dynhost/last_exec.log
```
