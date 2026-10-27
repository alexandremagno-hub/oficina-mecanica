import json
import sqlite3
from datetime import date
from pathlib import Path

from moeda import texto_para_centavos
from senhas import conferir_senha, gerar_hash

# Banco fica sempre na pasta do projeto, independente de onde o programa é executado
CAMINHO_BANCO = Path(__file__).resolve().parent / "DB_Oficina"

SITUACOES = ["Na fila", "Em andamento", "Concluído", "Entregue"]
CONCLUIDO = "Concluído"
ENTREGUE = "Entregue"

COLUNAS = ("id, cpf, nome, veiculo, placa, servico, valor, situacao, data_entrada, data_entrega, "
           "mao_de_obra, pecas, aberta_por, concluida_por")

# Campos de cada OS em listar_pedidos: as colunas da tabela e o nome de quem abriu e de quem
# concluiu o serviço
CAMPOS_LISTA = [coluna.strip() for coluna in COLUNAS.split(",")] + ["nome_abertura", "nome_conclusao"]

# Colunas acrescentadas depois da criação da tabela, com o tipo de cada uma
COLUNAS_NOVAS = {
    "data_entrada": "TEXT", "data_entrega": "TEXT", "mao_de_obra": "INTEGER", "pecas": "TEXT",
    "aberta_por": "INTEGER", "concluida_por": "INTEGER",
}

