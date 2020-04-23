import os
from operator import itemgetter

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

from websockets import typing

logger = logging.getLogger('discord')
logging.basicConfig(level=logging.INFO)

TOKEN = discord_token.TOKEN
GUILD_ID = 539879904506806282
log_channel = None
GUILD = None
OWNER = None

global bot
bot = commands.Bot(command_prefix='.')  # инициализируем бота с префиксом '.'
# client = discord.Client()

global voice_client

file_list = dir_helper.file_list("voice_files/")


def get_bot():
    return bot


def to_db_str(s):
    return "'" + str(s) + "'"


@bot.command(pass_context=True, help="отладка, не для смертных")
async def sql(ctx, *command: str):
    if ctx.author == OWNER:
        db_methods.cursor.execute(' '.join(command))
        db_methods.connection.commit()
        if "select" in ctx.message.content.lower():
            result = db_methods.cursor.fetchall()
            if result is not None:
                print(result)


# @bot.command(pass_context=True, help="отладка, не для смертных")
# async def init(ctx):
#     if ctx.author == OWNER:
#         # live_guilds = bot.guilds
#         db_guild = db_methods.select_request(columns=("guild_id", "bot_on_server"),
#                                              where="guild_id = " + to_db_str(ctx.guild.id))
#         if len(db_guild) == 1:
#             pass  # guild update
#         else:
#             # ctx.
#             db_methods.insert_request(columns=("guild_id", 'guild_name', 'bot_on_server', 'owner'),
#                                       values=(to_db_str(ctx.guild.id), ctx.guild.name, True, to_db_str(ctx.author.id)),
#                                       table='guild')
#
#
# @bot.command(pass_context=True, help="отладка, не для смертных")
# async def ti(ctx, *command: str):
#     if ctx.author == OWNER:
#         # result = db_methods.select_request()
#         # print(db_methods.insert_request())
#         db_methods.insert_request(columns=("guild_id", 'guild_name', 'bot_on_server'),
#                                   values=(("123", "guild name123", True),
#                                           ("456", "guild name456", True),
#                                           ("789", "guild name789", True)),
#                                   table="guild")
        # print(result)


async def send_and_add_reaction_for_delete(send_point, message_text):
    sanded_message = await send_point.send(message_text)
    await sanded_message.add_reaction("❌")


@bot.command(pass_context=True, help="- показывает как давно вы на сервере")
async def when_i_joined(ctx):
    request_user_info = ctx.author
    author_name = request_user_info.nick
    if author_name is None:
        author_name = request_user_info.name
    temp = datetime.datetime.today() - request_user_info.joined_at
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
    if ctx.author.nick is not None:
        res = ctx.author.nick
    else:
        res = ctx.author.name
    if ctx.author.name == "Fargus":
        if len(args) != 0:
            await ctx.send(eval("".join(args)))
    else:
        await send_and_add_reaction_for_delete(ctx, '||Пашел нахер, ' + res + "||")


@bot.command(name="roll", pass_context=True, help="<число или ничего> - выдает случайное число")
async def roll(ctx, *args):
    res = None
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


@bot.command(name="old", pass_context=True, help="<число> - Топ долгожителей этого сервера")
async def old(ctx, top: int, *args):
    all_members_with_days = list()
    for member in GUILD.members:
        all_members_with_days.append([member, datetime.datetime.today() - member.joined_at])

    all_members_with_days.sort(key=itemgetter(1), reverse=True)
    res = ""
    for member in all_members_with_days[:top]:
        res += member[0].name + " : " + str(member[1].days) + " дней на сервере\n"
    print(res)
    await send_and_add_reaction_for_delete(ctx, res)


@bot.command(name="choose", pass_context=True, help="<вариант1> <вариант2> <вариантХ> - выбирает один из вариантов")
async def choose(ctx, *args):
    while "или" in args:
        args.remove("или")
    res = random.randint(0, len(args) - 1)
    await send_and_add_reaction_for_delete(ctx, "Выбираю: " + args[res])


@bot.command(name="ping", pass_context=True)
async def ping(ctx, member: discord.Member):
    await ctx.send("<@!" + str(member.id) + ">")


@bot.command(aliases=["who_hase_this_role", "r", "role"], pass_context=True,
             help='<название роли или часть без опечаток> - выводит людей с ролью')
async def members_with_role(ctx, role_name: str):
    # if role_name[0] is '@':
    #     role_name = role_name[1:]
    # all_server_roles = {roles.name for roles in GUILD.roles}
    # if role_name in all_server_roles:
    required_role = get_role_by_name(role_name, GUILD.roles)

    if required_role is not None:
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
        res += ", ".join([roles.name for roles in GUILD.roles][1:])
        await send_and_add_reaction_for_delete(ctx, res)


@bot.event
async def on_ready():
    welcome_message = "я готов к использованию, если видишь меня онлайн на сервере.\nЧтобы узнать, что я могу введи .help"
    global GUILD
    global OWNER
    global log_channel
    db_methods.open_connection()
    db_methods.init_db()
    GUILD = bot.get_guild(GUILD_ID)
    OWNER = GUILD.owner
    log_channel = await  bot.fetch_channel(701183371166089276)

    for channel in GUILD.channels:
        # if channel.name == "флудильня":
        if "test_farbot" in channel.name:
            flud_chanel = channel
            break
    async for message in channel.history(limit=1):
        if message.author.id != bot.user.id:
            await send_and_add_reaction_for_delete(flud_chanel, welcome_message)
        else:
            if message.content != welcome_message:
                await send_and_add_reaction_for_delete(flud_chanel, welcome_message)
            else:
                await message.delete()
                await send_and_add_reaction_for_delete(flud_chanel, welcome_message)

    print('Ready! ' + "=" * 50)


