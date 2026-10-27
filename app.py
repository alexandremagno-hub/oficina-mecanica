import sys
from pathlib import Path

import streamlit as st
from streamlit import runtime
from streamlit.web import cli

from banco import Banco
from paginas import login

# Executado com "python app.py" (ex.: botão Run da IDE): inicia o servidor do Streamlit
if __name__ == "__main__" and not runtime.exists():
    sys.argv = ["streamlit", "run", __file__]
    sys.exit(cli.main())

st.set_page_config(page_title="Oficina Mecânica", page_icon=":material/build:", layout="wide")

# Uma conexão com o banco por sessão do navegador
if "banco" not in st.session_state:
    st.session_state.banco = Banco()

if "usuario" not in st.session_state:
    login.mostrar()
    st.stop()

from navegacao import ABRIR, ANDAMENTO, FATURAMENTO, ORDENS

st.logo(Path(__file__).parent / "imagens" / "logo.svg", size="large", icon_image=":material/build:")
pagina = st.navigation([ORDENS, ANDAMENTO, FATURAMENTO, ABRIR])
with st.sidebar:
    st.caption(f"Conectado como **{st.session_state.usuario}**")
    if st.button("Sair", icon=":material/logout:", width="stretch"):
        del st.session_state.usuario
        st.rerun()

if aviso := st.session_state.pop("aviso", None):
    st.toast(aviso, icon=":material/check_circle:")
pagina.run()
