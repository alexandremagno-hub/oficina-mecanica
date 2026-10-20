from tkinter import ttk, messagebox

from banco import SITUACOES
from telas.base import Pagina
from telas.componentes import FormularioPedido

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
        ttk.Button(botoes, text="Cancelar", command=lambda: self.app.mostrar("pedidos")).pack(
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
        valores = self.formulario.valores_validados()
        if valores is None:
            return
        situacao = self.campo_situacao.get()
        if not situacao:
            messagebox.showerror("Erro", "Preencha todos os campos!")
            return
        self.app.banco.atualizar_pedido(self.id_pedido, *valores, situacao)
        messagebox.showinfo("Sucesso", "Pedido atualizado!")
        self.app.mostrar("pedidos")
