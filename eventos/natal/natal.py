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
from .oficina import inicializar_oficina

# ==========================================
# MONTAR EMBED DO INVENTÁRIO
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

    for entrega in entregas:

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

            self.painel.recarregar_botoes()

            await interaction.response.edit_message(
                content=mensagem,
                embed=embed,
                view=self.painel,
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
# PAINEL PRINCIPAL DO NATAL
# ==========================================

class PainelNatal(discord.ui.View):

    def __init__(self, user_id):

        super().__init__(timeout=300)

        self.user_id = user_id

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
