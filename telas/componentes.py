import re
import tkinter as tk
from tkinter import ttk, messagebox

from moeda import texto_para_centavos, formatar_reais

# Partículas que ficam em minúsculo no meio de nomes ("Maria da Silva")
PARTICULAS = {"da", "das", "de", "di", "do", "dos", "du", "e"}

# CPF só com os números ("123.456.789-00" -> "12345678900"); None se não tiver 11 números
def normalizar_cpf(texto):
    cpf = re.sub(r"[.\-]", "", texto)
    return cpf if re.fullmatch(r"\d{11}", cpf) else None

# CPF com pontos e hífen para exibição: "12345678900" -> "123.456.789-00"
def formatar_cpf(cpf):
    if len(cpf) != 11 or not cpf.isdigit():
        return cpf
    return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"

# Nome com iniciais maiúsculas, mantendo partículas em minúsculo: "MARIA DA SILVA" -> "Maria da Silva"
def formatar_nome(texto):
    palavras = texto.split()
    return " ".join(
        palavra.lower() if indice > 0 and palavra.lower() in PARTICULAS else palavra.title()
        for indice, palavra in enumerate(palavras)
    )

# Data ISO do banco para exibição: "2026-10-20" -> "20/10/2026"
def formatar_data(data):
    if not data:
        return "—"
    ano, mes, dia = data.split("-")
    return f"{dia}/{mes}/{ano}"

# Tabela com rolagem que lista os pedidos; clicar no cabeçalho ordena pela coluna
class TabelaPedidos(ttk.Frame):
    colunas = [
        ("id", "Nº", 50),
        ("cpf", "CPF", 115),
        ("nome", "Cliente", 140),
        ("veiculo", "Veículo", 110),
        ("placa", "Placa", 80),
        ("servico", "Serviço", 140),
        ("valor", "Valor (R$)", 80),
        ("situacao", "Situação", 90),
        ("entrada", "Entrada", 85),
        ("entrega", "Entrega", 85),
    ]

    def __init__(self, pai, altura=10):
        super().__init__(pai, style="Cartao.TFrame")
        self.pedidos = []
        self.ordem = None  # (índice da coluna, decrescente)
        self.tabela = ttk.Treeview(
            self, columns=[c[0] for c in self.colunas], show="headings", height=altura,
            selectmode="browse",
        )
        for indice, (coluna, titulo, largura) in enumerate(self.colunas):
            self.tabela.heading(coluna, text=titulo, command=lambda i=indice: self.ordenar(i))
            self.tabela.column(
                coluna,
                width=largura,
                anchor="center" if coluna in ("id", "placa", "situacao", "entrada", "entrega") else "w",
            )
        rolagem_vertical = ttk.Scrollbar(self, orient="vertical", command=self.tabela.yview)
        rolagem_horizontal = ttk.Scrollbar(self, orient="horizontal", command=self.tabela.xview)
        self.tabela.configure(
            yscrollcommand=rolagem_vertical.set, xscrollcommand=rolagem_horizontal.set
        )
        self.tabela.grid(row=0, column=0, sticky="nsew")
        rolagem_vertical.grid(row=0, column=1, sticky="ns")
        rolagem_horizontal.grid(row=1, column=0, sticky="ew")
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.tabela.bind("<Button-1>", self._clique)
        self.tabela.bind("<Escape>", lambda _: self.desmarcar())

    # Clicar numa linha seleciona; clicar de novo nela ou numa área vazia tira a seleção.
    # A seleção é feita aqui (e não pelo Tk) para cliques seguidos não virarem clique duplo
    def _clique(self, evento):
        regiao = self.tabela.identify_region(evento.x, evento.y)
        linha = self.tabela.identify_row(evento.y)
        if regiao not in ("cell", "nothing"):
            return None
        self.tabela.focus_set()
        if regiao == "cell" and linha not in self.tabela.selection():
            self.tabela.selection_set(linha)
            self.tabela.focus(linha)
        else:
            self.desmarcar()
        return "break"

    def desmarcar(self):
        self.tabela.selection_remove(self.tabela.selection())

    # Mostrar os pedidos (tuplas na ordem de banco.COLUNAS), mantendo a ordenação escolhida
    def carregar(self, pedidos):
        self.pedidos = list(pedidos)
        self._exibir()

    # Ordenar pela coluna clicada; clicar de novo inverte a ordem
    def ordenar(self, indice):
        decrescente = self.ordem == (indice, False)
        self.ordem = (indice, decrescente)
        for i, (coluna, titulo, _) in enumerate(self.colunas):
            seta = (" ▼" if decrescente else " ▲") if i == indice else ""
            self.tabela.heading(coluna, text=titulo + seta)
        self._exibir()

    # Ordena pelos valores do banco (centavos, datas AAAA-MM-DD), com os vazios sempre no fim
    def _ordenados(self):
        if self.ordem is None:
            return self.pedidos
        indice, decrescente = self.ordem
        preenchidos = [p for p in self.pedidos if p[indice] is not None]
        vazios = [p for p in self.pedidos if p[indice] is None]
        chave = lambda p: p[indice].lower() if isinstance(p[indice], str) else p[indice]
        return sorted(preenchidos, key=chave, reverse=decrescente) + vazios

    def _exibir(self):
        self.tabela.delete(*self.tabela.get_children())
        for pedido in self._ordenados():
            id_pedido, cpf, nome, veiculo, placa, servico, valor, situacao, entrada, entrega = pedido
            valores = (
                id_pedido, formatar_cpf(cpf), nome, veiculo, placa, servico, formatar_reais(valor),
                situacao, formatar_data(entrada), formatar_data(entrega),
            )
            self.tabela.insert("", tk.END, values=valores)

    # Pedido da linha selecionada, já formatado para exibição
    # (id, cpf, nome, veiculo, placa, servico, valor, situacao, entrada, entrega)
    def selecionado(self):
        selecao = self.tabela.selection()
        if not selecao:
            return None
        return self.tabela.item(selecao[0], "values")

