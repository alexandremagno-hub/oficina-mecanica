import sqlite3
import tkinter as tk
from tkinter import messagebox

# Contas com acesso ao sistema
contas = [("lucas", "123"), ("gabriel", "666")]

# Janela principal da interface
janela = tk.Tk()
janela.title("PROTÓTIPO OFICINA MECÂNICA")
janela.minsize(640, 360)

# Conexão com sqlite e criação de tabela
conexao = sqlite3.connect("DB_Oficina")
cursor = conexao.cursor()
cursor.execute("""CREATE TABLE IF NOT EXISTS oficina(
id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
cpf TEXT NOT NULL,
nome TEXT NOT NULL,
veiculo TEXT NOT NULL,
placa TEXT NOT NULL UNIQUE,
servico TEXT NOT NULL,
valor TEXT NOT NULL,
situacao TEXT NOT NULL
)""")

# Checar credenciais do usuário e liberar acesso ao sistema
def login():
    usuario = campo_usuario.get()
    senha = campo_senha.get()
    if (usuario, senha) in contas:
        campo_usuario.delete(0, tk.END)
        campo_senha.delete(0, tk.END)
        pg_login.pack_forget()
        pg_menu.pack(fill="both", expand=True)
    elif not usuario or not senha:
        messagebox.showerror("Erro!", "Preencha todos os campos!")
    else:
        messagebox.showerror("Erro!", "Usuário ou senha incorretos!")

# Voltar à tela de login e pedir usuário e senhas novamente
def sair_menu():
    pg_menu.pack_forget()
    pg_login.pack(fill="both", expand=True)

# Voltar ao menu de gestão
def voltar_menu():
    pg_cadastro.pack_forget()
    pg_menu.pack(fill="both", expand=True)

# Página de cadastro de pedido
def ir_pg_cadastro():
    pg_menu.pack_forget()
    pg_cadastro.pack(fill="both", expand=True)

# Inserir todos os dados do pedido na tabela
def cadastrar():
    cpf = campo_cpf.get().strip()
    nome = campo_nome.get().strip().title()
    veiculo = campo_veiculo.get().strip()
    placa = campo_placa.get().strip()
    servico = campo_servico.get().strip()
    valor = campo_valor.get().strip()
    situacao = "Na fila"
    if not cpf or not nome or not veiculo or not placa or not servico or not valor:
        messagebox.showerror("Erro", "Preencha todos os campos!")
    else:
        cursor.execute("""INSERT INTO oficina (
        cpf, nome, veiculo, placa, servico, valor, situacao
        ) VALUES (?, ?, ?, ?, ?, ? ,?)""", (cpf, nome, veiculo, placa, servico, valor, situacao))
        campo_cpf.delete(0, tk.END)
        campo_nome.delete(0, tk.END)
        campo_veiculo.delete(0, tk.END)
        campo_placa.delete(0, tk.END)
        campo_servico.delete(0, tk.END)
        campo_valor.delete(0, tk.END)
        conexao.commit()
        messagebox.showinfo("Sucesso", "Pedido enviado!")

# Página inicial de login
pg_login = tk.Frame(janela, bg="#0078D4")
pg_login.pack(fill="both", expand=True)
tk.Label(pg_login, text="Insira nome e senha para acessar o sistema", bg="#0078D4", fg="#FFFFFF").pack()
tk.Label(pg_login, bg="#0078D4").pack()
tk.Label(pg_login, text="Usuário:", bg="#0078D4", fg="#FFFFFF").pack()
campo_usuario = tk.Entry(pg_login)
campo_usuario.pack()
tk.Label(pg_login, text="Senha:", bg="#0078D4", fg="#FFFFFF").pack()
campo_senha = tk.Entry(pg_login, show="*")
campo_senha.pack()
tk.Label(pg_login, bg="#0078D4").pack()
botao_login = tk.Button(pg_login, text="Login", command=login)
botao_login.pack()

# Menu de gestão
pg_menu = tk.Frame(janela, bg="#0078D4")
tk.Label(pg_menu, text="Escolha uma opção", bg="#0078D4", fg="#FFFFFF").pack()
tk.Label(pg_menu, bg="#0078D4").pack()
botao_ir_pg_cadastro = tk.Button(pg_menu, text="Cadastrar pedido", command=ir_pg_cadastro)
botao_ir_pg_cadastro.pack()
tk.Label(pg_menu, bg="#0078D4").pack()
botao_exibir = tk.Button(pg_menu, text="Exibir pedidos")
botao_exibir.pack()
tk.Label(pg_menu, bg="#0078D4").pack()
botao_ir_pg_atualizar = tk.Button(pg_menu, text="Atualizar pedido")
botao_ir_pg_atualizar.pack()
tk.Label(pg_menu, bg="#0078D4").pack()
botao_ir_pg_excluir = tk.Button(pg_menu, text="Excluir pedido")
botao_ir_pg_excluir.pack()
tk.Label(pg_menu, bg="#0078D4").pack()
botao_sair_menu = tk.Button(pg_menu, text="Sair do menu", command=sair_menu)
botao_sair_menu.pack()

# Página de cadastro
pg_cadastro = tk.Frame(janela, bg="#0078D4")
tk.Label(pg_cadastro, text="Insira os dados do pedido", bg="#0078D4", fg="#FFFFFF").grid(
    row=0, column=0
)
tk.Label(pg_cadastro, text="CPF do cliente:", bg="#0078D4", fg="#FFFFFF").grid(
    row=1, column=0
)
campo_cpf = tk.Entry(pg_cadastro)
campo_cpf.grid(row=1, column=1)
tk.Label(pg_cadastro, text="Nome do cliente:", bg="#0078D4", fg="#FFFFFF").grid(
    row=2, column=0
)
campo_nome = tk.Entry(pg_cadastro)
campo_nome.grid(row=2, column=1)
tk.Label(pg_cadastro, text="Modelo do veículo", bg="#0078D4", fg="#FFFFFF").grid(
    row=3, column=0
)
campo_veiculo = tk.Entry(pg_cadastro)
campo_veiculo.grid(row=3, column=1)
tk.Label(pg_cadastro, text="Placa do veículo", bg="#0078D4", fg="#FFFFFF").grid(
    row=4, column=0
)
campo_placa = tk.Entry(pg_cadastro)
campo_placa.grid(row=4, column=1)
tk.Label(pg_cadastro, text="Serviço solicitado", bg="#0078D4", fg="#FFFFFF").grid(
    row=5, column=0
)
campo_servico = tk.Entry(pg_cadastro)
campo_servico.grid(row=5, column=1)
tk.Label(pg_cadastro, text="Valor do serviço", bg="#0078D4", fg="#FFFFFF").grid(
    row=6, column=0
)
campo_valor = tk.Entry(pg_cadastro)
campo_valor.grid(row=6, column=1)
botao_cadastrar = tk.Button(pg_cadastro, text="Cadastrar pedido", command=cadastrar)
botao_cadastrar.grid(row=7, column=0)
botao_voltar_menu = tk.Button(pg_cadastro, text="Voltar ao menu", command=voltar_menu)
botao_voltar_menu.grid(row=7, column=1)

# Encerramento
janela.mainloop()
conexao.close()
