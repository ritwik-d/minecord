import discord
import sys
import yaml
import subprocess
import requests
import re
import threading


with open('config.yml', 'r') as f:
    config = yaml.safe_load(f)

chat_wh = config.get('webhook_chat')
logs_wh = config.get('webhook_server_logs')
avatars = config.get('avatars')
channels = config.get('channels')
online = []


def get_avatar(user):
    avatar = avatars.get(user)
    if avatar is None:
        return avatars.get('default')
    return avatar


def chat_send(user, message):
    info = get_avatar(user.replace(' ', ''))
    message = message.replace('@', '')

    data = {
        'content': message,
        'username': info['name'],
        'avatar_url': info['url']
    }
    requests.post(chat_wh, json=data)


def logs_send(message):
    pass
    #data = {
    #    'content': message
    #}
    #requests.post(logs_wh, json=data)


def process_output(cmd):
    #with cmd as cmd:
    for line in cmd.stdout:
        print(line, end='')

        if 'com.mojang.authlib.GameProfile' in line:
            logs_send(line)
        if '<' in line and '>' in line:
            chat_send(re.search('<(.*)>', line).group(1), line.split('> ')[1])
        if 'lost connection: Disconnected' in line:
            username = line.split(': ')[1].split()[0]
            online.remove(username)
            chat_send(username, f'----- **{username} disconnected** -----')
        elif 'joined the game' in line:
            username = line.split(': ')[1].split()[0]
            online.append(username)
            chat_send(username, f'----- **{username} joined** -----')
        elif 'Preparing spawn area: 0%' not in line:
            logs_send(line)


def discord_bot(token, cmd):
    client = discord.Client(intents=discord.Intents.all())

    @client.event
    async def on_ready():
        print('BOT: ONLINE')


    @client.event
    async def on_message(message):
        if message.author == client.user or len(message.content.replace(' ', '')) == 0:
            return

        if message.content == '!online':
            if len(online) == 0:
                return await message.channel.send('No one is online!')

            msg = f"**Online ({len(online)}):**\n\n"
            for num, i in enumerate(online):
                msg += f"{num + 1}. {i}\n"

            return await message.channel.send(msg)


        #elif message.channel.id == channels.get('general'):
        #    stdout_data = cmd.communicate(input=f'msg @a {message.author.name}: {message.content}')[0]
        #    cmd.stdin.write(f'msg @a {message.author.name}: {message.content}')
        #    cmd.stdin.flush()

        elif message.channel.id == channels.get('chat'):
            cmd.stdin.write(f'say {message.author.name}: {message.content}\n')

    client.run(token)


def server():
    cmd = subprocess.Popen(
        ['java', '-Xmx1024M', '-Xms1024M', '-jar', 'server.jar', 'nogui'],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        stdin=subprocess.PIPE,
        bufsize=1,
        universal_newlines=True,
        text=True
    )

    t1 = threading.Thread(target=process_output, args=(cmd,))
    t1.start()

    discord_bot(config.get('bot_token'), cmd)


if __name__ == '__main__':
    server()
