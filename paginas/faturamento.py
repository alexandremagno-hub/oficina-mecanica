from datetime import date

import altair as alt
import pandas as pd
import streamlit as st

from banco import ENTREGUE
from moeda import formatar_reais
from paginas.ordens import carregar_pedidos, formatar_data
from paginas.valores import valores_atuais

MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]
TODOS_MESES = "Todos os meses"

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

# "2026-11" -> "nov/2026"
def nome_mes(mes):
    return mes if mes == TODOS_MESES else f"{MESES[int(mes[5:]) - 1]}/{mes[:4]}"

def reais(centavos):
    return f"R$ {formatar_reais(int(centavos))}"

# Faturamento separado em mão de obra e peças: por mês, de janeiro a dezembro, ou por dia
# quando um mês é escolhido (meses ou dias sem OS ficam zerados)
def grafico(entregues, mes):
    if mes != TODOS_MESES:
        periodos = pd.period_range(f"{mes}-01", pd.Period(mes, freq="M").end_time.date(), freq="D")
        tamanho, rotulo, unidade = 10, lambda dia: f"{dia.day:02d}", "dia"
    else:
        # Ano inteiro, de janeiro a dezembro (de todos os anos com entregas, se houver mais de um)
        inicio = f"{entregues['data_entrega'].min()[:4]}-01"
        fim = f"{entregues['data_entrega'].max()[:4]}-12"
        periodos = pd.period_range(inicio, fim, freq="M")
        tamanho, rotulo, unidade = 7, lambda m: f"{MESES[m.month - 1]}/{str(m.year)[2:]}", "mês"
    eixo = "Dia" if unidade == "dia" else "Mês"
    por_periodo = (
        entregues.assign(periodo=entregues["data_entrega"].str[:tamanho])
        .groupby("periodo")[["mao", "pecas_total"]].sum()
        .reindex([str(p) for p in periodos], fill_value=0)
    )
    dados = pd.DataFrame([
        {
            eixo: rotulo(periodo),
            "Parte": parte,
            "Valor": linha[coluna] / 100,
            "Valor (R$)": formatar_reais(int(linha[coluna])),
            f"Total do {unidade} (R$)": formatar_reais(int(linha["mao"] + linha["pecas_total"])),
        }
        for periodo, (_, linha) in zip(periodos, por_periodo.iterrows())
        for parte, coluna in (("Mão de obra", "mao"), ("Peças", "pecas_total"))
    ])
    grafico = alt.Chart(dados).mark_bar().encode(
        x=alt.X(f"{eixo}:N", sort=None, title=None, axis=alt.Axis(labelAngle=0)),
        # Milhar com ponto, no padrão brasileiro
        y=alt.Y("Valor:Q", title="R$", stack="zero", axis=alt.Axis(
            labelExpr="replace(format(datum.value, ',.0f'), ',', '.')",
        )),
        color=alt.Color(
            "Parte:N", title=None, legend=alt.Legend(orient="top"),
            scale=alt.Scale(domain=list(CORES), range=list(CORES.values())),
        ),
        order=alt.Order("Parte:N"),
        tooltip=[eixo, "Parte", "Valor (R$)", f"Total do {unidade} (R$)"],
    )
    st.altair_chart(grafico, width="stretch")

