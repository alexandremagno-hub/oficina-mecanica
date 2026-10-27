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

# Sem login, o menu passa a ter só a página de login, escondido; sem isso o navegador
# continuaria mostrando o menu anterior depois de clicar em Sair
if "usuario" not in st.session_state:
    st.navigation([st.Page(login.mostrar, title="Entrar")], position="hidden").run()
    st.stop()

from navegacao import ABRIR, ANDAMENTO, FATURAMENTO, FUNCIONARIOS, ORDENS

st.logo(Path(__file__).parent / "imagens" / "logo.svg", size="large", icon_image=":material/build:")
# O administrador vê todas as páginas; os funcionários, só as de ordens de serviço. As páginas
# fora da lista também não abrem pelo endereço
admin = st.session_state.get("admin", False)
paginas = [ORDENS, ANDAMENTO, ABRIR] + ([FUNCIONARIOS, FATURAMENTO] if admin else [])
pagina = st.navigation(paginas)
with st.sidebar:
    st.caption(f"Conectado como **{st.session_state.get('nome_usuario', st.session_state.usuario)}**")
    if st.button("Sair", icon=":material/logout:", width="stretch"):
        for chave in ("usuario", "nome_usuario", "admin"):
            st.session_state.pop(chave, None)
        st.rerun()

if aviso := st.session_state.pop("aviso", None):
    st.toast(aviso, icon=":material/check_circle:")
pagina.run()
