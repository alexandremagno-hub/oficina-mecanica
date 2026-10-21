import pandas as pd
import streamlit as st

from banco import COLUNAS, ENTREGUE, SITUACOES
from formatos import corresponde, formatar_cpf
from moeda import formatar_reais
from paginas.formulario import (
    avisar, campos_pedido, mostrar_erro, preencher, valores_validados,
)
from paginas.valores import formulario_valores, resumo_valores

PREFIXO = "editar"

# Ícone de cada situação na tabela e nos filtros (situações antigas fora da lista usam ⚫)
ICONES = {"Na fila": "🟡", "Em andamento": "🔵", "Concluído": "🟢", "Entregue": "⚪"}

TITULOS = {
    "id": "Nº OS", "cpf": "CPF", "nome": "Cliente", "veiculo": "Veículo", "placa": "Placa",
    "servico": "Serviço", "valor": "Valor (R$)", "situacao": "Situação",
    "data_entrada": "Entrada", "data_entrega": "Entrega",
}

def com_icone(situacao):
    return f"{ICONES.get(situacao, '⚫')} {situacao}"

# Data ISO do banco para exibição: "2026-10-20" -> "20/10/2026"
def formatar_data(data):
    if not data:
        return "—"
    ano, mes, dia = data.split("-")
    return f"{dia}/{mes}/{ano}"

# Pedidos do banco numa tabela do pandas. As datas ficam no formato AAAA-MM-DD, que já
# ordena certo, e as vazias viram "" porque o Streamlit mostraria "None" nas células nulas
def carregar_pedidos():
    pedidos = pd.DataFrame(
        st.session_state.banco.listar_pedidos(), columns=[c.strip() for c in COLUNAS.split(",")]
    )
    for coluna in ("data_entrada", "data_entrega"):
        pedidos[coluna] = pedidos[coluna].fillna("")
    return pedidos

# Trocar a chave da tabela faz ela ser recriada sem nenhuma linha selecionada
def reiniciar_tabela():
    st.session_state.versao_tabela = st.session_state.get("versao_tabela", 0) + 1

# Indicadores por situação e total já faturado
def resumo(pedidos):
    contagem = pedidos["situacao"].value_counts()
    colunas = st.columns(len(SITUACOES) + 1)
    for coluna, situacao in zip(colunas, SITUACOES):
        coluna.metric(com_icone(situacao), int(contagem.get(situacao, 0)), border=True)
    faturado = int(pedidos.loc[pedidos["situacao"] == ENTREGUE, "valor"].sum())
    colunas[-1].metric("💰 Faturado (R$)", formatar_reais(faturado), border=True)

# Valor em reais para exibição, ou "—" se o serviço ainda não foi concluído
def formatar_valor(centavos):
    return formatar_reais(int(centavos)) if pd.notna(centavos) and centavos >= 0 else "—"

# Tabela com as OS visíveis; devolve a OS selecionada (ou None).
# O Styler só muda o que aparece: a ordenação ao clicar no cabeçalho usa os valores do banco.
# Valores vazios viram -1 só na tabela, porque o Streamlit mostraria "None" nas células nulas
def tabela(visiveis):
    estilo = visiveis.fillna({"valor": -1}).style.format({
        "cpf": formatar_cpf,
        "valor": formatar_valor,
        "situacao": com_icone,
        "data_entrada": formatar_data,
        "data_entrega": formatar_data,
    })
    ids = tuple(visiveis["id"])
    evento = st.dataframe(
        estilo,
        hide_index=True,
        width="stretch",
        column_config=TITULOS,
        column_order=list(TITULOS),
        on_select="rerun",
        selection_mode="single-row",
        # Mudar a busca ou o filtro também recria a tabela, para a seleção não apontar para outra OS
        key=f"tabela_{st.session_state.get('versao_tabela', 0)}_{hash(ids)}",
    )
    linhas = evento.selection.rows
    return visiveis.iloc[linhas[0]] if linhas else None

def salvar(id_pedido):
    valores = valores_validados(PREFIXO)
    if valores is None:
        return
    st.session_state.banco.atualizar_pedido(id_pedido, *valores)
    reiniciar_tabela()
    avisar(f"OS nº {id_pedido} atualizada!")

