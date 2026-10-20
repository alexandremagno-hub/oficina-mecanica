import sqlite3
from tkinter import ttk, messagebox

from telas.base import Pagina
from telas.componentes import TabelaPedidos, FormularioPedido

SITUACOES = ["Na fila", "Em andamento", "Concluído", "Entregue"]

# Página para escolher qual pedido atualizar
class TelaAtualizar(Pagina):
    titulo = "Atualizar pedido"
    subtitulo = "Selecione o pedido que deseja alterar"

    def __init__(self, app):
        super().__init__(app)
        self.tabela = TabelaPedidos(self.cartao)
        self.tabela.pack(fill="both", expand=True)
        self.tabela.tabela.bind("<Double-1>", self.editar)
        botoes = ttk.Frame(self.cartao, style="Cartao.TFrame")
        botoes.pack(fill="x", pady=(20, 0))
        ttk.Button(botoes, text="Voltar ao menu", command=lambda: self.app.mostrar("menu")).pack(
            side="left"
        )
        ttk.Button(
            botoes, text="Editar selecionado", style="Primario.TButton", command=self.editar
        ).pack(side="right")

    def ao_mostrar(self):
        self.tabela.carregar(self.app.banco.listar_pedidos())

    # Abrir o pedido selecionado na página de edição
    def editar(self, _event=None):
        pedido = self.tabela.selecionado()
        if pedido is None:
            messagebox.showwarning("Atenção", "Selecione um pedido na tabela!")
            return
        self.app.paginas["editar"].carregar(pedido)
        self.app.mostrar("editar")

# Página com o formulário de edição do pedido
class TelaEditar(Pagina):
    titulo = "Editar pedido"
    subtitulo = "Altere os dados e salve"

    def __init__(self, app):
        super().__init__(app)
        self.id_pedido = None
        self.formulario = FormularioPedido(self.cartao)
        self.formulario.pack(fill="x")
        linha = len(self.formulario.rotulos)
        ttk.Label(self.formulario, text="Situação").grid(
            row=linha, column=0, sticky="w", padx=(0, 15), pady=5
        )
        self.campo_situacao = ttk.Combobox(self.formulario, values=SITUACOES, state="readonly")
        self.campo_situacao.grid(row=linha, column=1, sticky="ew", pady=5)
        botoes = ttk.Frame(self.cartao, style="Cartao.TFrame")
        botoes.pack(fill="x", pady=(20, 0))
        ttk.Button(botoes, text="Cancelar", command=lambda: self.app.mostrar("atualizar")).pack(
            side="left"
        )
        ttk.Button(
            botoes, text="Salvar alterações", style="Primario.TButton", command=self.salvar
        ).pack(side="right")

    def carregar(self, pedido):
        self.id_pedido = pedido[0]
        self.formulario.preencher(pedido[1:7])
        self.campo_situacao.set(pedido[7])

    def ao_mostrar(self):
        self.formulario.focar()

    def salvar(self):
        valores = self.formulario.valores()
        situacao = self.campo_situacao.get()
        if not all(valores) or not situacao:
            messagebox.showerror("Erro", "Preencha todos os campos!")
            return
        try:
            self.app.banco.atualizar_pedido(self.id_pedido, *valores, situacao)
        except sqlite3.IntegrityError:
            messagebox.showerror("Erro", "Já existe outro pedido com essa placa!")
            return
        messagebox.showinfo("Sucesso", "Pedido atualizado!")
        self.app.mostrar("atualizar")
