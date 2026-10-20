import sqlite3
from datetime import date
from pathlib import Path

from moeda import texto_para_centavos

# Banco fica sempre na pasta do projeto, independente de onde o programa é executado
CAMINHO_BANCO = Path(__file__).resolve().parent / "DB_Oficina"

SITUACOES = ["Na fila", "Em andamento", "Concluído", "Entregue"]
ENTREGUE = "Entregue"

COLUNAS = "id, cpf, nome, veiculo, placa, servico, valor, situacao, data_entrada, data_entrega"

# Uma placa pode ter vários pedidos; o valor é guardado em centavos e as datas no formato AAAA-MM-DD
# (data_entrada fica vazia em pedidos cadastrados antes de as datas existirem)
ESQUEMA = """CREATE TABLE IF NOT EXISTS oficina(
id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
cpf TEXT NOT NULL,
nome TEXT NOT NULL,
veiculo TEXT NOT NULL,
placa TEXT NOT NULL,
servico TEXT NOT NULL,
valor INTEGER NOT NULL,
situacao TEXT NOT NULL,
data_entrada TEXT,
data_entrega TEXT
)"""

# Acesso ao banco de dados da oficina
class Banco:
    def __init__(self, caminho=CAMINHO_BANCO):
        self.conexao = sqlite3.connect(caminho)
        self.cursor = self.conexao.cursor()
        self._migrar_valor()
        self.cursor.execute(ESQUEMA)
        self._migrar_datas()

    # Converter bancos antigos (placa única e valor em texto) para o esquema atual
    def _migrar_valor(self):
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
            self.cursor.executemany("""INSERT INTO oficina (
            id, cpf, nome, veiculo, placa, servico, valor, situacao
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""", pedidos)
            self.cursor.execute("DROP TABLE oficina_antiga")

    # Adicionar as colunas de data em bancos criados antes delas
    def _migrar_datas(self):
        self.cursor.execute("PRAGMA table_info(oficina)")
        existentes = {coluna[1] for coluna in self.cursor.fetchall()}
        with self.conexao:
            for coluna in ("data_entrada", "data_entrega"):
                if coluna not in existentes:
                    self.cursor.execute(f"ALTER TABLE oficina ADD COLUMN {coluna} TEXT")

    # Inserir um pedido com a data de hoje como entrada; valor em centavos
    def cadastrar_pedido(self, cpf, nome, veiculo, placa, servico, valor, situacao=SITUACOES[0]):
        self.cursor.execute("""INSERT INTO oficina (
        cpf, nome, veiculo, placa, servico, valor, situacao, data_entrada
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (cpf, nome, veiculo, placa, servico, valor, situacao, date.today().isoformat()))
        self.conexao.commit()

    # Alterar os dados de um pedido; valor em centavos. A data de entrega é preenchida
    # quando o pedido passa a "Entregue" e apagada se ele voltar para outra situação
    def atualizar_pedido(self, id_pedido, cpf, nome, veiculo, placa, servico, valor, situacao):
        self.cursor.execute("""UPDATE oficina SET
        cpf = ?, nome = ?, veiculo = ?, placa = ?, servico = ?, valor = ?, situacao = ?,
        data_entrega = CASE WHEN ? = ? THEN COALESCE(data_entrega, ?) ELSE NULL END
        WHERE id = ?""", (cpf, nome, veiculo, placa, servico, valor, situacao,
                          situacao, ENTREGUE, date.today().isoformat(), id_pedido))
        self.conexao.commit()

    def excluir_pedido(self, id_pedido):
        self.cursor.execute("DELETE FROM oficina WHERE id = ?", (id_pedido,))
        self.conexao.commit()

    # Pedidos como tuplas na ordem de COLUNAS
    def listar_pedidos(self):
        self.cursor.execute(f"SELECT {COLUNAS} FROM oficina")
        return self.cursor.fetchall()

    def fechar(self):
        self.conexao.close()