# Formulário com os dados do pedido
class FormularioPedido(ttk.Frame):
    rotulos = [
        "CPF do cliente",
        "Nome do cliente",
        "Modelo do veículo",
        "Placa do veículo",
        "Serviço solicitado",
        "Valor do serviço (R$)",
    ]

    def __init__(self, pai):
        super().__init__(pai, style="Cartao.TFrame")
        self.campos = []
        for linha, rotulo in enumerate(self.rotulos):
            ttk.Label(self, text=rotulo).grid(row=linha, column=0, sticky="w", padx=(0, 15), pady=5)
            campo = ttk.Entry(self, width=32)
            campo.grid(row=linha, column=1, sticky="ew", pady=5)
            self.campos.append(campo)
        # CPF aceita só números, além de ponto e hífen para quem digitar já formatado
        self.campos[0].configure(
            validate="key", validatecommand=(self.register(self._cpf_permitido), "%P")
        )

    @staticmethod
    def _cpf_permitido(texto):
        return re.fullmatch(r"[\d.\-]{0,14}", texto) is not None

    # Valores digitados (cpf, nome, veiculo, placa, servico, valor)
    def valores(self):
        return tuple(campo.get().strip() for campo in self.campos)

    # Valores prontos para o banco (CPF só com números, valor em centavos);
    # mostra o erro e devolve None se houver problema
    def valores_validados(self):
        cpf, nome, veiculo, placa, servico, valor = self.valores()
        if not all((cpf, nome, veiculo, placa, servico, valor)):
            messagebox.showerror("Erro", "Preencha todos os campos!")
            return None
        cpf_normalizado = normalizar_cpf(cpf)
        if cpf_normalizado is None:
            messagebox.showerror("Erro", "CPF inválido! Digite os 11 números do CPF.")
            return None
        centavos = texto_para_centavos(valor)
        if centavos is None:
            messagebox.showerror("Erro", "Valor inválido! Use, por exemplo, 1500 ou 1.500,00.")
            return None
        return cpf_normalizado, formatar_nome(nome), veiculo, placa, servico, centavos

    def preencher(self, valores):
        self.limpar()
        for campo, valor in zip(self.campos, valores):
            campo.insert(0, valor)

    def limpar(self):
        for campo in self.campos:
            campo.delete(0, tk.END)

    def focar(self):
        self.campos[0].focus_set()
