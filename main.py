from operator import itemgetter

from checks import BotChecks
from events import BotEvents
from helpers import get_role_by_name, get_nick_or_name, list_to_sql_array
import dir_helper
import google_voice
import text_converter
import discord_token
import db_methods

import discord
import datetime
from discord.ext import commands
import logging
import random
import math

logger = logging.getLogger('discord')
logging.basicConfig(level=logging.INFO)

TOKEN = discord_token.TOKEN

# dev guild
FARGUS_TEAM_GUILD_ID = 539879904506806282
debug_channel_id = 692081802692526150
debug_channel = None
log_channel_id = 701183371166089276
log_channel = None
FARGUS_TEAM = None
FARGUS_TEAM_OWNER = None
DEBUG = discord_token.DEBUG

guild_prefixes_set = set()
bot_prefixes = ['f.']

global bot
bot = commands.Bot(command_prefix=bot_prefixes)  # инициализируем бота с префиксом '.'
# client = discord.Client()

global voice_client

file_list = dir_helper.file_list("voice_files/")


def get_bot():
    return bot


def int_dict():
    temp_dict_for_call_needed_constructor = dict([(1, 2)])
    temp_dict_for_call_needed_constructor.clear()
    return temp_dict_for_call_needed_constructor


class Permission:
    global_black_list = int_dict()  # list['member_id'] = {'name': str, 'reason': str'}
    global_white_list = int_dict()
    all_presets = {}  # {commands: set{commands}, priority: int}
    owners = int_dict()  # owners[guild_id] = {'id': id, 'name': owner_name}
    # prefixes = set()
    db_guilds = int_dict()
    '''
    db_guilds[guild_id] = { 'name': name, 'prefix': prefix, 'enable_presets': {0} 'black_role': {1}, 'white_role': {1}, 'black_member': {2}, 'white_member': {2}
    (0) = {'preset1', 'preset2', ...}
    (1)['role_id'] = set{'command1', 'command2', ...}
    '''

    def __init__(self):
        # fill global_black_list
        db_result_dict = db_methods.select_request(table='global_black_list')
        for row in db_result_dict:
            self.global_black_list[row['member_id']] = {'name': row['member_name'], 'reason': row['reason']}

        # fill global_white_list
        db_result_dict = db_methods.select_request(table='global_white_list')
        for row in db_result_dict:
            self.global_white_list[row['member_id']] = {'name': row['member_name'], 'reason': row['reason']}
        self.global_white_list[FARGUS_TEAM_OWNER.id] = {'name': 'Fargus', 'reason': 'bot creator'}

        # fill all_presets
        db_result_dict = db_methods.select_request(table='command_presets')
        for row in db_result_dict:
            self.all_presets[row['preset_name']] = {'commands': [command for command in row['commands']],
                                                    'priority': row['priority']}
            # self.all_presets[row['preset_name']]['priority'] = row['priority']
        self.all_presets['dev'] = {'commands': [command.name for command in bot.commands], 'priority': 0}
        # self.all_presets['dev']['priority'] = 0

        # fill guild_permisson
        db_result_dict = db_methods.select_request(table='guild', columns=('guild_id', 'guild_name', 'prefix'))

        exist_db_guild = [row['guild_id'] for row in db_result_dict]
        new_guild_was_added_to_db = False  # флаг для необходимости совершить новый запрос к обновившемуся списку гильдий
        for guild in bot.guilds:
            if guild.id not in exist_db_guild:
                init_guild(guild)
                new_guild_was_added_to_db = True
            self.db_guilds[guild.id] = {'black_role': int_dict(),
                                        'white_role': int_dict(),
                                        'black_member': int_dict(),
                                        'white_member': int_dict(),
                                        'enable_presets': set()}

        if new_guild_was_added_to_db:
            db_result_dict = db_methods.select_request(table='guild', columns=('guild_id', 'guild_name', 'prefix'))

        # fill guild prefix and name
        for row in db_result_dict:
            guild = self.db_guilds[row['guild_id']]
            guild['prefix'] = row['prefix']
            guild['name'] = row['guild_name']

        # fill guild enable presets
        db_result_dict = db_methods.select_request(table='enable_presets', columns=('guild_id', 'enable_preset'))
        for row in db_result_dict:
            self.db_guilds[row['guild_id']]['enable_presets'].add(row['enable_preset'])

        # fill role_black_list
        db_result_dict = db_methods.select_request(table='role_black_list',
                                                   columns=('guild_id', 'role_id', 'command_name'))
        for row in db_result_dict:
            if row['role_id'] in self.db_guilds[row['guild_id']]['black_role']:
                self.db_guilds[row['guild_id']]['black_role'][row['role_id']].add(row['command_name'])
            else:
                self.db_guilds[row['guild_id']]['black_role'][row['role_id']] = {row['command_name']}

        # fill role_white_list
        db_result_dict = db_methods.select_request(table='role_white_list',
                                                   columns=('guild_id', 'role_id', 'command_name'))
        for row in db_result_dict:
            if row['role_id'] in self.db_guilds[row['guild_id']]['white_role']:
                self.db_guilds[row['guild_id']]['white_role'][row['role_id']].add(row['command_name'])
            else:
                self.db_guilds[row['guild_id']]['white_role'][row['role_id']] = {row['command_name']}

        # TODO: fill member black and white lists

        # fill owners
        db_result_dict = db_methods.select_request(table='owners', columns=('guild_id', 'owner_id', 'owner_name'))
        for row in db_result_dict:
            self.owners[row['guild_id']] = {'id': row['owner_id'], 'name': row['owner_name']}

    def check_member_in_global_black_list(self, ctx):
        if ctx.author.id in self.global_black_list.keys():
            return True

    def check_member_in_global_white_list(self, ctx):
        if ctx.author.id in self.global_white_list.keys():
            return True

    def check_command_enable_on_this_guild(self, ctx):
        # TODO: неоптимально каждый раз формаровать список доступных комманд
        guild_enable_commands = self.get_enable_commands_for_guild(ctx.guild)

        if ctx.command.name in guild_enable_commands:
            return True
        else:
            return False

    def check_member_is_owner(self, ctx):
        if ctx.guild.owner_id == ctx.author.id and self.owners[ctx.guild.id]['id'] == ctx.author.id:
            return True
        else:
            return False

    def check_member_role_in_black_list(self, ctx):
        for role in ctx.author.roles:
            if role.id in self.db_guilds[ctx.guild.id]['black_role'].keys():
                if ctx.command.name in self.db_guilds[ctx.guild.id]['black_role'][role.id]:
                    return True
        return False

    def check_member_role_in_white_list(self, ctx):
        for role in ctx.author.roles:
            if role.id in self.db_guilds[ctx.guild.id]['white_role'].keys():
                if ctx.command.name in self.db_guilds[ctx.guild.id]['white_role'][role.id]:
                    return True
        return False

    def get_prefixes_set(self):
        prefixes = set()
        for guild_id in self.db_guilds:
            prefixes.add(self.db_guilds[guild_id]['prefix'])
        prefixes.add('f.')
        return prefixes

    def get_guild_prefix(self, guild_id):
        return self.db_guilds[guild_id]['prefix']

    def set_guild_prefix(self, guild_id, new_prefix):
        self.db_guilds[guild_id]['prefix'] = new_prefix

    def add_command_preset(self, guild_id, preset_name):
        self.db_guilds[guild_id]['enable_presets'].add(preset_name)

    def get_enable_commands_for_guild(self, guild):
        guild_enable_commands = set()
        for preset in self.db_guilds[guild.id]['enable_presets']:
            guild_enable_commands.update(self.all_presets[preset]['commands'])
        return guild_enable_commands

    def get_role_access_commands(self, ctx, role):
        if role.id in self.db_guilds[ctx.guild.id]['white_role']:
            return list(self.db_guilds[ctx.guild.id]['white_role'][role.id])
        else:
            return None


