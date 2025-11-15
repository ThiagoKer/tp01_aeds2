from faker import Faker
from dataclasses import dataclass
import random

# 1. Geração de dados
ENCODING = "latin-1"
fake = Faker("pt_BR")

cpfs_gerados = set()
matriculas_geradas = set()

cursos = [
    "Engenharia da Computação",
    "Engenharia Elétrica", 
    "Engenharia de Produção",
    "Sistemas de Informação",
]

@dataclass
class Pessoa:
    matricula: int
    nome: str
    cpf: str
    curso: str
    filiacao_mae: str
    filiacao_pai: str
    ano_ingresso: int
    coeficiente_academico: float

def gerar_pessoa():
    while True:
        matricula = random.randint(100000000, 999999999)
        if matricula not in matriculas_geradas:
            matriculas_geradas.add(matricula)
            break

    while True:
        cpf = fake.cpf().replace('.', '').replace('-', '')
        if cpf not in cpfs_gerados:
            cpfs_gerados.add(cpf)
            break

    nome = fake.name().encode(ENCODING, errors="ignore").decode(ENCODING)[:50]
    curso = random.choice(cursos)[:30]
    filiacao_mae = fake.name_female().encode(ENCODING, errors="ignore").decode(ENCODING)[:30]
    filiacao_pai = fake.name_male().encode(ENCODING, errors="ignore").decode(ENCODING)[:30]
    
    ano_ingresso = random.randint(2000, 2025)
    coeficiente_academico = round(random.uniform(0.0, 10.0), 2)

    return Pessoa(
        matricula,
        nome,
        cpf,
        curso,
        filiacao_mae,
        filiacao_pai,
        ano_ingresso,
        coeficiente_academico
    )

# 2. Entrada de dados do usuário

#Geração aleatória de pessoas
num_registros = int(input("Quantos registros deseja gerar? "))
pessoas = [gerar_pessoa() for _ in range(num_registros)]
print(f"\n{num_registros} registros gerados.")

modo_armazenamento = int(input(
    "\nEscolha o modo de armazenamento:\n"
    "(1) Registros de tamanho fixo\n"
    "(2) Registros de tamanho variável\n"
))

blocos = []
tam_max_bloco = int(input("Informe o tamanho máximo do bloco (em bytes): "))
NOME_ARQUIVO_SAIDA = "alunos.dat"

# Marcadores usando bytes especiais
MARCADOR_FIM_REGISTRO = b"\xFE"    # Byte 254
MARCADOR_CONTINUACAO = b"\xFF"     # Byte 255


# 3. Simulação de escrita

# Cabeçalho do arquivo
cabecalho = f"TAM_BLOCO:{tam_max_bloco},MODO:{modo_armazenamento}\n".encode(ENCODING)

if modo_armazenamento == 1:
    # Modo Fixo
    TAMANHO_REGISTRO_FIXO = 169
    
    if tam_max_bloco < TAMANHO_REGISTRO_FIXO:
        print(f"Erro: tamanho do bloco insuficiente para 1 registro.")
        exit()

    registros_bytes = []
    for p in pessoas:
        campos = [
            f"{str(p.matricula):<9}"[:9],
            f"{p.nome:<50}"[:50],  
            f"{p.cpf:<11}"[:11],
            f"{p.curso:<30}"[:30],
            f"{p.filiacao_mae:<30}"[:30],
            f"{p.filiacao_pai:<30}"[:30],
            f"{str(p.ano_ingresso):<4}"[:4],
            f"{p.coeficiente_academico:<5.2f}"[:5]
        ]
        registro_str = "".join(campos).ljust(TAMANHO_REGISTRO_FIXO, '#')
        registros_bytes.append(registro_str.encode(ENCODING))

    bloco_atual = b""
    for registro in registros_bytes:
        if len(bloco_atual) + TAMANHO_REGISTRO_FIXO <= tam_max_bloco:
            bloco_atual += registro
        else:
            blocos.append(bloco_atual)
            bloco_atual = registro
            
    if bloco_atual:
        blocos.append(bloco_atual)

