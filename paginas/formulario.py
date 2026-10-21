import streamlit as st

from formatos import validar_pedido

# Campos do pedido: (chave, rótulo, dica)
CAMPOS = [
    ("cpf", "CPF do cliente", "Somente os 11 números ou 000.000.000-00"),
    ("nome", "Nome do cliente", "Ex.: Maria da Silva"),
    ("veiculo", "Modelo do veículo", "Ex.: Fiat Uno 2015"),
    ("placa", "Placa do veículo", "Ex.: ABC1D23"),
    ("servico", "Serviço solicitado", "Ex.: Troca de óleo"),
]

# Campos do formulário em duas colunas; os valores ficam em st.session_state["<prefixo>_<campo>"]
def campos_pedido(prefixo):
    esquerda, direita = st.columns(2)
    for indice, (campo, rotulo, dica) in enumerate(CAMPOS):
        coluna = esquerda if indice % 2 == 0 else direita
        coluna.text_input(rotulo, key=f"{prefixo}_{campo}", placeholder=dica)

# Preencher os campos antes de desenhá-los (cpf, nome, veiculo, placa, servico)
def preencher(prefixo, valores):
    for (campo, _, _), valor in zip(CAMPOS, valores):
        st.session_state[f"{prefixo}_{campo}"] = valor

def limpar(prefixo):
    preencher(prefixo, [""] * len(CAMPOS))

# Valores validados do formulário; em caso de problema guarda o erro para exibir e devolve None
def valores_validados(prefixo):
    textos = [st.session_state.get(f"{prefixo}_{campo}", "").strip() for campo, _, _ in CAMPOS]
    valores, erro = validar_pedido(*textos)
    st.session_state[f"{prefixo}_erro"] = erro
    return valores

def mostrar_erro(prefixo):
    if erro := st.session_state.get(f"{prefixo}_erro"):
        st.error(erro, icon=":material/error:")

# Mensagem exibida como notificação na próxima execução da página
def avisar(mensagem):
    st.session_state.aviso = mensagem
