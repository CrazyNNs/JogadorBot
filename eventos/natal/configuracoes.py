from zoneinfo import ZoneInfo


# ==========================================
# CONFIGURAÇÕES GERAIS
# ==========================================

NOME_EVENTO = "Natal das Mil Estrelas"

FUSO_HORARIO = ZoneInfo("America/Sao_Paulo")

DURACAO_EVENTO = 14

EVENTO_ATIVO = False

DATA_INICIO = None
DATA_FIM = None


# ==========================================
# ECONOMIA
# ==========================================

LIMITE_EXPLORACOES_DIARIAS = 5

NOME_MOEDA = "Flocos de Neve"


# ==========================================
# ITENS DO EVENTO
# ==========================================

ITENS_NATALINOS = {
    "presente_vermelho": {
        "nome": "Presente Vermelho",
        "emoji": "🎁",
        "tipo": "presente",
    },

    "presente_dourado": {
        "nome": "Presente Dourado",
        "emoji": "🎁",
        "tipo": "presente",
    },

    "madeira_natalina": {
        "nome": "Madeira Natalina",
        "emoji": "🪵",
        "tipo": "material",
    },

    "tecido_festivo": {
        "nome": "Tecido Festivo",
        "emoji": "🧵",
        "tipo": "material",
    },

    "cristal_glacial": {
        "nome": "Cristal Glacial",
        "emoji": "💎",
        "tipo": "material",
    },

    "estrela_fragmentada": {
        "nome": "Estrela Fragmentada",
        "emoji": "⭐",
        "tipo": "material",
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
