import json
import random

from datetime import datetime, timedelta

from .banco import obter_conexao
from .configuracoes import FUSO_HORARIO, ITENS_NATALINOS
from .inventario import registrar_jogador


# ==========================================
# CONFIGURAÇÕES
# ==========================================

LIMITE_EXPLORACOES_DIARIAS = 5
ETAPAS_POR_EXPLORACAO = 3
TEMPO_INATIVIDADE_MINUTOS = 15

        {
            "id": "noel_especial",
            "raridade": "raro",
            "titulo": "O presente de Noel",
            "narrativa": (
                "Uma pequena carroça aparece na praça. "
                "Ao lado dela está Noel, organizando presentes "
                "para as famílias da vila. Ele percebe sua presença "
                "e decide conversar com você."
            ),
            "escolhas": {
                "ajudar": {
                    "texto": "🎁 Ajudar Noel",
                    "resultado": (
                        "Você ajuda a organizar os presentes. "
                        "Noel agradece e entrega uma recompensa especial."
                    ),
                    "itens": {"presente_dourado": 1},
                    "flocos": 20,
                    "pontos": 10,
                },

                "conversar": {
                    "texto": "💬 Conversar com Noel",
                    "resultado": (
                        "Noel conta uma antiga história sobre "
                        "a estrela mágica e presenteia você."
                    ),
                    "itens": {"presente_vermelho": 2},
                    "flocos": 15,
                    "pontos": 8,
                },
            },
        },

        {
            "id": "pipo_especial",
            "raridade": "incomum",
            "titulo": "O plano de Pipo",
            "narrativa": (
                "Pipo aparece carregando uma caixa enorme. "
                "Ele diz ter encontrado um caminho secreto "
                "para recuperar materiais, mas precisa de ajuda."
            ),
            "escolhas": {
                "acompanhar": {
                    "texto": "🧭 Acompanhar Pipo",
                    "resultado": (
                        "O caminho secreto realmente existe! "
                        "Vocês encontram materiais escondidos."
                    ),
                    "itens": {
                        "tecido_festivo": 3,
                        "madeira_natalina": 2,
                    },
                    "flocos": 12,
                    "pontos": 6,
                },

                "abrir_caixa": {
                    "texto": "📦 Abrir a caixa",
                    "resultado": (
                        "A caixa estava cheia de presentes "
                        "que Pipo havia esquecido de entregar."
                    ),
                    "itens": {"presente_vermelho": 2},
                    "flocos": 10,
                    "pontos": 5,
                },
            },
        },

# ==========================================
# REGIÕES
# ==========================================

REGIOES = {
    "floresta_nevada": {
        "nome": "Floresta Nevada",
        "emoji": "🌲",
        "descricao": (
            "Uma floresta coberta por neve. "
            "Entre árvores antigas e trilhas escondidas, "
            "existem materiais e presentes perdidos."
        ),
    },

    "vila_congelada": {
        "nome": "Vila Congelada",
        "emoji": "🏘️",
        "descricao": (
            "Um vilarejo tomado pelo gelo. "
            "Seus moradores precisam de ajuda, "
            "e algumas surpresas aguardam entre as casas."
        ),
    },

    "caverna_glacial": {
        "nome": "Caverna Glacial",
        "emoji": "💎",
        "descricao": (
            "Uma caverna misteriosa, repleta de cristais "
            "e fragmentos de uma antiga estrela."
        ),
    },
}

        {
            "id": "lumi_especial",
            "raridade": "raro",
            "titulo": "A luz de Lumi",
            "narrativa": (
                "Uma luz azulada ilumina a caverna. "
                "Lumi aparece diante de você e revela "
                "que está procurando fragmentos da estrela."
            ),
            "escolhas": {
                "ajudar": {
                    "texto": "✨ Ajudar Lumi",
                    "resultado": (
                        "Lumi utiliza sua magia para revelar "
                        "um fragmento escondido nas paredes."
                    ),
                    "itens": {
                        "estrela_fragmentada": 1,
                        "cristal_glacial": 2,
                    },
                    "flocos": 18,
                    "pontos": 10,
                },

                "perguntar": {
                    "texto": "❓ Perguntar sobre a estrela",
                    "resultado": (
                        "Lumi explica parte da história da estrela "
                        "e compartilha um pouco de sua energia."
                    ),
                    "itens": {"cristal_glacial": 3},
                    "flocos": 22,
                    "pontos": 8,
                },
            },
        },

        {
            "id": "frost_especial",
            "raridade": "lendario",
            "titulo": "A presença do Guardião",
            "narrativa": (
                "A temperatura despenca repentinamente. "
                "Uma silhueta surge entre os cristais. "
                "É Frost, o Guardião do Inverno. "
                "Ele observa você em silêncio antes de desaparecer."
            ),
            "escolhas": {
                "enfrentar": {
                    "texto": "❄️ Encarar o Guardião",
                    "resultado": (
                        "Frost libera uma onda de energia congelante. "
                        "Você resiste e encontra um fragmento "
                        "estelar deixado para trás."
                    ),
                    "itens": {"estrela_fragmentada": 2},
                    "flocos": 30,
                    "pontos": 18,
                },

                "observar": {
                    "texto": "👁️ Observar sua presença",
                    "resultado": (
                        "Você percebe símbolos antigos em sua armadura. "
                        "Frost desaparece, deixando cristais raros."
                    ),
                    "itens": {"cristal_glacial": 5},
                    "flocos": 25,
                    "pontos": 15,
                },
            },
        },