permission_obj = Permission


async def init_guild(guild):
    db_guild = db_methods.select_request(columns=("guild_id", "bot_on_server"),
                                         where=("guild_id", guild.id),
                                         table="guild")
    if len(db_guild) == 1:
        print("guild detected", db_guild)
        # db_methods.update_request("guild", (
        #     ("owner_id", None), ("owner_name", None)), ("guild_id", guild.id))
        db_methods.delete_request("owner", ("guild_id", guild.id))
        db_methods.delete_request("member", ("guild_id", guild.id))
        db_methods.delete_request("guild", ("guild_id", guild.id))
        await init_guild(guild)

    else:
        # добавление гильдии
        print("guild don't detected\nlet's create!")
        guild_id = guild.id
        db_methods.insert_request(columns=("guild_id", 'guild_name', 'bot_on_server', 'prefix'),
                                  values=(guild_id, guild.name, True, 'f.'),
                                  table='guild')

        # добавление всех членов гильдии
        guild_members = guild.members
        values = tuple((guild_id,
                        member.id,
                        member.name + '#' + member.discriminator,
                        True,
                        member.joined_at) for member in guild_members)

        db_methods.insert_request(columns=("guild_id", "member_id", 'member_name', 'activ', 'join_date'),
                                  values=values,
                                  table='member')

        # добавление хозяина гильдии
        db_methods.insert_request(columns=('guild_id', 'owner_id', 'owner_name'),
                                  values=(
                                      guild_id, guild.owner.id,
                                      guild.owner.name + "#" + guild.owner.discriminator),
                                  table="owners")
        # добавление для гильдии дефолтного пресета команд
        db_methods.insert_request(values=(guild_id, 'default'),
                                  columns=('guild_id', 'enable_preset'),
                                  table='enable_presets')


class MainCommands(commands.Cog, name='My Cog'):
    @commands.command(pass_context=True, help="отладка, не для смертных")
    async def sql(self, ctx, *command: str):
        if ctx.author == FARGUS_TEAM_OWNER:
            sql_command = ' '.join(command)
            print(sql_command)

            try:
                db_methods.cursor.execute(sql_command)
            except Exception:
                print("error")
            db_methods.connection.commit()
            if "select" in ctx.message.content.lower():
                result = db_methods.cursor.fetchall()
                if result is not None:
                    print(result)


@bot.command(pass_context=True, help="отладка, не для смертных")
async def init_guild_or_if_exist_delete_and_init(ctx):
    if ctx.author == ctx.guild.owner:
        await init_guild(ctx.guild)


