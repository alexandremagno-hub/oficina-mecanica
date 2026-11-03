import pandas as pd
import streamlit as st

from banco import CAMPOS_LISTA, CONCLUIDO, ENTREGUE, SITUACOES
from formatos import corresponde, formatar_cpf
from moeda import formatar_reais
from paginas.formulario import (
    CAMPOS, avisar, campos_pedido, mostrar_erro, preencher, pergunta, valores_validados,
)
from paginas.valores import adicionar_peca, campos_valores, resumo_valores, valores_atuais

PREFIXO = "editar"

# Ícone de cada situação nas listas e nos filtros (situações antigas fora da lista usam ⚫)
ICONES = {"Na fila": "🟡", "Em andamento": "🔵", "Concluído": "🟢", "Entregue": "⚪"}

TITULOS = {
    "id": "Nº", "cpf": "CPF", "nome": "Cliente", "veiculo": "Veículo", "placa": "Placa",
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
        st.session_state.banco.listar_pedidos(), columns=CAMPOS_LISTA
    )
    for coluna in ("data_entrada", "data_entrega"):
        pedidos[coluna] = pedidos[coluna].fillna("")
    return pedidos

# Quem abriu e quem concluiu a OS, em uma linha; "—" para quem não ficou registrado
def responsaveis(pedido):
    nome = lambda valor: valor if isinstance(valor, str) else "—"
    texto = f"Aberta por {nome(pedido['nome_abertura'])}"
    if pedido["situacao"] in (CONCLUIDO, ENTREGUE):
        texto += f" · concluída por {nome(pedido['nome_conclusao'])}"
    return texto

# Funcionários veem só as OS entregues que abriram ou concluíram; o administrador vê todas
def entregas_permitidas(pedidos):
    if st.session_state.get("admin", False):
        return pedidos
    eu = st.session_state.get("id_funcionario")
    minhas = (pedidos["aberta_por"] == eu) | (pedidos["concluida_por"] == eu)
    return pedidos[(pedidos["situacao"] != ENTREGUE) | minhas].reset_index(drop=True)

# Fecha a janela de edição depois de salvar, excluir ou ao clicar fora dela
def limpar_selecao():
    st.session_state.pop("selecao", None)
    st.session_state.pop("modo_os", None)
    st.session_state.pop("pendente_os", None)
    st.session_state.pop(f"{PREFIXO}_id", None)

# O que a janela de edição mostra: "editar" (dados da OS), "valores", "excluir" ou
# "confirmar"/"confirmar_valores" (a pergunta antes de gravar as alterações)
def mudar_modo(modo):
    st.session_state.modo_os = modo

# Indicadores por situação
def resumo(pedidos):
    contagem = pedidos["situacao"].value_counts()
    for coluna, situacao in zip(st.columns(len(SITUACOES)), SITUACOES):
        coluna.metric(com_icone(situacao), int(contagem.get(situacao, 0)), border=True)

# Valor em reais para exibição, ou "—" se o serviço ainda não foi concluído
def formatar_valor(centavos):
    return formatar_reais(int(centavos)) if pd.notna(centavos) and centavos >= 0 else "—"

# As duas listas têm o mesmo formato: a linha principal mostra o básico e a seta abre uma
# segunda linha com o resto; DETALHES de cada lado diz o que aparece nessa segunda linha.
# Na coluna "id" aparece a posição da OS na própria lista (1, 2, 3…), não o número da OS
RESUMIDAS = {"id": str, "nome": str, "veiculo": str, "placa": str}
DETALHES_ABERTAS = {
    "cpf": formatar_cpf, "servico": str, "valor": formatar_valor, "data_entrada": formatar_data,
}
DETALHES_ENTREGUES = {
    "cpf": formatar_cpf, "servico": str, "data_entrada": formatar_data,
    "data_entrega": formatar_data,
}
LARGURAS = [1, 3, 3, 2, 3, 1]

def alternar_detalhes(id_pedido):
    expandidas = st.session_state.setdefault("expandidas", set())
    expandidas.symmetric_difference_update({id_pedido})

def selecionar(id_pedido):
    st.session_state.selecao = id_pedido
    st.session_state.modo_os = "editar"

