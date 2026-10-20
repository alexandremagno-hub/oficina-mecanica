import re
import unicodedata
from tkinter import ttk, messagebox

from banco import SITUACOES
from telas.base import Pagina
from telas.componentes import TabelaPedidos, CampoComDica

TODAS = "Todas as situações"

# Texto em minúsculo e sem acentos, para a busca: "João" -> "joao"
def simplificar(texto):
    sem_acento = unicodedata.normalize("NFD", texto).encode("ascii", "ignore").decode()
    return sem_acento.lower()

# Página com a lista de ordens de serviço: busca, filtro por situação, cadastro, edição e exclusão
class TelaPedidos(Pagina):
    titulo = "Ordens de serviço"
    subtitulo = "Busque, abra, edite ou exclua ordens de serviço"
    expandir = True

    def __init__(self, app):
        super().__init__(app)
        self.pedidos = []

        filtros = ttk.Frame(self.cartao, style="Cartao.TFrame")
        filtros.pack(fill="x", pady=(0, 10))
        ttk.Label(filtros, text="Buscar").pack(side="left")
        self.busca = CampoComDica(filtros, "Nome, placa ou CPF", width=36)
        self.busca.variavel.trace_add("write", lambda *_: self.filtrar())
        self.busca.pack(side="left", padx=(8, 20))
        ttk.Label(filtros, text="Situação").pack(side="left")
        self.campo_situacao = ttk.Combobox(filtros, state="readonly", width=20)
        self.campo_situacao.set(TODAS)
        self.campo_situacao.bind("<<ComboboxSelected>>", lambda _: self.filtrar())
        self.campo_situacao.pack(side="left", padx=(8, 0))

        # Botões vêm antes da tabela para não sumirem quando a janela for pequena
        botoes = ttk.Frame(self.cartao, style="Cartao.TFrame")
        botoes.pack(side="bottom", fill="x", pady=(20, 0))
        ttk.Button(botoes, text="Voltar ao menu", command=lambda: self.app.mostrar("menu")).pack(
            side="left"
        )
        self.contador = ttk.Label(botoes, style="Subtitulo.TLabel")
        self.contador.pack(side="left", padx=20)
        ttk.Button(botoes, text="Excluir", style="Perigo.TButton", command=self.excluir).pack(
            side="right"
        )
        ttk.Button(botoes, text="Editar", command=self.editar).pack(side="right", padx=8)
        ttk.Button(
            botoes, text="Abrir OS", style="Primario.TButton",
            command=lambda: self.app.mostrar("cadastro"),
        ).pack(side="right")

        self.tabela = TabelaPedidos(self.cartao)
        self.tabela.pack(fill="both", expand=True)

    # Recarregar os pedidos sempre que a página é aberta, mantendo busca e filtro
    def ao_mostrar(self):
        self.pedidos = self.app.banco.listar_pedidos()
        # Situações fora da lista padrão (de pedidos antigos) também aparecem no filtro
        extras = sorted({p[7] for p in self.pedidos} - set(SITUACOES))
        self.campo_situacao["values"] = [TODAS] + SITUACOES + extras
        self.filtrar()

    def filtrar(self):
        situacao = self.campo_situacao.get()
        visiveis = [
            p for p in self.pedidos
            if (situacao == TODAS or p[7] == situacao) and self._corresponde(p)
        ]
        self.tabela.carregar(visiveis)
        self.contador.configure(text=f"{len(visiveis)} de {len(self.pedidos)} OS")

    # Busca no nome (sem diferenciar acentos), na placa (ignorando hífen) e,
    # se só tiver números, no CPF
    def _corresponde(self, pedido):
        termo = simplificar(self.busca.texto().strip())
        if not termo:
            return True
        cpf, nome, placa = pedido[1], pedido[2], pedido[4]
        sem_hifen = lambda texto: re.sub(r"[-\s]", "", texto.lower())
        if termo in simplificar(nome) or sem_hifen(termo) in sem_hifen(placa):
            return True
        return re.fullmatch(r"[\d.\-\s]+", termo) is not None and re.sub(r"\D", "", termo) in cpf

    # Abrir o pedido selecionado na página de edição
    def editar(self):
        pedido = self.tabela.selecionado()
        if pedido is None:
            messagebox.showwarning("Atenção", "Selecione uma OS na tabela!")
            return
        self.app.paginas["editar"].carregar(pedido)
        self.app.mostrar("editar")

    # Pedir confirmação e remover o pedido selecionado
    def excluir(self):
        pedido = self.tabela.selecionado()
        if pedido is None:
            messagebox.showwarning("Atenção", "Selecione uma OS na tabela!")
            return
        id_pedido, nome, placa = pedido[0], pedido[2], pedido[4]
        confirmar = messagebox.askyesno(
            "Confirmar exclusão",
            f"Excluir a OS nº {id_pedido} de {nome} (placa {placa})?\n"
            "Essa ação não pode ser desfeita.",
        )
        if not confirmar:
            return
        self.app.banco.excluir_pedido(id_pedido)
        self.ao_mostrar()
        messagebox.showinfo("Sucesso", "OS excluída!")
