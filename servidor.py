"""
SiCA - Sistema de Compartilhamento de Arquivos (SERVIDOR)

Servidor TCP que guarda arquivos em uma pasta local e atende clientes
com tres operacoes: ENVIAR, LISTAR e BAIXAR.

Protocolo (texto simples, uma linha por comando, terminada em "\n"):
    ENVIAR <nome> <tamanho>  -> servidor responde "OK" e le <tamanho> bytes
    LISTAR                   -> servidor responde "OK <n>" e n linhas com os nomes
    BAIXAR <nome>            -> servidor responde "OK <tamanho>" e envia os bytes
    SAIR                     -> encerra a conexao
Em caso de falha o servidor responde "ERRO <mensagem>".
"""

import os
import socket
import threading

HOST = "0.0.0.0"   # aceita conexoes de qualquer interface de rede
PORTA = 5050
PASTA = "arquivos_servidor"


def caminho_seguro(nome):
    """Impede que o cliente use caminhos como '../senha.txt' para sair da pasta."""
    return os.path.join(PASTA, os.path.basename(nome))


def receber_arquivo(entrada, saida, nome, tamanho):
    """
    Recebe um arquivo do cliente.

    Le exatamente 'tamanho' bytes do socket e grava em disco em blocos de 4 KB,
    para nao carregar o arquivo inteiro na memoria.
    """
    caminho = caminho_seguro(nome)
    restante = tamanho

    with open(caminho, "wb") as arquivo:
        while restante > 0:
            bloco = entrada.read(min(4096, restante))
            if not bloco:                 # cliente caiu no meio do envio
                raise ConnectionError("conexao interrompida durante o envio")
            arquivo.write(bloco)
            restante -= len(bloco)

    saida.write(f"OK arquivo '{nome}' recebido ({tamanho} bytes)\n".encode())
    saida.flush()


def listar_arquivos(saida):
    """Envia a quantidade de arquivos disponiveis e, em seguida, um nome por linha."""
    arquivos = sorted(os.listdir(PASTA))
    saida.write(f"OK {len(arquivos)}\n".encode())
    for nome in arquivos:
        saida.write(f"{nome}\n".encode())
    saida.flush()


def enviar_arquivo(saida, nome):
    """
    Envia um arquivo para o cliente.

    Primeiro manda o cabecalho "OK <tamanho>" para o cliente saber quantos
    bytes deve ler, depois transmite o conteudo em blocos de 4 KB.
    """
    caminho = caminho_seguro(nome)

    if not os.path.isfile(caminho):
        saida.write(b"ERRO arquivo nao encontrado\n")
        saida.flush()
        return

    tamanho = os.path.getsize(caminho)
    saida.write(f"OK {tamanho}\n".encode())

    with open(caminho, "rb") as arquivo:
        while True:
            bloco = arquivo.read(4096)
            if not bloco:
                break
            saida.write(bloco)
    saida.flush()


def atender_cliente(conexao, endereco):
    """
    Trata uma conexao inteira: le comandos em laco ate o cliente sair.

    Executa em uma thread propria, por isso varios clientes podem ser
    atendidos ao mesmo tempo.
    """
    print(f"[+] Cliente conectado: {endereco}")

    # makefile transforma o socket em objetos de arquivo, o que facilita
    # ler linhas de comando e blocos binarios usando o mesmo buffer.
    entrada = conexao.makefile("rb")
    saida = conexao.makefile("wb")

    try:
        while True:
            linha = entrada.readline().decode().strip()
            if not linha:
                break

            partes = linha.split()
            comando = partes[0].upper()
            print(f"    {endereco} -> {linha}")

            if comando == "ENVIAR":
                receber_arquivo(entrada, saida, partes[1], int(partes[2]))
            elif comando == "LISTAR":
                listar_arquivos(saida)
            elif comando == "BAIXAR":
                enviar_arquivo(saida, partes[1])
            elif comando == "SAIR":
                break
            else:
                saida.write(b"ERRO comando desconhecido\n")
                saida.flush()

    except (ConnectionError, IndexError, ValueError) as erro:
        print(f"[!] Erro com {endereco}: {erro}")
    finally:
        conexao.close()
        print(f"[-] Cliente desconectado: {endereco}")


def main():
    os.makedirs(PASTA, exist_ok=True)

    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # permite reiniciar o servidor na mesma porta sem esperar o timeout do SO
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor.bind((HOST, PORTA))
    servidor.listen(5)

    print(f"Servidor SiCA ouvindo em {HOST}:{PORTA} (pasta: {PASTA}/)")

    try:
        while True:
            conexao, endereco = servidor.accept()
            # daemon=True para as threads morrerem junto com o programa principal
            threading.Thread(
                target=atender_cliente, args=(conexao, endereco), daemon=True
            ).start()
    except KeyboardInterrupt:
        print("\nServidor encerrado.")
    finally:
        servidor.close()


if __name__ == "__main__":
    main()
