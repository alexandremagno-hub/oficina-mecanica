import sqlite3
from datetime import date

import pandas as pd
import streamlit as st

from banco import COLUNAS_FUNCIONARIOS
from formatos import formatar_nome, validar_funcionario, validar_senha
from paginas.formulario import avisar, pergunta
from paginas.ordens import formatar_data

# Funções sugeridas na lista; dá para digitar outra
FUNCOES = ["Mecânico", "Eletricista", "Funileiro", "Pintor", "Atendente", "Gerente"]

# Campos do cadastro vazios, guardados em st.session_state["novo_<campo>"]
def campos_novo_vazios():
    return {
        "nome": "", "usuario": "", "funcao": None, "admissao": date.today(), "senha": "",
        "confirmacao": "", "erro": None,
    }

# Campos da edição, guardados em st.session_state["editar_func_<campo>_<id>"]
CAMPOS_EDICAO = ["nome", "funcao", "admissao", "ativo", "senha", "confirmacao"]

def carregar_funcionarios():
    return pd.DataFrame(
        st.session_state.banco.listar_funcionarios(),
        columns=[c.strip() for c in COLUNAS_FUNCIONARIOS.split(",")],
    )

def texto(chave):
    return (st.session_state.get(chave) or "").strip()

def data_iso(chave):
    escolhida = st.session_state.get(chave)
    return escolhida.isoformat() if escolhida else None

# A seleção da tabela é por posição da linha; ao incluir ou alterar alguém a ordem pode mudar,
# então a tabela ganha uma chave nova e volta sem nada selecionado
def recomecar_tabela():
    st.session_state.versao_tabela = st.session_state.get("versao_tabela", 0) + 1

# Gravar o funcionário novo; roda antes de a página ser redesenhada, então pode limpar os campos
def cadastrar():
    valores, erro = validar_funcionario(
        texto("novo_usuario"), texto("novo_nome"), texto("novo_funcao"),
        st.session_state.novo_senha, st.session_state.novo_confirmacao,
    )
    if valores is None:
        st.session_state.novo_erro = erro
        return
    usuario, nome, funcao, senha = valores
    try:
        st.session_state.banco.cadastrar_funcionario(
            usuario, nome, funcao, data_iso("novo_admissao"), senha
        )
    except sqlite3.IntegrityError:
        st.session_state.novo_erro = f"Já existe um funcionário com o usuário {usuario}."
        return
    limpar_novo()
    recomecar_tabela()
    avisar(f"{nome} cadastrado!")

# O navegador mantém o que foi digitado se o campo só for apagado do estado; por isso os
# campos recebem os valores vazios
def limpar_novo():
    for campo, valor in campos_novo_vazios().items():
        st.session_state[f"novo_{campo}"] = valor

def formulario_novo():
    # Valores iniciais pelo estado (e não por value=/index=), já que limpar_novo também os define
    for campo, valor in campos_novo_vazios().items():
        st.session_state.setdefault(f"novo_{campo}", valor)
    with st.form("novo_funcionario"):
        st.subheader("Novo funcionário")
        st.text_input("Nome", key="novo_nome", placeholder="Ex.: Maria da Silva")
        usuario, funcao = st.columns(2)
        usuario.text_input("Usuário de acesso", key="novo_usuario", placeholder="Ex.: maria")
        funcao.selectbox(
            "Função", FUNCOES, key="novo_funcao", accept_new_options=True,
            placeholder="Escolha ou digite",
        )
        st.date_input("Data de admissão", key="novo_admissao", format="DD/MM/YYYY")
        senha, confirmacao = st.columns(2)
        senha.text_input("Senha", type="password", key="novo_senha")
        confirmacao.text_input("Confirmar senha", type="password", key="novo_confirmacao")
        if erro := st.session_state.get("novo_erro"):
            st.error(erro, icon=":material/error:")
        st.form_submit_button(
            "Cadastrar", type="primary", icon=":material/person_add:", on_click=cadastrar
        )