# @bot.command(pass_content=True)
# async def t(ctx):
#     url = 'https://i.gifer.com/RTjF.gif'
#     embed_obj = make_embed(None, None, get_nick_or_name(ctx.author), url, 'футерэ',
#                            url,
#                            url, asdf='asdfasdf', jasdjf='ifjaidjflasjdflsjadf' )
#     await ctx.send(embed=embed_obj)


@bot.command(pass_context=True, help="<prifix> - изменить префикс перед командами")
async def set_prefix(ctx, new_prefix: str):
    if 0 < len(new_prefix) < 10:

        if new_prefix != permission_obj.get_guild_prefix(ctx.guild.id):

            db_methods.update_request("guild", ('prefix', new_prefix), ('guild_id', ctx.guild.id))

            permission_obj.set_guild_prefix(ctx.guild.id, new_prefix)

            global guild_prefixes_set

            new_guild_prefixes_set = permission_obj.get_prefixes_set()

            if guild_prefixes_set != new_guild_prefixes_set:
                guild_prefixes_set = new_guild_prefixes_set
                # global bot_prefixes
                bot.command_prefix = list(guild_prefixes_set)


async def send_and_add_reaction_for_delete(send_point, message_text):
    message_text = '```\n' + message_text + '\n```'
    sanded_message = await send_point.send(message_text)
    await sanded_message.add_reaction("❌")


@bot.command(pass_context=True, help="- показывает как давно вы на сервере")
async def when_i_joined(ctx):
    author_name = get_nick_or_name(ctx.author)
    temp = datetime.datetime.today() - ctx.author.joined_at
    # print(type(ctx.guild.members))
    # if ctx.channel.name == "флудильня":
    res = "Товарищ " + author_name + ", вы присоединились к серверу " + str(temp.days) + " дней назад"
    # else:
    #     res = 'Напиши во "флудильню", не захламляй другие чаты'
    await send_and_add_reaction_for_delete(ctx, res)
    # sanded_message = await ctx.send(res)
    # await sanded_message.add_reaction("❌")


@bot.command(name="chance", pass_context=True, help="<любое событие> - вероятность события")
async def chance(ctx, *args):
    res = " "
    res = res.join(s for s in args)
    chance_var = str(res.lower().__hash__())[-2:]
    if chance_var[0] == "0":
        chance_var = chance_var[1]
    await send_and_add_reaction_for_delete(ctx, 'Вероятность события "' + res + '" равна ' + chance_var + "%")


@bot.command(aliases=["farbot", "f", "s", "sys"], pass_context=True)
async def system(ctx, *args):
    if ctx.author.id == FARGUS_TEAM_OWNER.id:
        if len(args) != 0:
            await ctx.send(eval(" ".join(args)))
    else:
        await send_and_add_reaction_for_delete(ctx, '||Ухади||')


@bot.command(name="roll", pass_context=True, help="<число или ничего> - выдает случайное число")
async def roll(ctx, *args):
    if len(args) > 0:
        a = args[0]

        if type(a) == int:
            res = random.randint(0, math.fabs(a))
        else:
            if a.isdigit():
                res = random.randint(0, int(math.fabs(int(a))))

            else:
                res = 'Введи .roll <Число>'
    else:
        res = random.randint(0, 100)

    await send_and_add_reaction_for_delete(ctx, str(res))


@bot.command(name="old", pass_context=True, help="<число> - Топ долгожителей этого сервера", )
async def old(ctx, top: int = 9999):
    all_members_with_days = list()
    for member in ctx.guild.members:
        all_members_with_days.append([get_nick_or_name(member), (datetime.datetime.today() - member.joined_at).days])

    all_members_with_days.sort(key=itemgetter(1), reverse=True)
    count = 0
    for member, time in all_members_with_days:
        if member == get_nick_or_name(ctx.author):
            res = '{author}, вы на {place} месте - {time} дней на сервере\n\n'.format(place=count, author=member,
                                                                                      time=time)
            count = 0
            break
        count += 1

    for member, time in all_members_with_days[:top]:
        # res += member[0].name + " : " + str(member[1].days) + " дней на сервере\n"
        res += '{count}. {name} : {time} дней на сервере\n'.format(count=count,
                                                                   name=member,
                                                                   time=time)
        count += 1
        if len(res) > 1500:
            print(res)
            await send_and_add_reaction_for_delete(ctx, res)
            res = ''
    print(res)
    await send_and_add_reaction_for_delete(ctx, res)


@bot.command(name="choose", pass_context=True, help="<вариант1> <вариант2> <вариантХ> - выбирает один из вариантов")
async def choose(ctx, *args):
    while "или" in args:
        args.remove("или")
    res = random.randint(0, len(args) - 1)
    await send_and_add_reaction_for_delete(ctx, "Выбираю: " + args[res])


# @bot.command(name="ping", pass_context=True)
# async def ping(ctx, member: discord.Member):
#     await ctx.send("<@!" + str(member.id) + ">")


@bot.command(aliases=["who_hase_this_role", "r", "role"], pass_context=True,
             help='<название роли или часть без опечаток> - выводит людей с ролью')
