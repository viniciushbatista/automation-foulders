import os
import tarfile
import re

# Caminhos principais
pasta_mae = r'/home/vinicius/Documentos/workspace/simulations'
pasta_destino_geral = r'/home/vinicius/Documentos/workspace/pasta-destino'

# Configuração de limite (opcional)
limite_por_tar = None
limite_total = 10
arquivos_processados = 0


def buscar_todos_tar(pasta_raiz):
    lista_tar = []
    for raiz, dirs, arquivos in os.walk(pasta_raiz):
        for arquivo in arquivos:
            if arquivo.endswith('.gz'):
                lista_tar.append(os.path.join(raiz, arquivo))
    return lista_tar


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
        print(f" Arquivo '{arquivo_nome}' não encontrado no .gz")
    except Exception as e:
        print(f" Erro ao ler '{arquivo_nome}': {e}")
    return None


def extrair_numero_da_outra_pasta(nome_pasta):
    partes = nome_pasta.split('_')
    if len(partes) >= 4:
        return partes[2] + "_" + partes[3]
    return nome_pasta


#def obter_nome_primeira_subpasta(caminho_tar):
#    caminho_relativo = os.path.relpath(caminho_tar, pasta_mae)
#    partes = caminho_relativo.split(os.sep)
#    return partes[0] if partes else "subpasta_desconhecida"

def obter_nome_primeira_subpasta(caminho_tar):
    caminho_relativo = os.path.relpath(caminho_tar, pasta_mae)
    partes = caminho_relativo.split(os.sep)
    
    if partes:
        primeiro_elemento = partes[0]
        # Divide o primeiro elemento pelo hífen e pega a primeira parte
        nome_curto = primeiro_elemento.split('-')[0]
        return nome_curto
    else:
        return "subpasta_desconhecida"

def processar_tar(caminho_tar, nomes_desejados, pasta_destino_geral, limite=None):
    global arquivos_processados

    with tarfile.open(caminho_tar) as gz:
        membros = gz.getmembers()
        encontrados = 0

        #Nome da primeira subpasta da pasta mãe
        nome_subpasta_principal = obter_nome_primeira_subpasta(caminho_tar)

        #Extrair machXXe
        mach_prefixo_match = re.match(r'(mach\d{2}e)-', nome_subpasta_principal, re.IGNORECASE)
        mach_prefixo = mach_prefixo_match.group(1) if mach_prefixo_match else "machN/A"

        #Extrair o sufixo tipo 12_32
        num_outra_pasta = extrair_numero_da_outra_pasta(nome_subpasta_principal)

        #Extrair valores de temperatura e velocidade
        temperatura = extrair_valor_por_chave(gz, 'initialConditions', 'temperatureBB')
        velocidade = extrair_valor_por_chave(gz, 'initialConditions', 'flowVelocityBB')

        velocidade_match = re.search(r'\(?([0-9]*\.?[0-9]+)', velocidade) if velocidade else None
        valor_velocidade = velocidade_match.group(1) if velocidade_match else "velN/A"

        #Nome da pasta destino
        nome_pasta_destino = f"{mach_prefixo}-T{temperatura}-{valor_velocidade}-{num_outra_pasta}"

        pasta_destino = os.path.join(pasta_destino_geral, nome_pasta_destino)
        if not os.path.exists(pasta_destino):
            os.makedirs(pasta_destino)

        # 🔗 Extrair os arquivos desejados
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
