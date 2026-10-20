import tkinter as tk
from tkinter import ttk, messagebox

from telas.base import Pagina

# Contas com acesso ao sistema
contas = [("alexandre", "123"), ("lucas", "123"), ("gabriel", "666")]

# Página inicial de login
class TelaLogin(Pagina):
    titulo = "Oficina Mecânica"
    subtitulo = "Insira nome e senha para acessar o sistema"

    def __init__(self, app):
        super().__init__(app)
        ttk.Label(self.cartao, text="Usuário").pack(anchor="w")
        self.campo_usuario = ttk.Entry(self.cartao, width=32)
        self.campo_usuario.pack(fill="x", pady=(2, 10))
        ttk.Label(self.cartao, text="Senha").pack(anchor="w")
        self.campo_senha = ttk.Entry(self.cartao, width=32, show="*")
        self.campo_senha.pack(fill="x", pady=(2, 20))
        ttk.Button(self.cartao, text="Entrar", style="Primario.TButton", command=self.login).pack(
            fill="x"
        )
        self.campo_usuario.bind("<Return>", self.login)
        self.campo_senha.bind("<Return>", self.login)

    def ao_mostrar(self):
        self.campo_usuario.focus_set()

    # Checar credenciais do usuário e liberar acesso ao sistema
    def login(self, _event=None):
        usuario = self.campo_usuario.get()
        senha = self.campo_senha.get()
        if (usuario, senha) in contas:
            self.campo_usuario.delete(0, tk.END)
            self.campo_senha.delete(0, tk.END)
            self.app.mostrar("menu")
        elif not usuario or not senha:
            messagebox.showerror("Erro!", "Preencha todos os campos!")
        else:
            messagebox.showerror("Erro!", "Usuário ou senha incorretos!")
