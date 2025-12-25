import tkinter as tk
import random as ram
import sys
import threading
import os

class tk_me:
    """
    criado com o intuido de deixar a criação de app tk bem mais fluida e menos cansativa,
    tk_me oferesse uma serie de funções que criam objetos tk de forma eficiente e até algumas coisas a mais

    defs:
        tk_import(nome_janela, tamanho_janela, arquivo_import)
        apenas_criar(nome_janela, tamanho_janela)
        label(texto, X1, Y1, fonte, tamanho)
        botão(texto, X1, Y1, fonte, tamanho, comando)
        botão(texto, X1, Y1, fonte, tamanho, comando)
        janela_de_Texto(tamanho_X, tamanho_y, local_X, local_y)
        janela_error()
        destruir_objetos(objeto)
        tk_import_tk(nome_janela1, arquivo_tk, texto_label, texto_botão)
        slider(num_min, num_max, comando, X, Y)

    """
    def tk_import(nome_janela, tamanho_janela, arquivo_import):
        """
    Cria uma janela tkinter que executa arquivos que normalmente só podem ser
    executados no terminal.

    Args:
        nome_janela (str): Nome da janela.
        tamanho_janela (str): Tamanho da janela no formato "LxA"
            (exemplo: "1000x700").
        arquivo_import (str): Caminho para o arquivo Python a ser executado.

    comportamento:
        - cria uma janela tk que simula um terminal
        - executa o arquivo informado
        - nessa janela é criado uma área de texto maior, uma menor, um botão e um label
        - na janela de texto maior, é simulado as chamadas de print
        - na janela de texto menor, é simulado as chamadas de input
        - o botão serve para começar/reiniciar o arquivo fornecido
        - o label da algumas informações e mostra os status

    Exemplo:
        >>> from py_me import tk_me
        >>> tk_me.tk_import("janela1", "1000x700", "meuscript.py")

    Observação:
        O código do arquivo importado é executado dentro da janela com suporte
        para redirecionamento de `print` e `input()`.

    returns:
        None
    """
        try:
            janela = tk.Tk()
            janela.title(nome_janela)
            janela.geometry(tamanho_janela)

            rotulo = tk.Label(janela, text=f"aproveite {nome_janela}")
            rotulo.pack(pady=20)

            saida = tk.Text(janela, height=30, width=100)
            saida.pack()

            class redirector:
                def __init__(self, widget):
                    self.widget = widget
                def write(self, text):
                    self.widget.insert(tk.END, text)
                def flush(self):
                    pass

            sys.stdout = redirector(saida)
            sys.stderr = redirector(saida)

            rotulo = tk.Label(janela, text="clique no botão abaixo para iniciar, coloque as informações nas barras de escrita abaixo do botão e disque Enter")
            rotulo.pack(pady=10)

            entrada = tk.Entry(janela)
            entrada.pack()

            entradas = []
            etapa_atual = [0]

            def criar_entradas(qtd):
                for i in range(qtd):
                    entrada_nova = tk.Entry(janela)
                    entrada_nova.pack()
                    entrada_nova.config(state='disabled')
                    entradas.append(entrada_nova)
                entradas[0].config(state='normal')

            def resetar_entradas():
                etapa_atual[0] = 0
                for entrada in entradas:
                    entrada.delete(0, tk.END)
                    entrada.config(state='disabled')
                entradas[0].config(state='normal')

            def fake_input(prompt=''):
                idx = etapa_atual[0]
                if idx >= len(entradas):
                    saida.insert(tk.END, "\n")
                    resetar_entradas()
                    return ""
                entrada = entradas[idx]
                saida.insert(tk.END, f"{prompt}\n")
                entrada.config(state="normal")
                entrada.focus()
                valor_var = tk.StringVar()
                def confirmar(event=None):
                    valor = entrada.get().strip()
                    if valor:
                        valor_var.set(valor)
                    else:
                        saida.insert(tk.END, f"vazio!\n")
                entrada.bind("<Return>", confirmar)
                janela.wait_variable(valor_var)
                etapa_atual[0] += 1
                if etapa_atual[0] < len(entradas):
                    entradas[etapa_atual[0]].config(state='normal')
                else:
                    saida.insert(tk.END, "\n")
                    resetar_entradas()
                return valor_var.get()

            def executar_o_codigo():
                rotulo.config(text="em uso... aperte o botão abaixo para resetar, caso queira.")
                try:
                    if getattr(sys, 'frozen', False):
                        pasta_base = sys._MEIPASS
                    else:
                        pasta_base = os.path.dirname(__file__)
                    caminho_arquivo = os.path.join(pasta_base, arquivo_import)
                    with open(caminho_arquivo, "r", encoding="utf-8") as arquivo:
                        conteudo = arquivo.read()
                        exec(conteudo, {**globals(), 'input': fake_input})
                except Exception as e:
                    rotulo.config(text=f"Erro: {e}")

            def clicar():
                etapa_atual[0] = 0
                for entrada in entradas:
                    entrada.delete(0, tk.END)
                    entrada.config(state='disabled')
                entradas[0].config(state='normal')
                thread = threading.Thread(target=executar_o_codigo)
                thread.start()

            botao = tk.Button(janela, text="iniciar/resetar", command=clicar)
            botao.pack(pady=10)
            criar_entradas(1)
            janela.mainloop()
        except Exception as p:
            print("error:", p)

    def apenas_criar(nome_janela, tamanho_janela):
        """
    Cria uma janela Tkinter de forma simplificada.

    Esta função é útil para reduzir a quantidade de código necessário
    ao criar uma janela Tkinter, especialmente em projetos mais longos.

    Args:
        nome_janela (str): O título da janela.
        tamanho_janela (str): O tamanho da janela no formato "largura x altura",
            por exemplo "800x600".

    comportamento:
        - cria uma janela tk com informações determinadas pelo programador que pode ser adicionado coisas dentro
    
    exemplo:
        >>> from py_me import tk_me
        >>> aaa = tk_me.apenas_criar("meu tk", "1000x100")
        >>> aaa.mainloop()

    Returns:
        tkinter.Tk: A instância da janela criada.
    """
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        try:
            janela = tk.Tk()
            janela.title(nome_janela)
            janela.geometry(tamanho_janela)
            return janela
        except Exception as y:
            print("error:", y)

    def label(texto, X1, Y1, fonte, tamanho):
        """
    Cria um widget Label no Tkinter de forma simplificada.

    Esta função reduz a quantidade de código necessária para criar
    e posicionar um Label totalmente funcional com as especificações
    fornecidas.

    Args:
        texto (str): O texto exibido no Label.
        x (int): Posição horizontal (coordenada X) onde o Label será exibido.
        y (int): Posição vertical (coordenada Y) onde o Label será exibido.
        fonte (str): Nome da fonte a ser usada no Label.
        tamanho (int): Tamanho da fonte do Label.

    comportamento:
        - cria um label editavel

    exemplo:
        >>> from py_me import tk_me
        >>> aaa = tk_me.apenas_criar("janela com label", "1000x100")
        >>> tk_me.label("olá mundo!", 0, 0, "Arial", 14)
        >>> aaa.mainloop()

    Returns:
        tkinter.Label: A instância do Label criado.
    """
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        try:
            label1 = tk.Label(text= texto, font= (fonte, tamanho))
            label1.place(x= X1, y= Y1)
            return label1
        except Exception as s:
            print("error:", s)

    def botão(texto, X1, Y1, fonte, tamanho, comando):
        """
    Cria um botão Tkinter com as especificações fornecidas.

    Esta função simplifica a criação de botões, permitindo configurar
    texto, fonte, tamanho e posição. Caso o texto seja vazio, o botão
    será criado apenas com a função associada ao comando.

    Args:
        texto (str): Texto exibido no botão. Se vazio, cria sem texto.
        x (int): Posição horizontal (coordenada X) do botão.
        y (int): Posição vertical (coordenada Y) do botão.
        fonte (str): Nome da fonte a ser usada no botão.
        tamanho (int): Tamanho da fonte.
        comando (Callable): Função a ser chamada quando o botão for clicado.

    comportamento:
        - cria um botão com as informações dadas pelo programador
    
    exemplo:
        >>> from py_me import tk_me
        >>> aaa = tk_me.apenas_criar("janela com botão", "1000x100")
        >>> def sair():
        >>>     aaa.destroy()
        >>> tk_me.botão("sair", 0, 0, "Arial", 14, sair)
        >>> aaa.mainloop()

    Returns:
        tkinter.Button: O botão criado.
    """
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        try:
            if not texto == "":
                botão = tk.Button(text= texto, command= comando, font=(fonte, tamanho))
                botão.place(x=X1, y=Y1)
                return botão
            else:
                botão = tk.Button(command= comando, font=(fonte, tamanho))
                botão.place(x=X1, y=Y1)
                return botão
        except Exception as b:
            print("error:", b)

    def janela_de_Texto(tamanho_X, tamanho_y, local_X, local_y): 
        """
    Cria uma caixa de texto (Text) no Tkinter com tamanho e posição definidos.

    Esta função simplifica a criação de caixas de texto, permitindo
    especificar dimensões e a posição na janela.

    Args:
        tamanho_x (int): Altura da caixa de texto (em linhas).
        tamanho_y (int): Largura da caixa de texto (em caracteres).
        local_x (int): Posição horizontal (coordenada X) da caixa de texto.
        local_y (int): Posição vertical (coordenada Y) da caixa de texto.

    comportamento:
        - cria uma janela de texto com as informações consedidas pelo programador

    exemplo:
        >>> from py_me import tk_me
        >>> aaa = tk_me.apenas_criar("tk com texto", "1000x100")
        >>> tk_me.janela_de_texto(100, 1, 0, 0)
        >>> aaa.mainloop

    Returns:
        tkinter.Text: O widget de caixa de texto criado.
    """
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        saida = tk.Text(height=tamanho_X, width=tamanho_y)
        saida.place(x=local_X, y=local_y)
        return saida

    def janela_error():
        """
    Cria uma janela de erro dinâmica no Tkinter que muda aleatoriamente
    a fonte e tamanho do texto "error" a cada 100ms.

    Esta função é útil para criar efeitos visuais aleatórios ou telas
    de demonstração, simulando um erro "instável".

    Args:
        None

    Comportamento:
        - A janela tem tamanho fixo 1600x700.
        - Um rótulo exibe a palavra "error" em fontes e tamanhos aleatórios.
        - Um botão "fechar" permite fechar a janela a qualquer momento.

    exemplo:
        >>> from py_me import tk_me
        >>> tk_me.janela_error()

    Returns:
        None
    """
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        janela = tk.Tk()
        janela.title("error")
        janela.geometry("1600x700")
        rotulo_status = tk.Label(text="", font=("Arial", 14))
        rotulo_status.pack()
        def error_ram():
            a = ram.randint(1,5)
            nu = ram.randint(1,500)
            fontes = {1: "Arial", 3: "Calibri", 4: "Times New Roman"}
            fonte = fontes.get(a, "Verdana")
            rotulo_status.config(text="error", font=(fonte, nu))
            janela.after(100, error_ram)
        error_ram()
        def fechar():
            janela.destroy()
        botao = tk.Button(text="fechar", font=("Arial", 14), command= fechar)
        botao.place(x=1000, y=100)
        janela.mainloop()

    def destruir_objetos(objeto):
        """
    Destroi um widget Tkinter, removendo-o da janela.

    Esta função é útil para apagar dinamicamente botões, labels, caixas
    de texto ou qualquer outro widget da interface.

    Args:
        objeto(tk widget): O widget que será destruído.

    comportamento:
        - destroi o widget indicado

    exemplo:
        >>> from py_me import tk_me
        >>> aaa = tk_me.apenas_criar("oioioio", "1000x100")
        >>> bbb = tk_me.label("não me mata", 0, 0, "Arial", 14)
        >>> tk_me.destruir_objetos(bbb)
        >>> aaa.mainloop()

    Returns:
        None
    """
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        objeto.destroy()

    def tk_import_tk(nome_janela1, arquivo_tk, texto_label, texto_botão):
        """
        Cria uma janela Tkinter com um label e um botão que executa um script externo.

        Esta função é útil para criar interfaces simples que carregam e executam
        arquivos Python dentro da própria janela, sem precisar do terminal.

        Args:
            nome_janela1 (str): O título da janela.
            arquivo_tk (str): Caminho para o arquivo Python a ser executado.
            texto_label (str): Texto a ser exibido no label dentro da janela.
            texto_botao (str): Texto exibido no botão que dispara a execução do arquivo.

        Comportamento:
            - Cria uma janela de tamanho fixo 500x500.
            - Exibe um label com `texto_label`.
            - Exibe um botão com `texto_botao`. Ao clicar:
                - Executa o script indicado em `arquivo_tk`.
                - Passa a própria janela como variável `janela` no escopo do script.
                - Fecha a janela antes de iniciar o arquivo executado ou se ocorrer erro.

        exemplo:
            >>> from py_me import tk_me
            >>> tk_me.tk_impot_tk("meu tk", "seu\\arquivo\\tk\\aqui.py", "diga, e diga direito", "eu digo")
        
        Returns:
            None
        """
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        janela = tk.Tk()
        janela.title(nome_janela1)
        janela.geometry("500x500")
        label = tk.Label(janela, text=texto_label, font=("Arial", 14))
        label.place(x=150, y=200)
        def rodar():
            janela.destroy()
            try:
                with open(arquivo_tk, "r", encoding="utf-8") as arquivo:
                    conteudo = arquivo.read()
                    exec(conteudo, {"janela": janela})
            except Exception as e:
                print(f"Erro ao executar o script: {e}")
        botao = tk.Button(janela, text=texto_botão, font=("Arial", 14), command=rodar)
        botao.place(x=150, y=250)
        janela.mainloop()
        # Cria o slider
    def slider(num_min, num_max, comando, X, Y):

        """
        cria um slider de forma rapida
        
        Args:
            num_min (int) (numero de onde o slider começa)
            num_max (int) (numero de limite do slider)
            comando (str) (o comando a ser executado)
            X (int) (posição x onde o slider vai ficar)
            Y (int) (posição y onde o slider vai ficar)
        comportamento:
            - cria um slider que vai de "num_min" até "num_max"
            - pisiciona esse slider nas cordenadas "X" "Y"
            - atribui o comando "comando" a o slider
        exemplo:
            >>> from py_me import tk_me
            >>> aaa = tk_me.apenas_criar("janela com slider", "1000x200")
            >>> selecionar = tk_me.slider(1, 1000, bolça_valores, 1000, 600)
            >>> aaa.mainloop
        returns:
            tkinter.Scale (o slider criado)
        """

        slider = tk.Scale(from_=num_min, to=num_max, orient="horizontal", command=comando, length=400)
        slider.place(x= X, y= Y)
        return slider