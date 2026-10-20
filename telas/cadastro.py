import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox

from telas.base import Pagina

# Página de cadastro de pedido
class TelaCadastro(Pagina):
    titulo = "Novo pedido"
    subtitulo = "Insira os dados do pedido"

    rotulos = [
        "CPF do cliente",
        "Nome do cliente",
        "Modelo do veículo",
        "Placa do veículo",
        "Serviço solicitado",
        "Valor do serviço (R$)",
    ]

    def __init__(self, app):
        super().__init__(app)
        formulario = ttk.Frame(self.cartao, style="Cartao.TFrame")
        formulario.pack(fill="x")
        self.campos = []
        for linha, rotulo in enumerate(self.rotulos):
            ttk.Label(formulario, text=rotulo).grid(
                row=linha, column=0, sticky="w", padx=(0, 15), pady=5
            )
            campo = ttk.Entry(formulario, width=32)
            campo.grid(row=linha, column=1, sticky="ew", pady=5)
            self.campos.append(campo)
        botoes = ttk.Frame(self.cartao, style="Cartao.TFrame")
        botoes.pack(fill="x", pady=(20, 0))
        ttk.Button(botoes, text="Voltar ao menu", command=lambda: self.app.mostrar("menu")).pack(
            side="left"
        )
        ttk.Button(
            botoes, text="Cadastrar pedido", style="Primario.TButton", command=self.cadastrar
        ).pack(side="right")

    def ao_mostrar(self):
        self.campos[0].focus_set()

    # Inserir todos os dados do pedido na tabela
    def cadastrar(self):
        cpf, nome, veiculo, placa, servico, valor = (campo.get().strip() for campo in self.campos)
        nome = nome.title()
        if not cpf or not nome or not veiculo or not placa or not servico or not valor:
            messagebox.showerror("Erro", "Preencha todos os campos!")
            return
        try:
            self.app.banco.cadastrar_pedido(cpf, nome, veiculo, placa, servico, valor)
        except sqlite3.IntegrityError:
            messagebox.showerror("Erro", "Já existe um pedido com essa placa!")
            return
        for campo in self.campos:
            campo.delete(0, tk.END)
        self.campos[0].focus_set()
        messagebox.showinfo("Sucesso", "Pedido enviado!")
