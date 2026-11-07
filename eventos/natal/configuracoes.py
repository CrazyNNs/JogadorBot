from datetime import datetime
from zoneinfo import ZoneInfo


# ==========================================
# CONFIGURAÇÕES GERAIS
# ==========================================

NOME_EVENTO = "Natal das Mil Estrelas"

FUSO_HORARIO = ZoneInfo("America/Sao_Paulo")

DURACAO_EVENTO = 14

# O evento começa desativado até a configuração
# das datas oficiais.

EVENTO_ATIVO = False

DATA_INICIO = None
DATA_FIM = None


# ==========================================
# ECONOMIA
# ==========================================

MOEDA_EVENTO = "flocos"

LIMITE_EXPLORACOES_DIARIAS = 5


# ==========================================
# ITENS
# ==========================================

ITENS_NATALINOS = {
    "presente_vermelho": {
        "nome": "Presente Vermelho",
        "emoji": "🎁",
    },

    "presente_dourado": {
        "nome": "Presente Dourado",
        "emoji": "🎁",
    },

    "madeira_natalina": {
        "nome": "Madeira Natalina",
        "emoji": "🪵",
    },

    "tecido_festivo": {
        "nome": "Tecido Festivo",
        "emoji": "🧵",
    },

    "cristal_glacial": {
        "nome": "Cristal Glacial",
        "emoji": "💎",
    },

    "estrela_fragmentada": {
        "nome": "Estrela Fragmentada",
        "emoji": "⭐",
    },
}


# ==========================================
# GUARDIÃO DO INVERNO
# ==========================================

GUARDIAO = {
    "nome": "Frost — Guardião do Inverno",

    "hp_maximo": 100000,

    "fases": {
        1: 75,
        2: 50,
        3: 25,
        4: 0,
    },
}
