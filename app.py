import sys
from pathlib import Path

import streamlit as st
from streamlit import runtime
from streamlit.web import cli

import sessao
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

sessao.restaurar()

# Sem login, o menu passa a ter só a página de login, escondido; sem isso o navegador
# continuaria mostrando o menu anterior depois de clicar em Sair
if "usuario" not in st.session_state:
    st.navigation([st.Page(login.mostrar, title="Entrar")], position="hidden").run()
    sessao.executar_scripts()
    st.stop()

from navegacao import ABRIR, ANDAMENTO, FATURAMENTO, FUNCIONARIOS, ORDENS

st.logo(Path(__file__).parent / "imagens" / "logo.svg", size="large", icon_image=":material/build:")
# O administrador vê todas as páginas; os funcionários, só as de ordens de serviço. As páginas
# fora da lista também não abrem pelo endereço
admin = st.session_state.get("admin", False)
paginas = [ORDENS, ANDAMENTO, ABRIR] + ([FUNCIONARIOS, FATURAMENTO] if admin else [])
pagina = st.navigation(paginas)
# Rodapé da barra lateral: quem está conectado, Sair e a lua que alterna claro/escuro.
# O CSS empurra o rodapé para o fim da barra
st.html("""<style>
[data-testid="stSidebarContent"] { display: flex; flex-direction: column; }
[data-testid="stSidebarUserContent"] { flex: 1; display: flex; flex-direction: column; padding-bottom: 1.5rem; }
[data-testid="stSidebarUserContent"] > div:first-child { flex: 1; }
[data-testid="stSidebarUserContent"] > div:first-child > [data-testid="stVerticalBlock"] { height: 100%; }
[data-testid="stLayoutWrapper"]:has(> .st-key-rodape_lateral) { margin-top: auto; }
</style>""")
with st.sidebar.container(key="rodape_lateral"):
    st.caption(f"Conectado como **{st.session_state.get('nome_usuario', st.session_state.usuario)}**")
    sair, tema = st.columns([4, 1], vertical_alignment="center")
    if sair.button("Sair", icon=":material/logout:", width="stretch"):
        sessao.sair()
        st.rerun()
    escuro = st.context.theme.type == "dark"
    tema.button(
        "", icon=":material/light_mode:" if escuro else ":material/dark_mode:",
        help="Tema claro" if escuro else "Tema escuro", on_click=sessao.trocar_tema,
    )

if aviso := st.session_state.pop("aviso", None):
    st.toast(aviso, icon=":material/check_circle:")
pagina.run()
# No fim, para os scripts de cookie e tema não abrirem espaço no topo da página
sessao.executar_scripts()
