import re
import unicodedata

# Partículas que ficam em minúsculo no meio de nomes ("Maria da Silva")
PARTICULAS = {"da", "das", "de", "di", "do", "dos", "du", "e"}

# CPF só com os números ("123.456.789-00" -> "12345678900"); None se não tiver 11 números
def normalizar_cpf(texto):
    cpf = re.sub(r"[.\-\s]", "", texto)
    return cpf if re.fullmatch(r"\d{11}", cpf) else None

# CPF com pontos e hífen para exibição: "12345678900" -> "123.456.789-00"
def formatar_cpf(cpf):
    if len(cpf) != 11 or not cpf.isdigit():
        return cpf
    return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"

# Nome com iniciais maiúsculas, mantendo partículas em minúsculo: "MARIA DA SILVA" -> "Maria da Silva"
def formatar_nome(texto):
    palavras = texto.split()
    return " ".join(
        palavra.lower() if indice > 0 and palavra.lower() in PARTICULAS else palavra.title()
        for indice, palavra in enumerate(palavras)
    )

# Texto em minúsculo e sem acentos, para a busca: "João" -> "joao"
def simplificar(texto):
    sem_acento = unicodedata.normalize("NFD", texto).encode("ascii", "ignore").decode()
    return sem_acento.lower()

# Busca no nome (sem diferenciar acentos), na placa (ignorando hífen) e,
# se só tiver números, no CPF
def corresponde(termo, cpf, nome, placa):
    termo = simplificar(termo.strip())
    if not termo:
        return True
    sem_hifen = lambda texto: re.sub(r"[-\s]", "", texto.lower())
    if termo in simplificar(nome) or sem_hifen(termo) in sem_hifen(placa):
        return True
    return re.fullmatch(r"[\d.\-\s]+", termo) is not None and re.sub(r"\D", "", termo) in cpf

# Valores digitados prontos para o banco (CPF só com números, nome formatado, placa em
# maiúsculo). Devolve (valores, None) ou (None, mensagem de erro)
def validar_pedido(cpf, nome, veiculo, placa, servico):
    if not all((cpf, nome, veiculo, placa, servico)):
        return None, "Preencha todos os campos!"
    cpf_normalizado = normalizar_cpf(cpf)
    if cpf_normalizado is None:
        return None, "CPF inválido! Digite os 11 números do CPF."
    return (cpf_normalizado, formatar_nome(nome), veiculo, placa.upper(), servico), None