# Lista de OS com a coluna extra da linha principal (campo e formatação) e os detalhes;
# devolve a OS selecionada (ou None)
def lista(visiveis, extra, detalhes):
    if visiveis.empty:
        st.info("Nenhuma OS aqui.", icon=":material/info:")
        return None
    resumidas = RESUMIDAS | dict([extra])
    for coluna, campo in zip(st.columns(LARGURAS), resumidas):
        coluna.caption(f"**{TITULOS[campo]}**")
    expandidas = st.session_state.get("expandidas", set())
    for posicao, pedido in enumerate(visiveis.itertuples(), start=1):
        id_pedido = int(pedido.id)
        aberta = id_pedido in expandidas
        with st.container(border=True):
            colunas = st.columns(LARGURAS, vertical_alignment="center")
            for coluna, (campo, formatar) in zip(colunas, resumidas.items()):
                coluna.write(str(posicao) if campo == "id" else formatar(getattr(pedido, campo)))
            colunas[-1].button(
                "", key=f"seta_{id_pedido}", type="tertiary",
                icon=":material/expand_less:" if aberta else ":material/expand_more:",
                help="Esconder detalhes" if aberta else "Mostrar detalhes",
                on_click=alternar_detalhes, args=(id_pedido,),
            )
            if aberta:
                for coluna, (campo, formatar) in zip(st.columns(len(detalhes) + 1), detalhes.items()):
                    coluna.caption(TITULOS[campo])
                    coluna.write(formatar(getattr(pedido, campo)))
                st.caption(responsaveis(pedido._asdict()))
                st.button(
                    "Editar", key=f"editar_{id_pedido}", icon=":material/edit:",
                    on_click=selecionar, args=(id_pedido,),
                )
    # A OS escolhida pode estar na outra lista ou ter sumido por causa da busca ou do filtro
    escolhida = visiveis[visiveis["id"] == st.session_state.get("selecao")]
    return escolhida.iloc[0] if not escolhida.empty else None

# Lista de (campo, antes, depois) só com o que mudou
def diferencas(antes, depois):
    return [(campo, a, d) for campo, a, d in zip(antes, antes.values(), depois) if a != d]

# Ao clicar em salvar, nada é gravado ainda: guarda o que foi digitado e pergunta antes
def salvar(pedido):
    valores = valores_validados(PREFIXO)
    if valores is None:
        return
    antes = {
        "CPF": formatar_cpf(pedido["cpf"]), "Nome": pedido["nome"], "Veículo": pedido["veiculo"],
        "Placa": pedido["placa"], "Serviço": pedido["servico"],
    }
    mudancas = diferencas(antes, (formatar_cpf(valores[0]), *valores[1:]))
    if not mudancas:
        limpar_selecao()
        avisar(f"Nenhuma alteração feita na OS nº {int(pedido['id'])}.")
        return
    st.session_state.pendente_os = {
        "valores": valores, "mudancas": mudancas,
        "textos": [st.session_state[f"{PREFIXO}_{campo}"] for campo, _, _ in CAMPOS],
    }
    mudar_modo("confirmar")

# Cancelar a confirmação volta para o formulário com o que tinha sido digitado (o Streamlit
# descarta os campos enquanto eles não aparecem na tela)
def voltar_dados(_id_pedido=None):
    preencher(PREFIXO, st.session_state.pop("pendente_os")["textos"])
    mudar_modo("editar")

def gravar_dados(id_pedido):
    st.session_state.banco.atualizar_pedido(id_pedido, *st.session_state.pendente_os["valores"])
    limpar_selecao()
    avisar(f"OS nº {id_pedido} atualizada!")

def confirmar_dados(id_pedido):
    pergunta(
        f"Quer mesmo fazer estas alterações na OS nº **{id_pedido}**?",
        st.session_state.pendente_os["mudancas"], voltar_dados, gravar_dados, (id_pedido,),
    )

# Peças em uma linha, para mostrar na confirmação: "2× Filtro (R$ 35,00), 1× Vela (R$ 20,00)"
def descrever_pecas(pecas):
    return ", ".join(
        f"{quantidade}× {descricao} (R$ {formatar_reais(unitario)})"
        for descricao, quantidade, unitario in pecas
    ) or "nenhuma"

