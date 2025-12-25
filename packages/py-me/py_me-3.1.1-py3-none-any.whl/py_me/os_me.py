import os
from datetime import datetime
import io
from rich.traceback import install, Console
import json
from dataclasses import dataclass, field
from typing import Optional, Callable, Any
import locale

@dataclass
class Details:
    log_file: str = "log.txt"
    timeline_file: str = "TIMELINE_os_me.json"

    encoding: str = "utf-8"

    language: str = "en"

    enable_logging: bool = True
    enable_rich_traceback: bool = True
    auto_snapshot_on_edit: bool = True
    avoid_duplicate_snapshots: bool = True

    timestamp_format: str = "%d/%m/%Y %H:%M:%S"

    custom_logger: Optional[Callable[[str], None]] = None

    _messages: dict = field(default_factory=lambda: {
        "en": {
            "start_flow": "[--__START OF FLOW__--]",
            "edit": "[EDIT] {}° flow event: {} was edited",
            "add": "[ADD] {}° flow event: content added to {}",
            "create": "[CREATE] {}° flow event: {} was created",
            "undo": "[UNDO] {}° flow event: {} restored to version {}",
            "error": "[ERROR] {}° flow event: {}",
            "file_not_found": "{} not found",
            "file_exists": "{} already exists",
            "undo_err": "[ERROR] {numero}° flow event: command undo invalid ({content})",
            "lost version": "version {} not found for {}",
            "add_err": "error while trying to ass {} error type: {}",
            "exec": "[EXEC] {}° flow event: {} executed successfully!",
            "exec_error": "error executing {} error type: {}",
            "error_sequence": "[ERROR_SEQUNECE] {}° flow event: error encountered during execution: {}",
            "error_list": "the specific list is an empty list",
            "error_not_list": "{} is not a list"
        },
        "pt": {
            "start_flow": "[--__INICIO DE FLUXO__--]",
            "edit": "[EDIT] {}° evento de fluxo: {path} foi editado",
            "add": "[ADD] {}° evento de fluxo: conteúdo adicionado a {path}",
            "create": "[CREATE] {}° evento de fluxo: {path} foi criado",
            "undo": "[UNDO] {}° evento de fluxo: {path} restaurado para versão {}",
            "error": "[ERROR] {}° evento de fluxo: {}",
            "file_not_found": "{} não existe",
            "file_exists": "{} já existe",
            "undo_err": "[ERROR] {}° evento de fluxo: comando undo inválido ({})",
            "lost version": "versão {} não encontrada para {}",
            "add_err": "erro ao tentar adicionar {} tipo de erro: {}",
            "exec": "[EXEC] {}° evento de fluxo: {} executado com exito!",
            "exec_error": "erro na execução de {} tipo de erro: {}",
            "error_sequence": "[ERROR_SEQUENCE] Evento de fluxo {}: erro encontrado durante a execução: {}",
            "error_list": "a lista especificada é uma lista vazia",
            "error_not_list": "{} não é uma lista"
        }
    })

    def get_message(self, key: str, *args, **fmt) -> str:
      lang_dict = self._messages.get(self.language, self._messages["en"])
      msg = lang_dict.get(key, key)  # fallback
      if args or fmt:
        # primeira tentativa: usar args posicionais e kwargs nominais
        try:
          return msg.format(*args, **fmt)
        except Exception:
          # se falhar, tente usar apenas args posicionais
          try:
            return msg.format(*args)
          except Exception:
            # se ainda falhar e houver kwargs, tente usar os valores dos kwargs
            if fmt:
              try:
                return msg.format(*fmt.values())
              except Exception:
                try:
                  return msg.format(**fmt)
                except Exception:
                  return msg
            return msg
      return msg

class os_me_error(Exception):
  def __init__(self, exception):
    super().__init__(exception)
    self.exception = exception