# ==========================================
# ACONTECIMENTOS
# ==========================================

EVENTOS = {

    "floresta_nevada": [

        {
            "id": "luz_dourada",
            "titulo": "Uma luz entre as árvores",
            "narrativa": (
                "Uma pequena luz dourada aparece atrás de uma "
                "árvore coberta de neve. Ela parece tentar "
                "chamar sua atenção."
            ),
            "escolhas": {
                "investigar": {
                    "texto": "🔍 Investigar a luz",
                    "resultado": (
                        "Você encontra um pequeno presente "
                        "escondido entre as raízes."
                    ),
                    "itens": {"presente_vermelho": 1},
                    "flocos": 8,
                    "pontos": 3,
                },

                "observar": {
                    "texto": "👀 Observar de longe",
                    "resultado": (
                        "A luz desaparece, mas deixa alguns "
                        "materiais próximos à árvore."
                    ),
                    "itens": {"madeira_natalina": 3},
                    "flocos": 5,
                    "pontos": 2,
                },

                "seguir": {
                    "texto": "🚶 Continuar caminhando",
                    "resultado": (
                        "Você segue pela trilha e encontra "
                        "alguns Flocos de Neve acumulados."
                    ),
                    "itens": {},
                    "flocos": 12,
                    "pontos": 1,
                },
            },
        },

        {
            "id": "raposa_perdida",
            "titulo": "A raposa perdida",
            "narrativa": (
                "Uma raposa branca aparece entre os arbustos. "
                "Ela parece estar procurando alguma coisa."
            ),
            "escolhas": {
                "ajudar": {
                    "texto": "🦊 Ajudar a raposa",
                    "resultado": (
                        "A raposa encontra o caminho de volta "
                        "e deixa um pequeno presente como agradecimento."
                    ),
                    "itens": {"presente_vermelho": 1},
                    "flocos": 6,
                    "pontos": 4,
                },

                "seguir_rastros": {
                    "texto": "🐾 Seguir suas pegadas",
                    "resultado": (
                        "As pegadas levam até um esconderijo "
                        "com madeira natalina."
                    ),
                    "itens": {"madeira_natalina": 4},
                    "flocos": 4,
                    "pontos": 2,
                },
            },
        },

        {
            "id": "arvore_antiga",
            "titulo": "A árvore antiga",
            "narrativa": (
                "Uma árvore gigantesca bloqueia parte da trilha. "
                "Seu tronco possui marcas brilhantes."
            ),
            "escolhas": {
                "examinar": {
                    "texto": "🌳 Examinar as marcas",
                    "resultado": (
                        "As marcas revelam um pequeno esconderijo "
                        "entre as raízes."
                    ),
                    "itens": {"madeira_natalina": 5},
                    "flocos": 5,
                    "pontos": 3,
                },

                "procurar": {
                    "texto": "🔎 Procurar ao redor",
                    "resultado": (
                        "Você encontra um presente preso "
                        "entre os galhos baixos."
                    ),
                    "itens": {"presente_vermelho": 1},
                    "flocos": 7,
                    "pontos": 2,
                },
            },
        },

        {
            "id": "acampamento_abandonado",
            "titulo": "O acampamento abandonado",
            "narrativa": (
                "Você encontra um antigo acampamento. "
                "Uma fogueira apagada está cercada por caixas."
            ),
            "escolhas": {
                "abrir_caixas": {
                    "texto": "📦 Abrir as caixas",
                    "resultado": (
                        "Uma das caixas contém materiais "
                        "deixados por antigos exploradores."
                    ),
                    "itens": {"madeira_natalina": 2},
                    "flocos": 10,
                    "pontos": 3,
                },

                "examinar_fogueira": {
                    "texto": "🔥 Examinar a fogueira",
                    "resultado": (
                        "Você encontra um pequeno embrulho "
                        "escondido sob as cinzas frias."
                    ),
                    "itens": {"presente_vermelho": 1},
                    "flocos": 6,
                    "pontos": 2,
                },
            },
        },
    ],

    "vila_congelada": [

        {
            "id": "lumi",
            "titulo": "Um encontro com Lumi",
            "narrativa": (
                "Lumi está tentando carregar alguns materiais "
                "pela praça congelada. Ela parece precisar de ajuda."
            ),
            "escolhas": {
                "ajudar": {
                    "texto": "✨ Ajudar Lumi",
                    "resultado": (
                        "Lumi agradece e entrega alguns tecidos "
                        "que estavam sobrando na oficina."
                    ),
                    "itens": {"tecido_festivo": 3},
                    "flocos": 8,
                    "pontos": 5,
                },

                "conversar": {
                    "texto": "💬 Conversar com Lumi",
                    "resultado": (
                        "Lumi conta histórias sobre a estrela "
                        "mágica e recompensa sua companhia."
                    ),
                    "itens": {},
                    "flocos": 14,
                    "pontos": 4,
                },
            },
        },

        {
            "id": "pipo",
            "titulo": "A confusão de Pipo",
            "narrativa": (
                "Pipo está cercado por presentes espalhados "
                "pela neve. Ele parece ter tropeçado durante "
                "uma entrega."
            ),
            "escolhas": {
                "organizar": {
                    "texto": "🎁 Organizar os presentes",
                    "resultado": (
                        "Pipo consegue recuperar os presentes "
                        "e oferece um deles como agradecimento."
                    ),
                    "itens": {"presente_vermelho": 1},
                    "flocos": 7,
                    "pontos": 4,
                },

                "procurar": {
                    "texto": "🔍 Procurar algo perdido",
                    "resultado": (
                        "Você encontra tecido festivo "
                        "embaixo de uma caixa."
                    ),
                    "itens": {"tecido_festivo": 3},
                    "flocos": 5,
                    "pontos": 3,
                },
            },
        },

        {
            "id": "casa_abandonada",
            "titulo": "A casa abandonada",
            "narrativa": (
                "Uma casa antiga está coberta de gelo. "
                "A porta está entreaberta e há marcas no chão."
            ),
            "escolhas": {
                "entrar": {
                    "texto": "🏠 Entrar na casa",
                    "resultado": (
                        "Dentro da casa, você encontra "
                        "um embrulho esquecido."
                    ),
                    "itens": {"presente_vermelho": 1},
                    "flocos": 8,
                    "pontos": 3,
                },

                "examinar": {
                    "texto": "👣 Examinar as marcas",
                    "resultado": (
                        "As marcas levam até um depósito "
                        "com tecidos festivos."
                    ),
                    "itens": {"tecido_festivo": 4},
                    "flocos": 5,
                    "pontos": 3,
                },
            },
        },

        {
            "id": "oficina_fechada",
            "titulo": "A oficina fechada",
            "narrativa": (
                "Você encontra uma pequena oficina. "
                "A porta está trancada, mas há uma janela aberta."
            ),
            "escolhas": {
                "janela": {
                    "texto": "🪟 Olhar pela janela",
                    "resultado": (
                        "Você avista alguns materiais "
                        "esquecidos perto da bancada."
                    ),
                    "itens": {"tecido_festivo": 2},
                    "flocos": 10,
                    "pontos": 3,
                },

                "entorno": {
                    "texto": "🚶 Explorar os arredores",
                    "resultado": (
                        "Atrás da oficina existe uma caixa "
                        "com um presente."
                    ),
                    "itens": {"presente_vermelho": 1},
                    "flocos": 7,
                    "pontos": 2,
                },
            },
        },
    ],

    "caverna_glacial": [

        {
            "id": "cristal_brilhante",
            "titulo": "O cristal brilhante",
            "narrativa": (
                "Um cristal azul ilumina a parede da caverna. "
                "Sua luz parece pulsar lentamente."
            ),
            "escolhas": {
                "extrair": {
                    "texto": "💎 Extrair o cristal",
                    "resultado": (
                        "Você consegue retirar alguns fragmentos "
                        "sem danificar a formação."
                    ),
                    "itens": {"cristal_glacial": 2},
                    "flocos": 8,
                    "pontos": 5,
                },

                "examinar": {
                    "texto": "🔬 Examinar o cristal",
                    "resultado": (
                        "A luz revela pequenos fragmentos "
                        "espalhados pelo chão."
                    ),
                    "itens": {"cristal_glacial": 1},
                    "flocos": 14,
                    "pontos": 4,
                },
            },
        },

        {
            "id": "fragmento_estelar",
            "titulo": "Um fragmento da estrela",
            "narrativa": (
                "No centro de uma pequena câmara, "
                "há um fragmento brilhante da estrela mágica."
            ),
            "escolhas": {
                "recolher": {
                    "texto": "⭐ Recolher o fragmento",
                    "resultado": (
                        "Você recolhe cuidadosamente o fragmento "
                        "e sente uma energia misteriosa."
                    ),
                    "itens": {"estrela_fragmentada": 1},
                    "flocos": 10,
                    "pontos": 8,
                },

                "observar": {
                    "texto": "👁️ Observar sua energia",
                    "resultado": (
                        "A energia libera cristais menores "
                        "ao redor da câmara."
                    ),
                    "itens": {"cristal_glacial": 3},
                    "flocos": 12,
                    "pontos": 5,
                },
            },
        },

        {
            "id": "ponte_de_gelo",
            "titulo": "A ponte de gelo",
            "narrativa": (
                "Uma ponte estreita atravessa uma fenda profunda. "
                "Do outro lado, algo parece brilhar."
            ),
            "escolhas": {
                "atravessar": {
                    "texto": "🌉 Atravessar a ponte",
                    "resultado": (
                        "Você chega ao outro lado e encontra "
                        "um pequeno esconderijo."
                    ),
                    "itens": {"cristal_glacial": 2},
                    "flocos": 12,
                    "pontos": 5,
                },

                "procurar": {
                    "texto": "🔍 Procurar outro caminho",
                    "resultado": (
                        "Uma passagem lateral leva até "
                        "um fragmento estelar."
                    ),
                    "itens": {"estrela_fragmentada": 1},
                    "flocos": 6,
                    "pontos": 7,
                },
            },
        },

        {
            "id": "frost_sinal",
            "titulo": "O sinal do Guardião",
            "narrativa": (
                "Uma corrente de ar gelado atravessa a caverna. "
                "Na parede, surge o símbolo de Frost, "
                "o Guardião do Inverno."
            ),
            "escolhas": {
                "examinar": {
                    "texto": "❄️ Examinar o símbolo",
                    "resultado": (
                        "O símbolo libera uma pequena energia "
                        "cristalizada."
                    ),
                    "itens": {"cristal_glacial": 2},
                    "flocos": 10,
                    "pontos": 6,
                },

                "seguir": {
                    "texto": "⭐ Seguir a energia",
                    "resultado": (
                        "Você encontra um fragmento da estrela "
                        "escondido em uma rachadura."
                    ),
                    "itens": {"estrela_fragmentada": 1},
                    "flocos": 8,
                    "pontos": 8,
                },
            },
        },
    ],
}


