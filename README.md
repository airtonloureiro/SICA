# SiCA — Sistema de Compartilhamento de Arquivos

Aplicação cliente/servidor em Python usando **sockets TCP**, feita para o Fórum
Avaliativo da disciplina de Desenvolvimento de Software C-S (PUC Goiás).

O cliente conecta ao servidor e pode:

1. **Enviar** um arquivo para o servidor
2. **Listar** os arquivos disponíveis no servidor
3. **Baixar** um dos arquivos disponíveis

## Arquivos

| Arquivo | Descrição |
|---|---|
| `servidor.py` | Servidor TCP multithread; guarda os arquivos em `arquivos_servidor/` |
| `cliente.py` | Cliente com menu de texto; salva os downloads em `downloads/` |

## Como executar

Em um terminal, inicie o servidor:

```bash
python3 servidor.py
```

Em outro terminal, execute o cliente:

```bash
python3 cliente.py
```

Para usar entre máquinas diferentes, altere a constante `HOST` em `cliente.py`
para o IP do servidor. A porta padrão é **5050** (definida em `PORTA` nos dois
arquivos).

## Como funciona

A comunicação usa um protocolo de texto simples: cada comando é uma linha
terminada em `\n`, e o conteúdo binário dos arquivos vem logo depois do
cabeçalho.

| Comando do cliente | Resposta do servidor |
|---|---|
| `ENVIAR <nome> <tamanho>` + bytes do arquivo | `OK arquivo '<nome>' recebido (<n> bytes)` |
| `LISTAR` | `OK <n>` seguido de `n` linhas, uma por nome |
| `BAIXAR <nome>` | `OK <tamanho>` + bytes do arquivo, ou `ERRO arquivo nao encontrado` |
| `SAIR` | encerra a conexão |

Pontos principais da implementação:

- **Tamanho no cabeçalho.** Como o TCP é um fluxo contínuo de bytes (sem
  fronteiras de mensagem), quem envia sempre informa antes quantos bytes serão
  transmitidos. O receptor lê exatamente essa quantidade, o que evita ler a mais
  ou de menos.
- **Transferência em blocos de 4 KB.** Arquivos são lidos e gravados aos poucos,
  então o consumo de memória não depende do tamanho do arquivo.
- **Uma thread por cliente.** O servidor aceita conexões em laço e delega cada
  uma a uma thread, atendendo vários clientes ao mesmo tempo.
- **`socket.makefile()`.** Transforma o socket em objetos de arquivo, permitindo
  ler linhas de comando (`readline`) e blocos binários (`read`) com o mesmo
  buffer, sem misturar dados.
- **Nomes sanitizados.** O servidor aplica `os.path.basename()` nos nomes
  recebidos, impedindo que um cliente use caminhos como `../../senha.txt` para
  escapar da pasta compartilhada.

## Exemplo de uso

```
===== SiCA =====
1 - Enviar arquivo
2 - Listar arquivos
3 - Baixar arquivo
0 - Sair
Opcao: 1
Caminho do arquivo: /tmp/relatorio.pdf
OK arquivo 'relatorio.pdf' recebido (2600 bytes)

Opcao: 2

1 arquivo(s) no servidor:
 - relatorio.pdf

Opcao: 3
Nome do arquivo: relatorio.pdf
Arquivo salvo em downloads/relatorio.pdf (2600 bytes)
```
