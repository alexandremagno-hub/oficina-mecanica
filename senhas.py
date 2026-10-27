import hashlib
import hmac
import secrets

ITERACOES = 200_000

# Senha guardada como "sal$hash" (PBKDF2-SHA256), nunca o texto digitado
def gerar_hash(senha):
    sal = secrets.token_hex(16)
    calculado = hashlib.pbkdf2_hmac("sha256", senha.encode(), bytes.fromhex(sal), ITERACOES)
    return f"{sal}${calculado.hex()}"

def conferir_senha(senha, guardado):
    sal, esperado = guardado.split("$")
    calculado = hashlib.pbkdf2_hmac("sha256", senha.encode(), bytes.fromhex(sal), ITERACOES)
    return hmac.compare_digest(calculado.hex(), esperado)
