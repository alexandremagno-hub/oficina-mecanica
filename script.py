import _sqlite3
import tkinter as tk
from tkinter import messagebox

# ESSA LISTA POSSUI OS USUÁRIOS E SENHAS HABILITADOS PARA LOGIN
contas = [
    ("lucas", "123")
]

janela_main = tk.Tk()
janela_main.title("SIMA'S CARS")
janela_main.minsize(600, 400)

conexao = _sqlite3.connect("DB_Oficina")
cursor = conexao.cursor()
cursor.execute("""CREATE TABLE IF NOT EXISTS oficina(
id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
cpf TEXT NOT NULL UNIQUE,
nome TEXT NOT NULL,
veiculo TEXT NOT NULL,
placa TEXT NOT NULL UNIQUE,
servicos TEXT NOT NULL,
valor TEXT NOT NULL,
situacao TEXT NOT NULL
)""")

conexao.commit()

pagina_login = tk.Frame(janela_main)
pagina_login.place(x=0, y=0, width=600, height=400)
pagina_login.configure(bg="#2f4f4f")


user_login = tk.Label(janela_main, text="Usuário:")
user_login.place(x=230, y=120)

campo_usuario = tk.Entry(janela_main)
campo_usuario.place(x=280, y=121)

user_password = tk.Label(janela_main, text="Senha:", padx=5)
user_password.place(x=230, y=142)

campo_senha = tk.Entry(janela_main, show='*')
campo_senha.place(x=280, y=144)

# RESUMINDO, A FUNCAO LOGIN, CASO O USUARIO E SENHA ESTEJAM NA LISTA 'CONTAS', ELA VAI ESCONDER A PAGINA DE LOGIN E CRIAR OUTRA EM CIMA
def login():
    usuario = campo_usuario.get()
    senha = campo_senha.get()
    if (usuario, senha) in contas:
        pagina_login.place_forget() #VAI ESCONDER A PAGINA DE LOGIN
        pagina_menu.place(x=0, y=0, width=600, height=400) #VAI MOSTRAR A PAGINA_MENU NO LUGAR DA PAGINA_LOGIN
    else:
        messagebox.showerror("Erro!",
                             "As credenciais são inválidas") 

botao = tk.Button(janela_main, text="Login", command=login, padx=10)
botao.place(x=295, y=195, anchor='center')


# PAGINA_MENU ONDE FICARÁ OS BOTÕES PARA CADA AÇÃO (CADASTRAR, EDITAR, DELETAR, ETC...)
pagina_menu = tk.Frame()
pagina_menu.configure(bg="#2f4f4f")

def pagina_de_cadastro():
    pagina_menu.place_forget()
    pagina_cadastro.place(x=0, y=0, width=600, height=400)

botao_cadastrar = tk.Button(pagina_menu, text='Cadastrar cliente', command=pagina_de_cadastro, padx=10)
botao_cadastrar.place(x=30, y=100)


def pagina_editar():
    pagina_menu.place_forget()
    pagina_editar_cadastro.place(x=0, y=0, width=600, height=400)

botao_editar_cadastro = tk.Button(pagina_menu, text='Editar cadastro', command=pagina_editar, padx=10)
botao_editar_cadastro.place(x=160, y=100)


def pagina_buscar():
    pagina_menu.place_forget()
    pagina_buscar_cadastro.place(x=0, y=0, width=600, height=400)

botao_buscar_cadastro = tk.Button(pagina_menu, text='Buscar cliente', command=pagina_buscar, padx=10)
botao_buscar_cadastro.place(x=280, y=100)


def pagina_deletar():
    pagina_menu.place_forget()
    pagina_deletar_cadastro.place(x=0, y=0, width=600, height=400)

botao_deletar_cadastro = tk.Button(pagina_menu, text='Deletar cadastro', command=pagina_deletar, padx=10)
botao_deletar_cadastro.place(x=400, y=100)


