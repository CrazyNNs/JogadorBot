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
