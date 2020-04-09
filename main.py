import os
from operator import itemgetter


import dir_helper
import google_voice
import text_converter


import discord
import datetime
from discord.ext import commands
import logging
import random
import math

from websockets import typing

logger = logging.getLogger('discord')
logging.basicConfig(level=logging.INFO)

TOKEN = "NjkyMDc3NjQ1MTY0NDQ1NzY3.XoVA6A.bbISsep_-UPSOsXoLg-M-Vl-4EU"
GUILD_ID = 539879904506806282
fargus_team = ""
FARGUS = ""


bot = commands.Bot(command_prefix='.') #инициализируем бота с префиксом '.'
# client = discord.Client()

global voice_client

file_list = dir_helper.file_list("voice_files/")

@bot.command(pass_context=True, help="- показывает как давно вы на сервере")
async def when_i_joined(ctx):
    request_user_info = ctx.author
    author_name = request_user_info.nick
    if author_name == None:
        author_name = request_user_info.name
    temp = datetime.datetime.today() - request_user_info.joined_at
    # print(type(ctx.guild.members))
    if ctx.channel.name == "флудильня":
        res = "Товарищ " + author_name + ", вы присоединились к серверу " + str(temp.days) + " дней назад"
    else:
        res = 'Напиши во "флудильню", не захламляй другие чаты'
    await ctx.send(res)

        # res = request_user_info.id
    # await ctx.send(res) #отправляем обратно аргумент


@bot.command(name="chance", pass_context=True, help="<любое событие> - вероятность события")
async def chance(ctx, *args):
    res = " "
    res = res.join(s for s in args)
    chance_var = str(res.lower().__hash__())[-2:]
    if chance_var[0] == "0":
        chance_var = chance_var[1]
    await ctx.send('Вероятность события "' + res + '" равна ' + chance_var + "%")


@bot.command(name="farbot", pass_context=True)
async def pasholnahuy(ctx, *args):
    if ctx.author.nick is not None:
        res = ctx.author.nick
    else:
        res = ctx.author.name
    if ctx.author.name == "Fargus":
        if len(args) != 0:
            print(eval(args[0]))
    else:
        await ctx.send('||Пашел нахер, ' + res + "||")


@bot.command(name="roll", pass_context=True, help="<число или ничего> - выдает случайное число")
async def roll(ctx, *args):
    res = "temp"
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

    await ctx.send(str(res))


@bot.command(name="old", pass_context=True, help="<число> - Топ долгожителей этого сервера")
async def old(ctx, top: int, *args):
    all_members_with_days = list()
    for member in fargus_team.members:
        all_members_with_days.append([member, datetime.datetime.today() - member.joined_at])

    all_members_with_days.sort(key=itemgetter(1), reverse=True)
    res = ""
    for member in all_members_with_days[:top]:
        res += member[0].name + " : " + str(member[1].days) + " дней на сервере\n"
    print(res)
    await ctx.send(res)


@bot.command(name="choose", pass_context=True, help="<вариант1> <вариант2> <вариантХ> - выбирает один из вариантов")
async def choose(ctx, *args):
    while "или" in args:
        args.remove("или")
    res = random.randint(0, len(args)-1)
    await ctx.send("Выбираю: " + args[res])


@bot.command(name="ping", pass_context=True)
async def ping(ctx, member: discord.Member):

    await ctx.send("<@!" + str(member.id) + ">")


# @bot.command(name="help", pass_context=True)
# async def help(ctx, member: discord.Member):
#
#     await ctx.send(".ping\n.choose <вариант1> <вариант2> <вариантХ>\n")

#
# @client.command(name='t', pass_context=True)
# async def nope(ctx):
#     request_user_info = ctx.author
#     if request_user_info.id == 337582745314263041:
#         print(ctx.guild.roles)