# Corrigir a mão de obra e as peças de uma OS já concluída
@st.dialog("Valores do serviço", width="large")
def alterar_valores(pedido):
    if formulario_valores(pedido, "Salvar valores", ":material/save:"):
        reiniciar_tabela()
        avisar(f"Valores da OS nº {int(pedido['id'])} atualizados!")
        st.rerun()

@st.dialog("Excluir ordem de serviço")
def confirmar_exclusao(id_pedido, nome, placa):
    st.write(f"Excluir a OS nº **{id_pedido}** de **{nome}** (placa {placa})?")
    st.caption("Essa ação não pode ser desfeita.")
    cancelar, excluir = st.columns(2)
    if cancelar.button("Cancelar", width="stretch"):
        st.rerun()
    if excluir.button("Excluir", type="primary", icon=":material/delete:", width="stretch"):
        st.session_state.banco.excluir_pedido(id_pedido)
        reiniciar_tabela()
        avisar(f"OS nº {id_pedido} excluída!")
        st.rerun()

# Formulário de edição e botão de exclusão da OS selecionada
def painel(pedido):
    id_pedido = int(pedido["id"])
    # Preenche os campos só quando outra OS é selecionada, para não apagar o que foi digitado
    if st.session_state.get(f"{PREFIXO}_id") != id_pedido:
        st.session_state[f"{PREFIXO}_id"] = id_pedido
        st.session_state[f"{PREFIXO}_erro"] = None
        preencher(PREFIXO, (
            formatar_cpf(pedido["cpf"]), pedido["nome"], pedido["veiculo"], pedido["placa"],
            pedido["servico"],
        ))

    with st.container(border=True):
        titulo, excluir = st.columns([4, 1], vertical_alignment="center")
        titulo.subheader(f"OS nº {id_pedido} · {pedido['nome']}")
        if excluir.button("Excluir", icon=":material/delete:", width="stretch"):
            confirmar_exclusao(id_pedido, pedido["nome"], pedido["placa"])
        with st.form(f"form_{PREFIXO}", border=False):
            campos_pedido(PREFIXO)
            mostrar_erro(PREFIXO)
            st.form_submit_button(
                "Salvar alterações", type="primary", icon=":material/save:",
                on_click=salvar, args=(id_pedido,),
            )
        # Os valores são informados ao concluir o serviço e podem ser corrigidos depois
        if pd.notna(pedido["valor"]):
            st.markdown("**Valores do serviço**")
            st.markdown(resumo_valores(pedido))
            if st.button("Alterar valores", icon=":material/edit:"):
                alterar_valores(pedido.to_dict())
        st.caption(
            f"Situação: {com_icone(pedido['situacao'])} (mude na página Andamento) · "
            f"Entrada: {formatar_data(pedido['data_entrada'])} · "
            f"Entrega: {formatar_data(pedido['data_entrega'])}"
        )

# Página com a lista de ordens de serviço: resumo, busca, filtro por situação, edição e exclusão
def mostrar():
    from navegacao import ABRIR

    titulo, botao = st.columns([4, 1], vertical_alignment="bottom")
    titulo.title("Ordens de serviço")
    if botao.button("Abrir OS", type="primary", icon=":material/add:", width="stretch"):
        st.switch_page(ABRIR)

    pedidos = carregar_pedidos()
    if pedidos.empty:
        st.info("Nenhuma ordem de serviço cadastrada ainda.", icon=":material/info:")
        return
    resumo(pedidos)

    busca, filtro = st.columns([2, 3], vertical_alignment="bottom")
    termo = busca.text_input(
        "Buscar", placeholder="Nome, placa ou CPF", icon=":material/search:"
    )
    extras = sorted(set(pedidos["situacao"]) - set(SITUACOES))
    escolhidas = filtro.pills(
        "Situação", SITUACOES + extras, selection_mode="multi", format_func=com_icone,
    )
    mascara = [
        (not escolhidas or p.situacao in escolhidas) and corresponde(termo, p.cpf, p.nome, p.placa)
        for p in pedidos.itertuples()
    ]
    visiveis = pedidos[pd.Series(mascara, index=pedidos.index, dtype=bool)].reset_index(drop=True)

    pedido = tabela(visiveis)
    st.caption(
        f"{len(visiveis)} de {len(pedidos)} OS · clique no cabeçalho para ordenar · "
        "selecione uma linha para editar ou excluir"
    )
    if pedido is not None:
        painel(pedido)