# Ao clicar em salvar, nada é gravado ainda: guarda o que foi digitado e pergunta antes
def salvar(funcionario):
    id_funcionario = int(funcionario.id)
    chave = lambda campo: f"editar_func_{campo}_{id_funcionario}"
    nome, funcao = texto(chave("nome")), texto(chave("funcao"))
    senha = st.session_state[chave("senha")]
    erro = None
    if not nome or not funcao:
        erro = "Preencha o nome e a função!"
    elif senha or st.session_state[chave("confirmacao")]:
        erro = validar_senha(senha, st.session_state[chave("confirmacao")])
    st.session_state[chave("erro")] = erro
    if erro:
        return
    dados = (formatar_nome(nome), funcao, data_iso(chave("admissao")),
             st.session_state[chave("ativo")], senha or None)
    situacao = lambda ativo: "Ativo" if ativo else "Inativo"
    antes = [
        ("Nome", funcionario.nome, dados[0]),
        ("Função", funcionario.funcao, dados[1]),
        ("Admissão", formatar_data(funcionario.data_admissao if pd.notna(funcionario.data_admissao) else ""),
         formatar_data(dados[2] or "")),
        ("Situação", situacao(funcionario.ativo), situacao(dados[3])),
    ]
    mudancas = [(campo, a, d) for campo, a, d in antes if a != d]
    if senha:
        mudancas.append(("Senha", "atual", "nova senha"))
    if not mudancas:
        fechar_edicao(id_funcionario)
        avisar(f"Nenhuma alteração feita em {funcionario.nome}.")
        return
    st.session_state[chave("pendente")] = {
        "dados": dados, "mudancas": mudancas,
        "digitado": {campo: st.session_state[chave(campo)] for campo in CAMPOS_EDICAO},
    }

# Cancelar a confirmação volta para o formulário com o que tinha sido digitado (o Streamlit
# descarta os campos enquanto eles não aparecem na tela)
def voltar_edicao(id_funcionario):
    pendente = st.session_state.pop(f"editar_func_pendente_{id_funcionario}")
    for campo, valor in pendente["digitado"].items():
        st.session_state[f"editar_func_{campo}_{id_funcionario}"] = valor

def gravar(id_funcionario):
    dados = st.session_state[f"editar_func_pendente_{id_funcionario}"]["dados"]
    st.session_state.banco.atualizar_funcionario(id_funcionario, *dados)
    fechar_edicao(id_funcionario)
    avisar(f"Dados de {dados[0]} atualizados!")

# Descarta o que foi digitado e a confirmação pendente (também ao fechar a janela no X ou
# clicando fora); da próxima vez os campos voltam com os dados do banco
def descartar_edicao():
    for chave in [c for c in st.session_state if str(c).startswith("editar_func_")]:
        del st.session_state[chave]
    recomecar_tabela()

# Fecha a janela de edição ao gravar ou cancelar
def fechar_edicao(id_funcionario=None):
    descartar_edicao()
    st.session_state.fechar_funcionario = True

def pendente(id_funcionario):
    return st.session_state.get(f"editar_func_pendente_{id_funcionario}")

# Janela pequena, no meio da tela, que pergunta antes de gravar. Ao cancelar ou confirmar,
# recarrega a página para voltar à edição ou fechar
@st.dialog("Confirmar alteração", on_dismiss=descartar_edicao)
def confirmacao(funcionario):
    id_funcionario = int(funcionario.id)
    if st.session_state.pop("fechar_funcionario", False) or not pendente(id_funcionario):
        st.rerun()
    pergunta(
        f"Quer mesmo fazer estas alterações em **{funcionario.nome}**?",
        pendente(id_funcionario)["mudancas"], voltar_edicao, gravar, (id_funcionario,),
    )

