from tkinter import ttk

# Paleta de cores da interface
COR_FUNDO = "#0078D4"
COR_CARTAO = "#FFFFFF"
COR_TEXTO = "#1F1F1F"
COR_TEXTO_SUAVE = "#5F6B7A"
COR_DESTAQUE = "#0078D4"
COR_DESTAQUE_ESCURO = "#005A9E"
COR_PERIGO = "#C42B1C"
COR_PERIGO_ESCURO = "#A32316"

FONTE = "Segoe UI"

# Estilos dos widgets ttk
def aplicar_estilos():
    estilo = ttk.Style()
    estilo.theme_use("clam")
    estilo.configure("Fundo.TFrame", background=COR_FUNDO)
    estilo.configure("Cartao.TFrame", background=COR_CARTAO)
    estilo.configure("TLabel", background=COR_CARTAO, foreground=COR_TEXTO, font=(FONTE, 10))
    estilo.configure("Titulo.TLabel", font=(FONTE, 16, "bold"))
    estilo.configure("Subtitulo.TLabel", foreground=COR_TEXTO_SUAVE)
    estilo.configure("TEntry", padding=5)
    estilo.configure("TButton", font=(FONTE, 10), padding=(12, 6))
    estilo.configure(
        "Primario.TButton", background=COR_DESTAQUE, foreground="#FFFFFF", bordercolor=COR_DESTAQUE
    )
    estilo.map("Primario.TButton", background=[("active", COR_DESTAQUE_ESCURO)])
    estilo.configure(
        "Perigo.TButton", background=COR_PERIGO, foreground="#FFFFFF", bordercolor=COR_PERIGO
    )
    estilo.map("Perigo.TButton", background=[("active", COR_PERIGO_ESCURO)])
    estilo.configure("Treeview", rowheight=26, font=(FONTE, 10))
    estilo.configure("Treeview.Heading", font=(FONTE, 10, "bold"))
