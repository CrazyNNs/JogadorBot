import discord
from .banco import inicializar_banco
from .configuracoes import (
    NOME_EVENTO,
    EVENTO_ATIVO,
    DURACAO_EVENTO,
    ITENS_NATALINOS,
)
from .inventario import consultar_inventario
from .entregas import (
    consultar_entregas,
    concluir_entrega,
    DIFICULDADES,
)
from .oficina import (
    inicializar_oficina,
    fabricar_presente,
    consultar_receitas,
    consultar_progresso_vila,
    contribuir_para_vila,
    consultar_ranking_vila,
)

from .exploracao import (
    REGIOES,
    iniciar_exploracao,
    consultar_exploracao,
    consultar_tentativas,
    registrar_escolha,
)

# ==========================================
# MONTAR EMBED DO INVENTÁRIO-
# ==========================================

def montar_embed_inventario(user_id):

    inventario = consultar_inventario(user_id)

    embed = discord.Embed(
        title="🎒 Inventário Natalino",

        description=(
            "Confira os recursos acumulados "
            "durante o Natal das Mil Estrelas."
        ),

        color=discord.Color.from_rgb(80, 170, 255),
    )

    # ----------------------------------
    # FLOCOS DE NEVE
    # ----------------------------------

    embed.add_field(
        name="❄️ Flocos de Neve",

        value=f"**{inventario['flocos']:,}**",

        inline=False,
    )

    # ----------------------------------
    # PONTOS
    # ----------------------------------

    embed.add_field(
        name="⭐ Espírito Natalino",

        value=f"**{inventario['pontos']:,}**",

        inline=False,
    )

    # ----------------------------------
    # MATERIAIS E PRESENTES
    # ----------------------------------

    itens = inventario["itens"]

    if itens:

        linhas = []

        for item_id, quantidade in itens.items():

            dados = ITENS_NATALINOS.get(item_id)

            if dados is None:
                continue

            nome = dados["nome"]

            emoji = dados["emoji"]

            linhas.append(
                f"{emoji} **{nome}:** {quantidade}"
            )

        if linhas:

            embed.add_field(
                name="🎁 Materiais e Presentes",

                value="\n".join(linhas),

                inline=False,
            )

        else:

            embed.add_field(
                name="🎁 Materiais e Presentes",

                value="Seu inventário está vazio.",

                inline=False,
            )

    else:

        embed.add_field(
            name="🎁 Materiais e Presentes",

            value="Seu inventário está vazio.",

            inline=False,
        )

    embed.set_footer(
        text=f"{NOME_EVENTO} • Sakurai"
    )

    return embed
    
# ==========================================
# MONTAR EMBED DAS ENTREGAS
# ==========================================


def montar_embed_entregas(user_id):
    entregas = consultar_entregas(user_id)

    embed = discord.Embed(
        title="📦 Entregas Natalinas",
        description=(
            "Ajude os moradores e a oficina da vila!\n"
            "Você recebe três pedidos por dia. "
            "Conclua-os para ganhar Flocos de Neve e Espírito Natalino."
        ),
        color=discord.Color.from_rgb(80, 170, 255),
    )

    if not entregas:
        embed.add_field(
            name="📭 Nenhuma entrega disponível",
            value="Você já concluiu todos os pedidos de hoje!",
            inline=False,
        )
        return embed

    for indice, entrega in enumerate(entregas):

        # Separador entre as entregas
        if indice > 0:
            embed.add_field(
                name="\u200b",
                value="━━━━━━━━━━━━━━━━━━",
                inline=False,
            )

        pedido = entrega["pedido"]

        dificuldade = pedido["dificuldade"]
        dados_dificuldade = DIFICULDADES[dificuldade]

        materiais = pedido["materiais"]
        linhas_materiais = []

        for item_id, quantidade in materiais.items():
            dados_item = ITENS_NATALINOS.get(item_id)

            if dados_item is None:
                nome = item_id
                emoji = "📦"
            else:
                nome = dados_item["nome"]
                emoji = dados_item["emoji"]

            linhas_materiais.append(
                f"{emoji} **{nome}:** {quantidade}"
            )

        recompensa = (
            f"❄️ **{entrega['recompensa_flocos']} Flocos de Neve**\n"
            f"⭐ **{entrega['recompensa_pontos']} Espírito Natalino**"
        )

        embed.add_field(
            name=(
                f"{dados_dificuldade['emoji']} "
                f"{dados_dificuldade['nome']} — {pedido['titulo']}"
            ),
            value=(
                f"{pedido['descricao']}\n\n"
                f"**Materiais necessários:**\n"
                f"{chr(10).join(linhas_materiais)}\n\n"
                f"**Recompensa:**\n{recompensa}"
            ),
            inline=False,
        )

    embed.set_footer(
        text="Os pedidos são renovados diariamente."
    )

    return embed

# ==========================================
# EMBED DA OFICINA NATALINA
# ==========================================


def montar_embed_oficina():
    receitas = consultar_receitas()

    embed = discord.Embed(
        title="🛠️ Oficina Natalina",
        description=(
            "Bem-vindo à oficina! Aqui você pode fabricar "
            "presentes e ajudar a reconstruir a vila."
        ),
        color=discord.Color.from_rgb(80, 170, 255),
    )

    for indice, (receita_id, receita) in enumerate(receitas.items()):

        # Separador entre as receitas
        if indice > 0:
            embed.add_field(
                name="\u200b",
                value="━━━━━━━━━━━━━━━━━━",
                inline=False,
            )

        linhas = []

        for material_id, quantidade in receita["materiais"].items():
            dados = ITENS_NATALINOS.get(material_id, {})
            emoji = dados.get("emoji", "📦")
            nome = dados.get("nome", material_id)

            linhas.append(
                f"{emoji} **{nome}:** {quantidade}"
            )

        embed.add_field(
            name=f"{receita['emoji']} {receita['nome']}",
            value=(
                f"**Materiais necessários:**\n"
                f"{chr(10).join(linhas)}"
            ),
            inline=False,
        )

    embed.set_footer(
        text="Os materiais são consumidos durante a fabricação."
    )

    return embed

