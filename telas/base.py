from tkinter import ttk

# Página com fundo azul e um cartão branco centralizado
class Pagina(ttk.Frame):
    titulo = ""
    subtitulo = ""

    def __init__(self, app):
        super().__init__(app, style="Fundo.TFrame")
        self.app = app
        self.cartao = ttk.Frame(self, style="Cartao.TFrame", padding=30)
        self.cartao.place(relx=0.5, rely=0.5, anchor="center")
        ttk.Label(self.cartao, text=self.titulo, style="Titulo.TLabel").pack(anchor="w")
        ttk.Label(self.cartao, text=self.subtitulo, style="Subtitulo.TLabel").pack(
            anchor="w", pady=(2, 20)
        )

    # Chamado sempre que a página é exibida
    def ao_mostrar(self):
        pass
