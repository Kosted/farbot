from discord.ext import commands

import db_methods
from helpers import make_embed, get_nick_or_name, hard_prefix_check


class BotEvents(commands.Cog):


    def __init__(self, bot, permission_obj, log_channel):
        self.log_channel = log_channel
        self.permission_obj = permission_obj
        self.bot = bot
        self.guild_prefixes_set = self.permission_obj.get_prefixes_set()


    @commands.command(pass_content=True)
    async def t(self, ctx):
        url = 'https://i.gifer.com/RTjF.gif'
        embed_obj = make_embed(None, None, get_nick_or_name(ctx.author), url, 'футерэ',
                               url,
                               url, asdf='asdfasdf', jasdjf='ifjaidjflasjdflsjadf' )
        await ctx.send(embed=embed_obj)

    @commands.Cog.listener()
    async def on_reaction_remove(self, reaction, user):
        # if reaction.name == "test_farbot":
        #
        #     await channel.send(user.name)
        # else:
        print("remove")

    # @commands.Cog.listener()
    # async def on_message(self, message):
    #     if message.author != self.bot.user:
    #         print("prefix", await self.bot.get_prefix(message), message.content)
    #
    #         guild_prefix = self.permission_obj.get_guild_prefix(message.guild.id)
    #
    #         if hard_prefix_check(guild_prefix, self.guild_prefixes_set):
    #             if message.content.startswith(guild_prefix):
    #                 message.content = 'f.' + message.content[len(guild_prefix):]
    #             else:
    #                 print("префикс гильдии неверен")
    #                 return
    #
    #         await self.bot.process_commands(message)
    #     return

    @commands.Cog.listener()
    async def on_member_join(self, member):
        db_methods.insert_request(columns=('guild_id', 'member_id', 'member_name', 'activ', 'join_date'),
                                  values=(member.guild.id, member.id, member.name + '#' + member.discriminator,
                                          True,
                                          member.joined_at),
                                  table="member")

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        member_db_info = db_methods.select_request(table='member',
                                                   where=(
                                                       ("guild_id", member.guild.id), ('member_id', member.id)))[0]

        log_message = member_db_info['member_name'] + ' ушел. Присоединился он ' + str(
            member.joined_at.day) + '.' + str(
            member.joined_at.month) + '.' + str(member.joined_at.year)
        # embed_log_message = make_embed()
        db_methods.delete_request(table='member', where=(("guild_id", member.guild.id), ('member_id', member.id)))

        await self.log_channel.send(str(log_message))

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.member != self.bot.user:
            channel = self.bot.get_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)
            if message.author == self.bot.user and payload.emoji.name == "❌":
                await message.delete()
            #     TODO: добавить настройку включения выключения логирования эмодзи
            # log_message = get_nick_or_name(payload.member) + " add: " + payload.emoji.name + ' on ' + channel.name
            # print(log_message)
            # await log_channel.send(log_message)