from tkinter import ttk

# Página com fundo azul e um cartão branco centralizado
# (com expandir = True, o cartão ocupa quase toda a janela e cresce junto com ela)
class Pagina(ttk.Frame):
    titulo = ""
    subtitulo = ""
    expandir = False

    def __init__(self, app):
        super().__init__(app, style="Fundo.TFrame")
        self.app = app
        self.cartao = ttk.Frame(self, style="Cartao.TFrame", padding=30)
        if self.expandir:
            self.cartao.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.95, relheight=0.92)
        else:
            self.cartao.place(relx=0.5, rely=0.5, anchor="center")
        ttk.Label(self.cartao, text=self.titulo, style="Titulo.TLabel").pack(anchor="w")
        ttk.Label(self.cartao, text=self.subtitulo, style="Subtitulo.TLabel").pack(
            anchor="w", pady=(2, 20)
        )

    # Chamado sempre que a página é exibida
    def ao_mostrar(self):
        pass