async def members_with_role(ctx, *role_name: str):
    required_role = get_role_by_name(" ".join(role_name), ctx.guild.roles)
    if type(required_role) == list:
        await send_and_add_reaction_for_delete(ctx.channel,
                                               "Я нашел несколько ролей похожих на то, что вы искали: {}.\nУточните запрос.".format(
                                                   ", ".join(role.name for role in required_role)))
        return

    if required_role:
        res = 'Роль "' + required_role.name + '" имеют ' + str(len(required_role.members)) + ' человек.\n'
        if required_role.name == "@everyone":
            res += 'Или иными словами - все на этом сервере и для справки вообще каждый человек в дискорде'
            res = res.replace("@everyone", 'everyone')
        else:
            if len(required_role.members) != 0:
                members_with_required_role = [get_nick_or_name(member) for member in required_role.members]
                res += 'А конкретно: ' + ", ".join(members_with_required_role)
        await send_and_add_reaction_for_delete(ctx, res)
    else:
        res = 'Не могу найти похожей роли. Вот все роли, что имеются на сервере:\n'
        res += ", ".join([roles.name for roles in ctx.guild.roles][1:])
        await send_and_add_reaction_for_delete(ctx, res)


@bot.event
async def on_ready():
    welcome_message = "я готов к использованию, если видишь меня онлайн на сервере.\nЧтобы узнать, что я могу введи .help"
    global FARGUS_TEAM
    FARGUS_TEAM = bot.get_guild(FARGUS_TEAM_GUILD_ID)
    global FARGUS_TEAM_OWNER
    FARGUS_TEAM_OWNER = FARGUS_TEAM.owner
    global log_channel
    log_channel = bot.get_channel(log_channel_id)
    global debug_channel
    debug_channel = bot.get_channel(debug_channel_id)

    db_methods.open_connection()
    db_exist_flag = db_methods.init_db()

    if not db_exist_flag:
        db_methods.insert_request(values=('default', '{"roll", "set_preset", role}', 5),
                                  columns=('preset_name', 'commands', 'priority'), table='command_presets')
        for guild in bot.guilds:
            await init_guild(guild)
    #
    #
    # global bot_prefixes

    global permission_obj
    permission_obj = Permission()
    permission_obj.add_command_preset(FARGUS_TEAM_GUILD_ID, 'dev')

    global guild_prefixes_set
    guild_prefixes_set = permission_obj.get_prefixes_set()

    # global bot_prefixes
    bot.command_prefix = list(guild_prefixes_set)

    # if DEBUG:
    #     async for message in debug_channel.history(limit=1):
    #         if message.author.id != bot.user.id:
    #             await send_and_add_reaction_for_delete(debug_channel, welcome_message)
    #         else:
    #             if message.content != welcome_message:
    #                 await send_and_add_reaction_for_delete(debug_channel, welcome_message)
    #             else:
    #                 await message.delete()
    #                 await send_and_add_reaction_for_delete(debug_channel, welcome_message)
    bot.add_cog(BotEvents(bot, permission_obj, log_channel))
    bot.add_cog(BotChecks(bot, permission_obj, log_channel, debug_channel, FARGUS_TEAM, FARGUS_TEAM_OWNER))
    print('== Ready! ', "=" * 50)


@bot.command(pass_context=True)
async def create_preset(ctx, preset_name=None, *commands):
    # TODO: разрешить применять этот метод только разработчику
    if ctx.author.id == FARGUS_TEAM_OWNER.id:
        all_commands = [command.name for command in bot.commands]
        values = list()
        if preset_name is None:
            return
        for args_command in commands:
            if args_command in all_commands:
                values.append(args_command)

        if values:
            db_methods.insert_request(table='command_presets', columns=('preset_name', 'commands'),
                                      values=(preset_name, list_to_sql_array(values)))
            await send_and_add_reaction_for_delete(ctx.channel,
                                                   'Добавлен присет - **{}**.\nВ него вошли команды: {}'.format(
                                                       preset_name, ", ".join(values)))


@bot.command(pass_context=True)
async def join(ctx):
    channel = ctx.message.author.voice.channel
    await channel.connect()


@bot.command(pass_context=True)
async def leave(ctx):
    # TODO: проверить метод на кроссерверность и сделать его таким в противном случае
    author = ctx.message.author
    voice = author.voice

    author_name = get_nick_or_name(author)

    if voice is not None:
        author_voice = voice.channel
    else:
        await send_and_add_reaction_for_delete(ctx, author_name + ", вы не подключены не к одному голосовому каналу")
        return
    if len(bot.voice_clients) == 0:
        await send_and_add_reaction_for_delete(ctx, "Бот не подключен к чату")
        return
    else:
        if bot.voice_clients[0].channel.id != author_voice.id:
            await send_and_add_reaction_for_delete(ctx, author_name + ", вы с ботом находитесь в разных чатах")
            return
        await bot.voice_clients[0].disconnect()


