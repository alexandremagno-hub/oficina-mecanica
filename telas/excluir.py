from tkinter import ttk, messagebox

from telas.base import Pagina
from telas.componentes import TabelaPedidos

# Página de exclusão de pedido
class TelaExcluir(Pagina):
    titulo = "Excluir pedido"
    subtitulo = "Selecione o pedido que deseja excluir"

    def __init__(self, app):
        super().__init__(app)
        self.tabela = TabelaPedidos(self.cartao)
        self.tabela.pack(fill="both", expand=True)
        botoes = ttk.Frame(self.cartao, style="Cartao.TFrame")
        botoes.pack(fill="x", pady=(20, 0))
        ttk.Button(botoes, text="Voltar ao menu", command=lambda: self.app.mostrar("menu")).pack(
            side="left"
        )
        ttk.Button(
            botoes, text="Excluir selecionado", style="Perigo.TButton", command=self.excluir
        ).pack(side="right")

    def ao_mostrar(self):
        self.tabela.carregar(self.app.banco.listar_pedidos())

    # Pedir confirmação e remover o pedido selecionado
    def excluir(self):
        pedido = self.tabela.selecionado()
        if pedido is None:
            messagebox.showwarning("Atenção", "Selecione um pedido na tabela!")
            return
        id_pedido, nome, placa = pedido[0], pedido[2], pedido[4]
        confirmar = messagebox.askyesno(
            "Confirmar exclusão",
            f"Excluir o pedido nº {id_pedido} de {nome} (placa {placa})?\n"
            "Essa ação não pode ser desfeita.",
        )
        if not confirmar:
            return
        self.app.banco.excluir_pedido(id_pedido)
        self.ao_mostrar()
        messagebox.showinfo("Sucesso", "Pedido excluído!")