pagina_cadastro = tk.Frame()
pagina_cadastro.configure(bg="#2f4f4f")

def cadastrar():
    cpf = cpf_entrada.get()
    nome = nome_entrada.get()
    veiculo = veiculo_entrada.get()
    placa = placa_entrada.get()
    servicos = servicos_entrada.get()
    valor = valor_entrada.get()
    situacao = situacao_entrada.get()

    conexao = _sqlite3.connect("DB_Oficina")
    cursor = conexao.cursor()
    cursor.execute("""INSERT INTO oficina (cpf, nome, veiculo, placa, servicos, valor, situacao) VALUES (?, ?, ?, ?, ?, ?, ?)""", (cpf, nome, veiculo, placa, servicos, valor, situacao))

    conexao.commit()

    if not cpf or not nome or not veiculo or not placa or not servicos or not valor or not situacao:
        messagebox.showerror(
            "Erro",
            "Preencha todos os campos!"
        )
        return
    
    messagebox.showinfo(
        "Sucesso",
        "Aluno Cadastrado com sucesso!"
    )

    cpf_entrada.delete(0, tk.END)
    nome_entrada.delete(0, tk.END)
    veiculo_entrada.delete(0, tk.END)
    placa_entrada.delete(0, tk.END)
    servicos_entrada.delete(0, tk.END)
    valor_entrada.delete(0, tk.END)
    situacao_entrada.delete(0, tk.END)


campo_cpf = tk.Label(pagina_cadastro, text="CPF:")
campo_cpf.place(x=50, y=30)
cpf_entrada = tk.Entry(pagina_cadastro)
cpf_entrada.place(x=102, y=30)

campo_nome = tk.Label(pagina_cadastro, text="Nome:")
campo_nome.place(x=50, y=60)
nome_entrada = tk.Entry(pagina_cadastro)
nome_entrada.place(x=102, y=60)

campo_veiculo = tk.Label(pagina_cadastro, text="Veículo:")
campo_veiculo.place(x=50, y=90)
veiculo_entrada = tk.Entry(pagina_cadastro)
veiculo_entrada.place(x=102, y=90)

campo_placa = tk.Label(pagina_cadastro, text="Placa:")
campo_placa.place(x=50, y=120)
placa_entrada = tk.Entry(pagina_cadastro)
placa_entrada.place(x=102, y=120)

campo_servicos = tk.Label(pagina_cadastro, text="Servicos:")
campo_servicos.place(x=50, y=150)
servicos_entrada = tk.Entry(pagina_cadastro)
servicos_entrada.place(x=102, y=150)

campo_valor = tk.Label(pagina_cadastro, text="Valor:")
campo_valor.place(x=50, y=180)
valor_entrada = tk.Entry(pagina_cadastro)
valor_entrada.place(x=102, y=180)

campo_situacao = tk.Label(pagina_cadastro, text="Situação:")
campo_situacao.place(x=50, y=210)
situacao_entrada = tk.Entry(pagina_cadastro)
situacao_entrada.place(x=102, y=210)

confirmar_cadastro = tk.Button(pagina_cadastro, text="Cadastrar", command=cadastrar, padx=10)
confirmar_cadastro.place(x=100, y=240)




pagina_editar_cadastro = tk.Frame()
pagina_editar_cadastro.configure(bg="#2f4f4f")
tk.Label(pagina_editar_cadastro, text='BEM VINDO A PAGINA MENU!').place(x=25, y=25)




pagina_buscar_cadastro = tk.Frame()
pagina_buscar_cadastro.configure(bg="#2f4f4f")
tk.Label(pagina_buscar_cadastro, text='BEM VINDO A PAGINA MENU!').place(x=25, y=25)




pagina_deletar_cadastro = tk.Frame()
pagina_deletar_cadastro.configure(bg="#2f4f4f")
tk.Label(pagina_deletar_cadastro, text='BEM VINDO A PAGINA MENU!').place(x=25, y=25)





janela_main.mainloop()
