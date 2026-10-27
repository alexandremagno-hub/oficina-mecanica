import streamlit as st

from paginas import abrir_os, andamento, faturamento, funcionarios, ordens

# Páginas do sistema após o login (usadas no menu lateral e nos links entre páginas)
ORDENS = st.Page(
    ordens.mostrar, title="Ordens de serviço", icon=":material/list_alt:", url_path="ordens",
    default=True,
)
ANDAMENTO = st.Page(
    andamento.mostrar, title="Andamento", icon=":material/view_kanban:", url_path="andamento",
)
ABRIR = st.Page(abrir_os.mostrar, title="Abrir OS", icon=":material/add_circle:", url_path="abrir")
FATURAMENTO = st.Page(
    faturamento.mostrar, title="Faturamento", icon=":material/payments:", url_path="faturamento",
)
FUNCIONARIOS = st.Page(
    funcionarios.mostrar, title="Funcionários", icon=":material/badge:", url_path="funcionarios",
)