# ==========================================
# DATA E HORA
# ==========================================

def obter_agora():
    return datetime.now(FUSO_HORARIO)


def obter_data_rotacao():
    return obter_agora().date().isoformat()


def calcular_expiracao():
    return (
        obter_agora()
        + timedelta(minutes=TEMPO_INATIVIDADE_MINUTOS)
    ).isoformat()


# ==========================================
# FUNÇÕES AUXILIARES
# ==========================================

def localizar_evento(regiao, evento_id):
    for evento in EVENTOS.get(regiao, []):
        if evento["id"] == evento_id:
            return evento

    return None


def montar_dados_evento(evento):
    return {
        "id": evento["id"],
        "titulo": evento["titulo"],
        "narrativa": evento["narrativa"],
        "escolhas": [
            {
                "id": escolha_id,
                "texto": dados["texto"],
            }
            for escolha_id, dados in evento["escolhas"].items()
        ],
    }


def carregar_estado(estado_json):
    try:
        estado = json.loads(estado_json)
    except (TypeError, json.JSONDecodeError):
        return None

    if not isinstance(estado, dict):
        return None

    return estado


def validar_recompensas(itens):
    for item_id, quantidade in itens.items():
        if item_id not in ITENS_NATALINOS:
            return False

        if not isinstance(quantidade, int) or quantidade <= 0:
            return False

    return True



