import streamlit as st

from paginas.formulario import avisar, campos_pedido, limpar, mostrar_erro, valores_validados

PREFIXO = "abrir"

# Inserir o pedido; roda antes de a página ser redesenhada, então pode limpar os campos
def cadastrar():
    valores = valores_validados(PREFIXO)
    if valores is None:
        return
    st.session_state.banco.cadastrar_pedido(*valores)
    limpar(PREFIXO)
    avisar(f"Ordem de serviço de {valores[1]} aberta!")

# Página de cadastro de pedido
def mostrar():
    st.title("Abrir ordem de serviço")
    st.caption("Insira os dados do cliente e do serviço. O valor é informado quando o serviço for concluído")
    with st.form("abrir_os", border=True):
        campos_pedido(PREFIXO)
        mostrar_erro(PREFIXO)
        st.form_submit_button(
            "Abrir OS", type="primary", icon=":material/add:", on_click=cadastrar
        )
    from navegacao import ORDENS
    st.page_link(ORDENS, label="Ver ordens de serviço")
