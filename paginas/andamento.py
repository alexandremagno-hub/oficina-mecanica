import pandas as pd
import streamlit as st

from banco import CONCLUIDO, ENTREGUE, SITUACOES
from paginas.formulario import avisar
from paginas.ordens import carregar_pedidos, com_icone, formatar_data, formatar_valor, responsaveis
from paginas.valores import formulario_valores

# Quantas OS entregues aparecem no quadro (as mais recentes); as demais ficam na lista de OS
LIMITE_ENTREGUES = 10

def mover(id_pedido, nome, situacao):
    st.session_state.banco.mudar_situacao(
        id_pedido, situacao, st.session_state.get("id_funcionario")
    )
    avisar(f"OS de {nome} → {situacao}")

# Ao concluir, pergunta a mão de obra e as peças colocadas (já preenchidas se a OS voltou de etapa)
@st.dialog("Concluir serviço", width="large")
def concluir(pedido):
    if formulario_valores(pedido, "Concluir", ":material/check:"):
        mover(int(pedido["id"]), pedido["nome"], CONCLUIDO)
        st.rerun()

# Cartão de uma OS com os botões para voltar e avançar uma etapa; o número é a posição do
# cartão na própria coluna (1, 2, 3…), não o número da OS
def cartao(pedido, etapa, posicao):
    id_pedido = int(pedido.id)
    with st.container(border=True):
        st.markdown(f"**{posicao}** · {pedido.nome}")
        st.caption(
            f"{pedido.veiculo} · {pedido.placa}  \n{pedido.servico}  \n"
            + (f"R$ {formatar_valor(pedido.valor)}" if pd.notna(pedido.valor) else "valor a definir")
            + f" · entrada {formatar_data(pedido.data_entrada)}  \n{responsaveis(pedido._asdict())}"
        )
        voltar, avancar = st.columns([1, 3])
        if etapa > 0:
            anterior = SITUACOES[etapa - 1]
            voltar.button(
                "", icon=":material/arrow_back:", key=f"voltar_{id_pedido}",
                help=f"Voltar para {anterior}", on_click=mover, args=(id_pedido, pedido.nome, anterior),
            )
        if etapa < len(SITUACOES) - 1:
            proxima = SITUACOES[etapa + 1]
            clicou = avancar.button(
                "Avançar", icon=":material/arrow_forward:", icon_position="right",
                key=f"avancar_{id_pedido}", type="primary", width="stretch",
                help=f"Mover para {proxima}",
            )
            if clicou and proxima == CONCLUIDO:
                concluir(pedido._asdict())
            elif clicou:
                mover(id_pedido, pedido.nome, proxima)
                st.rerun()

# Quadro com uma coluna por situação, para levar cada OS adiante etapa por etapa
def mostrar():
    st.title("Andamento dos serviços")
    st.caption("Use **Avançar** para levar cada OS para a próxima etapa")

    pedidos = carregar_pedidos()
    colunas = st.columns(len(SITUACOES))
    for etapa, (coluna, situacao) in enumerate(zip(colunas, SITUACOES)):
        da_etapa = pedidos[pedidos["situacao"] == situacao]
        # Entregues: as mais recentes primeiro; nas outras etapas, as mais antigas primeiro (fila)
        if situacao == ENTREGUE:
            da_etapa = da_etapa.sort_values(["data_entrega", "id"], ascending=False)
        with coluna:
            st.markdown(f"##### {com_icone(situacao)} :gray-badge[{len(da_etapa)}]")
            if da_etapa.empty:
                st.caption("Nenhuma OS")
            visiveis = da_etapa.head(LIMITE_ENTREGUES) if situacao == ENTREGUE else da_etapa
            for posicao, pedido in enumerate(visiveis.itertuples(), start=1):
                cartao(pedido, etapa, posicao)
            if situacao == ENTREGUE and len(da_etapa) > LIMITE_ENTREGUES:
                st.caption(f"+ {len(da_etapa) - LIMITE_ENTREGUES} entregues na lista de OS")

    # OS com situações antigas, fora das etapas, não entram no quadro
    fora = (~pedidos["situacao"].isin(SITUACOES)).sum()
    if fora:
        st.caption(f"{fora} OS com situação fora das etapas aparecem só na lista de OS.")