def criar_proximo_evento(regiao, eventos_usados):

    pesos = {
        "comum": 70,
        "incomum": 22,
        "raro": 7,
        "lendario": 1,
    }

    disponiveis = [
        evento
        for evento in EVENTOS.get(regiao, [])
        if evento["id"] not in eventos_usados
    ]

    if not disponiveis:
        return None

    pesos_eventos = [
        pesos.get(
            evento.get("raridade", "comum"),
            pesos["comum"],
        )
        for evento in disponiveis
    ]

    return random.choices(
        disponiveis,
        weights=pesos_eventos,
        k=1,
    )[0]



# ==========================================
# EXPIRAR AVENTURAS
# ==========================================

def expirar_exploracoes():
    agora = obter_agora().isoformat()
    data_hoje = obter_data_rotacao()

    with obter_conexao() as conn:
        cursor = conn.execute("""
            UPDATE natal_exploracoes

            SET status = 'expirada'

            WHERE status = 'ativa'

            AND (
                expira_em <= ?
                OR data_rotacao != ?
            )
        """, (
            agora,
            data_hoje,
        ))

        return cursor.rowcount


# ==========================================
# CONSULTAR TENTATIVAS
# ==========================================

def consultar_tentativas(user_id):
    registrar_jogador(user_id)

    expirar_exploracoes()

    data_hoje = obter_data_rotacao()

    with obter_conexao() as conn:
        resultado = conn.execute("""
            SELECT COUNT(*) AS total

            FROM natal_exploracoes

            WHERE user_id = ?

            AND data_rotacao = ?
        """, (
            user_id,
            data_hoje,
        )).fetchone()

        ativa = conn.execute("""
            SELECT id

            FROM natal_exploracoes

            WHERE user_id = ?

            AND status = 'ativa'

            LIMIT 1
        """, (user_id,)).fetchone()

    utilizadas = resultado["total"]

    return {
        "utilizadas": utilizadas,
        "restantes": max(
            0,
            LIMITE_EXPLORACOES_DIARIAS - utilizadas,
        ),
        "limite": LIMITE_EXPLORACOES_DIARIAS,
        "tem_ativa": ativa is not None,
        "exploracao_id": (
            ativa["id"]
            if ativa is not None
            else None
        ),
    }


