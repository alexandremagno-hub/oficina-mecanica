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

# Tabela com rolagem que lista os pedidos
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
        self.tabela = ttk.Treeview(
            self, columns=[c[0] for c in self.colunas], show="headings", height=altura,
            selectmode="browse",
        )
        for coluna, titulo, largura in self.colunas:
            self.tabela.heading(coluna, text=titulo)
            self.tabela.column(
                coluna,
                width=largura,
                anchor="center" if coluna in ("id", "placa", "situacao", "entrada", "entrega") else "w",
            )
        barra_rolagem = ttk.Scrollbar(self, orient="vertical", command=self.tabela.yview)
        self.tabela.configure(yscrollcommand=barra_rolagem.set)
        self.tabela.pack(side="left", fill="both", expand=True)
        barra_rolagem.pack(side="right", fill="y")

    def carregar(self, pedidos):
        self.tabela.delete(*self.tabela.get_children())
        for pedido in pedidos:
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