# todo: update steam id 64
# @bot.command(name='stid', pass_context=True)
# async def steam_id64(ctx, *urls):
#     if urls:
#         correct_url = ''
#         wrong_url = ''
#         for url in urls:
#             if re.search('https://steamcommunity\.com/(id)|(profiles)/.+', url):
#                 if url.endswith('/'):
#                     url = url[:-1]
#                 profile_name = url.split('/').pop()
#                 if profile_name.isdigit():
#                     correct_url += profile_name + '\n'
#                 else:
#                     r = requests.get('https://csgopedia.com/ru/steam-id-finder/?profiles=' + profile_name + '/')
#
#                     a = re.search('<td>SteamID64</td> *\n* *<td><strong>\d+</strong></td>', r.text)
#                     a = re.search('\d+.\d', a.group(0))
#                     correct_url += profile_name + ' ' + a.group(0) + '\n'
#             else:
#                 wrong_url += url + ' не похоже на ссылку Steam профиля.\n'
#
#         await send_and_add_reaction_for_delete(ctx, correct_url + '\n' + wrong_url)
#     else:
#         await send_and_add_reaction_for_delete(ctx, 'После команды вставьте ссылку на стим профиль')


@bot.command(aliases=["c", "clear"], pass_context=True, help="<число> удаляет заданное колличество новых сообщений")
async def clear_all_message(ctx, count_on_delete_message: int):
    count = 0
    authors_of_deleted_messages = {}
    async for message in ctx.channel.history(limit=count_on_delete_message + 1):
        message_author_name = get_nick_or_name(message.author)
        if message_author_name in authors_of_deleted_messages:
            authors_of_deleted_messages[message_author_name] += 1
        else:
            authors_of_deleted_messages[message_author_name] = 1
        await message.delete()
        count += 1

    # удаление упомнинания об команде удаления в отчете от бота
    authors_of_deleted_messages[get_nick_or_name(ctx.author)] -= 1
    if authors_of_deleted_messages[get_nick_or_name(ctx.author)] == 0:
        authors_of_deleted_messages.pop(get_nick_or_name(ctx.author))

    res = "Я удалил " + str(count - 1) + " сообщений\n"
    for elem in list(authors_of_deleted_messages.items()):
        res += str(elem[1]) + ' от ' + elem[0] + '\n'
    await ctx.send(res, delete_after=5)


@bot.command(name="clear_my_message", aliases=['cm', 'cmm'], pass_context=True,
             help="<число> удаляет заданное кол-во ваших сообщений из последних 100 сообщений")
async def clear_my_message(ctx, count_on_delete_message: int):
    request_author = ctx.author
    count_on_delete_message += 1

    count = -1
    async for message in ctx.channel.history(limit=200 + 1):
        if request_author == message.author:
            await message.delete()
            count_on_delete_message -= 1
            count += 1
        if count_on_delete_message == 0:
            res = "Я удалил " + str(count) + " ваших сообщений"
            await ctx.send(res, delete_after=5)
            return
    await ctx.send("Я удалил " + str(count) + " ваших сообщений", delete_after=5)


@bot.command(name="count", pass_context=True, help="Выводит колличество сообщений в этом чате для каждого пользователя")
async def count_message(ctx):
    all_message_in_channel_map = {}
    channel = ctx.channel
    count = 0
    async for message in channel.history(limit=None):
        # if message.author.nick is not None:
        #     author_name = message.author.nick
        # else:
        author_name = message.author.name  # переделать на новый метод
        if author_name in all_message_in_channel_map:
            all_message_in_channel_map[author_name] += 1
        else:
            all_message_in_channel_map[author_name] = 1
        count += 1
        if count % 1000 == 0:
            print(count)
    sorted_all_message = sorted(all_message_in_channel_map.items(), key=lambda x: x[1], reverse=True)
    '''
m = {}
m["asdf"]=5
m["asdf1"]=6
m["asdf2"]=7

def conq_tupple(tupple):
    res = " ".join(map(lambda y: str(y), tupple))
    return res

data = list(m.items())
res = map(lambda x : conq_tupple(x), data)
res = "\n".join(res)
print(res)
    '''
    for user_message_info in sorted_all_message[::-1]:
        if user_message_info[1] < 3:
            sorted_all_message.remove(user_message_info)

    split_result = []
    # one_part_len = int(len(sorted_all_message)/arg)
    one_part_len = 10
    print("one part len = " + str(one_part_len))

    parts = len(sorted_all_message) / one_part_len
    if parts > int(parts):
        parts = int(parts) + 1
    print("parts = " + str(parts))

    for i in range(parts):
        split_result.append(sorted_all_message[i * one_part_len:i * one_part_len + one_part_len])

    await send_and_add_reaction_for_delete(ctx, "Всего сообщения в этом чате: " + str(count))

    for part in split_result:
        res = "\n".join(map(lambda x: " - ".join(map(lambda y: str(y), x)), part))
        print(res)
        await send_and_add_reaction_for_delete(ctx, res)


@bot.command(name="move", pass_context=True, help="<название воиса> - перенос в воис")
async def move(ctx, voice_name: str):
    # TODO: сделать настройки для этого метода с разрешенными воисами для ролей
    for channel in ctx.guild.channels:
        if channel.name == voice_name:
            await ctx.author.edit(voice_channel=channel)
            return