# ==========================================
# INICIAR EXPLORAÇÃO
# ==========================================

def iniciar_exploracao(user_id, regiao):
    if regiao not in REGIOES:
        return {
            "sucesso": False,
            "motivo": "regiao_invalida",
        }

    registrar_jogador(user_id)

    agora_dt = obter_agora()
    agora = agora_dt.isoformat()
    data_hoje = agora_dt.date().isoformat()

    expiracao = (
        agora_dt
        + timedelta(minutes=TEMPO_INATIVIDADE_MINUTOS)
    ).isoformat()

    with obter_conexao() as conn:
        conn.execute("BEGIN IMMEDIATE")

        conn.execute("""
            UPDATE natal_exploracoes

            SET status = 'expirada'

            WHERE user_id = ?

            AND status = 'ativa'

            AND (
                expira_em <= ?
                OR data_rotacao != ?
            )
        """, (
            user_id,
            agora,
            data_hoje,
        ))

        ativa = conn.execute("""
            SELECT id

            FROM natal_exploracoes

            WHERE user_id = ?

            AND status = 'ativa'

            LIMIT 1
        """, (user_id,)).fetchone()

        if ativa is not None:
            return {
                "sucesso": False,
                "motivo": "aventura_ativa",
                "exploracao_id": ativa["id"],
            }

        resultado = conn.execute("""
            SELECT COUNT(*) AS total

            FROM natal_exploracoes

            WHERE user_id = ?

            AND data_rotacao = ?
        """, (
            user_id,
            data_hoje,
        )).fetchone()

        utilizadas = resultado["total"]

        if utilizadas >= LIMITE_EXPLORACOES_DIARIAS:
            return {
                "sucesso": False,
                "motivo": "limite_diario",
                "utilizadas": utilizadas,
                "restantes": 0,
            }

        primeiro_evento = criar_proximo_evento(
            regiao,
            [],
        )

        estado = {
            "itens": {},
            "flocos": 0,
            "pontos": 0,
            "eventos_usados": [
                primeiro_evento["id"]
            ],
        }

        cursor = conn.execute("""
            INSERT INTO natal_exploracoes (
                user_id,
                regiao,
                etapa,
                status,
                estado_json,
                data_rotacao,
                iniciada_em,
                atualizada_em,
                expira_em
            )

            VALUES (?, ?, 1, 'ativa', ?, ?, ?, ?, ?)
        """, (
            user_id,
            regiao,
            json.dumps(estado, ensure_ascii=False),
            data_hoje,
            agora,
            agora,
            expiracao,
        ))

        exploracao_id = cursor.lastrowid

        conn.execute("""
            INSERT INTO natal_exploracao_eventos (
                exploracao_id,
                etapa,
                evento_id,
                narrativa,
                criado_em
            )

            VALUES (?, 1, ?, ?, ?)
        """, (
            exploracao_id,
            primeiro_evento["id"],
            primeiro_evento["narrativa"],
            agora,
        ))

    return {
        "sucesso": True,
        "exploracao_id": exploracao_id,
        "regiao": REGIOES[regiao],
        "etapa": 1,
        "total_etapas": ETAPAS_POR_EXPLORACAO,
        "evento": montar_dados_evento(primeiro_evento),
        "tentativas_restantes": (
            LIMITE_EXPLORACOES_DIARIAS
            - utilizadas
            - 1
        ),
    }