def descrever_valores(mao_de_obra, pecas):
    total = (mao_de_obra or 0) + sum(q * v for _, q, v in pecas)
    return (
        f"R$ {formatar_reais(mao_de_obra)}" if mao_de_obra is not None else "—",
        descrever_pecas(pecas), f"R$ {formatar_reais(total)}",
    )

# Corrigir a mão de obra e as peças de uma OS já concluída (dentro da janela de edição,
# já que o Streamlit não abre uma janela dentro de outra)
def alterar_valores(pedido):
    id_pedido = int(pedido["id"])
    st.button("Voltar", icon=":material/arrow_back:", type="tertiary",
              on_click=mudar_modo, args=("editar",))
    st.markdown(f"**{pedido['nome']}**  \n{pedido['servico']}")
    valores, erro = campos_valores(pedido)
    if not st.button("Salvar valores", type="primary", icon=":material/save:", width="stretch"):
        return
    if erro:
        st.error(erro, icon=":material/error:")
        return
    rotulos = ("Mão de obra", "Peças", "Total")
    mudancas = diferencas(
        dict(zip(rotulos, descrever_valores(*valores_atuais(pedido)))), descrever_valores(*valores)
    )
    if not mudancas:
        limpar_selecao()
        avisar(f"Nenhuma alteração feita nos valores da OS nº {id_pedido}.")
    else:
        st.session_state.pendente_os = {"valores": valores, "mudancas": mudancas, "id": id_pedido}
        mudar_modo("confirmar_valores")
    st.rerun()

# Cancelar volta para os campos de valores com o que tinha sido digitado
def voltar_valores(_id_pedido=None):
    pendente = st.session_state.pop("pendente_os")
    id_pedido, (mao_de_obra, pecas) = pendente["id"], pendente["valores"]
    st.session_state[f"mao_de_obra_{id_pedido}"] = formatar_reais(mao_de_obra)
    st.session_state[f"linhas_{id_pedido}"] = []
    for descricao, quantidade, unitario in pecas:
        adicionar_peca(id_pedido, descricao, quantidade, formatar_reais(unitario))
    mudar_modo("valores")

def gravar_valores(id_pedido):
    st.session_state.banco.definir_valores(id_pedido, *st.session_state.pendente_os["valores"])
    limpar_selecao()
    avisar(f"Valores da OS nº {id_pedido} atualizados!")

def confirmar_valores(id_pedido):
    pergunta(
        f"Quer mesmo alterar os valores da OS nº **{id_pedido}**?",
        st.session_state.pendente_os["mudancas"], voltar_valores, gravar_valores, (id_pedido,),
    )

def confirmar_exclusao(id_pedido, nome, placa):
    st.write(f"Excluir a OS nº **{id_pedido}** de **{nome}** (placa {placa})?")
    st.caption("Essa ação não pode ser desfeita.")
    cancelar, excluir = st.columns(2)
    cancelar.button("Cancelar", width="stretch", on_click=mudar_modo, args=("editar",))
    if excluir.button("Excluir", type="primary", icon=":material/delete:", width="stretch"):
        st.session_state.banco.excluir_pedido(id_pedido)
        limpar_selecao()
        avisar(f"OS nº {id_pedido} excluída!")
        st.rerun()

def formulario_edicao(pedido, id_pedido):
    titulo, excluir = st.columns([4, 1], vertical_alignment="center")
    titulo.subheader(f"OS nº {id_pedido} · {pedido['nome']}")
    excluir.button("Excluir", icon=":material/delete:", width="stretch",
                   on_click=mudar_modo, args=("excluir",))
    with st.form(f"form_{PREFIXO}", border=False):
        campos_pedido(PREFIXO)
        mostrar_erro(PREFIXO)
        # Cancelar fecha a janela sem gravar nada (para quem clicou em Editar sem querer)
        cancelar, salvar_botao = st.columns(2)
        cancelar.form_submit_button(
            "Cancelar", icon=":material/close:", width="stretch", on_click=limpar_selecao,
        )
        salvar_botao.form_submit_button(
            "Salvar alterações", type="primary", icon=":material/save:", width="stretch",
            on_click=salvar, args=(pedido,),
        )
    # Os valores são informados ao concluir o serviço e podem ser corrigidos depois
    if pd.notna(pedido["valor"]):
        st.markdown("**Valores do serviço**")
        st.markdown(resumo_valores(pedido))
        st.button("Alterar valores", icon=":material/edit:",
                  on_click=mudar_modo, args=("valores",))
    st.caption(
        f"Situação: {com_icone(pedido['situacao'])} (mude na página Andamento) · "
        f"Entrada: {formatar_data(pedido['data_entrada'])} · "
        f"Entrega: {formatar_data(pedido['data_entrega'])}  \n{responsaveis(pedido)}"
    )

