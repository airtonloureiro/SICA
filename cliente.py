"""
SiCA - Sistema de Compartilhamento de Arquivos (CLIENTE)

Cliente TCP com um menu de texto que permite enviar um arquivo ao servidor,
listar os arquivos disponiveis e baixar um deles.

O protocolo usado esta descrito no cabecalho de servidor.py.
"""

import os
import socket

HOST = "127.0.0.1"     # endereco do servidor (troque pelo IP da outra maquina)
PORTA = 5050
PASTA = "downloads"    # onde os arquivos baixados sao gravados


def enviar(entrada, saida, caminho):
    """
    Envia um arquivo local ao servidor.

    Manda o cabecalho "ENVIAR <nome> <tamanho>" e, logo apos, o conteudo
    do arquivo em blocos de 4 KB.
    """
    if not os.path.isfile(caminho):
        print("Arquivo nao encontrado.")
        return

    nome = os.path.basename(caminho)
    tamanho = os.path.getsize(caminho)
    saida.write(f"ENVIAR {nome} {tamanho}\n".encode())

    with open(caminho, "rb") as arquivo:
        while True:
            bloco = arquivo.read(4096)
            if not bloco:
                break
            saida.write(bloco)
    saida.flush()

    print(entrada.readline().decode().strip())


def listar(entrada, saida):
    """Pede a lista de arquivos e mostra na tela os nomes recebidos."""
    saida.write(b"LISTAR\n")
    saida.flush()

    resposta = entrada.readline().decode().split()
    quantidade = int(resposta[1])

    if quantidade == 0:
        print("Nenhum arquivo no servidor.")
        return

    print(f"\n{quantidade} arquivo(s) no servidor:")
    for _ in range(quantidade):
        print(" -", entrada.readline().decode().strip())


def baixar(entrada, saida, nome):
    """
    Baixa um arquivo do servidor.

    Le o cabecalho de resposta para descobrir o tamanho e entao consome
    exatamente essa quantidade de bytes, gravando na pasta de downloads.
    """
    saida.write(f"BAIXAR {nome}\n".encode())
    saida.flush()

    resposta = entrada.readline().decode().strip()
    if resposta.startswith("ERRO"):
        print(resposta)
        return

    tamanho = int(resposta.split()[1])
    restante = tamanho
    caminho = os.path.join(PASTA, os.path.basename(nome))

    with open(caminho, "wb") as arquivo:
        while restante > 0:
            bloco = entrada.read(min(4096, restante))
            if not bloco:
                print("Conexao interrompida durante o download.")
                return
            arquivo.write(bloco)
            restante -= len(bloco)

    print(f"Arquivo salvo em {caminho} ({tamanho} bytes)")


def menu():
    print("\n===== SiCA =====")
    print("1 - Enviar arquivo")
    print("2 - Listar arquivos")
    print("3 - Baixar arquivo")
    print("0 - Sair")


def main():
    os.makedirs(PASTA, exist_ok=True)

    cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    cliente.connect((HOST, PORTA))
    print(f"Conectado ao servidor {HOST}:{PORTA}")

    entrada = cliente.makefile("rb")
    saida = cliente.makefile("wb")

    try:
        while True:
            menu()
            opcao = input("Opcao: ").strip()

            if opcao == "1":
                enviar(entrada, saida, input("Caminho do arquivo: ").strip())
            elif opcao == "2":
                listar(entrada, saida)
            elif opcao == "3":
                baixar(entrada, saida, input("Nome do arquivo: ").strip())
            elif opcao == "0":
                saida.write(b"SAIR\n")
                saida.flush()
                break
            else:
                print("Opcao invalida.")
    finally:
        cliente.close()
        print("Conexao encerrada.")


if __name__ == "__main__":
    main()