# ==========================================
# CONSULTAR EXPLORAÇÃO ATIVA
# ==========================================

def consultar_exploracao(user_id):
    expirar_exploracoes()

    with obter_conexao() as conn:
        exploracao = conn.execute("""
            SELECT *

            FROM natal_exploracoes

            WHERE user_id = ?

            AND status = 'ativa'

            LIMIT 1
        """, (user_id,)).fetchone()

        if exploracao is None:
            return None

        evento_registrado = conn.execute("""
            SELECT *

            FROM natal_exploracao_eventos

            WHERE exploracao_id = ?

            AND escolha_id IS NULL

            ORDER BY etapa DESC

            LIMIT 1
        """, (exploracao["id"],)).fetchone()

    if evento_registrado is None:
        return None

    evento = localizar_evento(
        exploracao["regiao"],
        evento_registrado["evento_id"],
    )

    if evento is None:
        return None

    return {
        "exploracao_id": exploracao["id"],
        "regiao": REGIOES[exploracao["regiao"]],
        "etapa": exploracao["etapa"],
        "total_etapas": ETAPAS_POR_EXPLORACAO,
        "expira_em": exploracao["expira_em"],
        "evento": montar_dados_evento(evento),
    }


# ==========================================
# ENTREGAR RECOMPENSAS
# ==========================================