def confirmando():
    return st.session_state.get("modo_os", "editar").startswith("confirmar")

# Janela pequena, no meio da tela, que pergunta antes de gravar as alterações da OS. Ao
# cancelar ou confirmar, recarrega a página para voltar à edição ou fechar
@st.dialog("Confirmar alteração", on_dismiss=limpar_selecao)
def confirmacao(pedido):
    if "selecao" not in st.session_state or not confirmando():
        st.rerun()
    if st.session_state.modo_os == "confirmar":
        confirmar_dados(int(pedido["id"]))
    else:
        confirmar_valores(int(pedido["id"]))

# Janela por cima da página com a edição da OS selecionada; fechá-la desfaz a seleção
@st.dialog("Editar ordem de serviço", width="large", on_dismiss=limpar_selecao)
def painel(pedido):
    # Depois de gravar, a seleção some: fecha a janela recarregando a página inteira. Ao pedir
    # a confirmação, recarrega também, para a página trocar esta janela pela pequena
    if "selecao" not in st.session_state or confirmando():
        st.rerun()
    id_pedido = int(pedido["id"])
    # Preenche os campos ao abrir a janela, para não apagar o que foi digitado; preenche de novo
    # se o Streamlit tiver descartado os campos (ao passar pelos valores ou pela exclusão)
    if st.session_state.get(f"{PREFIXO}_id") != id_pedido or f"{PREFIXO}_cpf" not in st.session_state:
        st.session_state[f"{PREFIXO}_id"] = id_pedido
        st.session_state[f"{PREFIXO}_erro"] = None
        preencher(PREFIXO, (
            formatar_cpf(pedido["cpf"]), pedido["nome"], pedido["veiculo"], pedido["placa"],
            pedido["servico"],
        ))

    modo = st.session_state.get("modo_os", "editar")
    if modo == "valores":
        alterar_valores(pedido.to_dict())
    elif modo == "excluir":
        confirmar_exclusao(id_pedido, pedido["nome"], pedido["placa"])
    else:
        formulario_edicao(pedido, id_pedido)

# Página com a lista de ordens de serviço: resumo, busca, filtro por situação, edição e exclusão
def mostrar():
    from navegacao import ABRIR

    titulo, botao = st.columns([4, 1], vertical_alignment="bottom")
    titulo.title("Ordens de serviço")
    if botao.button("Abrir OS", type="primary", icon=":material/add:", width="stretch"):
        st.switch_page(ABRIR)

    pedidos = entregas_permitidas(carregar_pedidos())
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

    # Em aberto à esquerda, com a situação, e entregues à direita, com o valor cobrado
    entregues = visiveis["situacao"] == ENTREGUE
    esquerda, direita = st.columns(2)
    with esquerda:
        st.subheader("Em aberto")
        pedido_aberto = lista(
            visiveis[~entregues], ("situacao", com_icone), DETALHES_ABERTAS,
        )
    with direita:
        st.subheader("Entregues" if st.session_state.get("admin", False) else "Minhas entregas")
        pedido_entregue = lista(
            visiveis[entregues], ("valor", formatar_valor), DETALHES_ENTREGUES,
        )
    st.caption(
        f"{len(visiveis)} de {len(pedidos)} OS · use a seta para ver os detalhes "
        "e editar ou excluir uma OS"
    )
    pedido = pedido_aberto if pedido_aberto is not None else pedido_entregue
    if pedido is not None:
        confirmacao(pedido) if confirmando() else painel(pedido)