@bot.command(name="say", pass_context=True, help="<текст> - произносит в воисе")
async def say(ctx, *args):
    # TODO: проверить метод на кросгильдность и сделать его таким в противном случае
    author = ctx.message.author
    voice = author.voice
    author_name = get_nick_or_name(author)
    if voice is not None:
        voice = voice.channel
        if len(bot.voice_clients) == 0:
            await voice.connect()
    else:
        await send_and_add_reaction_for_delete(ctx, author_name + ", вы не подключены не к одному голосовому каналу")
        return

    text = " ".join(args)
    if text_converter.spam(text):
        await send_and_add_reaction_for_delete(ctx,
                                               author_name + " не спамь. Если бот ошибся и это не было спамом сообщите Fargus#3924")
        return

    # text = text[:200]

    text = text_converter.remove_non_alphanumeric(author_name) + " говорит: " + text[:200]

    if text[:40] not in file_list:
        file_path = google_voice.convert_text_to_voice(text)
    else:
        file_path = "voice_files/" + text[:40] + ".mp3"
    voice_clients = bot.voice_clients
    voice_clients[0].play(discord.FFmpegPCMAudio(file_path))


# @bot.event
# async def on_typing(channel, user, when):
#     if channel.name == "флудильня" and user.name in ["Ascendant  (Эмиль)"]:
#         await channel.send(user.nick + ", хватит спамить, иди погуляй")
#     else:
#         print(user.name + " in " + channel.name)
#         await log_channel.send(get_nick_or_name(user) + " in " + channel.name)


@bot.command(pass_context=True, help="Отбирает роль тестировщика и доступ в чат")
async def stop_test(ctx):
    member = ctx.author
    role = get_role_by_name("Тестировщик", member.roles)
    await member.remove_roles(role)

    # await


@bot.command(name='role_ban', aliases=["rb"], pass_context=True, help="Добавить новую роль в банлист")
async def add_role_ban(ctx, *term):
    # TODO
    pass


@bot.command(name='add_role_access', aliases=["ara"], pass_context=True,
             help="Добавить новую роль в white_list, в ролях из нескольких слов пробелы заменяйте точками")
async def add_role_access(ctx, *args):
    keys = ('-all_commands', '-allc', 'all_roles', '-allr')

    all_command_flag = False
    all_roles_flag = False

    # all_roles = (role.name for role in ctx.guild.roles)
    all_commands = permission_obj.get_enable_commands_for_guild(ctx.guild)

    hold_roles = []
    hold_commands = []

    args = [str(arg).replace('.', ' ') for arg in args]

    for arg in args:
        if arg in keys:
            if not all_command_flag and arg in keys[:2]:
                all_command_flag = True
                hold_commands = all_commands
            elif not all_roles_flag and arg in keys[2:]:
                all_roles_flag = True
                hold_roles = (role.name for role in ctx.guild.roles)
            elif arg not in keys:
                await send_and_add_reaction_for_delete(ctx.channel, "Вы ввели неверный ключ {}".format(arg))
            else:
                await send_and_add_reaction_for_delete(ctx.channel,
                                                       'Ключ {} повторяется, я не могу это так оставить'.format(arg))
        # if arg is role
        else:

            role = get_role_by_name(arg, ctx.guild.roles)

            if role:
                if all_roles_flag:
                    res = 'Вы уже использовали флаг "-all_roles" добавив все роли,' \
                          ' добавление роли {} избыточно'.format(arg)

                    await send_and_add_reaction_for_delete(ctx.channel, res)
                    return
                elif type(role) == list:
                    res = 'Не могу понять какую роль вы имели ввиду под "{}": {}'.format(arg, ', '.join(
                        [one_role.name for one_role in role]))
                    await send_and_add_reaction_for_delete(ctx.channel, res)
                    return
                elif role in hold_roles:
                    res = 'Вы уже добавили роль "{}", добавление роли {} избыточно'.format(role.name, arg)
                    await send_and_add_reaction_for_delete(ctx.channel, res)
                    return
                else:
                    hold_roles.append(role)
            # if arg is command
            else:

                if arg not in all_commands:
                    res = 'Не могу разобрать эту команду или роль "{}"'.format(arg)
                    await send_and_add_reaction_for_delete(ctx.channel, res)
                    return

                elif all_command_flag:
                    res = 'Вы уже использовали флаг "-all_commands" ' \
                          'добавив все команды, добавление команды {} избыточно'.format(arg)
                    await send_and_add_reaction_for_delete(ctx.channel, res)
                    return

                elif arg in hold_commands:
                    res = 'Вы уже добавили команду "{}", повторное добавление избыточно'.format(arg)
                    await send_and_add_reaction_for_delete(ctx.channel, res)
                    return
                else:
                    hold_commands.append(arg)

    if not hold_commands:
        res = 'Не было распознано не одной команды'
        await send_and_add_reaction_for_delete(ctx.channel, res)
        return
    elif not hold_roles:
        res = 'Не было распознано не одной роли'
        await send_and_add_reaction_for_delete(ctx.channel, res)
        return

        # exist_rows = db_methods.select_request(columns=('role_id', 'command_name'),
    #                                        table='role_white_list',
    #                                        where=('guild_id', ctx.guild.id))

    guild_white_list = permission_obj.db_guilds[ctx.guild.id]['white_role']
    for hold_role in hold_roles:
        if hold_role.id in guild_white_list.keys():
            new_commands = set(hold_commands).difference(guild_white_list[hold_role.id])
            guild_white_list[hold_role.id].update(new_commands)
        else:
            new_commands = set(hold_commands)
            guild_white_list[hold_role.id] = new_commands

        value = [[ctx.guild.id, hold_role.id, command] for command in new_commands]
        if value:
            db_methods.insert_request(table='role_white_list',
                                      columns=('guild_id', 'role_id', 'command_name'),
                                      values=value)