# ==========================================
# EMBED DA RECONSTRUÇÃO DA VILA
# ==========================================

def montar_embed_progresso_vila():
    melhorias = consultar_progresso_vila()

    embed = discord.Embed(
        title="🏘️ Reconstrução da Vila",
        description=(
            "A comunidade precisa trabalhar unida para "
            "restaurar o vilarejo e recuperar seu espírito natalino."
        ),
        color=discord.Color.from_rgb(80, 170, 255),
    )

    for melhoria in melhorias:
        linhas = []

        for material_id, dados in melhoria["materiais"].items():
            item = ITENS_NATALINOS.get(material_id, {})
            emoji = item.get("emoji", "📦")
            nome = item.get("nome", material_id)

            atual = dados["atual"]
            objetivo = dados["objetivo"]

            linhas.append(
                f"{emoji} **{nome}:** {atual}/{objetivo}"
            )

        if melhoria["concluida"]:
            status = "✅ **Concluída**"
        elif melhoria["ativa"]:
            status = "🟢 **Em construção**"
        else:
            status = "🔒 **Aguardando etapa anterior**"

        embed.add_field(
            name=f"{melhoria['emoji']} {melhoria['nome']}",
            value=(
                f"{melhoria['descricao']}\n\n"
                f"{chr(10).join(linhas)}\n\n"
                f"{status}"
            ),
            inline=False,
        )

    embed.set_footer(
        text="Cada material doado contribui para o progresso coletivo."
    )

    return embed


# ==========================================
# EMBED DO RANKING DA VILA
# ==========================================

def montar_embed_ranking_vila():
    ranking = consultar_ranking_vila(10)

    embed = discord.Embed(
        title="🏆 Heróis da Reconstrução",
        description=(
            "Os jogadores que mais contribuíram "
            "para restaurar a vila."
        ),
        color=discord.Color.gold(),
    )

    if not ranking:
        embed.description = "Ainda não existem contribuições registradas."
        return embed

    medalhas = ["🥇", "🥈", "🥉"]

    linhas = []

    for posicao, jogador in enumerate(ranking, start=1):
        medalha = (
            medalhas[posicao - 1]
            if posicao <= 3
            else f"`#{posicao}`"
        )

        linhas.append(
            f"{medalha} <@{jogador['user_id']}> — "
            f"**{jogador['total_materiais']} materiais**"
        )

    embed.add_field(
        name="Classificação",
        value="\n".join(linhas),
        inline=False,
    )

    return embed
    
# ==========================================
# EMBEDS DA EXPLORAÇÃO NATALINA
# ==========================================

def montar_embed_regioes(user_id):

    tentativas = consultar_tentativas(user_id)

    embed = discord.Embed(
        title="🧭 Exploração Natalina",
        description=(
            "Escolha uma região para iniciar sua aventura!\n\n"
            "Cada exploração possui três acontecimentos "
            "com decisões e recompensas."
        ),
        color=discord.Color.from_rgb(80, 170, 255),
    )

    embed.add_field(
        name="🎟️ Tentativas disponíveis",
        value=(
            f"**{tentativas['restantes']}**/"
            f"**{tentativas['limite']}** restantes hoje."
        ),
        inline=False,
    )

    for regiao_id, regiao in REGIOES.items():
        embed.add_field(
            name=f"{regiao['emoji']} {regiao['nome']}",
            value=regiao["descricao"],
            inline=False,
        )

    embed.set_footer(
        text="As tentativas são renovadas diariamente à meia-noite."
    )

    return embed


def montar_embed_evento(
    exploracao,
    resultado_escolha=None,
    recompensas=None,
):

    regiao = exploracao["regiao"]
    evento = exploracao["evento"]

    raridades = {
        "comum": "⚪ Comum",
        "incomum": "🟢 Incomum",
        "raro": "🟣 Raro",
        "lendario": "🌟 Lendário",
    }

    raridade = raridades.get(
        evento.get("raridade", "comum"),
        "⚪ Comum",
    )

    embed = discord.Embed(
        title=(
            f"{regiao['emoji']} {regiao['nome']}"
        ),
        description=(
            f"**Etapa {exploracao['etapa']}/"
            f"{exploracao['total_etapas']}**\n\n"
            f"**{evento['titulo']}**\n"
            f"{raridade}\n\n"
            f"{evento['narrativa']}"
        ),
        color=discord.Color.from_rgb(80, 170, 255),
    )

    if resultado_escolha is not None:

        embed.add_field(
            name="📖 Sua decisão",
            value=(
                f"{resultado_escolha['texto']}\n"
                f"{resultado_escolha['resultado']}"
            ),
            inline=False,
        )

        embed.add_field(
            name="🎁 Recompensa encontrada",
            value=(
                f"❄️ {resultado_escolha['flocos']} Flocos de Neve\n"
                f"⭐ {resultado_escolha['pontos']} Espírito Natalino"
            ),
            inline=False,
        )

    if recompensas is not None:

        linhas = []

        for item_id, quantidade in recompensas["itens"].items():
            dados = ITENS_NATALINOS.get(item_id, {})
            emoji = dados.get("emoji", "📦")
            nome = dados.get("nome", item_id)

            linhas.append(
                f"{emoji} **{nome}:** {quantidade}"
            )

        if not linhas:
            linhas.append("Nenhum material encontrado.")

        embed.add_field(
            name="🎒 Materiais acumulados",
            value="\n".join(linhas),
            inline=False,
        )

        embed.add_field(
            name="🏆 Resultado final",
            value=(
                f"❄️ **{recompensas['flocos']} Flocos de Neve**\n"
                f"⭐ **{recompensas['pontos']} Espírito Natalino**"
            ),
            inline=False,
        )

        embed.set_footer(
            text="Exploração concluída! Suas recompensas foram entregues."
        )

    else:
        embed.set_footer(
            text="Escolha uma ação para continuar sua aventura."
        )

    return embed

