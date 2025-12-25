# hito_tools module

Ce repository contient le module Pyhton `hito_tools` utilisé par les autres outils Python autour de Hito (OSITAH, hito2lists...).


## Installation

### Environnement Python

L'installation de [hito_tools](https://pypi.org/project/hito-tools) nécessite un environnement Python avec une version >= 3.8.
Il est conseillé d'utiliser un environnement
virtuel pour chaque groupe d'applications et de déployer le module `hito_tools` dans cet environnemnt. Il est recommandé d'utiliser
une distribution de Python totalement indépendante du système d'exploitation comme [pyenv](https://github.com/pyenv/pyenv),
[poetry](https://python-poetry.org) ou [Anaconda](https://www.anaconda.com/products/individual). Pour la création d'un
environnement virtuel avec Conda, voir la 
[documentation spécifique](https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#creating-an-environment-with-commands).

Les modules Python requis par ce module sont :
* pandas (conda-forge)
* requests (conda-forge)

Avec `conda`, il faut utiliser l'option `-c conda-forge` lors de la commande `conda install`. 


### Installation du module hito_tools

L'installation se fait avec la commande `pip` de l'environnement Python utilisé :

```bash
pip install hito_tools
```