@bot.command(name='remove_role_access', aliases=["rra"], pass_context=True,
             help="Убрать роль из white_list, в ролях из нескольких слов пробелы заменяйте точками")
async def remove_role_access(ctx, *args):
    keys = ('-all_commands', '-allc,', 'all_roles', '-allr')

    all_command_flag = False
    all_roles_flag = False

    # all_roles = (role.name for role in ctx.guild.roles)
    all_commands = permission_obj.get_enable_commands_for_guild(ctx.guild)

    hold_roles = []
    hold_commands = []

    args = [str(arg).replace('.', ' ') for arg in args]

    for arg in args:
        if arg in keys:
            if not all_command_flag and arg in keys[:2]:
                all_command_flag = True
                hold_commands = all_commands
            elif not all_roles_flag and arg in keys[2:]:
                all_roles_flag = True
                hold_roles = (role.name for role in ctx.guild.roles)
            elif arg not in keys:
                await send_and_add_reaction_for_delete(ctx.channel, "Вы ввели неверный ключ {}".format(arg))
            else:
                await send_and_add_reaction_for_delete(ctx.channel,
                                                       'Ключ {} повторяется, я не могу это так оставить'.format(arg))
        # if arg is role
        else:

            role = get_role_by_name(arg, ctx.guild.roles)

            if role:
                if all_roles_flag:
                    res = 'Вы уже использовали флаг "-all_roles" добавив все роли,' \
                          ' добавление роли {} избыточно'.format(arg)

                    await send_and_add_reaction_for_delete(ctx.channel, res)
                    return
                elif type(role) == list:
                    res = 'Не могу понять какую роль вы имели ввиду под "{}": {}'.format(arg, ', '.join(
                        [one_role.name for one_role in role]))
                    await send_and_add_reaction_for_delete(ctx.channel, res)
                    return
                elif role in hold_roles:
                    res = 'Вы уже добавили роль "{}", добавление роли {} избыточно'.format(role.name, arg)
                    await send_and_add_reaction_for_delete(ctx.channel, res)
                    return
                else:
                    hold_roles.append(role)
            # if arg is command
            else:

                if arg not in all_commands:
                    res = 'Не могу разобрать эту команду или роль "{}"'.format(arg)
                    await send_and_add_reaction_for_delete(ctx.channel, res)
                    return

                elif all_command_flag:
                    res = 'Вы уже использовали флаг "-all_commands" ' \
                          'добавив все команды, добавление команды {} избыточно'.format(arg)
                    await send_and_add_reaction_for_delete(ctx.channel, res)
                    return

                elif arg in hold_commands:
                    res = 'Вы уже добавили команду "{}", повторное добавление избыточно'.format(arg)
                    await send_and_add_reaction_for_delete(ctx.channel, res)
                    return
                else:
                    hold_commands.append(arg)

    if not hold_commands:
        res = 'Не было распознано не одной команды'
        await send_and_add_reaction_for_delete(ctx.channel, res)
        return
    elif not hold_roles:
        res = 'Не было распознано не одной роли'
        await send_and_add_reaction_for_delete(ctx.channel, res)
        return

        # exist_rows = db_methods.select_request(columns=('role_id', 'command_name'),
    #                                        table='role_white_list',
    #                                        where=('guild_id', ctx.guild.id))

    guild_white_list = permission_obj.db_guilds[ctx.guild.id]['white_role']
    guild_id = ctx.guild.id
    for hold_role in hold_roles:
        new_commands = None
        if hold_role.id in guild_white_list.keys():
            new_commands = guild_white_list[hold_role.id].difference(set(hold_commands))
            guild_white_list[hold_role.id] = new_commands
        # else:
        #     new_commands = set(hold_commands)
        #     guild_white_list[hold_role.id] = new_commands
        where = list()
        if new_commands:
            where = [('command_name', command, '<>') for command in new_commands]
        where.append(('guild_id', guild_id))
        where.append(('role_id', hold_role.id))

        db_methods.delete_request(table='role_white_list',
                                  where=where)


@bot.command(name='role_access', aliases=["ra"], pass_context=True, help="Просмотр команд разрешенных для роли")
async def role_access(ctx, *args):
    full_role_name = " ".join(args)

    role = get_role_by_name(full_role_name, ctx.guild.roles)
    if not role:
        await send_and_add_reaction_for_delete(ctx, 'Не знаю такой роли: {}'.format(full_role_name))

    elif type(role) is list:
        await send_and_add_reaction_for_delete(ctx, 'Я нашел несколько ролей: {}.\nУточните название.'.format(
            ", ".join([r.name for r in role])))
    else:
        role_access_commands = permission_obj.get_role_access_commands(ctx, role)
        if role_access_commands:
            await send_and_add_reaction_for_delete(ctx,
                                                   'Роль "{role}" может применять эти команды: {commands}.'.format(
                                                       role=role.name,
                                                       commands=', '.join(role_access_commands)))
        else:
            await send_and_add_reaction_for_delete(ctx, 'Роль "{role}" не имеет разрешенных команд.'.format(
                role=role.name))