# ==========================================
# PAINEL DE EXPLORAÇÃO
# ==========================================

class BotaoFecharExploracao(discord.ui.Button):

    def __init__(self):
        super().__init__(
            label="Fechar",
            emoji="❌",
            style=discord.ButtonStyle.secondary,
        )

    async def callback(self, interaction):

        self.view.stop()

        await interaction.response.edit_message(
            content="Painel de exploração fechado.",
            embed=None,
            view=None,
        )


class BotaoEscolherRegiao(discord.ui.Button):

    def __init__(self, painel, regiao_id):
        self.painel = painel
        self.regiao_id = regiao_id

        regiao = REGIOES[regiao_id]

        super().__init__(
            label=regiao["nome"],
            emoji=regiao["emoji"],
            style=discord.ButtonStyle.primary,
        )

    async def callback(self, interaction):

        resultado = iniciar_exploracao(
            self.painel.user_id,
            self.regiao_id,
        )

        if not resultado["sucesso"]:

            if resultado["motivo"] == "aventura_ativa":
                exploracao = consultar_exploracao(
                    self.painel.user_id
                )

                if exploracao is not None:
                    await interaction.response.edit_message(
                        content=None,
                        embed=montar_embed_evento(exploracao),
                        view=PainelEscolhas(
                            self.painel.user_id,
                            exploracao["exploracao_id"],
                            exploracao["evento"]["escolhas"],
                        ),
                    )
                    return

                mensagem = (
                    "Você já possui uma aventura ativa, "
                    "mas não foi possível recuperá-la."
                )

            elif resultado["motivo"] == "limite_diario":
                mensagem = (
                    "Você já utilizou suas cinco explorações "
                    "de hoje. Volte amanhã!"
                )

            else:
                mensagem = "Não foi possível iniciar essa exploração."

            await interaction.response.send_message(
                f"⚠️ {mensagem}",
                ephemeral=True,
            )
            return

        exploracao = {
            "regiao": resultado["regiao"],
            "etapa": resultado["etapa"],
            "total_etapas": resultado["total_etapas"],
            "evento": resultado["evento"],
            "exploracao_id": resultado["exploracao_id"],
        }

        await interaction.response.edit_message(
            content=None,
            embed=montar_embed_evento(exploracao),
            view=PainelEscolhas(
                self.painel.user_id,
                resultado["exploracao_id"],
                resultado["evento"]["escolhas"],
            ),
        )


class PainelRegioes(discord.ui.View):

    def __init__(self, user_id):
        super().__init__(timeout=300)

        self.user_id = user_id

        for regiao_id in REGIOES:
            self.add_item(
                BotaoEscolherRegiao(self, regiao_id)
            )

        self.add_item(BotaoFecharExploracao())

    async def interaction_check(self, interaction):

        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "Esta exploração pertence a outro jogador.",
                ephemeral=True,
            )
            return False

        return True


# ==========================================
# BOTÕES DAS ESCOLHAS
# ==========================================

class BotaoEscolhaExploracao(discord.ui.Button):

    def __init__(
        self,
        painel,
        escolha,
    ):
        self.painel = painel
        self.escolha_id = escolha["id"]

        super().__init__(
            label=escolha["texto"],
            style=discord.ButtonStyle.primary,
        )

    async def callback(self, interaction):

        resultado = registrar_escolha(
            self.painel.user_id,
            self.painel.exploracao_id,
            self.escolha_id,
        )

        if not resultado["sucesso"]:

            motivos = {
                "exploracao_indisponivel": (
                    "Esta aventura não está mais disponível."
                ),
                "expirada": (
                    "Sua aventura expirou por inatividade."
                ),
                "escolha_invalida": (
                    "Essa escolha não está disponível."
                ),
                "estado_invalido": (
                    "Não foi possível recuperar o estado da aventura."
                ),
                "evento_indisponivel": (
                    "O acontecimento atual não está disponível."
                ),
            }

            mensagem = motivos.get(
                resultado["motivo"],
                "Não foi possível registrar sua escolha.",
            )

            await interaction.response.send_message(
                f"⚠️ {mensagem}",
                ephemeral=True,
            )
            return

        escolha = resultado["resultado_escolha"]

        if resultado["concluida"]:

            recompensas = resultado["recompensas"]

            exploracao = {
                "regiao": REGIOES[
                    self.painel.regiao_id
                ],
                "etapa": 3,
                "total_etapas": 3,
                "evento": {
                    "titulo": "Aventura concluída!",
                    "narrativa": (
                        "Você terminou sua jornada e conseguiu "
                        "retornar em segurança. Todas as suas "
                        "recompensas foram entregues!"
                    ),
                },
            }

            embed = montar_embed_evento(
                exploracao,
                resultado_escolha=escolha,
                recompensas=recompensas,
            )

            await interaction.response.edit_message(
                content=None,
                embed=embed,
                view=PainelExploracaoConcluida(),
            )
            return

        exploracao = {
            "regiao": REGIOES[
                self.painel.regiao_id
            ],
            "etapa": resultado["etapa"],
            "total_etapas": resultado["total_etapas"],
            "evento": resultado["proximo_evento"],
        }

        embed = montar_embed_evento(
            exploracao,
            resultado_escolha=escolha,
        )

        await interaction.response.edit_message(
            content=None,
            embed=embed,
            view=PainelEscolhas(
                self.painel.user_id,
                self.painel.exploracao_id,
                resultado["proximo_evento"]["escolhas"],
                regiao_id=self.painel.regiao_id,
            ),
        )