class utilidades:
    def __init__(self, details: Details):
        self.details = details
    
    def registrar_log(self, mensagem: str):
        if not self.details.enable_logging:
            return
        if self.details.custom_logger:
            self.details.custom_logger(mensagem)
            return
        
        with open(self.details.log_file, "a", encoding=self.details.encoding) as log:
            timestamp = datetime.now().strftime(self.details.timestamp_format)
            log.write(f"[{timestamp}] {mensagem}\n")

class file_class:
  def __init__(self, details: Details = None):
    self.details = details or Details()  # default config
    self.utilidades = utilidades(self.details)
    self.ultilidades = self.utilidades
    self.numero = 1
    self.inicio_de_fluxo = True
    self.lista_de_erros = []
    self.numero_versao = 1
    if self.details.enable_rich_traceback:
      install()

  def replace(self, path: str, content: str) -> None:
    if self.inicio_de_fluxo:
        if self.details.enable_logging:
          self.utilidades.registrar_log(
            self.details.get_message("start_flow")
          )
          self.inicio_de_fluxo = False

    if not os.path.exists(path):
        try:
            raise os_me_error(
               self.details.get_message("file_not_found", caminho = path)
            )
        except os_me_error as a:
            if self.details.enable_rich_traceback:
              console = Console()
              console.print_exception()
            if self.details.enable_logging:
              self.utilidades.registrar_log(
                self.details.get_message("error", number= self.numero, message= a)
              )
              self.numero += 1
              return

    # Ler conteúdo atual
    with open(path, "r", encoding="utf-8") as filer_r:
        conteudo_atual = filer_r.read()

    # Criar snapshot
    if self.details.auto_snapshot_on_edit:
      snapshot = {
        "versao": self.numero_versao,
        "timestamp": datetime.now().isoformat(),
        "conteudo": conteudo_atual
      }

      # Atualizar timeline
      if os.path.exists(self.details.timeline_file) and os.path.getsize(self.details.timeline_file) > 0:
          try:
              with open(self.details.timeline_file, "r", encoding="utf-8") as f:
                  data = json.load(f)
          except json.JSONDecodeError:
              data = {}
      else:
          data = {}

      if path not in data:
          data[path] = []

      # Evitar duplicação de versão e conteúdo
      versoes_existentes = [s["versao"] for s in data[path]]
      conteudos_existentes = [s["conteudo"] for s in data[path]]

      if snapshot["conteudo"] in conteudos_existentes:
        # já existe esse conteúdo, não precisa salvar de novo
        pass
      else:
        # garantir que o número da versão seja único
        while snapshot["versao"] in versoes_existentes:
          self.numero_versao += 1
          snapshot["versao"] = self.numero_versao

        data[path].append(snapshot)


      with open(self.details.log_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

      self.numero_versao += 1

      # Escrever novo conteúdo ou desfazer
      with open(path, "w", encoding="utf-8") as filer:
          if content.startswith("undo"):
              try:
                  versao_pedida = int(content.split()[1])
              except (IndexError, ValueError):
                  if self.details.enable_logging:
                    self.ultilidades.registrar_log(
                      self.details.get_message("undo_err", numero = self.numero, content = content)
                    )
                  return

              if path in data:
                for snapshot in data[path]:
                    if snapshot["versao"] == versao_pedida:
                        filer.write(snapshot["conteudo"])
                        if self.details.enable_logging:
                          self.ultilidades.registrar_log(
                            self.details.get_message("undo", number = self.numero, path = path, version = versao_pedida)
                          )
                        self.numero += 1
                        return
              try:
                 raise os_me_error(self.details.get_message("file_not_found", caminho = path))
              except os_me_error:
                if self.details.enable_logging:
                  self.ultilidades.registrar_log(
                    self.details.get_message("error", number = self.numero, conteudo = self.details.get_message("file_not_found", caminho = path))
                  )
          else:
            filer.write(content)
            if self.details.enable_logging:
              self.ultilidades.registrar_log(
                self.details.get_message("edit", number = self.numero)
              )
            self.numero += 1

  def create(self, new_path: str, content: str = "") -> str:
    if self.inicio_de_fluxo == True:
      if self.details.enable_logging:
        self.ultilidades.registrar_log(
          self.details.get_message("start_flow")
        )
        self.inicio_de_fluxo = False
      if not os.path.exists(new_path):
        with open(new_path, "x", encoding="utf-8") as filer:
          filer.write(content)
        if self.details.enable_logging:
          self.ultilidades.registrar_log(
              self.details.get_message("create", numero = self.numero)
          )
          self.numero += 1
          return new_path
      else:
          try:
            raise os_me_error(self.details.get_message("file_exists", ooo = new_path))
          except os_me_error as a:
            if self.details.enable_rich_traceback == True:
              console = Console()
              console.print_exception()
            if self.details.enable_logging:
              self.ultilidades.registrar_log(
                self.details.get_message("error", numero = self.numero, erro = self.details.get_message("file_exists", ooo = new_path))
              )
              self.numero += 1

  def add(self, path: str, content: str) -> None:
    if self.inicio_de_fluxo == True:
      if self.details.enable_logging:
        self.ultilidades.registrar_log(
          self.details.get_message("start_flow")
        )
        self.inicio_de_fluxo = False
    if os.path.exists(path):
      with open(path, "a", encoding="utf-8") as so:
        so.write(content)
      if self.details.enable_logging:
        self.ultilidades.registrar_log(
          self.details.get_message("add", numero = self.numero)
        )
      with open(path, "r", encoding="utf-8") as filer_r:
        conteudo_atual = filer_r.read()

      # Criar snapshot
    if self.details.auto_snapshot_on_edit:
      snapshot = {
        "versao": self.numero_versao,
        "timestamp": datetime.now().isoformat(),
        "conteudo": conteudo_atual
      }

      # Atualizar timeline
      if os.path.exists(self.details.timeline_file) and os.path.getsize(self.details.timeline_file) > 0:
          try:
              with open(self.details.timeline_file, "r", encoding="utf-8") as f:
                  data = json.load(f)
          except json.JSONDecodeError:
              data = {}
      else:
          data = {}

      if path not in data:
          data[path] = []

      # Evitar duplicação de versão e conteúdo
      versoes_existentes = [s["versao"] for s in data[path]]
      conteudos_existentes = [s["conteudo"] for s in data[path]]

      if snapshot["conteudo"] in conteudos_existentes:
        # já existe esse conteúdo, não precisa salvar de novo
        pass
      else:
        # garantir que o número da versão seja único
        while snapshot["versao"] in versoes_existentes:
          self.numero_versao += 1
          snapshot["versao"] = self.numero_versao

        data[path].append(snapshot)
      if not os.path.exists(path):
        try:
          raise os_me_error(self.details.get_message("file_not_found", caminho = path))
        except os_me_error:
          if self.details.enable_rich_traceback:
            console = Console()
            console.print_exception()
          if self.details.enable_logging:
            self.ultilidades.registrar_log(
              self.details.get_message("error", numero = self.numero, erro = self.details.get_message("add_err", verção = self.numero_versao, erro = self.details.get_message("file_not_found", caminho = path)))
            )
            self.numero += 1
      else:
        with open(self.details.log_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        self.numero_versao += 1

  def execution_sequence(self, paths: list, ignore_error: bool = False, list_erros: bool = False) -> None:
    if self.inicio_de_fluxo == True:
      if self.details.enable_logging:
        self.ultilidades.registrar_log(
          self.details.get_message("start_flow")
        )
        self.inicio_de_fluxo = False
    if isinstance(paths, list):
      if paths:
        for filer in paths:
          if os.path.exists(filer):
            with open(filer, "r", encoding="utf-8") as exe:
              e = exe.read()
              try:
                exec(e, {})
                if self.details.enable_logging:
                  self.utilidades.registrar_log(
                    self.details.get_message("exec", numero = self.numero, exec = filer)
                  )
              except Exception as err:
                if ignore_error == True:
                   pass
                elif list_erros == True:
                   self.lista_de_erros.append(err)
                else:
                  if self.details.enable_logging:
                    self.utilidades.registrar_log(
                      self.details.get_message("exec_error", aaa = filer, tipo = err)
                    )
                  raise err
              finally:
                if self.details.enable_logging:
                 self.numero +=1
          else:
            try:
              raise os_me_error(self.details.get_message("file_not_found", arquivo = filer))
            except os_me_error:
              if self.details.enable_rich_traceback:
                console = Console()
                console.print_exception()
              if self.details.enable_logging:
                self.utilidades.registrar_log(
                  self.details.get_message("error", numero = self.numero, erro = self.details.get_message("file_not_found", arquivo = filer))
                )
                self.numero +=1
        else:
          if list_erros:
            for erro in self.lista_de_erros:
              print(str(erro))
              if self.details.enable_logging:
                self.utilidades.registrar_log(
                  self.details.get_message("error_sequence", numero = self.numero, error = erro)
                )
                self.numero += 1
            self.lista_de_erros.clear()
      else:
        try:
          raise os_me_error(self.details.get_message("error_list"))
        except os_me_error:
          if self.details.enable_rich_traceback:
            console = Console()
            console.print_exception()
          if self.details.enable_logging:
            self.utilidades.registrar_log(
              self.details.get_message("error", numero = self.numero, erro = self.details.get_message("error_list"))
            )
            self.numero += 1
    else:
      try:
        raise os_me_error(self.details.get_message("error_not_list", lista = paths))
      except os_me_error:
        if self.details.enable_rich_traceback:
          console = Console()
          console.print_exception()
        if self.details.enable_logging:
          self.utilidades.registrar_log(
            self.details.get_message("error", numero = self.numero, erro = self.details.get_message("error_not_list", lista = paths))
          )

class path_class:
    def __init__(self, details: Details = None):
        self.FilerBust = None
        self.FilerBust_inverse = None
        self.details = details or Details() 
        install()

    def FileHunter(self, relative_path: str) -> str | None:
        # ponto inicial
        path = self.FilerBust or os.getcwd()
        a = os.path.join(path, relative_path)

        if os.path.exists(a):
            print(f"{relative_path} exist: ✅")
            self.FilerBust = None
            return a
        else:
            pasta_pai = os.path.dirname(path)
            self.FilerBust = pasta_pai

            # condição de parada genérica: chegou na raiz
            if not pasta_pai == path:
                return self.FileHunter(relative_path)
            else:
                self.FilerBust = None
                try:
                  raise os_me_error(f"{relative_path} exist: ❌")
                except os_me_error as a:
                  if self.details.enable_rich_traceback:
                    console = Console()
                    console.print_exception()
                return None
            
    def FileHunter_inverse(self, relative_path: str, start: str = None) -> str | None:
      if not start:
        start = os.getcwd()
      for root, dirs, files in os.walk(start):
        # procura por diretórios que batem exatamente ou pelo sufixo
        for d in dirs:
          candidate = os.path.join(root, d)
          if d == relative_path or candidate.endswith(relative_path):
            print(f"{relative_path} exist: ✅")
            return candidate
        # procura por arquivos que batem exatamente ou pelo sufixo
        for f in files:
          candidate = os.path.join(root, f)
          if f == relative_path or candidate.endswith(relative_path):
            print(f"{relative_path} foi encontrada com sucesso em {root}")
            return candidate
      # não encontrado
      try:
        raise os_me_error(f"{relative_path} exist: ❌")
      except os_me_error:
        if self.details.enable_rich_traceback:
          console = Console()
          console.print_exception()
      return None

    def FileHunter_SUPER(self, relative_path: str) -> str | None:
      user_home = os.path.expanduser("~")  
      a = self.FileHunter(user_home)       
      b = self.FileHunter_inverse(relative_path, a)  
      return b
  
    class TIMELINE():
        def get_version(path):
          pathh = path_class()
          versões = []
          if os.path.exists(pathh.details.timeline_file) and os.path.getsize(pathh.details.timeline_file) > 0:
              try:
                  with open(pathh.details.timeline_file, "r", encoding="utf-8") as f:
                      data = json.load(f)
              except json.JSONDecodeError:
                  data = {}
              if path in data:
                  for snapshot in data[path]:
                      versões.append(snapshot["versao"])
          return versões
        def get_content(path):
          pathh = path_class()
          conteúdos = []
          if os.path.exists(pathh.details.timeline_file) and os.path.getsize(pathh.details.timeline_file) > 0:
              try:
                  with open(pathh.details.timeline_file, "r", encoding="utf-8") as f:
                      data = json.load(f)
              except json.JSONDecodeError:
                  data = {}
              if path in data:
                  for snapshot in data[path]:
                      conteúdos.append(snapshot["conteudo"])
          return conteúdos
        def get_TIMELINE(path):
          pathh = path_class()
          timeline = []
          if os.path.exists(pathh.details.timeline_file) and os.path.getsize(pathh.details.timeline_file) > 0:
              try:
                  with open(pathh.details.timeline_file, "r", encoding="utf-8") as f:
                      data = json.load(f)
              except json.JSONDecodeError:
                  data = {}
              if path in data:
                  for snapshot in data[path]:
                      timeline.append(snapshot)
              else:
                try:
                  raise os_me_error(f"no history for {path}")
                except:
                  if pathh.details.enable_rich_traceback:
                    console = Console()
                    console.print_exception()
          return timeline
        def show_TIMELINE(path):
          pathh = path_class()
          if os.path.exists(pathh.details.timeline_file) and os.path.getsize(pathh.details.timeline_file) > 0:
              try:
                  with open(pathh.details.timeline_file, "r", encoding="utf-8") as f:
                      data = json.load(f)
              except json.JSONDecodeError:
                  data = {}
              if path in data:
                  for snapshot in data[path]:
                      print(f"Versão: {snapshot['versao']}, Timestamp: {snapshot['timestamp']}\nConteúdo:\n{snapshot['conteudo']}\n{'-'*40}")
              else:
                try:
                  raise os_me_error(f"no history for {path}")
                except os_me_error:
                  if pathh.details.enable_rich_traceback:
                    console = Console()
                    console.print_exception()
          else:
            try:
              raise os_me_error("no history")
            except os_me_error:
                if pathh.details.enable_rich_traceback:
                  console = Console()
                  console.print_exception()
        def del_TIMELINE(path):
          pathh = path_class()
          if os.path.exists(pathh.details.timeline_file) and os.path.getsize(pathh.details.timeline_file) > 0:
              try:
                  with open(pathh.details.timeline_file, "r", encoding="utf-8") as f:
                      data = json.load(f)
              except json.JSONDecodeError:
                  data = {}
              if path in data:
                  del data[path]
                  with open(pathh.details.timeline_file, "w", encoding="utf-8") as f:
                      json.dump(data, f, indent=2)
                  print(f"history of {path} was deleted")
              else:
                try:
                  raise os_me_error(f"no history for {path}")
                except os_me_error:
                  if pathh.details.enable_rich_traceback:
                    console = Console()
                    console.print_exception()
          else:
            try:
              raise os_me_error("Nenhum histórico disponível.")
            except os_me_error:
                if pathh.details.enable_rich_traceback:
                  console = Console()
                  console.print_exception()
        def execution_versions(path):
          pathh = path_class()
          if os.path.exists(pathh.details.timeline_file) and os.path.getsize(pathh.details.timeline_file) > 0:
              try:
                  with open(pathh.details.timeline_file, "r", encoding="utf-8") as f:
                      data = json.load(f)
              except json.JSONDecodeError:
                  data = {}
              if path in data:
                  for snapshot in data[path]:
                      exec(snapshot["conteudo"], {})
              else:
                try:
                  raise os_me_error(f"no history for {path}")
                except os_me_error:
                  if pathh.details.enable_rich_traceback:
                    console = Console()
                    console.print_exception()
        def del_all():
          pathh = path_class()
          data = {}
          with open(pathh.details.timeline_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
          
      
class os_me:
   details = Details()
   file = file_class(details)
   path = path_class(details)