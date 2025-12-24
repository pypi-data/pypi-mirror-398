import discord
from discord.ext import commands
from discord.utils import get, find
import asyncio

def createclient(intents=None):
    return discord.Client(intents=intents)

def defaultintents():
    return discord.Intents.default()

def allintents():
    return discord.Intents.all()

def attachfile(filename):
    return discord.File(filename)

def onready(client, bot=None, syncslash=False):
    @client.event
    async def on_ready():
        print(f'Logged in as {client.user}')
        if syncslash and bot:
            await asyncio.sleep(3)
            await bot.tree.sync()

def onmessage(client, handler):
    @client.event
    async def on_message(message):
        await handler(message)

def onmemberjoin(client, handler):
    @client.event
    async def on_member_join(member):
        await handler(member)

def onreactionadd(client, handler):
    @client.event
    async def on_reaction_add(reaction, user):
        await handler(reaction, user)

def onmemberremove(client, handler):
    @client.event
    async def on_member_remove(member):
        await handler(member)

def onvoicestateupdate(client, handler):
    @client.event
    async def on_voice_state_update(member, before, after):
        await handler(member, before, after)

def addcommand(bot, name, handler):
    @bot.command(name=name)
    async def command(ctx, *args):
        await handler(ctx, *args)

def addgroup(bot, name, handler):
    @bot.group(name=name)
    async def group(ctx):
        await handler(ctx)

async def send(channel, content):
    return await channel.send(content)

async def delete(message):
    return await message.delete()

async def edit(message, newcontent):
    return await message.edit(content=newcontent)

async def kick(member):
    return await member.kick()

async def ban(member):
    return await member.ban()

def createembed(title="", description="", color=0x00ff00):
    return discord.Embed(title=title, description=description, color=color)

def addfield(embed, name, value, inline=False):
    embed.add_field(name=name, value=value, inline=inline)
    return embed

def setfooter(embed, text):
    embed.set_footer(text=text)
    return embed

def setimage(embed, url):
    embed.set_image(url=url)
    return embed

def getfrom(items, **kwargs):
    return get(items, **kwargs)

def findin(items, predicate):
    return find(predicate, items)

def createbot(commandprefix, intents):
    bot = commands.Bot(command_prefix=commandprefix, intents=intents)
    return bot

def addslash(bot, name, description, handler):
    @bot.tree.command(name=name, description=description)
    async def slash(interaction):
        await handler(interaction)