elif modo_armazenamento == 2:
    # Modo Variável
    tipo_registro = int(input(
        "Escolha o tipo de registro:\n"
        "(1) Registros Contíguos\n"
        "(2) Registros Espalhados\n"
    ))

    registros_bytes = []
    for p in pessoas:
        registro_str = f"{p.matricula},{p.nome},{p.cpf},{p.curso},{p.filiacao_mae},{p.filiacao_pai},{p.ano_ingresso},{p.coeficiente_academico}"
        registro_byte = registro_str.encode(ENCODING) + MARCADOR_FIM_REGISTRO
        registros_bytes.append(registro_byte)

    bloco_atual = b""

    if tipo_registro == 1:
        # Contíguos
        for registro in registros_bytes:
            if len(registro) > tam_max_bloco:
                print(f"Erro: Registro não cabe em bloco único.")
                exit()
                
            if len(bloco_atual) + len(registro) <= tam_max_bloco:
                bloco_atual += registro
            else:
                blocos.append(bloco_atual)
                bloco_atual = registro
                
        if bloco_atual:
            blocos.append(bloco_atual)

    else:
        # Espalhados
        for registro in registros_bytes:
            registro_restante = registro
            
            while registro_restante:
                espaco_livre = tam_max_bloco - len(bloco_atual)
                
                if len(registro_restante) <= espaco_livre:
                    bloco_atual += registro_restante
                    registro_restante = b""
                else:
                    if espaco_livre > len(MARCADOR_CONTINUACAO):
                        bytes_para_este_bloco = espaco_livre - len(MARCADOR_CONTINUACAO)
                        bloco_atual += registro_restante[:bytes_para_este_bloco] + MARCADOR_CONTINUACAO
                        registro_restante = registro_restante[bytes_para_este_bloco:]
                    blocos.append(bloco_atual)
                    bloco_atual = b""
            
        if bloco_atual:
            blocos.append(bloco_atual)

else:
    print("Opção inválida.")
    exit()

# Gravação do arquivo
with open(NOME_ARQUIVO_SAIDA, "wb") as arquivo:
    arquivo.write(cabecalho)
    for bloco in blocos:
        arquivo.write(bloco)

print(f"\n{len(blocos)} blocos gravados no arquivo '{NOME_ARQUIVO_SAIDA}'.")


# 4. Cálculo e exibição de estatísticas

print("\n=== RELATÓRIO DE ARMAZENAMENTO ===")

total_blocos = len(blocos)
total_bytes_utilizados = sum(len(bloco) for bloco in blocos)
total_bytes_maximos = total_blocos * tam_max_bloco

# Cálculo preciso de bytes úteis
bytes_uteis = 0
if modo_armazenamento == 1:
    bytes_uteis = len(pessoas) * 169
else:
    for p in pessoas:
        registro_str = f"{p.matricula},{p.nome},{p.cpf},{p.curso},{p.filiacao_mae},{p.filiacao_pai},{p.ano_ingresso},{p.coeficiente_academico}"
        bytes_uteis += len(registro_str.encode(ENCODING))

percentuais = [(len(bloco) / tam_max_bloco) * 100 for bloco in blocos]
percentual_medio = sum(percentuais) / total_blocos if total_blocos > 0 else 0

blocos_parciais = sum(1 for bloco in blocos if len(bloco) < tam_max_bloco)
eficiencia_real = (bytes_uteis / total_bytes_maximos) * 100 if total_bytes_maximos > 0 else 0

# Mapa de ocupação
for i, bloco in enumerate(blocos, start=1):
    ocupacao = (len(bloco) / tam_max_bloco) * 100
    print(f"Bloco {i}: {len(bloco)} bytes ({ocupacao:.1f}% cheio)")

# Resumo 
print(f"\nTotal de blocos: {total_blocos}")
print(f"Blocos parcialmente utilizados: {blocos_parciais}")
print(f"Percentual médio de ocupação: {percentual_medio:.1f}%")
print(f"Eficiência de armazenamento: {eficiencia_real:.1f}%")

print("=====================================")