def entregar_recompensas(
    conn,
    user_id,
    itens,
    flocos,
    pontos,
    agora,
):
    if not validar_recompensas(itens):
        raise ValueError("Recompensas inválidas.")

    if (
        not isinstance(flocos, int)
        or flocos < 0
        or not isinstance(pontos, int)
        or pontos < 0
    ):
        raise ValueError("Valores de recompensa inválidos.")

    if flocos > 0 or pontos > 0:
        conn.execute("""
            UPDATE natal_jogadores

            SET
                flocos = flocos + ?,
                pontos = pontos + ?

            WHERE user_id = ?
        """, (
            flocos,
            pontos,
            user_id,
        ))

    if flocos > 0:
        conn.execute("""
            INSERT INTO natal_transacoes (
                user_id,
                tipo,
                quantidade,
                descricao,
                data
            )

            VALUES (?, 'credito', ?, ?, ?)
        """, (
            user_id,
            flocos,
            "Recompensa de exploração natalina",
            agora,
        ))

    for item_id, quantidade in itens.items():
        conn.execute("""
            INSERT INTO natal_inventario (
                user_id,
                item_id,
                quantidade
            )

            VALUES (?, ?, ?)

            ON CONFLICT(user_id, item_id)

            DO UPDATE SET
                quantidade = quantidade + excluded.quantidade
        """, (
            user_id,
            item_id,
            quantidade,
        ))

        conn.execute("""
            INSERT INTO natal_transacoes (
                user_id,
                tipo,
                item_id,
                quantidade,
                descricao,
                data
            )

            VALUES (?, 'credito', ?, ?, ?, ?)
        """, (
            user_id,
            item_id,
            quantidade,
            "Recompensa de exploração natalina",
            agora,
        ))


# ==========================================
# REGISTRAR ESCOLHA
# ==========================================