class PainelEscolhas(discord.ui.View):

    def __init__(
        self,
        user_id,
        exploracao_id,
        escolhas,
        regiao_id=None,
    ):
        super().__init__(timeout=900)

        self.user_id = user_id
        self.exploracao_id = exploracao_id

        self.regiao_id = regiao_id

        if self.regiao_id is None:
            exploracao = consultar_exploracao(user_id)

            if exploracao is not None:
                for regiao_id, dados in REGIOES.items():
                    if dados == exploracao["regiao"]:
                        self.regiao_id = regiao_id
                        break

        for escolha in escolhas:
            self.add_item(
                BotaoEscolhaExploracao(
                    self,
                    escolha,
                )
            )

        self.add_item(BotaoFecharExploracao())

    async def interaction_check(self, interaction):

        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "Esta aventura pertence a outro jogador.",
                ephemeral=True,
            )
            return False

        return True


class PainelExploracaoConcluida(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=180)

        self.add_item(BotaoFecharExploracao())


# ==========================================
# BOTÃO DE ABRIR EXPLORAÇÃO
# ==========================================

class BotaoAbrirExploracao(discord.ui.Button):

    def __init__(self, user_id):
        self.user_id = user_id

        super().__init__(
            label="Explorar",
            emoji="🧭",
            style=discord.ButtonStyle.success,
        )

    async def callback(self, interaction):

        exploracao = consultar_exploracao(
            self.user_id
        )

        if exploracao is not None:

            embed = montar_embed_evento(exploracao)

            view = PainelEscolhas(
                self.user_id,
                exploracao["exploracao_id"],
                exploracao["evento"]["escolhas"],
                regiao_id=next(
                    (
                        regiao_id
                        for regiao_id, dados in REGIOES.items()
                        if dados == exploracao["regiao"]
                    ),
                    None,
                ),
            )

            await interaction.response.send_message(
                content="🔄 Você possui uma aventura em andamento!",
                embed=embed,
                view=view,
                ephemeral=True,
            )
            return

        embed = montar_embed_regioes(
            self.user_id
        )

        await interaction.response.send_message(
            embed=embed,
            view=PainelRegioes(self.user_id),
            ephemeral=True,
        )

# ==========================================
# BOTÃO INDIVIDUAL DE ENTREGA
# ==========================================

class BotaoConcluirEntrega(discord.ui.Button):

    def __init__(self, painel, entrega):

        self.painel = painel
        self.entrega_id = entrega["id"]

        super().__init__(
            label="Entregar",
            emoji="📦",
            style=discord.ButtonStyle.success,
        )

    async def callback(self, interaction):

        resultado = concluir_entrega(
            self.painel.user_id,
            self.entrega_id,
        )

        if resultado.get("sucesso"):

            embed = montar_embed_entregas(
                self.painel.user_id
            )

            mensagem = (
                f"✅ **Entrega concluída: {resultado['titulo']}**\n\n"
                f"Você recebeu:\n"
                f"❄️ **{resultado['flocos']} Flocos de Neve**\n"
                f"⭐ **{resultado['pontos']} Espírito Natalino**"
            )
            
        else:
            motivo = resultado.get("motivo")
            if motivo == "materiais_insuficientes":
                
                faltantes = resultado.get("faltantes", {})
                linhas = []

                for item_id, quantidade in faltantes.items():

                    dados = ITENS_NATALINOS.get(item_id)

                    if dados:
                        emoji = dados["emoji"]
                        nome = dados["nome"]
                    else:
                        emoji = "📦"
                        nome = item_id

                    linhas.append(
                        f"{emoji} **{nome}:** faltam {quantidade}"
                    )

                mensagem = (
                    "Você ainda não possui todos os materiais necessários:\n\n"
                    + "\n".join(linhas)
                )

            elif motivo == "expirada":

                mensagem = "Esse pedido já expirou."

            elif motivo == "indisponivel":

                mensagem = "Esse pedido já foi concluído ou não está mais disponível."

            else:

                mensagem = "Não foi possível encontrar essa entrega."

            await interaction.response.send_message(
                f"⚠️ {mensagem}",
                ephemeral=True,
            )


# ==========================================
# BOTÕES DE CONTROLE DAS ENTREGAS
# ==========================================

class BotaoAtualizarEntregas(discord.ui.Button):

    def __init__(self, painel):

        self.painel = painel

        super().__init__(
            label="Atualizar",
            emoji="🔄",
            style=discord.ButtonStyle.primary,
        )

    async def callback(self, interaction):

        self.painel.recarregar_botoes()

        embed = montar_embed_entregas(
            self.painel.user_id
        )

        await interaction.response.edit_message(
            content=None,
            embed=embed,
            view=self.painel,
        )


