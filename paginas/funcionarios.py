import sqlite3
from datetime import date

import pandas as pd
import streamlit as st

from banco import COLUNAS_FUNCIONARIOS
from formatos import formatar_nome, validar_funcionario, validar_senha
from paginas.formulario import avisar
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

# Gravar as alterações; os campos do funcionário são descartados para voltarem com os
# dados do banco da próxima vez que ele for aberto
def salvar(id_funcionario):
    chave = lambda campo: f"editar_func_{campo}_{id_funcionario}"
    nome, funcao = texto(chave("nome")), texto(chave("funcao"))
    senha = st.session_state[chave("senha")]
    erro = None
    if not nome or not funcao:
        erro = "Preencha o nome e a função!"
    elif senha or st.session_state[chave("confirmacao")]:
        erro = validar_senha(senha, st.session_state[chave("confirmacao")])
    if erro:
        st.session_state[chave("erro")] = erro
        return
    st.session_state.banco.atualizar_funcionario(
        id_funcionario, formatar_nome(nome), funcao, data_iso(chave("admissao")),
        st.session_state[chave("ativo")], senha or None,
    )
    for campo in CAMPOS_EDICAO + ["erro"]:
        st.session_state.pop(chave(campo), None)
    recomecar_tabela()
    avisar(f"Dados de {formatar_nome(nome)} atualizados!")

def formulario_edicao(funcionario):
    id_funcionario = int(funcionario.id)
    chave = lambda campo: f"editar_func_{campo}_{id_funcionario}"
    # Quem está usando o sistema não pode se desativar, para não ficar sem acesso
    eu_mesmo = funcionario.usuario == st.session_state.get("usuario")
    funcoes = FUNCOES if funcionario.funcao in FUNCOES else FUNCOES + [funcionario.funcao]
    with st.form(f"editar_funcionario_{id_funcionario}"):
        st.subheader(f"Editar {funcionario.nome}")
        st.caption(f"Usuário de acesso: **{funcionario.usuario}**")
        st.text_input("Nome", value=funcionario.nome, key=chave("nome"))
        funcao, admissao = st.columns(2)
        funcao.selectbox(
            "Função", funcoes, index=funcoes.index(funcionario.funcao), key=chave("funcao"),
            accept_new_options=True,
        )
        admissao.date_input(
            "Data de admissão", key=chave("admissao"), format="DD/MM/YYYY",
            value=date.fromisoformat(funcionario.data_admissao) if pd.notna(funcionario.data_admissao) else None,
        )
        st.toggle(
            "Ativo", value=bool(funcionario.ativo), key=chave("ativo"), disabled=eu_mesmo,
            help="Você não pode desativar a própria conta" if eu_mesmo
            else "Funcionários inativos não conseguem entrar no sistema",
        )
        st.markdown("**Trocar senha** (deixe em branco para manter a atual)")
        senha, confirmacao = st.columns(2)
        senha.text_input("Nova senha", type="password", key=chave("senha"))
        confirmacao.text_input("Confirmar nova senha", type="password", key=chave("confirmacao"))
        if erro := st.session_state.get(chave("erro")):
            st.error(erro, icon=":material/error:")
        st.form_submit_button(
            "Salvar alterações", type="primary", icon=":material/save:",
            on_click=salvar, args=(id_funcionario,),
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
            formulario_edicao(funcionario)
    with novo:
        formulario_novo()