# Faturamento de hoje, o faturamento do mês escolhido (ou o geral desde o
# início, com "Todos os meses") e a quantidade e o ticket médio do que está filtrado
def indicadores(do_periodo, todas, mes):
    hoje = date.today()
    do_dia = todas[todas["data_entrega"] == hoje.isoformat()]
    total = do_periodo["valor"].sum()
    colunas = iter(st.columns(4))
    next(colunas).metric(
        "Faturamento do dia", reais(do_dia["valor"].sum()), border=True,
        help=f"{len(do_dia)} OS entregues hoje ({hoje.strftime('%d/%m/%Y')})",
    )
    if mes != TODOS_MESES:
        next(colunas).metric(
            f"Faturamento de {nome_mes(mes)}", reais(total), border=True,
            help=f"{len(do_periodo)} OS entregues em {nome_mes(mes)}",
        )
    else:
        next(colunas).metric(
            "Faturamento geral", reais(total), border=True,
            help=f"{len(todas)} OS entregues desde o início",
        )
    next(colunas).metric("OS entregues", len(do_periodo), border=True)
    next(colunas).metric(
        "Ticket médio", reais(total // len(do_periodo)) if len(do_periodo) else "—", border=True
    )

# Entregas e faturamento de cada funcionário no período, contando cada OS para quem concluiu o
# serviço. Ordena por entregas e, no empate, pelo faturamento. OS sem esse registro (antigas)
# ficam de fora
def ranking_equipe(entregues):
    feitas = entregues[entregues["nome_conclusao"].notna()]
    return (
        feitas.groupby("nome_conclusao")
        .agg(entregas=("id", "size"), faturado=("valor", "sum"), mao=("mao", "sum"))
        .sort_values(["entregas", "faturado"], ascending=False)
        .reset_index()
    )

# Mês da tela toda, entre o mês atual (mesmo sem entregas ainda) e os meses que tiveram
# entregas, de todos os anos (o mais recente primeiro). Começa no mês atual
def escolher_mes(entregues):
    atual = date.today().isoformat()[:7]
    meses = sorted(set(entregues["data_entrega"].str[:7]) | {atual}, reverse=True)
    return st.selectbox(
        "Mês", meses + [TODOS_MESES], index=meses.index(atual),
        format_func=nome_mes, key="mes_dashboard",
    )

# Destaque para quem mais entregou no mês escolhido e o ranking de toda a equipe
def desempenho(entregues, mes):
    ranking = ranking_equipe(entregues)
    sem_registro = len(entregues) - int(ranking["entregas"].sum())
    if ranking.empty:
        st.info("Nenhuma entrega do período tem o funcionário que concluiu registrado.",
                icon=":material/info:")
        return

    melhor = ranking.iloc[0]
    empatados = ranking[ranking["entregas"] == melhor["entregas"]]
    with st.container(border=True):
        titulo = ("Destaque do período" if mes == TODOS_MESES
                  else f"Destaque de {nome_mes(mes)}")
        st.markdown(f"#### :material/emoji_events: {titulo}: {melhor['nome_conclusao']}")
        if len(empatados) > 1:
            outros = ", ".join(empatados["nome_conclusao"].iloc[1:])
            st.caption(f"Empatado em entregas com {outros}; fica à frente quem faturou mais")
        entregas, faturado, mao, ticket = st.columns(4)
        entregas.metric(
            "Entregas", int(melhor["entregas"]),
            help=f"{melhor['entregas'] / ranking['entregas'].sum():.0%} das entregas da equipe",
        )
        faturado.metric("Faturamento", reais(melhor["faturado"]))
        mao.metric("Mão de obra", reais(melhor["mao"]))
        ticket.metric("Ticket médio", reais(melhor["faturado"] // melhor["entregas"]))

    st.dataframe(
        pd.DataFrame({
            "Posição": [f"{posicao}º" for posicao in range(1, len(ranking) + 1)],
            "Funcionário": ranking["nome_conclusao"],
            "Entregas": ranking["entregas"],
            "Faturamento (R$)": ranking["faturado"].map(formatar_reais),
            "Ticket médio (R$)": (ranking["faturado"] // ranking["entregas"]).map(formatar_reais),
        }),
        hide_index=True, width="stretch",
        column_config={"Entregas": st.column_config.ProgressColumn(
            "Entregas", format="%d", min_value=0, max_value=int(ranking["entregas"].max()),
        )},
    )
    if sem_registro:
        st.caption(f"{sem_registro} OS entregues sem o funcionário que concluiu registrado "
                   "não entram no ranking")

# Tabela com as OS que entraram no faturamento do período
def tabela(entregues):
    st.dataframe(
        pd.DataFrame({
            "Nº": range(1, len(entregues) + 1),
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

# Dashboard com o faturamento das OS entregues, contado pela data de entrega, e o desempenho
# da equipe; o mês escolhido no topo vale para a tela toda
def mostrar():
    st.title("Dashboard")
    st.caption("Conta as OS entregues, pela data de entrega")

    pedidos = carregar_pedidos()
    com_valor = pedidos[pedidos["valor"].notna()]
    entregues = com_valor[(com_valor["situacao"] == ENTREGUE) & (com_valor["data_entrega"] != "")]
    if entregues.empty:
        st.info("Nenhuma OS entregue com valor ainda.", icon=":material/info:")
        return
    entregues = separar_valores(entregues).sort_values(["data_entrega", "id"], ascending=False)

    filtro, _ = st.columns([1, 3])
    with filtro:
        mes = escolher_mes(entregues)
    do_periodo = entregues
    if mes != TODOS_MESES:
        do_periodo = entregues[entregues["data_entrega"].str.startswith(mes)]

    indicadores(do_periodo, entregues, mes)
    st.subheader("Desempenho da equipe")
    st.caption("Cada entrega conta para o funcionário que concluiu o serviço")
    desempenho(do_periodo, mes)
    st.subheader("Por dia" if mes != TODOS_MESES else "Por mês")
    grafico(do_periodo, mes)
    st.subheader("Todas as OS entregues" if mes == TODOS_MESES
                 else f"OS entregues em {nome_mes(mes)}")
    tabela(do_periodo)
