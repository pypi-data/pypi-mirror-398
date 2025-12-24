

# 🚀 GoLV-VM
<div align="center">

![GoLV Platform](https://img.shields.io/badge/>__GoLV_Virtual_Machines-1e3c72?style=for-the-badge&logo=proxmox&logoColor=white&labelColor=0d47a1)
[![Vercel Deployment](https://img.shields.io/badge/vercel-appGoLV-blue?logo=vercel)](https://vercel.com/mauricio-100s-projects/golvcloud/HUH6zJsuxbyoxNbRkHLFTtjPf8an)
[![PyPI Version](https://img.shields.io/pypi/v/golv?color=blue&label=PyPI)](https://pypi.org/project/golv/)
[![Python Version](https://img.shields.io/badge/python-3.12-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Build Status](https://img.shields.io/github/actions/workflow/status/MauricioKk-ship-it/GoLV-VM/.github/workflows/pypi-package.yml?branch=main&label=build&logo=github)](https://github.com/MauricioKk-ship-it/GoLV-VM/actions)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen)]()

GoLV-VM est un **SDK Python pour la gestion de VMs sécurisées** et l'exécution de commandes via un agent intelligent.  
Il permet de créer, configurer et exécuter des commandes sur des VMs distantes de manière simple et sécurisée, prêt pour l'intégration avec IA et automation.

---

## ⚡ Features

- ✅ Création et gestion de VMs (Ubuntu, Debian, Python-Dev, NodeJS, Docker, Wordpress)  
- ✅ SDK facile à utiliser (`GoLVSetup`)  
- ✅ Agent sécurisé pour exécuter des commandes avec filtrage et sécurité  
- ✅ Support pour exécuter du code Python et des commandes Git  
- ✅ Commandes prédéfinies pour automatiser vos VMs  
- ✅ Gestion des erreurs et sécurité avancée (commandes interdites, longueur maximale, etc.)  

---

## 📦 Installation

# Cloner le repo
```bash
git clone https://github.com/gopu-inc/GoLV-VM.git
cd GoLV-VM

# Installer en mode editable
pip install -e .
```
# via python
```bash
pip install golv
```

---

# 🧰 Usage

Initialisation du SDK
```python
from golv import GoLVSetup, VMType

# Initialiser le SDK
setup = GoLVSetup(api_key="votre_clef_api")
client = setup.get_client()

# Créer une VM Ubuntu par défaut
vm_config = setup.create_default_vm("ma-vm")
vm = client.create_vm(vm_config)
print("VM créée:", vm)

Création d’un agent sécurisé

from golv import GoLVSetup

setup = GoLVSetup(api_key="votre_clef_api")

# Créer un agent avec commandes autorisées
agent = setup.create_agent(
    allowed_commands=["echo", "python", "git"]
)

# Exécuter une commande
result = agent.execute("echo 'Hello GoLV'")
print(result.output)

# Exécuter du code Python
py_result = agent.execute_python("print('Hello from Python')")
print(py_result.output)

Commandes sécurisées et prédéfinies

# Commande prédéfinie (ex: list_files)
predef = agent.predefined("list_files")
print(predef.output)

# Gestion des erreurs de sécurité
try:
    agent.execute("rm -rf /")
except Exception as e:
    print("Sécurité:", e)

```
---

# 📊 Structure du SDK
```bash
golv/
├── __init__.py          # Expose GoLVSetup, Client, Agent, Exceptions
├── client.py            # Client HTTP pour API GoLV
├── agent.py             # Agent sécurisé pour exécution de commandes
├── models.py            # Dataclasses VMConfig, CommandResult, VMType...
├── exceptions.py        # Gestion des erreurs et sécurité
└── setup_golv.py        # Classe GoLVSetup (point d'entrée SDK)

```
---

# 🛡️ Sécurité

Commandes interdites détectées automatiquement (rm -rf, shutdown, etc.)

Longueur maximale des commandes configurable

Liste blanche de commandes autorisées

Agent isolé et sécurisé pour exécution IA



---

# 🧪 Tests
```bash
python test_golv_sdk.py
```
Ce script teste :

Création de VM

Agent sécurisé

Exécution de commandes (echo, Python, Git)

Sécurité et exceptions

Commandes prédéfinies



---

# 🔗 Liens

[GitHub Repo](https://github.com/gopu-inc/GoLV-VM)

[PyPI Package](https://pypi.org/project/golv-py/)


-
---

# 📄 License

MIT © GOPU.inc

---