class BotaoFecharEntregas(discord.ui.Button):

    def __init__(self, painel):

        self.painel = painel

        super().__init__(
            label="Fechar",
            emoji="❌",
            style=discord.ButtonStyle.secondary,
        )

    async def callback(self, interaction):

        self.painel.stop()

        await interaction.response.edit_message(
            content="Painel de entregas fechado.",
            embed=None,
            view=None,
        )


# ==========================================
# PAINEL DE ENTREGAS
# ==========================================

class PainelEntregas(discord.ui.View):

    def __init__(self, user_id):

        super().__init__(timeout=300)

        self.user_id = user_id

        self.recarregar_botoes()

    async def interaction_check(self, interaction):

        if interaction.user.id != self.user_id:

            await interaction.response.send_message(
                "Este painel de entregas pertence a outro jogador.",
                ephemeral=True,
            )

            return False

        return True

    def recarregar_botoes(self):

        self.clear_items()

        entregas = consultar_entregas(self.user_id)

        for entrega in entregas:

            self.add_item(
                BotaoConcluirEntrega(self, entrega)
            )

        self.add_item(
            BotaoAtualizarEntregas(self)
        )

        self.add_item(
            BotaoFecharEntregas(self)
        )
        
# ==========================================
# VIEW DO INVENTÁRIO
# ==========================================

class PainelInventario(discord.ui.View):

    def __init__(self, user_id):

        super().__init__(timeout=180)

        self.user_id = user_id

    # ----------------------------------
    # VERIFICAR PROPRIETÁRIO
    # ----------------------------------

    async def interaction_check(self, interaction):

        if interaction.user.id != self.user_id:

            await interaction.response.send_message(
                "Este inventário pertence a outro jogador.",

                ephemeral=True,
            )

            return False

        return True

    # ----------------------------------
    # ATUALIZAR INVENTÁRIO
    # ----------------------------------

    @discord.ui.button(
        label="Atualizar",

        emoji="🔄",

        style=discord.ButtonStyle.primary,
    )
    async def atualizar(self, interaction, button):

        embed = montar_embed_inventario(
            self.user_id
        )

        await interaction.response.edit_message(
            embed=embed,

            view=self,
        )

    # ----------------------------------
    # FECHAR INVENTÁRIO
    # ----------------------------------

    @discord.ui.button(
        label="Fechar",

        emoji="❌",

        style=discord.ButtonStyle.secondary,
    )
    async def fechar(self, interaction, button):

        self.stop()

        await interaction.response.edit_message(
            content="Inventário fechado.",

            embed=None,

            view=None,
        )


# ==========================================
# MODAL DE QUANTIDADE DA OFICINA
# ==========================================
class ModalQuantidadeOficina(discord.ui.Modal):

    def __init__(self, painel, acao, item_id, nome):
        super().__init__(title=f"Quantidade — {nome}")

        self.painel = painel
        self.acao = acao
        self.item_id = item_id

        self.quantidade = discord.ui.TextInput(
            label="Quantidade",
            placeholder="Digite um número inteiro",
            default="1",
            min_length=1,
            max_length=5,
        )

        self.add_item(self.quantidade)



    async def on_submit(self, interaction):
        try:
            quantidade = int(self.quantidade.value)
        except ValueError:
            await interaction.response.send_message(
                "Digite uma quantidade numérica válida.",
                ephemeral=True,
            )
            return

        if quantidade <= 0:
            await interaction.response.send_message(
                "A quantidade precisa ser maior que zero.",
                ephemeral=True,
            )
            return

        if self.acao == "fabricar":
            resultado = fabricar_presente(
                interaction.user.id,
                self.item_id,
                quantidade,
            )
        else:
            resultado = contribuir_para_vila(
                interaction.user.id,
                self.item_id,
                quantidade,
            )

        if not resultado["sucesso"]:
            motivos = {
                "materiais_insuficientes": (
                    "Você não possui materiais suficientes."
                ),
                "quantidade_acima_do_necessario": (
                    f"Você pode contribuir com no máximo "
                    f"{resultado.get('restante', 0)} unidades."
                ),
                "material_nao_necessario": (
                    "Esse material não é necessário para a melhoria atual."
                ),
                "vila_completa": (
                    "Todas as melhorias da vila já foram concluídas!"
                ),
                "item_nao_e_material": (
                    "Esse item não pode ser utilizado na reconstrução."
                ),
                "receita_inexistente": (
                    "Essa receita não existe."
                ),
            }

            mensagem = motivos.get(
                resultado.get("motivo"),
                "Não foi possível realizar essa operação.",
            )

            await interaction.response.send_message(
                f"⚠️ {mensagem}",
                ephemeral=True,
            )
            return

        if self.acao == "fabricar":
            mensagem = (
                f"✅ Você fabricou **{resultado['quantidade']}x "
                f"{resultado['nome']}**!"
            )
        else:
            mensagem = (
                f"🎁 Você contribuiu com **{quantidade}x** "
                f"material para **{resultado['melhoria']}**!"
            )

            if resultado["melhoria_concluida"]:
                mensagem += (
                    f"\n\n🎉 **Melhoria concluída!**\n"
                    f"{resultado['beneficio']}"
                )

        await interaction.response.send_message(
            content=mensagem,
            ephemeral=True,
        )

        await interaction.response.send_message(
            content=mensagem,
            ephemeral=True,
        )

# ==========================================
# BOTÃO DE FABRICAÇÃO
# ==========================================

