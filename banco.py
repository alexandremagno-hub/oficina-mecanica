import json
import sqlite3
from datetime import date
from pathlib import Path

from moeda import texto_para_centavos

# Banco fica sempre na pasta do projeto, independente de onde o programa é executado
CAMINHO_BANCO = Path(__file__).resolve().parent / "DB_Oficina"

SITUACOES = ["Na fila", "Em andamento", "Concluído", "Entregue"]
CONCLUIDO = "Concluído"
ENTREGUE = "Entregue"

COLUNAS = ("id, cpf, nome, veiculo, placa, servico, valor, situacao, data_entrada, data_entrega, "
           "mao_de_obra, pecas")

# Colunas acrescentadas depois da criação da tabela, com o tipo de cada uma
COLUNAS_NOVAS = {"data_entrada": "TEXT", "data_entrega": "TEXT", "mao_de_obra": "INTEGER", "pecas": "TEXT"}

# Uma placa pode ter vários pedidos. Os valores ficam em centavos e vazios até o serviço ser
# concluído: valor é o total (mão de obra + peças) e pecas é uma lista em JSON com
# descrição, quantidade e valor unitário. As datas ficam no formato AAAA-MM-DD (data_entrada
# fica vazia em pedidos cadastrados antes de as datas existirem)
ESQUEMA = """CREATE TABLE IF NOT EXISTS oficina(
id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
cpf TEXT NOT NULL,
nome TEXT NOT NULL,
veiculo TEXT NOT NULL,
placa TEXT NOT NULL,
servico TEXT NOT NULL,
valor INTEGER,
situacao TEXT NOT NULL,
data_entrada TEXT,
data_entrega TEXT,
mao_de_obra INTEGER,
pecas TEXT
)"""

# Peças guardadas na OS como lista de (descrição, quantidade, valor unitário em centavos)
def ler_pecas(texto):
    return [tuple(peca) for peca in json.loads(texto)] if texto else []

# Acesso ao banco de dados da oficina
class Banco:
    def __init__(self, caminho=CAMINHO_BANCO):
        # O Streamlit executa cada interação numa thread diferente, sempre uma por vez em cada sessão
        self.conexao = sqlite3.connect(caminho, check_same_thread=False)
        self.cursor = self.conexao.cursor()
        self._migrar_valor()
        self._migrar_valor_opcional()
        self.cursor.execute(ESQUEMA)
        self._migrar_colunas()
        with self.conexao:
            self._renumerar()

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
                raise ValueError(f"OS nº {pedido[0]} tem valor inválido: {pedido[6]!r}")
            pedidos.append(pedido[:6] + (centavos,) + pedido[7:])
        with self.conexao:
            self.cursor.execute("ALTER TABLE oficina RENAME TO oficina_antiga")
            self.cursor.execute(ESQUEMA)
            self.cursor.executemany("""INSERT INTO oficina (
            id, cpf, nome, veiculo, placa, servico, valor, situacao
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""", pedidos)
            self.cursor.execute("DROP TABLE oficina_antiga")

    # Recriar a tabela de bancos em que o valor era obrigatório (o SQLite não deixa tirar
    # o NOT NULL de uma coluna), copiando todos os pedidos
    def _migrar_valor_opcional(self):
        self.cursor.execute("SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'oficina'")
        tabela = self.cursor.fetchone()
        if tabela is None or "valor INTEGER NOT NULL" not in tabela[0]:
            return
        self._migrar_colunas()
        with self.conexao:
            self.cursor.execute("ALTER TABLE oficina RENAME TO oficina_antiga")
            self.cursor.execute(ESQUEMA)
            self.cursor.execute(f"INSERT INTO oficina ({COLUNAS}) SELECT {COLUNAS} FROM oficina_antiga")
            self.cursor.execute("DROP TABLE oficina_antiga")

    # Adicionar as colunas novas em bancos criados antes delas
    def _migrar_colunas(self):
        self.cursor.execute("PRAGMA table_info(oficina)")
        existentes = {coluna[1] for coluna in self.cursor.fetchall()}
        with self.conexao:
            for coluna, tipo in COLUNAS_NOVAS.items():
                if coluna not in existentes:
                    self.cursor.execute(f"ALTER TABLE oficina ADD COLUMN {coluna} {tipo}")

    # Renumerar as OS em sequência (1, 2, 3…) sem buracos, mantendo a ordem, e alinhar o
    # contador do AUTOINCREMENT para a próxima OS seguir a última. Os ids passam primeiro
    # para negativos para não colidirem com os existentes durante a troca
    def _renumerar(self):
        self.cursor.execute("SELECT id FROM oficina ORDER BY id")
        ids = [linha[0] for linha in self.cursor.fetchall()]
        self.cursor.execute("UPDATE oficina SET id = -id")
        self.cursor.executemany("UPDATE oficina SET id = ? WHERE id = ?",
                                [(numero, -id_antigo) for numero, id_antigo in enumerate(ids, start=1)])
        self.cursor.execute("""UPDATE sqlite_sequence SET seq = (SELECT COALESCE(MAX(id), 0) FROM oficina)
        WHERE name = 'oficina'""")

    # Inserir um pedido com a data de hoje como entrada; o valor é informado ao concluir
    def cadastrar_pedido(self, cpf, nome, veiculo, placa, servico, situacao=SITUACOES[0]):
        self.cursor.execute("""INSERT INTO oficina (
        cpf, nome, veiculo, placa, servico, situacao, data_entrada
        ) VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (cpf, nome, veiculo, placa, servico, situacao, date.today().isoformat()))
        self.conexao.commit()

    # Alterar os dados de um pedido. Os valores mudam só por definir_valores e a situação
    # só por mudar_situacao
    def atualizar_pedido(self, id_pedido, cpf, nome, veiculo, placa, servico):
        self.cursor.execute("""UPDATE oficina SET
        cpf = ?, nome = ?, veiculo = ?, placa = ?, servico = ?
        WHERE id = ?""", (cpf, nome, veiculo, placa, servico, id_pedido))
        self.conexao.commit()

    # Gravar a mão de obra e as peças (descrição, quantidade, valor unitário) em centavos,
    # com o total no valor do pedido
    def definir_valores(self, id_pedido, mao_de_obra, pecas):
        total = mao_de_obra + sum(quantidade * unitario for _, quantidade, unitario in pecas)
        self.cursor.execute("""UPDATE oficina SET mao_de_obra = ?, pecas = ?, valor = ?
        WHERE id = ?""", (mao_de_obra, json.dumps(pecas, ensure_ascii=False), total, id_pedido))
        self.conexao.commit()

    # Mudar a situação do pedido. A data de entrega é preenchida quando ele passa a
    # "Entregue" e apagada se ele voltar para outra situação
    def mudar_situacao(self, id_pedido, situacao):
        self.cursor.execute("""UPDATE oficina SET situacao = ?,
        data_entrega = CASE WHEN ? = ? THEN COALESCE(data_entrega, ?) ELSE NULL END
        WHERE id = ?""", (situacao, situacao, ENTREGUE, date.today().isoformat(), id_pedido))
        self.conexao.commit()

    def excluir_pedido(self, id_pedido):
        self.cursor.execute("DELETE FROM oficina WHERE id = ?", (id_pedido,))
        self._renumerar()
        self.conexao.commit()

    # Pedidos como tuplas na ordem de COLUNAS
    def listar_pedidos(self):
        self.cursor.execute(f"SELECT {COLUNAS} FROM oficina")
        return self.cursor.fetchall()

    def fechar(self):
        self.conexao.close()