# Uma placa pode ter vários pedidos. Os valores ficam em centavos e vazios até o serviço ser
# concluído: valor é o total (mão de obra + peças) e pecas é uma lista em JSON com
# descrição, quantidade e valor unitário. As datas ficam no formato AAAA-MM-DD (data_entrada
# fica vazia em pedidos cadastrados antes de as datas existirem). aberta_por e concluida_por
# guardam o id do funcionário que abriu a OS e o que concluiu o serviço (vazios em OS
# anteriores a esse registro)
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
pecas TEXT,
aberta_por INTEGER REFERENCES funcionarios(id),
concluida_por INTEGER REFERENCES funcionarios(id)
)"""

# Funcionários da oficina, que também são as contas de acesso ao sistema. A senha fica só
# como hash; quem sai da oficina é desativado (ativo = 0) em vez de apagado. Administradores
# (admin = 1) acessam todas as páginas; os demais, só as de ordens de serviço
ESQUEMA_FUNCIONARIOS = """CREATE TABLE IF NOT EXISTS funcionarios(
id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
usuario TEXT NOT NULL UNIQUE,
nome TEXT NOT NULL,
funcao TEXT NOT NULL,
data_admissao TEXT,
senha TEXT NOT NULL,
ativo INTEGER NOT NULL DEFAULT 1,
admin INTEGER NOT NULL DEFAULT 0
)"""

COLUNAS_FUNCIONARIOS = "id, usuario, nome, funcao, data_admissao, ativo, admin"

# Contas que existiam fixas no código antes do cadastro de funcionários; entram no banco
# na primeira vez para ninguém perder o acesso (usuário, nome, senha)
CONTAS_INICIAIS = [("alexandre", "Alexandre", "123"), ("lucas", "Lucas", "123"), ("gabriel", "Gabriel", "666")]

# Conta de administrador criada quando o banco ainda não tem nenhum (usuário, nome, senha)
ADMIN_INICIAL = ("admin", "Administrador", "admin")

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
        self._criar_funcionarios()

    # Criar a tabela de funcionários com as contas iniciais, se ainda não existir nenhum, e
    # garantir que exista um administrador
    def _criar_funcionarios(self):
        with self.conexao:
            self.cursor.execute(ESQUEMA_FUNCIONARIOS)
            self.cursor.execute("PRAGMA table_info(funcionarios)")
            if "admin" not in {coluna[1] for coluna in self.cursor.fetchall()}:
                self.cursor.execute("ALTER TABLE funcionarios ADD COLUMN admin INTEGER NOT NULL DEFAULT 0")
            self.cursor.execute("SELECT COUNT(*) FROM funcionarios")
            if self.cursor.fetchone()[0] == 0:
                self.cursor.executemany(
                    "INSERT INTO funcionarios (usuario, nome, funcao, senha) VALUES (?, ?, 'A definir', ?)",
                    [(usuario, nome, gerar_hash(senha)) for usuario, nome, senha in CONTAS_INICIAIS],
                )
            self.cursor.execute("SELECT COUNT(*) FROM funcionarios WHERE admin = 1")
            if self.cursor.fetchone()[0] == 0:
                usuario, nome, senha = ADMIN_INICIAL
                self.cursor.execute(
                    """INSERT INTO funcionarios (usuario, nome, funcao, senha, admin)
                    VALUES (?, ?, 'Administrador', ?, 1)""", (usuario, nome, gerar_hash(senha)),
                )

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

    # Inserir um pedido com a data de hoje como entrada e o funcionário que o abriu; o valor
    # é informado ao concluir
    def cadastrar_pedido(self, cpf, nome, veiculo, placa, servico, aberta_por=None,
                         situacao=SITUACOES[0]):
        self.cursor.execute("""INSERT INTO oficina (
        cpf, nome, veiculo, placa, servico, situacao, data_entrada, aberta_por
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (cpf, nome, veiculo, placa, servico, situacao, date.today().isoformat(), aberta_por))
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
    # "Entregue" e apagada se ele voltar para outra situação. Quem concluiu é o funcionário
    # que passou a OS para "Concluído"; continua registrado na entrega (ou se a OS voltar da
    # entrega para concluída) e é apagado se o serviço voltar para a fila ou para o andamento
    def mudar_situacao(self, id_pedido, situacao, id_funcionario=None):
        self.cursor.execute("""UPDATE oficina SET situacao = :situacao,
        data_entrega = CASE WHEN :situacao = :entregue THEN COALESCE(data_entrega, :hoje) ELSE NULL END,
        concluida_por = CASE
            WHEN :situacao = :concluido THEN COALESCE(concluida_por, :funcionario)
            WHEN :situacao = :entregue THEN concluida_por
        END
        WHERE id = :id""", {
            "situacao": situacao, "entregue": ENTREGUE, "concluido": CONCLUIDO,
            "hoje": date.today().isoformat(), "funcionario": id_funcionario, "id": id_pedido,
        })
        self.conexao.commit()

    def excluir_pedido(self, id_pedido):
        self.cursor.execute("DELETE FROM oficina WHERE id = ?", (id_pedido,))
        self._renumerar()
        self.conexao.commit()

    # Pedidos como tuplas na ordem de CAMPOS_LISTA, com o nome de quem abriu e de quem concluiu
    def listar_pedidos(self):
        colunas = ", ".join(f"o.{coluna.strip()}" for coluna in COLUNAS.split(","))
        self.cursor.execute(f"""SELECT {colunas}, abertura.nome, conclusao.nome FROM oficina o
        LEFT JOIN funcionarios abertura ON abertura.id = o.aberta_por
        LEFT JOIN funcionarios conclusao ON conclusao.id = o.concluida_por""")
        return self.cursor.fetchall()

    # Cadastrar um funcionário ativo. Gera sqlite3.IntegrityError se o usuário já existir
    def cadastrar_funcionario(self, usuario, nome, funcao, data_admissao, senha):
        self.cursor.execute("""INSERT INTO funcionarios (
        usuario, nome, funcao, data_admissao, senha
        ) VALUES (?, ?, ?, ?, ?)""", (usuario, nome, funcao, data_admissao, gerar_hash(senha)))
        self.conexao.commit()

    # Alterar os dados de um funcionário; a senha só muda se uma nova for informada
    def atualizar_funcionario(self, id_funcionario, nome, funcao, data_admissao, ativo, senha=None):
        self.cursor.execute("""UPDATE funcionarios SET
        nome = ?, funcao = ?, data_admissao = ?, ativo = ?
        WHERE id = ?""", (nome, funcao, data_admissao, int(ativo), id_funcionario))
        if senha:
            self.cursor.execute("UPDATE funcionarios SET senha = ? WHERE id = ?",
                                (gerar_hash(senha), id_funcionario))
        self.conexao.commit()

    # Funcionários como tuplas na ordem de COLUNAS_FUNCIONARIOS, em ordem alfabética
    def listar_funcionarios(self):
        self.cursor.execute(f"SELECT {COLUNAS_FUNCIONARIOS} FROM funcionarios ORDER BY nome")
        return self.cursor.fetchall()

    # (id, nome, é administrador) se o usuário existir, estiver ativo e a senha conferir;
    # senão None
    def autenticar(self, usuario, senha):
        self.cursor.execute(
            "SELECT id, nome, admin, senha FROM funcionarios WHERE usuario = ? AND ativo = 1",
            (usuario,),
        )
        encontrado = self.cursor.fetchone()
        if encontrado and conferir_senha(senha, encontrado[3]):
            return encontrado[0], encontrado[1], bool(encontrado[2])
        return None

    def fechar(self):
        self.conexao.close()
