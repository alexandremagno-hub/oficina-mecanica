from datetime import date

import altair as alt
import pandas as pd
import streamlit as st

from banco import ENTREGUE
from moeda import formatar_reais
from paginas.ordens import carregar_pedidos, formatar_data
from paginas.valores import valores_atuais

MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]
TODOS = "Todos"

# Cores das partes do faturamento no gráfico
CORES = {"Mão de obra": "#2a78d6", "Peças": "#eb6834"}

# Mão de obra e total das peças de cada OS, em centavos
def separar_valores(pedidos):
    partes = [valores_atuais(pedido) for _, pedido in pedidos.iterrows()]
    pedidos = pedidos.assign(
        mao=[mao_de_obra or 0 for mao_de_obra, _ in partes],
        pecas_total=[sum(q * v for _, q, v in pecas) for _, pecas in partes],
    )
    pedidos["valor"] = pedidos["valor"].astype(int)
    return pedidos

def reais(centavos):
    return f"R$ {formatar_reais(int(centavos))}"

# Faturamento de cada mês do período, separado em mão de obra e peças (meses sem OS ficam zerados)
def grafico_mensal(entregues, ano):
    if ano == TODOS:
        inicio, fim = entregues["data_entrega"].min()[:7], entregues["data_entrega"].max()[:7]
    else:
        inicio, fim = f"{ano}-01", f"{ano}-12"
    meses = pd.period_range(inicio, fim, freq="M")
    por_mes = (
        entregues.assign(mes=entregues["data_entrega"].str[:7])
        .groupby("mes")[["mao", "pecas_total"]].sum()
        .reindex([str(mes) for mes in meses], fill_value=0)
    )
    dados = pd.DataFrame([
        {
            "Mês": f"{MESES[mes.month - 1]}/{str(mes.year)[2:]}",
            "Parte": parte,
            "Valor": linha[coluna] / 100,
            "Valor (R$)": formatar_reais(int(linha[coluna])),
            "Total do mês (R$)": formatar_reais(int(linha["mao"] + linha["pecas_total"])),
        }
        for mes, (_, linha) in zip(meses, por_mes.iterrows())
        for parte, coluna in (("Mão de obra", "mao"), ("Peças", "pecas_total"))
    ])
    grafico = alt.Chart(dados).mark_bar().encode(
        x=alt.X("Mês:N", sort=None, title=None, axis=alt.Axis(labelAngle=0)),
        # Milhar com ponto, no padrão brasileiro
        y=alt.Y("Valor:Q", title="R$", stack="zero", axis=alt.Axis(
            labelExpr="replace(format(datum.value, ',.0f'), ',', '.')",
        )),
        color=alt.Color(
            "Parte:N", title=None, legend=alt.Legend(orient="top"),
            scale=alt.Scale(domain=list(CORES), range=list(CORES.values())),
        ),
        order=alt.Order("Parte:N"),
        tooltip=["Mês", "Parte", "Valor (R$)", "Total do mês (R$)"],
    )
    st.altair_chart(grafico, width="stretch")

# Faturamento de hoje e do mês atual, a quantidade e o ticket médio do período escolhido e,
# com o período "Todos", o faturamento geral desde o início
def indicadores(do_periodo, todas, ano):
    hoje = date.today()
    do_dia = todas[todas["data_entrega"] == hoje.isoformat()]
    do_mes = todas[todas["data_entrega"].str.startswith(hoje.isoformat()[:7])]
    total = do_periodo["valor"].sum()
    colunas = iter(st.columns(5 if ano == TODOS else 4))
    next(colunas).metric(
        "Faturamento do dia", reais(do_dia["valor"].sum()), border=True,
        help=f"{len(do_dia)} OS entregues hoje ({hoje.strftime('%d/%m/%Y')})",
    )
    next(colunas).metric(
        "Faturamento do mês", reais(do_mes["valor"].sum()), border=True,
        help=f"{len(do_mes)} OS entregues em {MESES[hoje.month - 1]}/{hoje.year}",
    )
    if ano == TODOS:
        next(colunas).metric(
            "Faturamento geral", reais(total), border=True,
            help=f"{len(todas)} OS entregues desde o início",
        )
    next(colunas).metric("OS entregues", len(do_periodo), border=True)
    next(colunas).metric(
        "Ticket médio", reais(total // len(do_periodo)) if len(do_periodo) else "—", border=True
    )

# Tabela com as OS que entraram no faturamento do período
def tabela(entregues):
    st.dataframe(
        pd.DataFrame({
            "Nº OS": entregues["id"],
            "Cliente": entregues["nome"],
            "Placa": entregues["placa"],
            "Serviço": entregues["servico"],
            "Entrega": entregues["data_entrega"].map(formatar_data),
            "Concluída por": entregues["nome_conclusao"].fillna("—"),
            "Mão de obra (R$)": entregues["mao"].map(formatar_reais),
            "Peças (R$)": entregues["pecas_total"].map(formatar_reais),
            "Total (R$)": entregues["valor"].map(formatar_reais),
        }),
        hide_index=True, width="stretch",
    )

# Página com o faturamento das OS entregues, contado pela data de entrega
def mostrar():
    st.title("Faturamento")
    st.caption("Conta as OS entregues, pela data de entrega")

    pedidos = carregar_pedidos()
    com_valor = pedidos[pedidos["valor"].notna()]
    entregues = com_valor[(com_valor["situacao"] == ENTREGUE) & (com_valor["data_entrega"] != "")]
    if entregues.empty:
        st.info("Nenhuma OS entregue com valor ainda.", icon=":material/info:")
        return
    entregues = separar_valores(entregues).sort_values(["data_entrega", "id"], ascending=False)

    anos = sorted(entregues["data_entrega"].str[:4].unique(), reverse=True)
    atual = str(date.today().year)
    ano = st.segmented_control(
        "Período", anos + [TODOS], default=atual if atual in anos else anos[0],
    ) or TODOS
    do_periodo = entregues
    if ano != TODOS:
        do_periodo = entregues[entregues["data_entrega"].str.startswith(ano)]

    indicadores(do_periodo, entregues, ano)
    st.subheader("Por mês")
    grafico_mensal(do_periodo, ano)
    st.subheader("OS entregues no período")
    tabela(do_periodo)
