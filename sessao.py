import json
import secrets

import streamlit as st

# Login que sobrevive ao recarregar a página (F5 ou troca de tema): ao entrar, o navegador
# guarda um código aleatório num cookie, e o servidor lembra a qual funcionário ele pertence.
# Os códigos ficam só na memória do servidor: reiniciar o streamlit pede login de novo
COOKIE = "oficina_sessao"
CHAVES = ("usuario", "id_funcionario", "nome_usuario", "admin")

# Caminhos das páginas; o Streamlit guarda o tema escolhido no navegador separado por caminho
CAMINHOS = ("/", "/ordens", "/andamento", "/abrir", "/dashboard", "/funcionarios")


@st.cache_resource
def _sessoes():
    return {}


def restaurar():
    """Se o navegador tem um cookie de sessão válido, refaz o login sem pedir a senha."""
    if "usuario" in st.session_state:
        return
    dados = _sessoes().get(st.context.cookies.get(COOKIE, ""))
    if dados:
        st.session_state.update(dados)


def entrar(usuario, conta):
    id_funcionario, nome, admin = conta
    st.session_state.update(zip(CHAVES, (usuario, id_funcionario, nome, admin)))
    _gravar_cookie()


# Cria o código da sessão atual e manda o navegador guardá-lo no cookie
def _gravar_cookie():
    codigo = secrets.token_urlsafe(32)
    _sessoes()[codigo] = {chave: st.session_state[chave] for chave in CHAVES}
    _script(f"document.cookie = {json.dumps(f'{COOKIE}={codigo}; path=/; SameSite=Strict; max-age=2592000')};")


def sair():
    _sessoes().pop(st.context.cookies.get(COOKIE, ""), None)
    for chave in CHAVES:
        st.session_state.pop(chave, None)
    _script(f"document.cookie = {json.dumps(f'{COOKIE}=; path=/; max-age=0')};")


def trocar_tema():
    """Grava no navegador o tema oposto ao atual e recarrega a página para aplicá-lo."""
    novo = "Light" if st.context.theme.type == "dark" else "Dark"
    # Login feito sem cookie (ex.: antes desta versão): grava agora, para o recarregar não deslogar
    if "usuario" in st.session_state and st.context.cookies.get(COOKIE) not in _sessoes():
        _gravar_cookie()
    chaves = json.dumps([f"stActiveTheme-{caminho}-v2" for caminho in CAMINHOS])
    _script(
        f"for (const chave of {chaves}) localStorage.setItem(chave, {json.dumps(json.dumps(novo))});"
        "location.reload();"
    )


# Os scripts rodam na próxima execução da página (depois do st.rerun de quem os pediu)
def _script(codigo):
    st.session_state.setdefault("scripts", []).append(codigo)


def executar_scripts():
    for codigo in st.session_state.pop("scripts", []):
        st.html(f"<script>{codigo}</script>", unsafe_allow_javascript=True, width="content")
