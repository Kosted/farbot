import discord
from discord.ext import commands
from discord_token import DEBUG


class BotChecks(commands.Cog):


    def __init__(self, bot, permission_obj, log_channel, debug_channel, FARGUS_TEAM, FARGUS_TEAM_OWNER):
        self.FARGUS_TEAM_OWNER = FARGUS_TEAM_OWNER
        self.FARGUS_TEAM = FARGUS_TEAM
        self.debug_channel = debug_channel
        self.log_channel = log_channel
        self.permission_obj = permission_obj
        self.bot = bot


    # @commands.check
    # async def globally_debug_mod_check(self, ctx):
    #     # global debug_channel
    #     # global log_channel
    #     print(DEBUG, self.FARGUS_TEAM.id, ctx.guild.id, self.FARGUS_TEAM_OWNER.name, ctx.author.name, ctx.channel.name,
    #           self.debug_channel.name)
    #     if DEBUG and self.FARGUS_TEAM == ctx.guild and self.FARGUS_TEAM_OWNER == ctx.author and ctx.channel == self.debug_channel:
    #         print("debug mod Fargus in test_farbot channel")
    #         return True
    #     elif not DEBUG:
    #         if ctx.channel == self.debug_channel:
    #             if ctx.author != self.FARGUS_TEAM_OWNER:
    #                 print("not debug not Fargus in in test_farbot channel")
    #                 return True
    #             else:
    #                 print("not debug Fargus in test_farbot channel")
    #                 return False
    #         else:
    #             print("not debug anybody not in test_farbot channel")
    #             return True
    #     else:
    #         print("debug anybody or not in test_farbot channel")
    #         return False