@bot.event
async def on_ready():
    welcome_message = "я готов к использованию, если видишь меня онлайн на сервере.\nЧтобы узнать, что я могу введи .help"
    global fargus_team
    global FARGUS
    fargus_team = bot.get_guild(GUILD_ID)
    FARGUS = fargus_team.owner


    for channel in fargus_team.channels:
        # if channel.name == "флудильня":
        if channel.name == "test_farbot":
            flud_chanel = channel
            break
    async for message in channel.history(limit=1):
        if message.author.id != bot.user.id:
            await flud_chanel.send(welcome_message)
            print("yes")
        else:
            if message.content != welcome_message:
                await flud_chanel.send(welcome_message)
            else:
                await message.delete()
                await flud_chanel.send(welcome_message)


    print('Ready! ' + "="*50)


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
        await ctx.send(author_name + ", вы не подключены не к одному голосовому каналу")
        return
    if len(bot.voice_clients) == 0:
        await ctx.send("Бот не подключен к чату")
        return
    else:
        if bot.voice_clients[0].channel.id != author_voice.id:
            await ctx.send(author_name + ", вы с ботом находитесь в разных чатах")
            return
        await bot.voice_clients[0].disconnect()



# @bot.command(name="p", pass_context=True, help="воспроизводит один из файлов: " + ", ".join(file_list))
# async def play_local(ctx, file_name):
#
#     file_path = "/home/mcs/Загрузки/dm/" + file_name + ".mp3"
#     # channel = ctx.message.author.voice.channel
#     # voice = await channel.connect()
#     voice_clients = bot.voice_clients
#     voice_clients[0].play(discord.FFmpegPCMAudio(file_path))


@bot.command(name="clear", pass_context=True, help="<число> удаляет заданное колличество новых сообщений")
async def clear(ctx, count_on_delete_message: int):
    # global FARGUS
    if ctx.author == FARGUS:
        count = 0
        async for message in ctx.channel.history(limit=count_on_delete_message):
            await message.delete()
            count += 1
        await ctx.send("Я удалил " + str(count) + " сообщений", delete_after=5)
    else:
        await ctx.send(ctx.author.name + ", у вас нет прав на это. Пока что... ")


@bot.command(name="count", pass_context=True, help="Выводит колличество сообщений в этом чате для каждого пользователя")
async def count_message(ctx, arg: int):
    if ctx.author.name != "Fargus":
        print("не фаргус")
        await ctx.send("Ты не Fargus")
        return
    all_messege_in_channel_map ={}
    channel = ctx.channel
    count = 0
    async for message in channel.history(limit=None):
        # if message.author.nick is not None:
        #     author_name = message.author.nick
        # else:
        author_name = message.author.name
        if author_name in all_messege_in_channel_map:
            all_messege_in_channel_map[author_name] +=1
        else:
            all_messege_in_channel_map[author_name] = 1
        count += 1
        if count % 1000 == 0:
            print(count)
    sorted_all_message = sorted(all_messege_in_channel_map.items(), key= lambda x: x[1], reverse=True)
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
    one_part_len = arg
    print("one part len = " + str(one_part_len))

    parts = len(sorted_all_message) / one_part_len
    if parts > int(parts):
        parts = int(parts) + 1
    print("parts = " + str(parts))

    for i in range(parts):
        split_result.append(sorted_all_message[i*one_part_len:i*one_part_len+one_part_len])
    await ctx.send("Всего сообщения в этом чате: " + count)
    for part in split_result:
        res = "\n".join(map(lambda x: " - ".join(map(lambda y: str(y), x)), part))
        print(res)
        await ctx.send(res)


@bot.command(name="say", pass_context=True, help="<текст> - произносит в воисе")
async def say(ctx, *args):

    author = ctx.message.author
    voice = author.voice
    if author.nick is not None:
        author_name = author.nick
    else:
        author_name = author.name
    if voice is not None:
        voice = voice.channel
        if len(bot.voice_clients) == 0:
            await voice.connect()
    else:
        await ctx.send(author_name + ", вы не подключены не к одному голосовому каналу")
        return

    text = " ".join(args)
    if text_converter.spam(text):
        await ctx.send(author_name + " не спамь. Если бот ошибся и это не было спамом сообщи мне, попытаюсь исправить")
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


@bot.event
async def on_reaction_add(reaction, user):
    # if reaction.name == "test_farbot":
    #
    #     await channel.send(user.name)
    # else:
    print("add")


@bot.event
async def on_reaction_remove(reaction, user):
    # if reaction.name == "test_farbot":
    #
    #     await channel.send(user.name)
    # else:
    print("remove")



# @bot.check
# async def globally_block_dms(ctx):
#     if ctx.channel.name == "test_farbot":
#         return ctx.send("opa")


# @discord.client.event(pass_context=True)
# async def on_message(ctx):
#     request_user_info = ctx.author
#     if request_user_info.id == "337582745314263041":
#         await ctx.send("op")

bot.run(TOKEN)