# Janela por cima da página com a edição do funcionário escolhido na tabela; fechá-la
# desfaz a seleção da tabela
@st.dialog("Editar funcionário", width="large", on_dismiss=descartar_edicao)
def formulario_edicao(funcionario):
    # Depois de gravar ou cancelar, fecha a janela recarregando a página inteira
    if st.session_state.pop("fechar_funcionario", False):
        st.rerun()
    id_funcionario = int(funcionario.id)
    chave = lambda campo: f"editar_func_{campo}_{id_funcionario}"
    # Ao pedir a confirmação, recarrega a página para ela trocar esta janela pela pequena
    if pendente(id_funcionario):
        st.rerun()

    # Valores iniciais pelo estado (e não por value=/index=), já que voltar_edicao também os define
    iniciais = {
        "nome": funcionario.nome, "funcao": funcionario.funcao,
        "admissao": date.fromisoformat(funcionario.data_admissao)
        if pd.notna(funcionario.data_admissao) else None,
        "ativo": bool(funcionario.ativo), "senha": "", "confirmacao": "",
    }
    for campo, valor in iniciais.items():
        st.session_state.setdefault(chave(campo), valor)
    # Quem está usando o sistema não pode se desativar, para não ficar sem acesso
    eu_mesmo = funcionario.usuario == st.session_state.get("usuario")
    funcoes = list(dict.fromkeys(FUNCOES + [funcionario.funcao, st.session_state[chave("funcao")]]))
    with st.form(f"editar_funcionario_{id_funcionario}", border=False):
        st.subheader(funcionario.nome)
        st.caption(f"Usuário de acesso: **{funcionario.usuario}**")
        st.text_input("Nome", key=chave("nome"))
        funcao, admissao = st.columns(2)
        funcao.selectbox("Função", funcoes, key=chave("funcao"), accept_new_options=True)
        admissao.date_input("Data de admissão", key=chave("admissao"), format="DD/MM/YYYY")
        st.toggle(
            "Ativo", key=chave("ativo"), disabled=eu_mesmo,
            help="Você não pode desativar a própria conta" if eu_mesmo
            else "Funcionários inativos não conseguem entrar no sistema",
        )
        st.markdown("**Trocar senha** (deixe em branco para manter a atual)")
        senha, confirmacao = st.columns(2)
        senha.text_input("Nova senha", type="password", key=chave("senha"))
        confirmacao.text_input("Confirmar nova senha", type="password", key=chave("confirmacao"))
        if erro := st.session_state.get(chave("erro")):
            st.error(erro, icon=":material/error:")
        # Cancelar fecha a janela sem gravar nada (para quem clicou na linha sem querer)
        cancelar, salvar_botao = st.columns(2)
        cancelar.form_submit_button(
            "Cancelar", icon=":material/close:", width="stretch",
            on_click=fechar_edicao, args=(id_funcionario,),
        )
        salvar_botao.form_submit_button(
            "Salvar alterações", type="primary", icon=":material/save:", width="stretch",
            on_click=salvar, args=(funcionario,),
        )

# Tabela dos funcionários; devolve o que foi selecionado (ou None)
def tabela(funcionarios):
    selecao = st.dataframe(
        pd.DataFrame({
            "Nome": funcionarios["nome"],
            "Usuário": funcionarios["usuario"],
            "Função": funcionarios["funcao"],
            "Admissão": funcionarios["data_admissao"].fillna("").map(formatar_data),
            "Situação": funcionarios["ativo"].map({1: "🟢 Ativo", 0: "⚪ Inativo"}),
            "Acesso": funcionarios["admin"].map({1: "Administrador", 0: "Funcionário"}),
        }),
        hide_index=True, width="stretch", on_select="rerun", selection_mode="single-row",
        key=f"tabela_funcionarios_{st.session_state.get('versao_tabela', 0)}",
    )
    linhas = selecao.selection.rows
    return next(funcionarios.iloc[linhas].itertuples()) if linhas else None

# Página de cadastro dos funcionários, que também são as contas de acesso ao sistema
def mostrar():
    st.title("Funcionários")
    st.caption("Cada funcionário ativo entra no sistema com o próprio usuário e senha")

    funcionarios = carregar_funcionarios()
    lista, novo = st.columns([3, 2])
    with lista:
        ativos = int(funcionarios["ativo"].sum())
        st.subheader("Equipe")
        st.caption(f"{ativos} ativos de {len(funcionarios)} · clique numa linha para editar")
        funcionario = tabela(funcionarios)
        if funcionario is not None:
            if pendente(int(funcionario.id)):
                confirmacao(funcionario)
            else:
                formulario_edicao(funcionario)
    with novo:
        formulario_novo()
