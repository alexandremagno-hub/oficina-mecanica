import pandas as pd
import streamlit as st

from banco import ler_pecas
from moeda import formatar_reais, texto_para_centavos

# Mão de obra (centavos ou None) e peças já gravadas na OS. OS antigas, que só têm o
# valor total, aparecem com esse total como mão de obra
def valores_atuais(pedido):
    pecas = ler_pecas(pedido["pecas"]) if pd.notna(pedido["pecas"]) else []
    if pd.notna(pedido["mao_de_obra"]):
        return int(pedido["mao_de_obra"]), pecas
    if pd.notna(pedido["valor"]) and not pecas:
        return int(pedido["valor"]), pecas
    return None, pecas

# Preencher os campos com o que já está gravado na OS. Roda só quando o diálogo abre: ao fechar,
# o Streamlit apaga o estado dos campos (como o da mão de obra) que deixaram de aparecer
def iniciar_campos(pedido, id_pedido):
    mao_de_obra, pecas = valores_atuais(pedido)
    st.session_state[f"mao_de_obra_{id_pedido}"] = (
        formatar_reais(mao_de_obra) if mao_de_obra is not None else ""
    )
    st.session_state[f"linhas_{id_pedido}"] = []
    for descricao, quantidade, unitario in pecas:
        adicionar_peca(id_pedido, descricao, quantidade, formatar_reais(unitario))

# Nova linha de peça; cada linha tem um número próprio para as chaves dos campos
# não se misturarem quando outra linha é removida
def adicionar_peca(id_pedido, descricao="", quantidade=1, valor=""):
    linhas = st.session_state[f"linhas_{id_pedido}"]
    linha = max(linhas, default=-1) + 1
    linhas.append(linha)
    st.session_state[f"peca_{id_pedido}_{linha}"] = descricao
    st.session_state[f"qtd_{id_pedido}_{linha}"] = quantidade
    st.session_state[f"unitario_{id_pedido}_{linha}"] = valor

def remover_peca(id_pedido, linha):
    st.session_state[f"linhas_{id_pedido}"].remove(linha)

# Peças digitadas como (descrição, quantidade, valor unitário em centavos); linhas sem peça
# e sem valor são ignoradas. Devolve (pecas, None) ou (None, mensagem de erro)
def pecas_digitadas(id_pedido):
    pecas = []
    for numero, linha in enumerate(st.session_state[f"linhas_{id_pedido}"], start=1):
        descricao = st.session_state[f"peca_{id_pedido}_{linha}"].strip()
        texto_valor = st.session_state[f"unitario_{id_pedido}_{linha}"].strip()
        if not descricao and not texto_valor:
            continue
        unitario = texto_para_centavos(texto_valor) if texto_valor else None
        if not descricao or unitario is None:
            return None, f"Peça {numero}: preencha o nome da peça e um valor válido (ex.: 35,50)."
        pecas.append((descricao, int(st.session_state[f"qtd_{id_pedido}_{linha}"]), unitario))
    return pecas, None

# Campos de mão de obra e peças com o total calculado na hora. Devolve
# ((mão de obra, peças), None) ou (None, mensagem de erro)
def campos_valores(pedido):
    id_pedido = int(pedido["id"])
    if f"mao_de_obra_{id_pedido}" not in st.session_state:
        iniciar_campos(pedido, id_pedido)

    texto_mao = st.text_input(
        "Mão de obra (R$)", placeholder="Ex.: 150,00", key=f"mao_de_obra_{id_pedido}"
    )
    st.markdown("**Peças colocadas**")
    linhas = st.session_state[f"linhas_{id_pedido}"]
    if not linhas:
        st.caption("Nenhuma peça. Use o botão abaixo se alguma peça foi colocada.")
    for indice, linha in enumerate(linhas):
        # Os rótulos aparecem só na primeira linha, como o cabeçalho de uma tabela
        rotulo = "visible" if indice == 0 else "collapsed"
        peca, quantidade, unitario, remover = st.columns([5, 1.6, 2.4, 0.7], vertical_alignment="bottom")
        peca.text_input(
            "Peça", key=f"peca_{id_pedido}_{linha}", placeholder="Ex.: Filtro de óleo",
            label_visibility=rotulo,
        )
        quantidade.number_input(
            "Qtd.", min_value=1, step=1, key=f"qtd_{id_pedido}_{linha}", label_visibility=rotulo
        )
        unitario.text_input(
            "Valor unitário (R$)", key=f"unitario_{id_pedido}_{linha}", placeholder="Ex.: 35,50",
            label_visibility=rotulo,
        )
        remover.button(
            "", icon=":material/delete:", key=f"remover_{id_pedido}_{linha}", help="Remover peça",
            on_click=remover_peca, args=(id_pedido, linha),
        )
    st.button(
        "Adicionar peça", icon=":material/add:", type="tertiary",
        on_click=adicionar_peca, args=(id_pedido,),
    )

    pecas, erro = pecas_digitadas(id_pedido)
    mao_de_obra = texto_para_centavos(texto_mao) if texto_mao.strip() else None
    if erro is None and mao_de_obra is None:
        erro = ("Informe a mão de obra (use 0 se não houve)." if not texto_mao.strip()
                else "Mão de obra inválida! Use, por exemplo, 150 ou 1.500,00.")

    # O resumo usa só o que já está válido, para ir mostrando o total enquanto se digita
    total_pecas = sum(q * v for _, q, v in pecas or [])
    mao, itens, total = st.columns(3)
    mao.metric("Mão de obra", f"R$ {formatar_reais(mao_de_obra or 0)}")
    itens.metric(f"Peças ({len(pecas or [])})", f"R$ {formatar_reais(total_pecas)}")
    total.metric("Total", f"R$ {formatar_reais((mao_de_obra or 0) + total_pecas)}")
    return (None, erro) if erro else ((mao_de_obra, pecas), None)

# Formulário completo dentro de um diálogo: grava os valores ao clicar no botão e devolve
# True se gravou
def formulario_valores(pedido, rotulo, icone):
    st.markdown(f"**OS nº {int(pedido['id'])}** · {pedido['nome']}  \n{pedido['servico']}")
    valores, erro = campos_valores(pedido)
    if not st.button(rotulo, type="primary", icon=icone, width="stretch"):
        return False
    if erro:
        st.error(erro, icon=":material/error:")
        return False
    st.session_state.banco.definir_valores(int(pedido["id"]), *valores)
    return True

# Tabela em Markdown com a mão de obra, cada peça e o total, para mostrar na OS
# ("R\\$" porque o Markdown do Streamlit trata o texto entre dois "$" como fórmula)
def resumo_valores(pedido):
    mao_de_obra, pecas = valores_atuais(pedido)
    linhas = [
        "| Item | Qtd. | Unitário (R\\$) | Subtotal (R\\$) |",
        "| --- | ---: | ---: | ---: |",
        f"| Mão de obra | | | {formatar_reais(mao_de_obra or 0)} |",
    ]
    linhas += [
        f"| {descricao.replace('|', '\\|')} | {quantidade} | {formatar_reais(unitario)} | {formatar_reais(quantidade * unitario)} |"
        for descricao, quantidade, unitario in pecas
    ]
    linhas.append(f"| **Total** | | | **{formatar_reais(int(pedido['valor']))}** |")
    return "\n".join(linhas)
