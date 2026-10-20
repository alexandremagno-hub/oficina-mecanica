import tkinter as tk

from banco import Banco
from estilos import COR_FUNDO, aplicar_estilos
from telas import TelaLogin, TelaMenu, TelaCadastro, TelaExibir

# Janela principal: guarda o banco e troca entre as páginas
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PROTÓTIPO OFICINA MECÂNICA")
        self.minsize(800, 500)
        self.configure(bg=COR_FUNDO)
        aplicar_estilos()

        self.banco = Banco()
        self.paginas = {
            "login": TelaLogin(self),
            "menu": TelaMenu(self),
            "cadastro": TelaCadastro(self),
            "exibir": TelaExibir(self),
        }
        self.pagina_atual = None
        self.protocol("WM_DELETE_WINDOW", self.encerrar)
        self.mostrar("login")

    # Esconder a página atual e mostrar outra
    def mostrar(self, nome):
        if self.pagina_atual is not None:
            self.pagina_atual.pack_forget()
        self.pagina_atual = self.paginas[nome]
        self.pagina_atual.pack(fill="both", expand=True)
        self.pagina_atual.ao_mostrar()

    def encerrar(self):
        self.banco.fechar()
        self.destroy()
