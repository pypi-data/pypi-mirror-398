import threading
import os
import pygame
import time
import tempfile
from pydub import AudioSegment

class alxiliar:
    def __init__(self):
        self.sound = None
        self.thread = None

class music_me:
    """
    criada para executar e manipular aldio para qualquer proposito (apesar do nome)

    defs:
        trilha_sonora_inloop(velocidade, arquivo)
        elemento_musical(velocidade, arquivo, tempo_a_esperar=0)
        elemento_musical_entonado(velocidade, entonacao, arquivo, tempo_a_esperar=0)
        dell(elemento, tempo_após_o_inicio_da_reprodução_para_o_del)

    """
    pygame.mixer.init()
    def trilha_sonora_inloop(velocidade, arquivo):
        """
        Toca uma música em loop infinito com alteração de velocidade.
        
        Args:
            velocidade(int) (a velocidade ao qual o arquivo será tocado)
            arquivo(str) (exatamente o arquivo que será tocado)

        comportamento:
            - toca um arquivo em loop
            - pode ou não modificar sua velocidade
        exemplo:
            >>> from py_me import music_me
            >>> music_me.trilha_sonora_inloop(2, "minha batida.mp3")
        returns:
            pygame.mixer.Sound(temp_path) (som a ser reproduzido, possibilitando modificações leves)
        """
        som = alxiliar()
        def player():
            audio = AudioSegment.from_file(arquivo)
            audio = audio._spawn(audio.raw_data, overrides={
                "frame_rate": int(audio.frame_rate * velocidade)
            }).set_frame_rate(audio.frame_rate)

            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
            temp_path = temp_file.name
            temp_file.close()
            audio.export(temp_path, format="wav")

            som.sound = pygame.mixer.Sound(temp_path)
            som.sound.play(loops=-1)
            

            print(f"Tocando {arquivo} em loop (velocidade {velocidade}x)")
                

            while True:
                time.sleep(0.1)


        aaa = threading.Thread(target=player, daemon=True)
        som.thread = aaa
        aaa.start()
        return som

    def elemento_musical(velocidade, arquivo, tempo_a_esperar=0):
        """
        Toca um elemento musical após um tempo definido.
        
        Args:
            velocidade(int) (a velocidade de reprodução do arquivo)
            arquivo(str) (o arquivo a ser tocado)
            tempo_a_espera(int) (o segundo exato, considerando deis de o inicio da execução, que o arquivo irá tocar)

        comportamento:
            - toca um arquivo
            - pode ou não mudar sua velocidade
            - espera determinado tempo para tocar o som
        
        exemplo:
            >>> from py_me import music_me
            >>> music_me.elemento_musical(1, "meu_som.mp3", 21) #executa depois de vinte e um segundos após iniciar o codigo

        returns:
            pygame.mixer.Sound(temp_path) (som a ser reproduzido, possibilitando modificações leves)
        """
        som = alxiliar()
        def player():
                if tempo_a_esperar > 0:
                    time.sleep(tempo_a_esperar)

                audio = AudioSegment.from_file(arquivo)
                audio = audio._spawn(audio.raw_data, overrides={
                    "frame_rate": int(audio.frame_rate * velocidade)
                }).set_frame_rate(audio.frame_rate)

                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
                temp_path = temp_file.name
                temp_file.close()
                audio.export(temp_path, format="wav")

                som.sound = pygame.mixer.Sound(temp_path)
                som.sound.play()


                print(f"Tocando {arquivo} (velocidade {velocidade}x) após {tempo_a_esperar}s")

                time.sleep(audio.duration_seconds)
                os.remove(temp_path)

        aaa = threading.Thread(target=player, daemon=True)
        som.thread = aaa
        aaa.start()
        return som

    def elemento_musical_entonado(velocidade, entonacao, arquivo, tempo_a_esperar=0):
        """
        Toca um elemento musical com velocidade e entonação ajustáveis.
        
        Args:
            velocidade(int) (a velocidade que o arquivo será reproduzido)
            entonação(int) (a entonação que o arquivo irá tocar)
            arquivo(str) (o arquivo a ser reproduzido)
            tempo_a_esperar(int) (o segundo exato, considerando deis de o inicio da execução, que o arquivo irá tocar)
        
        comportamento:
            - toca um arquivo de som
            - pode ou não alterar sua velocidade
            - pode ou não alterar sua entonação
            - toca ele somente depois de determinado tempo
        
        exemplo:
            >>> from py_me import music_me
            >>> music_me.elemento_musical_entonado(1, 3, "meu_som.wav", 12) #executa depois de doze segundos após iniciar o codigo
        
        returns:
            pygame.mixer.Sound(temp_path) (som a ser reproduzido, possibilitando modificações leves)
        """
        som = alxiliar()
        def player():
                if tempo_a_esperar > 0:
                    time.sleep(tempo_a_esperar)

                audio = AudioSegment.from_file(arquivo)
                audio = audio._spawn(audio.raw_data, overrides={
                    "frame_rate": int(audio.frame_rate * velocidade * entonacao)
                }).set_frame_rate(audio.frame_rate)

                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
                temp_path = temp_file.name
                temp_file.close()
                audio.export(temp_path, format="wav")

                som.sound = pygame.mixer.Sound(temp_path)
                som.sound.play()



                print(f"Tocando {arquivo} (velocidade {velocidade}x, entonação {entonacao}x)")

                time.sleep(audio.duration_seconds)
                os.remove(temp_path)
        aaa = threading.Thread(target=player, daemon=True)
        som.thread = aaa
        aaa.start()
        return som
    def dell(som, tempo_após_o_inicio_da_reprodução_para_o_del):
        """
        Interrompe a reprodução do elemento após 'tempo' segundos.

        Args:
        elemento(str) (o elemento a ser remoivido)
        tempo_após_o_inicio_da_reprodução_para_o_del(int) (o segundo exato onde o elemento deve parar de ser tocado, considerando o inicio da reprodução do elemento)
        
        comportamento:
            - interrompe um elemento musical depois do tempo indicado
        
        exemplo:
            >>> from py_me import music_me
            >>> aaa = music_me.elemento_musical(1, "som.wav", 12)
            >>> music_me.dell(aaa, 23) #vinte e três segundos
        obs:
            certifique-se que a variavel a ser deletada sejá um elemento musical
        
        returns:
            None
        """
        def parar():
            try:
                if hasattr(som, "sound") and som.sound:
                    som.sound.stop()
                    print("Reprodução interrompida automaticamente.")
            except Exception as e:
                print(f"Erro ao tentar parar o elemento: {e}")

        threading.Timer(tempo_após_o_inicio_da_reprodução_para_o_del, parar).start()
    def stop(tempo):
        """
        para tudo que está em reprodução de uma vez

        Args:
            tempo(float) (o tempo após o inicio do programa)
        
        comportamento:
            - interrompe todos os sons executados depois do tempo determinado

        exemplo:
            >>> from py_me import music_me
            >>> music_me.trilha_sonora_inloop(2, "minha\\batida.mp3")
            >>> music_me.elemento_musical(1, "meu\\elemento.wav", 2)
            >>> music_me.stop(20)
        returns:
            None
        """
        def para():
            try:
                if pygame.mixer.get_init() and pygame.mixer.get_busy():
                    pygame.mixer.stop()
                    print("Tudo interrompido")
                else:
                    print("Não há sons tocando")
            except Exception as e:
                print("Erro inesperado aconteceu:")
                print(e)
    
        threading.Timer(tempo, para).start()
    def volume_geral(volume,  tempo):
        """
        Ajusta o volume geral de todos os sons.

        Args:
            volume(float) (o volume desejado, entre 0.0 e 1.0)
            tempo(float) (o tempo após o inicio do programa)
        
        comportamento:
            - ajusta o volume geral de todos os sons depois do tempo determinado

        exemplo:
            >>> from py_me import music_me
            >>> music_me.trilha_sonora_inloop(2, "minha\\batida.mp3")
            >>> music_me.elemento_musical(1, "meu\\elemento.wav", 2)
            >>> music_me.volume_geral(0.5, 20) #ajusta o volume para 50% depois de vinte segundos
        
          returns:
            None
        """
        def ajusta_volume():
            try:
                if 0.0 <= volume <= 1.0:
                    for i in range(pygame.mixer.get_num_channels()):
                        ch = pygame.mixer.Channel(i)
                        if ch.get_busy():
                            snd = ch.get_sound()
                            if snd:
                                snd.set_volume(volume)
                    print(f"Volume geral ajustado para {volume * 100}%")
                else:
                    print("Volume deve estar entre 0.0 e 1.0")
            except Exception as e:
                print("Erro inesperado aconteceu:")
                print(e)
    
        threading.Timer(tempo, ajusta_volume).start()
    def volume_elemento(som, volume, tempo):
        """
        Ajusta o volume de um elemento especifico.

        Args:
            elemento(pygame.mixer.Sound) (o elemento a ter o volume ajustado)
            volume(float) (o volume desejado, entre 0.0 e 1.0)
            tempo(float) (o tempo após o inicio do programa)

        comportamento:
            - ajusta o volume de um elemento especifico depois do tempo determinado

        exemplo:
            >>> from py_me import music_me
            >>> aaa = music_me.elemento_musical(1, "meu\\elemento.wav", 2)
            >>> music_me.volume_elemento(aaa, 0.3, 20) #ajusta o volume do elemento aaa para 30% depois de vinte segundos
        returns:
            None
        """
        def ajusta_volume():
            try:
                if hasattr(som, "sound") and som.sound:
                    if 0.0 <= volume <= 1.0:
                        for i in range(pygame.mixer.get_num_channels()):
                            channel = pygame.mixer.Channel(i)
                            if channel.get_sound() == som.sound:
                                channel.set_volume(volume)
                        print(f"Volume do elemento ajustado para {volume * 100}%")
                    else:
                        print("Volume deve estar entre 0.0 e 1.0")
                else:
                    print("Elemento inválido ou não está tocando")
            except Exception as e:
                print("Erro inesperado aconteceu:")
                print(e)
        threading.Timer(tempo, ajusta_volume).start()