class BotaoFabricarPresente(discord.ui.Button):

    def __init__(self, painel, receita_id, nome, emoji):
        self.painel = painel
        self.receita_id = receita_id

        super().__init__(
            label=nome,
            emoji=emoji,
            style=discord.ButtonStyle.success,
        )

    async def callback(self, interaction):

        await interaction.response.send_modal(
            ModalQuantidadeOficina(
                self.painel,
                "fabricar",
                self.receita_id,
                self.label,
            )
        )


# ==========================================
# BOTÃO DE CONTRIBUIÇÃO
# ==========================================

class BotaoDoarMaterial(discord.ui.Button):

    def __init__(self, painel, material_id):
        self.painel = painel
        self.material_id = material_id

        dados = ITENS_NATALINOS[material_id]

        super().__init__(
            label=dados["nome"],
            emoji=dados["emoji"],
            style=discord.ButtonStyle.primary,
        )

    async def callback(self, interaction):

        await interaction.response.send_modal(
            ModalQuantidadeOficina(
                self.painel,
                "contribuir",
                self.material_id,
                self.label,
            )
        )

# ==========================================
# BOTÃO DE ATUALIZAÇÃO DA OFICINA
# ==========================================

class BotaoAtualizarOficina(discord.ui.Button):

    def __init__(self, painel):
        self.painel = painel

        super().__init__(
            label="Atualizar",
            emoji="🔄",
            style=discord.ButtonStyle.secondary,
        )

    async def callback(self, interaction):

        self.painel.recarregar_botoes()

        await interaction.response.edit_message(
            content=None,
            embed=montar_embed_oficina(),
            view=self.painel,
        )

# ==========================================
# PAINEL DA OFICINA
# ==========================================

class PainelOficina(discord.ui.View):

    def __init__(self, user_id):
        super().__init__(timeout=300)

        self.user_id = user_id
        self.recarregar_botoes()

    async def interaction_check(self, interaction):

        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "Esta oficina pertence a outro jogador.",
                ephemeral=True,
            )
            return False

        return True

    def recarregar_botoes(self):

        self.clear_items()

        self.add_item(
            BotaoFabricarPresente(
                self,
                "presente_vermelho",
                "Presente Vermelho",
                "🎁",
            )
        )

        self.add_item(
            BotaoFabricarPresente(
                self,
                "presente_dourado",
                "Presente Dourado",
                "🌟",
            )
        )

        melhorias = consultar_progresso_vila()

        melhoria_atual = next(
            (
                melhoria
                for melhoria in melhorias
                if melhoria["ativa"]
            ),
            None,
        )

        if melhoria_atual is not None:
            for material_id in melhoria_atual["materiais"]:
                self.add_item(
                    BotaoDoarMaterial(
                        self,
                        material_id,
                    )
                )

        self.add_item(BotaoVerVila(self))
        self.add_item(BotaoVerRankingVila(self))
        self.add_item(BotaoAtualizarOficina(self))
        self.add_item(BotaoFecharOficina(self))


# ==========================================
# BOTÃO DE PROGRESSO DA VILA
# ==========================================

class BotaoVerVila(discord.ui.Button):

    def __init__(self, painel):
        self.painel = painel

        super().__init__(
            label="Progresso da Vila",
            emoji="🏘️",
            style=discord.ButtonStyle.primary,
        )

    async def callback(self, interaction):

        self.painel.recarregar_botoes()

        await interaction.response.edit_message(
            content=None,
            embed=montar_embed_progresso_vila(),
            view=self.painel,
        )


# ==========================================
# BOTÃO DE RANKING
# ==========================================

class BotaoVerRankingVila(discord.ui.Button):

    def __init__(self, painel):
        self.painel = painel

        super().__init__(
            label="Ranking",
            emoji="🏆",
            style=discord.ButtonStyle.secondary,
        )

    async def callback(self, interaction):

        await interaction.response.edit_message(
            content=None,
            embed=montar_embed_ranking_vila(),
            view=self.painel,
        )


# ==========================================
# BOTÃO DE FECHAR A OFICINA
# ==========================================

class BotaoFecharOficina(discord.ui.Button):

    def __init__(self, painel):
        self.painel = painel

        super().__init__(
            label="Fechar",
            emoji="❌",
            style=discord.ButtonStyle.danger,
        )

    async def callback(self, interaction):

        self.painel.stop()

        await interaction.response.edit_message(
            content="Oficina fechada.",
            embed=None,
            view=None,
        )

# ==========================================
# EXPLORAÇÃO NATALINA — COMPONENTS V2
# ==========================================

class BotaoExploracao(discord.ui.Button):

    def __init__(self, painel, label, emoji, acao, valor=None, estilo=None):
        self.painel = painel
        self.acao = acao
        self.valor = valor

        super().__init__(
            label=label,
            emoji=emoji,
            style=estilo or discord.ButtonStyle.primary,
        )

    async def callback(self, interaction):
        await self.painel.executar(
            interaction,
            self.acao,
            self.valor,
        )


