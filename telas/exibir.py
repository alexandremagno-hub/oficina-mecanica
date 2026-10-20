from tkinter import ttk

from telas.base import Pagina
from telas.componentes import TabelaPedidos

# Página de exibição dos pedidos
class TelaExibir(Pagina):
    titulo = "Pedidos"
    subtitulo = "Todos os pedidos cadastrados"

    def __init__(self, app):
        super().__init__(app)
        self.tabela = TabelaPedidos(self.cartao)
        self.tabela.pack(fill="both", expand=True)
        ttk.Button(self.cartao, text="Voltar ao menu", command=lambda: self.app.mostrar("menu")).pack(
            anchor="w", pady=(20, 0)
        )

    # Recarregar os pedidos sempre que a página é aberta
    def ao_mostrar(self):
        self.tabela.carregar(self.app.banco.listar_pedidos())
