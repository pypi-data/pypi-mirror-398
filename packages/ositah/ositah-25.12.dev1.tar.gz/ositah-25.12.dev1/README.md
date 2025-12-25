# OSITAH : Outil de Suivi de Temps et d'Activités basé sur Hito

OSITAH est une application web, basée sur le framework [Dash](https://dash.plotly.com), qui permet
le suivi des déclarations de temps dans Hito, leur validation et leur exportation dans NSIP.
L'accès aux différentes fonctionnalités est soumis à l'authentification de
l'utilisateur : les droits dans `ositah` sont dérivés de ceux dans Hito.

OSITAH nécessite un fichier de configuration `ositah.cfg` : par défaut il est recherché dans le
répertoire courant et s'il n'existe pas, dans le répertoire où est installé l'application OSITAH. 
L'option `--configuration-file` permet de spécifier un autre fichier/localisation, par exemple pour
utiliser une configuration de test. 

L'instance de production s'exécute normalement à travers [gunicorn](https://gunicorn.org), un serveur
SWGI écrit en Python et fournit par le module `gunicorn`. Dans ce contexte, le fichier de configuration
doit être placé dans le répertoire défini comme le répertoire courant de l'application (l'option
`--configuration-file` n'est pas utilisable).

L'exécution de `ositah` suppose l'accès à la base de donnée Hito.

## Installation

Le déploiement d'OSITAH nécessite le déploiement d'un environnement Python, de préférence distinct
de ce qui est délivré par l'OS car cela pose de gros problèmes avec les prérequis sur les versions
des dépendances. Les environnements recommandés sont [pyenv](https://github.com/pyenv/pyenv),
[poetry](https://python-poetry.org) ou [Anaconda](https://www.anaconda.com/products/individual). 
Pour la création d'un environnement virtuel avec Conda, voir la
[documentation spécifique](https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#creating-an-environment-with-commands).

Pour installer OSITAH, il faut utiliser les commandes suivantes :

```bash
pip install ositah
```

### Dépendances 

Pour connaitre la liste des dépendances de l'application OSITAH, voir la propriété `dependencies`
dans le fichier `pyproject.toml` se trouvant dans les sources de l'application. 
Elles sont automatiquement installées par la commande `pip`.


## Configuration

### OSITAH

Toute la configuration de l'application OSITAH est déclarée dans le fichier `ositah.cfg` qui doit
se trouver dans le répertoire courant de l'application pour une instance de production gérée par 
le serveur SWGI, `gunicorn`. Pour une instance de test ou de développement qui n'utilise pas
`gunicorn`, il est possible de spécifier le fichier de configuration à utiliser avec l'option
`--configuration-file`.

### Gunicorn

`gunicorn` est le serveur WSGI recommandé pour exécuter une instance de production. Son installation
consiste à installer 2 modules Python : `gunicorn` et `greenlet`.

Le repository Git de'OSITAH contient un répertoire `gunicorn.config` avec les 3 fichiers importants
pour la configuration de `gunicorn` qu'il faut éditer pour adapter les répertoires à la configuration
du site :

* `gunicorn@.service` : script `systemd` à installer pour démarrer l'instance OSITAH. Si le
l'instance OSITAH s'appelle `ositah`, la systemd unit à utiliser pour gérer le service est
`gunicorn@ositah`.
* `gunicorn.ositah` : fichier à placer en `/etc/sysconfig` définissant la configuration spécifique
à OSITAH (répertoire courant, options `gunicorn`, entry point).
* `app.conf.py` : options `gunicorn` à utiliser avec l'instance OSITAH

## Validation des déclarations : structure des tables OSITAH

La validation des déclarations de temps se fait agent par agent, en utilisant le bouton de validation correspondant
à l'agent. Ce bouton n'est actif qu'à partir de la date définie dans la table `ositah_validation_period` pour la
période en cours, sauf si on a ajouté des exceptions dans le fichier de configuration, telles que :

```
validation:
  override_period:
    - ROLE_SUPER_ADMIN
```

`override_period` est une liste de roles qui peuvent faire des validations hors de la période standard.

La validation d'une déclaration a pour effet d'enregistrer le temps déclaré sur chacune des activités de l'agent dans
la table `ositah_project_declaration`. Cette entrée est associée à une entrée dans la table `ositah_validation` qui
contient la date de la validation, l'agent concerné par cette validation (son `agent id` Hito), la validation période
à laquelle correspond cette validation (référence à la table `ositah_validation_period`) ainsi que le statut
de la validation. Si on invalide cette validation ultérieurement, le statut passe à `0` et la date de la validation
est copiée dans l'attribut `initial_timestamp`. L'entrée dans `ositah_project_declaration` n'est pas détruite. Lorsque 
la déclaration de  l'agent est à nouveau validée ultérieurement, une nouvelle entrée est créée à la fois dans 
`ositah_project_declaration` et dans `ositah_validation`, comme pour la validation initiale. 
Il est donc possible d'avoir un historique des opérations de validation sur une période donnée (pas exploité
par l'application OSITAH pour l'instant). Par contre, quand on lit les validations, il faut faire attention à
prendre la dernière dans une période donnée qui a son statut à `1`.

La création de l'entrée pour définir une période de déclaration dans `ositah_validation_period` (date de début et 
date de fin de la période, date de  début de la validation) n'est pas gérée par OSITAH actuellement : il faut créer
une entrée dans la table avec la commande SQL `INSERT INTO`.


## Export NSIP

OSITAH permet d'exporter vers NSIP les déclarations validées. La table du menu `Export` indique
l'état de la synchronisation entre NSIP et OSITAH, agent par agent. Un code couleur permet
d'identifier facilement si une déclaration est correctement synchronisée ou non. Seules les
déclarations qui ne sont pas correctement synchronisées peut être exportées. Lors de l'export,
la déclaration est indiquée comme validée par le responsable dans NSIP, avec la date de sa validation
dans OSITAH.

Il est possible d'exporter toutes les déclarations ou de les sélectionner agent par  agent.
Lorsqu'un agent est sélectionné, toutes ses déclarations non synchronisées sont exportées. Le bouton
de sélection dans la barre de titre permet de sélectionner tous les agents sélectionnables en un clic.

Les déclarations d'un agent ne peuvent pas être exportées si l'agent n'existe pas dans NSIP,
c'est-à-dire s'il est absent de RESEDA. La correction du problème, si on souhaite que les
déclarations da cet agent soient mises dans NSIP, nécessite une intervention du Service RH
pour ajouter la personne dans RESEDA.

Il peut aussi y avoir des déclarations qui ont été faites directement dans NSIP et qui ne sont 
pas encore validées dans OSITAH. Dans ce cas, elles apparaitront comme manquantes dans OSITAH, 
même si elles sont présentes, tant qu'elles ne seront pas validées.