class PainelExploracao(discord.ui.LayoutView):

    def __init__(self, user_id):
        super().__init__(timeout=300)

        self.user_id = user_id
        self.mensagem_status = None
        self.resultado_final = None

        self.montar()

    async def interaction_check(self, interaction):

        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "Esta exploração pertence a outro jogador.",
                ephemeral=True,
            )
            return False

        return True

    # ----------------------------------
    # FORMATAÇÃO DAS RECOMPENSAS
    # ----------------------------------

    def formatar_recompensas(self, recompensas):

        linhas = []

        flocos = recompensas.get("flocos", 0)
        pontos = recompensas.get("pontos", 0)
        itens = recompensas.get("itens", {})

        if flocos:
            linhas.append(
                f"❄️ **{flocos} Flocos de Neve**"
            )

        if pontos:
            linhas.append(
                f"⭐ **{pontos} Espírito Natalino**"
            )

        for item_id, quantidade in itens.items():

            dados = ITENS_NATALINOS.get(item_id, {})

            emoji = dados.get("emoji", "📦")
            nome = dados.get("nome", item_id)

            linhas.append(
                f"{emoji} **{nome}:** {quantidade}"
            )

        return "\n".join(linhas) if linhas else "Nenhuma recompensa."

    # ----------------------------------
    # MONTAR INTERFACE
    # ----------------------------------

    def montar(self):

        self.clear_items()

        container = discord.ui.Container()
        container.accent_color = discord.Color.from_rgb(
            80, 170, 255
        )

        container.add_item(
            discord.ui.TextDisplay(
                "# ❄️ Exploração Natalina"
            )
        )

        container.add_item(
            discord.ui.Separator(
                spacing=discord.SeparatorSpacing.large
            )
        )

        # ----------------------------------
        # RESULTADO FINAL
        # ----------------------------------

        if self.resultado_final is not None:

            container.add_item(
                discord.ui.TextDisplay(
                    "## 🎉 Exploração concluída!"
                )
            )

            container.add_item(
                discord.ui.TextDisplay(
                    self.resultado_final
                )
            )

            container.add_item(
                discord.ui.Separator()
            )

            container.add_item(
                discord.ui.TextDisplay(
                    "As recompensas foram adicionadas "
                    "ao seu inventário natalino."
                )
            )

            self.add_item(container)
            return

        # ----------------------------------
        # CONSULTAR AVENTURA ATIVA
        # ----------------------------------

        exploracao = consultar_exploracao(
            self.user_id
        )

        if exploracao is not None:

            regiao = exploracao["regiao"]
            evento = exploracao["evento"]

            container.add_item(
                discord.ui.TextDisplay(
                    f"## {regiao['emoji']} {regiao['nome']}"
                )
            )

            container.add_item(
                discord.ui.TextDisplay(
                    f"**Etapa:** {exploracao['etapa']}"
                    f"/{exploracao['total_etapas']}"
                )
            )

            container.add_item(
                discord.ui.Separator()
            )

            container.add_item(
                discord.ui.TextDisplay(
                    f"### {evento['titulo']}\n"
                    f"{evento['narrativa']}"
                )
            )

            container.add_item(
                discord.ui.Separator()
            )

            container.add_item(
                discord.ui.TextDisplay(
                    "### O que você deseja fazer?"
                )
            )

            botoes = []

            for escolha in evento["escolhas"]:

                botoes.append(
                    BotaoExploracao(
                        self,
                        escolha["texto"],
                        None,
                        "escolha",
                        escolha["id"],
                        discord.ButtonStyle.primary,
                    )
                )

            if botoes:
                container.add_item(
                    discord.ui.ActionRow(*botoes)
                )

            if self.mensagem_status:

                container.add_item(
                    discord.ui.Separator()
                )

                container.add_item(
                    discord.ui.TextDisplay(
                        self.mensagem_status
                    )
                )

            self.add_item(container)
            return

        # ----------------------------------
        # MENU DE REGIÕES
        # ----------------------------------

        tentativas = consultar_tentativas(
            self.user_id
        )

        container.add_item(
            discord.ui.TextDisplay(
                "Escolha uma região para começar sua aventura."
            )
        )

        container.add_item(
            discord.ui.Separator()
        )

        container.add_item(
            discord.ui.TextDisplay(
                f"**Explorações disponíveis hoje:** "
                f"{tentativas['restantes']}/{tentativas['limite']}"
            )
        )

        if tentativas["restantes"] <= 0:

            container.add_item(
                discord.ui.TextDisplay(
                    "⚠️ Você já utilizou todas as suas "
                    "explorações de hoje. Volte amanhã!"
                )
            )


        else:

            for regiao_id, dados in REGIOES.items():

                container.add_item(
                    discord.ui.Separator()
                )

                container.add_item(
                    discord.ui.ActionRow(
                        BotaoExploracao(
                            self,
                            dados["nome"],
                            dados["emoji"],
                            "regiao",
                            regiao_id,
                            discord.ButtonStyle.primary,
                        )
                    )
                )

                container.add_item(
                    discord.ui.TextDisplay(
                        dados["descricao"]
                    )
                )

        if self.mensagem_status:

            container.add_item(
                discord.ui.Separator()
            )

            container.add_item(
                discord.ui.TextDisplay(
                    self.mensagem_status
                )
            )

        container.add_item(
            discord.ui.Separator()
        )
        
        self.add_item(container)

    # ----------------------------------
    # PROCESSAR INTERAÇÕES
    # ----------------------------------

    async def executar(self, interaction, acao, valor=None):

        if acao == "fechar":

            self.stop()

            await interaction.response.edit_message(
                view=None
            )
            return

        if acao == "atualizar":

            self.mensagem_status = None
            self.montar()

            await interaction.response.edit_message(
                view=self
            )
            return

        # ----------------------------------
        # INICIAR EXPLORAÇÃO
        # ----------------------------------

        if acao == "regiao":

            resultado = iniciar_exploracao(
                self.user_id,
                valor,
            )

            if not resultado["sucesso"]:

                motivos = {
                    "regiao_invalida": "Essa região não existe.",
                    "aventura_ativa": "Você já possui uma exploração ativa.",
                    "limite_diario": "Você já utilizou suas cinco explorações de hoje.",
                    "sem_eventos_disponiveis": "Não há acontecimentos disponíveis nessa região.",
                }

                self.mensagem_status = (
                    "⚠️ "
                    + motivos.get(
                        resultado.get("motivo"),
                        "Não foi possível iniciar a exploração.",
                    )
                )

            else:

                self.mensagem_status = (
                    f"🧭 Você começou uma exploração em "
                    f"**{resultado['regiao']['nome']}**!"
                )

        # ----------------------------------
        # REGISTRAR ESCOLHA
        # ----------------------------------

        elif acao == "escolha":

            exploracao = consultar_exploracao(
                self.user_id
            )

            if exploracao is None:

                self.mensagem_status = (
                    "⚠️ Sua exploração não está mais disponível."
                )

            else:

                resultado = registrar_escolha(
                    self.user_id,
                    exploracao["exploracao_id"],
                    valor,
                )

                if not resultado["sucesso"]:

                    motivos = {
                        "expirada": "Sua exploração expirou.",
                        "exploracao_indisponivel": "Essa exploração não está mais disponível.",
                        "escolha_invalida": "Essa escolha não é válida.",
                        "evento_indisponivel": "O acontecimento não está mais disponível.",
                    }

                    self.mensagem_status = (
                        "⚠️ "
                        + motivos.get(
                            resultado.get("motivo"),
                            "Não foi possível registrar sua escolha.",
                        )
                    )

                else:

                    escolha = resultado["resultado_escolha"]

                    self.mensagem_status = (
                        f"### {escolha['texto']}\n"
                        f"{escolha['resultado']}"
                    )

                    if resultado["concluida"]:

                        recompensas = self.formatar_recompensas(
                            resultado["recompensas"]
                        )

                        self.resultado_final = (
                            f"**Resultado da última escolha:**\n"
                            f"{escolha['resultado']}\n\n"
                            f"**Recompensas recebidas:**\n"
                            f"{recompensas}"
                        )

        self.montar()

        await interaction.response.edit_message(
            view=self
        )

