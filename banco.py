import sqlite3
from pathlib import Path

from moeda import texto_para_centavos

# Banco fica sempre na pasta do projeto, independente de onde o programa é executado
CAMINHO_BANCO = Path(__file__).resolve().parent / "DB_Oficina"

# Uma placa pode ter vários pedidos; o valor é guardado em centavos
ESQUEMA = """CREATE TABLE IF NOT EXISTS oficina(
id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
cpf TEXT NOT NULL,
nome TEXT NOT NULL,
veiculo TEXT NOT NULL,
placa TEXT NOT NULL,
servico TEXT NOT NULL,
valor INTEGER NOT NULL,
situacao TEXT NOT NULL
)"""

# Acesso ao banco de dados da oficina
class Banco:
    def __init__(self, caminho=CAMINHO_BANCO):
        self.conexao = sqlite3.connect(caminho)
        self.cursor = self.conexao.cursor()
        self._migrar()
        self.cursor.execute(ESQUEMA)

    # Converter bancos antigos (placa única e valor em texto) para o esquema atual
    def _migrar(self):
        self.cursor.execute("SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'oficina'")
        tabela = self.cursor.fetchone()
        if tabela is None or "valor TEXT" not in tabela[0]:
            return
        self.cursor.execute("SELECT * FROM oficina")
        pedidos = []
        for pedido in self.cursor.fetchall():
            centavos = texto_para_centavos(pedido[6])
            if centavos is None:
                raise ValueError(f"Pedido nº {pedido[0]} tem valor inválido: {pedido[6]!r}")
            pedidos.append(pedido[:6] + (centavos,) + pedido[7:])
        with self.conexao:
            self.cursor.execute("ALTER TABLE oficina RENAME TO oficina_antiga")
            self.cursor.execute(ESQUEMA)
            self.cursor.executemany("INSERT INTO oficina VALUES (?, ?, ?, ?, ?, ?, ?, ?)", pedidos)
            self.cursor.execute("DROP TABLE oficina_antiga")

    # Inserir um pedido; valor em centavos
    def cadastrar_pedido(self, cpf, nome, veiculo, placa, servico, valor, situacao="Na fila"):
        self.cursor.execute("""INSERT INTO oficina (
        cpf, nome, veiculo, placa, servico, valor, situacao
        ) VALUES (?, ?, ?, ?, ?, ?, ?)""", (cpf, nome, veiculo, placa, servico, valor, situacao))
        self.conexao.commit()

    # Alterar os dados de um pedido; valor em centavos
    def atualizar_pedido(self, id_pedido, cpf, nome, veiculo, placa, servico, valor, situacao):
        self.cursor.execute("""UPDATE oficina SET
        cpf = ?, nome = ?, veiculo = ?, placa = ?, servico = ?, valor = ?, situacao = ?
        WHERE id = ?""", (cpf, nome, veiculo, placa, servico, valor, situacao, id_pedido))
        self.conexao.commit()

    def excluir_pedido(self, id_pedido):
        self.cursor.execute("DELETE FROM oficina WHERE id = ?", (id_pedido,))
        self.conexao.commit()

    def listar_pedidos(self):
        self.cursor.execute("SELECT * FROM oficina")
        return self.cursor.fetchall()

    def fechar(self):
        self.conexao.close()
