import discord

from .banco import inicializar_banco

from .configuracoes import (
    NOME_EVENTO,
    EVENTO_ATIVO,
    DURACAO_EVENTO,
    ITENS_NATALINOS,
)

from .inventario import consultar_inventario


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


# ==========================================
# CONFIGURAR EVENTO
# ==========================================

def configurar_natal(bot):

    inicializar_banco()

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