@bot.command(pass_context=True)
async def join(ctx):
    author = ctx.message.author
    channel = author.voice.channel
    await channel.connect()


@bot.command(pass_context=True)
async def leave(ctx):
    author = ctx.message.author
    voice = author.voice

    if author.nick is not None:
        author_name = author.nick
    else:
        author_name = author.name

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


@bot.command(aliases=["c", "clear"], pass_context=True, help="<число> удаляет заданное колличество новых сообщений")
async def clear_all_message(ctx, count_on_delete_message: int):
    if ctx.author == OWNER:
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
    else:
        await ctx.send(ctx.author.name + ", у вас нет прав на это. Пока что... ",
                                               delete_after=5)


@bot.command(name="clear_my_message", pass_context=True,
             help="<число> удаляет заданное кол-во ваших сообщений из последних 100 сообщений")
async def clear_my_message(ctx, count_on_delete_message: int):
    request_author = ctx.author
    count_on_delete_message += 1
    author_roles = {roles.name for roles in request_author.roles}
    # истина если не имеют общих элементов
    if author_roles.isdisjoint({"Вассал", "Доверенный вассал", "Монарх"}):
        await ctx.send(ctx.author.name + ", у вас нет прав на это. Пока что... ", delete_after=5)

    else:
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
    if ctx.author != OWNER:
        print("не фаргус")
        await log_channel.send(get_nick_or_name(ctx.author) + ", count только для фаргуса")
        await send_and_add_reaction_for_delete(ctx, "Ты не Fargus")
        return
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
    if ctx.author == OWNER:
        for channel in GUILD.channels:
            if channel.name == voice_name:
                await ctx.author.edit(voice_channel=channel)
                break


@bot.command(name="say", pass_context=True, help="<текст> - произносит в воисе")
async def say(ctx, *args):
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
                                               author_name + " не спамь. Если бот ошибся и это не было спамом сообщи мне, попытаюсь исправить")
        return

    # text = text[:200]

    text = text_converter.remove_non_alphanumeric(author_name) + " говорит: " + text[:200]

    if text[:40] not in file_list:
        file_path = google_voice.convert_text_to_voice(text)
    else:
        file_path = "voice_files/" + text[:40] + ".mp3"
    voice_clients = bot.voice_clients
    voice_clients[0].play(discord.FFmpegPCMAudio(file_path))


@bot.event
async def on_typing(channel, user, when):
    if channel.name == "флудильня" and user.name in ["Ascendant  (Эмиль)"]:
        await channel.send(user.nick + ", хватит спамить, иди погуляй")
    else:
        print(user.name + " in " + channel.name)
        await log_channel.send(get_nick_or_name(user) + " in " + channel.name)


@bot.event
async def on_raw_reaction_add(payload):
    if payload.member != bot.user:
        channel = await bot.fetch_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        if message.author == bot.user and payload.emoji.name == "❌":
            await message.delete()
        log_message = get_nick_or_name(payload.member) + " add: " + payload.emoji.name + ' on ' + channel.name
        print(log_message)
        await log_channel.send(log_message)


@bot.command(pass_context=True, help="Отбирает роль тестировщика и доступ в чат")
async def stop_test(ctx):
    member = ctx.author
    role = get_role_by_name("Тестировщик", member.roles)
    await member.remove_roles(role)

    # await


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
            await send_and_add_reaction_for_delete(ctx, member_name + ", больше вас не будут предупреждать о начале стрима")
        else:
            await send_and_add_reaction_for_delete(ctx, member_name + ", у вас нет роли \"Жду Стрима\"")

    else:
        await send_and_add_reaction_for_delete(ctx, member_name + ", введите \"+\" либо \"-\"")



@bot.event
async def on_reaction_remove(reaction, user):
    # if reaction.name == "test_farbot":
    #
    #     await channel.send(user.name)
    # else:
    print("remove")


def get_nick_or_name(author):
    if author.nick is not None:
        return author.nick
    else:
        return author.name


''' 
Принимает на вход название роли и место в котором хранится массив с ними

При полном совпадении возвращает объект роли
За неимением полного совпадения возвращает первое вхождение искомого в полное название роли
'''


def get_role_by_name(role_name, search_start_point):
    '''
    role_like_required = None
    role_name = role_name.lower()

    role_names_list = [role.name.lower() for role in search_start_point]
    for server_role in role_names_list:
        if role_name in server_role:
            if role_name == server_role:
                return role
            else:
                if role_like_required is None:
                    role_like_required = role
    return role_like_required
    '''
    role_name = role_name.lower()
    role_like_required = None
    for role in search_start_point:
        if role_name in role.name.lower():
            if role_name == role.name.lower():
                return role
            else:
                if role_like_required is None:
                    role_like_required = role
    return role_like_required


# @bot.check
# async def globally_block_dms(ctx):
#     if ctx.channel.name == "test_farbot":
#         return ctx.send("opa")


# @discord.client.event(pass_context=True)
# async def on_message(ctx):
#     request_user_info = ctx.author
#     if request_user_info.id == "337582745314263041":
#         await ctx.send("op")

def fill_guild_information():
    guilds = bot.guilds


bot.run(TOKEN)