def registrar_escolha(
    user_id,
    exploracao_id,
    escolha_id,
):
    agora_dt = obter_agora()
    agora = agora_dt.isoformat()

    expiracao = (
        agora_dt
        + timedelta(minutes=TEMPO_INATIVIDADE_MINUTOS)
    ).isoformat()

    with obter_conexao() as conn:
        conn.execute("BEGIN IMMEDIATE")

        exploracao = conn.execute("""
            SELECT *

            FROM natal_exploracoes

            WHERE id = ?

            AND user_id = ?

            AND status = 'ativa'
        """, (
            exploracao_id,
            user_id,
        )).fetchone()

        if exploracao is None:
            return {
                "sucesso": False,
                "motivo": "exploracao_indisponivel",
            }

        if (
            exploracao["expira_em"] <= agora
            or exploracao["data_rotacao"] != agora_dt.date().isoformat()
        ):
            conn.execute("""
                UPDATE natal_exploracoes

                SET status = 'expirada'

                WHERE id = ?
            """, (exploracao_id,))

            return {
                "sucesso": False,
                "motivo": "expirada",
            }

        estado = carregar_estado(
            exploracao["estado_json"]
        )

        if estado is None:
            return {
                "sucesso": False,
                "motivo": "estado_invalido",
            }

        evento_registrado = conn.execute("""
            SELECT *

            FROM natal_exploracao_eventos

            WHERE exploracao_id = ?

            AND etapa = ?

            AND escolha_id IS NULL
        """, (
            exploracao_id,
            exploracao["etapa"],
        )).fetchone()

        if evento_registrado is None:
            return {
                "sucesso": False,
                "motivo": "evento_indisponivel",
            }

        evento = localizar_evento(
            exploracao["regiao"],
            evento_registrado["evento_id"],
        )

        if evento is None:
            return {
                "sucesso": False,
                "motivo": "evento_invalido",
            }

        escolha = evento["escolhas"].get(escolha_id)

        if escolha is None:
            return {
                "sucesso": False,
                "motivo": "escolha_invalida",
            }

        itens = escolha.get("itens", {})
        flocos = escolha.get("flocos", 0)
        pontos = escolha.get("pontos", 0)

        if not validar_recompensas(itens):
            return {
                "sucesso": False,
                "motivo": "recompensa_invalida",
            }

        estado["flocos"] += flocos
        estado["pontos"] += pontos

        for item_id, quantidade in itens.items():
            estado["itens"][item_id] = (
                estado["itens"].get(item_id, 0)
                + quantidade
            )

        conn.execute("""
            UPDATE natal_exploracao_eventos

            SET
                escolha_id = ?,
                escolha_texto = ?,
                consequencia_json = ?

            WHERE id = ?
        """, (
            escolha_id,
            escolha["texto"],
            json.dumps(
                {
                    "resultado": escolha["resultado"],
                    "itens": itens,
                    "flocos": flocos,
                    "pontos": pontos,
                },
                ensure_ascii=False,
            ),
            evento_registrado["id"],
        ))

        etapa_atual = exploracao["etapa"]

        resultado_escolha = {
            "texto": escolha["texto"],
            "resultado": escolha["resultado"],
            "itens": itens,
            "flocos": flocos,
            "pontos": pontos,
        }

        # ----------------------------------
        # CONCLUIR AVENTURA
        # ----------------------------------

        if etapa_atual >= ETAPAS_POR_EXPLORACAO:
            entregar_recompensas(
                conn,
                user_id,
                estado["itens"],
                estado["flocos"],
                estado["pontos"],
                agora,
            )

            conn.execute("""
                UPDATE natal_exploracoes

                SET
                    status = 'concluida',
                    estado_json = ?,
                    atualizada_em = ?,
                    expira_em = ?

                WHERE id = ?
            """, (
                json.dumps(estado, ensure_ascii=False),
                agora,
                agora,
                exploracao_id,
            ))

            return {
                "sucesso": True,
                "concluida": True,
                "resultado_escolha": resultado_escolha,
                "recompensas": {
                    "itens": estado["itens"],
                    "flocos": estado["flocos"],
                    "pontos": estado["pontos"],
                },
            }

        # ----------------------------------
        # AVANÇAR PARA PRÓXIMA ETAPA
        # ----------------------------------

        proxima_etapa = etapa_atual + 1

        proximo_evento = criar_proximo_evento(
            exploracao["regiao"],
            estado["eventos_usados"],
        )

        if proximo_evento is None:
            return {
                "sucesso": False,
                "motivo": "sem_eventos_disponiveis",
            }

        estado["eventos_usados"].append(
            proximo_evento["id"]
        )

        conn.execute("""
            INSERT INTO natal_exploracao_eventos (
                exploracao_id,
                etapa,
                evento_id,
                narrativa,
                criado_em
            )

            VALUES (?, ?, ?, ?, ?)
        """, (
            exploracao_id,
            proxima_etapa,
            proximo_evento["id"],
            proximo_evento["narrativa"],
            agora,
        ))

        conn.execute("""
            UPDATE natal_exploracoes

            SET
                etapa = ?,
                estado_json = ?,
                atualizada_em = ?,
                expira_em = ?

            WHERE id = ?
        """, (
            proxima_etapa,
            json.dumps(estado, ensure_ascii=False),
            agora,
            expiracao,
            exploracao_id,
        ))

    return {
        "sucesso": True,
        "concluida": False,
        "etapa": proxima_etapa,
        "total_etapas": ETAPAS_POR_EXPLORACAO,
        "resultado_escolha": resultado_escolha,
        "proximo_evento": montar_dados_evento(
            proximo_evento
        ),
    }
