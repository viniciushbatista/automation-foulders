import os
import tarfile
import re

#caminhos principais
pasta_mae = r'/home/vinicius/Documentos/workspace/simulations' #caminho da pasta principal
pasta_destino_geral = r'/home/vinicius/Documentos/workspace/pasta-destino' #caminho da pasta onde irão os arquivos

#Configuração de limite
limite_por_tar = None
limite_total = 50
arquivos_processados = 0

#busca todos os arquivos .tar (windows) ou .tar.gz (linux/ubuntu)
def buscar_todos_tar(pasta_raiz):
    lista_tar = []
    for raiz, dirs, arquivos in os.walk(pasta_raiz):
        for arquivo in arquivos:
            if arquivo.endswith('.gz'):
                lista_tar.append(os.path.join(raiz, arquivo))
    return lista_tar

#ler os dados que eu quero do arquivo
def extrair_valor_por_chave(gz, arquivo_nome, chave):
    try:
        membro = next(m for m in gz.getmembers() if arquivo_nome in m.name)
        arquivo = gz.extractfile(membro)
        if arquivo:
            linhas = arquivo.read().decode('utf-8').splitlines()
            for linha in linhas:
                if chave in linha:
                    valor = linha.split(chave)[1].strip()
                    valor = re.sub(' +', ' ', valor)
                    return valor
    except StopIteration:
        print(f"Arquivo '{arquivo_nome}' não encontrado no .gz")
    except Exception as e:
        print(f"Erro ao ler '{arquivo_nome}': {e}")
    return None


def extrair_numero_do_nome_tar(caminho_arquivo_tar):
    """
    Extrai o padrão xxx_xx do nome do arquivo .tar
    Exemplo: teste_axi_008_04.tar → retorna 008_04
    """
    nome_arquivo = os.path.basename(caminho_arquivo_tar)  #nome do arquivo .tar.gz teste_axi_xxx_xx

    match = re.search(r'teste_axi_(\d{3}_\d{2})\.tar\.gz$', nome_arquivo)
    if match:
        return match.group(1)
    else:
        return "numN/A"

#nome da pasta machxe
def obter_nome_primeira_subpasta(caminho_tar):
    caminho_relativo = os.path.relpath(caminho_tar, pasta_mae)
    partes = caminho_relativo.split(os.sep)
    return partes[0] if partes else "subpasta_desconhecida"


def processar_tar(caminho_tar, nomes_desejados, pasta_destino_geral, limite=None):
    global arquivos_processados

    with tarfile.open(caminho_tar) as gz:
        membros = gz.getmembers()
        encontrados = 0

        #Nome da subpasta principal (ex: mach08e-blabla)
        nome_subpasta_principal = obter_nome_primeira_subpasta(caminho_tar)

        #Extrair machXXe do nome da subpasta
        mach_prefixo_match = re.match(r'(mach\d{2}e)-', nome_subpasta_principal, re.IGNORECASE)
        mach_prefixo = mach_prefixo_match.group(1) if mach_prefixo_match else "machN/A"

        #Extrair o numero do nome do .gz (ex: 008_04)
        nome_tar = os.path.basename(caminho_tar)
        num_outra_pasta = extrair_numero_do_nome_tar(nome_tar)

        #Extrair temperatura e velocidade
        temperatura = extrair_valor_por_chave(gz, 'initialConditions', 'temperatureBB')
        velocidade = extrair_valor_por_chave(gz, 'initialConditions', 'flowVelocityBB')

        #Pegando a string completa da velocidade, removendo parênteses e trocando espaços por underline
        if velocidade:
            valor_velocidade = (
                velocidade.strip()
                .replace('(', '')
                .replace(')', '')
                .replace(' ', '_')
                .replace(';', '')
            )
        else:
            valor_velocidade = "velN/A"

        if temperatura:
            valor_temperatura = (
                temperatura.strip()
                .replace(';', '')
            )
        else:
            valor_temperatura = "TempN/A"

        #Nome da pasta destino
        nome_pasta_destino = f"{mach_prefixo}-T{valor_temperatura}-V{valor_velocidade}-{num_outra_pasta}"

        pasta_destino = os.path.join(pasta_destino_geral, nome_pasta_destino)
        if not os.path.exists(pasta_destino):
            os.makedirs(pasta_destino)

        #Extrair os arquivos desejados
        for membro in membros:
            if membro.isfile() and any(nome.lower() in membro.name.lower() for nome in nomes_desejados):
                print(f"Encontrado no .gz: {membro.name}")

                arquivo = gz.extractfile(membro)
                if arquivo:
                    caminho_destino = os.path.join(pasta_destino, os.path.basename(membro.name))
                    with open(caminho_destino, 'wb') as f_out:
                        f_out.write(arquivo.read())
                    print(f"Copiado para: {caminho_destino}")

                encontrados += 1
                arquivos_processados += 1

                if limite is not None and encontrados >= limite:
                    print(f"Limite de {limite} arquivos atingido para este .gz")
                    break

                if limite_total is not None and arquivos_processados >= limite_total:
                    print(f"Limite total de {limite_total} arquivos atingido. Encerrando processo.")
                    exit()


#Execução principal
print("\n Buscando arquivos .gz...")

lista_de_tars = buscar_todos_tar(pasta_mae)

if not lista_de_tars:
    print("Nenhum arquivo .gz encontrado.")
else:
    print(f"{len(lista_de_tars)} arquivos .gz encontrados.")

    for caminho_tar in lista_de_tars:
        print(f"\n Processando {caminho_tar}")

        nomes_arquivos_desejados = ['coefficient.dat']  #Arquivos desejados

        processar_tar(
            caminho_tar,
            nomes_arquivos_desejados,
            pasta_destino_geral,
            limite=limite_por_tar
        )

print("\n Processo concluído com sucesso!")
