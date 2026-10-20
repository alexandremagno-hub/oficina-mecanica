import sqlite3

CAMINHO_BANCO = "DB_Oficina"

# Acesso ao banco de dados da oficina
class Banco:
    def __init__(self, caminho=CAMINHO_BANCO):
        self.conexao = sqlite3.connect(caminho)
        self.cursor = self.conexao.cursor()
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS oficina(
        id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        cpf TEXT NOT NULL,
        nome TEXT NOT NULL,
        veiculo TEXT NOT NULL,
        placa TEXT NOT NULL UNIQUE,
        servico TEXT NOT NULL,
        valor TEXT NOT NULL,
        situacao TEXT NOT NULL
        )""")

    # Inserir um pedido; levanta sqlite3.IntegrityError se a placa já existir
    def cadastrar_pedido(self, cpf, nome, veiculo, placa, servico, valor, situacao="Na fila"):
        self.cursor.execute("""INSERT INTO oficina (
        cpf, nome, veiculo, placa, servico, valor, situacao
        ) VALUES (?, ?, ?, ?, ?, ?, ?)""", (cpf, nome, veiculo, placa, servico, valor, situacao))
        self.conexao.commit()

    # Alterar os dados de um pedido; levanta sqlite3.IntegrityError se a placa já existir
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