@bot.command(name='all_role_accepts', pass_context=True, help="Просмотр всех разрешенных команд на сервере")
async def all_role_accept(ctx):
    res = list()
    for role in ctx.guild.roles:
        role_access_comands = permission_obj.get_role_access_commands(ctx, role)
        if role_access_comands:
            res.append(
                '"{role}" может применять: {commands}'.format(role=role.name, commands=", ".join(role_access_comands)))
    if res:
        await send_and_add_reaction_for_delete(ctx, '\n'.join(res))
    else:
        await send_and_add_reaction_for_delete(ctx,
                                               'Неожиданно... Нет ни одной разрешенной команды.\nВремя их создать!')


@bot.command(aliases=["stream", "st"], pass_context=True, help="Дает роль, для оповещений о стриме")
async def stream_notify(ctx, *term):
    member = ctx.author
    member_name = get_nick_or_name(member)
    role = get_role_by_name("Жду стрима", ctx.guild.roles)
    if len(term) != 0:
        term = term[0]
    else:
        await send_and_add_reaction_for_delete(ctx, member_name + ", введите после команды stream \"+\" либо \"-\"")
        return
    if term == "+":
        await member.add_roles(role)
        await send_and_add_reaction_for_delete(ctx, member_name + ", роль \"Жду Стрима\" добавлена")
    elif term == "-":
        role = get_role_by_name("Жду стрима", member.roles)
        if role is not None:
            await member.remove_roles(role)
            await send_and_add_reaction_for_delete(ctx,
                                                   member_name + ", больше вас не будут предупреждать о начале стрима")
        else:
            await send_and_add_reaction_for_delete(ctx, member_name + ", у вас нет роли \"Жду Стрима\"")

    else:
        await send_and_add_reaction_for_delete(ctx, member_name + ", введите \"+\" либо \"-\"")


@bot.event
async def on_guild_join(guild):
    # log_channel = await  bot.fetch_channel(701183371166089276)

    # for channel in guild.channels:
    #     # if channel.name == "флудильня":
    #     if "test_farbot" in channel.name:
    #         await send_and_add_reaction_for_delete(channel, 'Я сейчас все настрою и буду готов\nА пока введи .help')
    if guild.system_channel:
        await send_and_add_reaction_for_delete(guild.system_channel,
                                               'Я сейчас все настрою и буду готов\nА пока введи f.help')
        await init_guild(guild)

''' 
Принимает на вход название роли и место в котором хранится массив с ними

При полном совпадении возвращает объект роли
За неимением полного совпадения возвращает первое вхождение искомого в полное название роли
'''


# @bot.check
# async def globally_block_dms(ctx):
#     if ctx.channel.name == "test_farbot":
#         return ctx.send("opa")


@bot.check
async def permission(ctx):
    if permission_obj.check_member_in_global_black_list(ctx):
        print('global_black_list - False')
        return False

    if permission_obj.check_member_in_global_white_list(ctx):
        print('global_white_list - True')
        return True

    if not permission_obj.check_command_enable_on_this_guild(ctx):
        print('enable_command - False')
        return False

    if permission_obj.check_member_is_owner(ctx):
        print('is_owner - True')
        return True

    if permission_obj.check_member_role_in_black_list(ctx):
        print('member_role_black_list - False')
        return False

    if permission_obj.check_member_role_in_white_list(ctx):
        print('member_role_white_list - False')
        return True

    # TODO: check member black and white list

    # запретить выполнение команды, так как ниодним белым списком не разрешено
    print('dont have permission on this command - False')
    return False


# TODO delete this code or update for new permission class structure
# def check_predicat_in_list(ctx, guild_lists, list_name, role_or_member):
#     id_dict_with_commands = guild_lists[list_name][str(ctx.guild.id)]
#     id_dict_keys = id_dict_with_commands.keys()
#
#     if role_or_member == 'role':
#         for role in ctx.author.roles:
#             if str(role.id) in id_dict_keys:
#                 if ctx.command.name in id_dict_with_commands[str(role.id)]:
#                     return True
#     elif role_or_member == 'member':
#         if ctx.author.id in id_dict_keys:
#                 if ctx.command.name in id_dict_with_commands[ctx.author.id]:
#                     return True
#     return False


# @bot.check
# async def prefix_control(ctx):
#     # guild_prefix = "f."
#     global guild_prefixes
#     if hard_prefix_check(ctx.message):
#         if ctx.message.content.startswith(guild_prefix):
#             ctx.message.content = '.' + ctx.message.content[len(guild_prefix):]
#         else:
#             print("аборт это грех")
#             return False
#     return True


async def develop():
    async def predicate(ctx):
        if ctx.author == FARGUS_TEAM_OWNER:
            return True
        else:
            return False





# bot.add_cog(MainCommands())

bot.run(TOKEN)
