import streamlit as st

# Página inicial de login, num cartão centralizado. As contas são os funcionários ativos
def mostrar():
    _, centro, _ = st.columns([1, 1.2, 1])
    with centro:
        st.space("large")
        st.title(":material/build: Oficina Mecânica")
        st.caption("Insira nome e senha para acessar o sistema")
        with st.form("login"):
            usuario = st.text_input("Usuário")
            senha = st.text_input("Senha", type="password")
            entrar = st.form_submit_button("Entrar", type="primary", width="stretch")
        if not entrar:
            return
        if not usuario or not senha:
            st.error("Preencha todos os campos!")
        elif conta := st.session_state.banco.autenticar(usuario.strip().lower(), senha):
            st.session_state.usuario = usuario.strip().lower()
            (st.session_state.id_funcionario, st.session_state.nome_usuario,
             st.session_state.admin) = conta
            st.rerun()
        else:
            st.error("Usuário ou senha incorretos!")
