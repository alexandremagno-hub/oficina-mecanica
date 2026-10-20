import re
from decimal import Decimal, InvalidOperation

# Converter o texto digitado ("1.234,56", "1234.56", "R$ 80") em centavos; None se for inválido
def texto_para_centavos(texto):
    texto = str(texto).replace("R$", "").replace(" ", "")
    if "," in texto:
        texto = texto.replace(".", "").replace(",", ".")
    elif re.fullmatch(r"\d{1,3}(\.\d{3})+", texto):
        texto = texto.replace(".", "")
    try:
        valor = Decimal(texto)
    except InvalidOperation:
        return None
    if not valor.is_finite() or valor < 0 or valor != round(valor, 2):
        return None
    return int(valor * 100)

# Formatar centavos no padrão brasileiro: 123456 -> "1.234,56"
def formatar_reais(centavos):
    reais = f"{centavos // 100:,}".replace(",", ".")
    return f"{reais},{centavos % 100:02d}"
