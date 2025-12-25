import os

class project_me:
  def criar_projeto():
    nome = input("qual é o nome do prejeto?: ")
    altor = input("qual é o seu nome?: ")
    email = input("qual é o seu email?: ")
    sim_ou_não = input("tem dependente?: ")
    dependentes = []
    while sim_ou_não == "sim":
      sim_ou_não = input("tem dependente?: ")
      dependente = input("coloque o dependente: ")
      dependentes.append(dependente)
    descrição = input("coloque a descrição do projeto: ")
    if not " " in nome:
      pasta_base = os.path.dirname(os.path.abspath(__file__))
      project = os.path.join(pasta_base, f"{nome}_project")
      os.makedirs(project, exist_ok= True)
      pasta_principal = os.path.join(project, f"{nome}")
      os.makedirs(pasta_principal,exist_ok= True)
      __initpy__ = os.path.join(pasta_principal, "__init__.py")
      with open(__initpy__, "w") as __init__:
        inscritura___init__ = f"""from .modulo1 import modulo1 #coloque o nome do modulo"""
        __init__.write(inscritura___init__)
      modulo = os.path.join(pasta_principal, "modulo1.py")
      with open(modulo, "w", encoding="utf-8") as modulo1:
        inscritura_modulo1 =  f"""class modulo1:
        
  def olá_mundo():
    print("olá_mundo")"""
        modulo1.write(inscritura_modulo1)
      licensa = os.path.join(project, "LICENSE.txt")
      with open (licensa, "w", encoding="utf-8") as License:
        inscritura_License = """coloque sua licensa aqui"""
        License.write(inscritura_License)
      toml = os.path.join(project, "pyproject.toml")
      with open (toml, "w", encoding="utf-8") as pyproject_toml:
        toml_alxiliar = f"altor = {altor}, email = {email}"
        toml_cisença = """file = "LICENSE"""""
        toml_depententes = """,
""".join(dependentes)
        inscritura_toml = f"""[project]
name = {nome}
version = "1.1.1"
description = {descrição}
authors = [{toml_alxiliar}]
maintainers = [{toml_alxiliar}]
readme = "README.md"
license = {toml_cisença}
requires-python = ">=verção do python minima para o seu projeto" 
  dependencies = [
      {toml_depententes}
  ]
keywords = ["coloque", "uma", "tag"]
classifiers = [
  "Programming Language :: Python :: 3", #definido por padrão, mas você pode trocar
  "Topic :: Multimedia :: Sound/Audio",
  "Topic :: Software Development :: Libraries",
  "Intended Audience :: Developers",
  "Operating System :: OS Independent"
  ]

[project.urls]
"Homepage" = "https://github.com/" #coloque aqui o repositorio onde o projeto vai estar
"Source" = "https://github.com/"
"Issues" = "https://github.com/"


[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"
"""
        pyproject_toml.write(inscritura_toml)
        leia_me = os.path.join(project, "README.MD")
        with open (leia_me, "w", encoding="utf-8") as README_md:
          inscritura_README_md = f"""# {nome}
## verção
**1.1.1**
## modulo1
### funções
- olá_mundo()
### exemplo
```python
from {nome} import modulo1

  modulo1.olá_mundo()
```
"""
          README_md.write(inscritura_README_md)
        setdown = os.path.join(project, "setup.py")
        with open(setdown, "w", encoding="utf-8") as setup:
          inscritura_setup = f"""from setuptools import setup, find_packages

setup(
name='{nome}',
version='1.1.1',
packages=find_packages(),
description={descrição},
author={altor},
author_email={email}
)
          """
          setup.write(inscritura_setup)
        

    else:
      raise ValueError(f"{nome} contem um espaço em branco, poderia por favor remove-lo ou substituilo por '_' ")