# ==========================================
# PAINEL PRINCIPAL DO NATAL
# ==========================================

class PainelNatal(discord.ui.View):

    def __init__(self, user_id):

        super().__init__(timeout=300)

        self.user_id = user_id

        self.recarregar_botoes()
    # ----------------------------------
    # VERIFICAR PROPRIETÁRIO
    # ----------------------------------

    async def interaction_check(self, interaction):

        if interaction.user.id != self.user_id:

            await interaction.response.send_message(
                "Este painel pertence a outro jogador.",

                ephemeral=True,
            )

            return False

        return True

    # ----------------------------------
    # ABRIR INVENTÁRIO
    # ----------------------------------

    @discord.ui.button(
        label="Inventário",

        emoji="🎒",

        style=discord.ButtonStyle.primary,
    )
    async def inventario(self, interaction, button):

        embed = montar_embed_inventario(
            self.user_id
        )

        await interaction.response.send_message(
            embed=embed,

            view=PainelInventario(self.user_id),

            ephemeral=True,
        )
        
    # ----------------------------------
    # ABRIR ENTREGAS
    # ----------------------------------

    @discord.ui.button(
        label="Entregas",
        emoji="📦",
        style=discord.ButtonStyle.success,
    )
    async def entregas(self, interaction, button):

        embed = montar_embed_entregas(
            self.user_id
        )

        await interaction.response.send_message(
            embed=embed,
            view=PainelEntregas(self.user_id),
            ephemeral=True,
        )

    # ----------------------------------
    # ABRIR OFICINA NATALINA
    # ----------------------------------

    @discord.ui.button(
        label="Oficina",
        emoji="🛠️",
        style=discord.ButtonStyle.primary,
    )
    async def oficina(self, interaction, button):

        embed = montar_embed_oficina()

        await interaction.response.send_message(
            embed=embed,
            view=PainelOficina(self.user_id),
            ephemeral=True,
        )

    # ----------------------------------
    # ABRIR EXPLORAÇÃO
    # ----------------------------------

    @discord.ui.button(
        label="Explorar",
        emoji="🧭",
        style=discord.ButtonStyle.success,
    )
    async def explorar(self, interaction, button):

        painel = PainelExploracao(
            self.user_id
        )

        await interaction.response.send_message(
            view=painel,
            ephemeral=True,
        )

# ==========================================
# CONFIGURAR EVENTO
# ==========================================

def configurar_natal(bot):

    inicializar_banco()
    inicializar_oficina()
    
    @bot.command(name="natal")
    async def natal(ctx):

        embed = discord.Embed(
            title=f"🎄 {NOME_EVENTO}",

            description=(
                "A estrela mágica foi fragmentada!\n\n"
                "Explore regiões congeladas, encontre presentes, "
                "ajude a oficina e prepare-se para enfrentar "
                "o Guardião do Inverno."
            ),

            color=discord.Color.from_rgb(80, 170, 255),
        )

        embed.add_field(
            name="❄️ Economia",

            value="Flocos de Neve e materiais natalinos.",

            inline=False,
        )

        embed.add_field(
            name="⏳ Duração",

            value=f"{DURACAO_EVENTO} dias",

            inline=True,
        )

        if EVENTO_ATIVO:

            status = "🟢 Evento em andamento."

        else:

            status = "🟡 O evento ainda não começou."

        embed.add_field(
            name="📅 Status",

            value=status,

            inline=True,
        )

        embed.set_footer(
            text="Natal das Mil Estrelas • Sakurai"
        )

        await ctx.send(
            embed=embed,

            view=PainelNatal(ctx.author.id),
        )
