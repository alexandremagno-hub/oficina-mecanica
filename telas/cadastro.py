from tkinter import ttk, messagebox

from telas.base import Pagina
from telas.componentes import FormularioPedido

# Página de cadastro de pedido
class TelaCadastro(Pagina):
    titulo = "Novo pedido"
    subtitulo = "Insira os dados do pedido"

    def __init__(self, app):
        super().__init__(app)
        self.voltar_para = "menu"
        self.formulario = FormularioPedido(self.cartao)
        self.formulario.pack(fill="x")
        botoes = ttk.Frame(self.cartao, style="Cartao.TFrame")
        botoes.pack(fill="x", pady=(20, 0))
        ttk.Button(botoes, text="Voltar", command=lambda: self.app.mostrar(self.voltar_para)).pack(
            side="left"
        )
        ttk.Button(
            botoes, text="Cadastrar pedido", style="Primario.TButton", command=self.cadastrar
        ).pack(side="right")

    def ao_mostrar(self):
        self.voltar_para = self.app.nome_anterior
        self.formulario.focar()

    # Inserir todos os dados do pedido na tabela
    def cadastrar(self):
        valores = self.formulario.valores_validados()
        if valores is None:
            return
        self.app.banco.cadastrar_pedido(*valores)
        self.formulario.limpar()
        self.formulario.focar()
        messagebox.showinfo("Sucesso", "Pedido enviado!")
