# Copyright (C) 2019 The Raphielscape Company LLC.
#
# Licensed under the Raphielscape Public License, Version 1.c (the "License");
# you may not use this file except in compliance with the License.
#
""" Userbot module for getting information about the server. """

import platform
import shutil
import sys
import time
from asyncio import create_subprocess_exec as asyncrunapp
from asyncio.subprocess import PIPE as asyncPIPE
from os import remove
from platform import python_version, uname
from shutil import which

from git import Repo
from telethon import version
from telethon.errors.rpcerrorlist import MediaEmptyError

from userbot import ALIVE_LOGO, ALIVE_NAME, CMD_HELP, HEROKU_APP_NAME, StartTime, bot
from userbot.events import register

# ================= CONSTANT =================
DEFAULTUSER = str(ALIVE_NAME) if ALIVE_NAME else uname().node
repo = Repo()
modules = CMD_HELP
# ============================================


async def get_readable_time(seconds: int) -> str:
    count = 0
    up_time = ""
    time_list = []
    time_suffix_list = ["s", "m", "h", "days"]

    while count < 4:
        count += 1
        if count < 3:
            remainder, result = divmod(seconds, 60)
        else:
            remainder, result = divmod(seconds, 24)
        if seconds == 0 and remainder == 0:
            break
        time_list.append(int(result))
        seconds = int(remainder)

    for x in range(len(time_list)):
        time_list[x] = str(time_list[x]) + time_suffix_list[x]
    if len(time_list) == 4:
        up_time += time_list.pop() + ", "

    time_list.reverse()
    up_time += ":".join(time_list)

    return up_time


@register(outgoing=True, pattern=r"^\.sysd$")
async def sysdetails(sysd):
    """For .sysd command, get system info using neofetch."""
    if not sysd.text[0].isalpha() and sysd.text[0] not in ("/", "#", "@", "!"):
        try:
            fetch = await asyncrunapp(
                "neofetch",
                "--stdout",
                stdout=asyncPIPE,
                stderr=asyncPIPE,
            )

            stdout, stderr = await fetch.communicate()
            result = str(stdout.decode().strip()) + str(stderr.decode().strip())

            await sysd.edit("`" + result + "`")
        except FileNotFoundError:
            await sysd.edit("`Instal neofetch terlebih dahulu!`")


@register(outgoing=True, pattern=r"^\.botver$")
async def bot_ver(event):
    """For .botver command, get the bot version."""
    if not event.text[0].isalpha() and event.text[0] not in ("/", "#", "@", "!"):
        if which("git") is not None:
            ver = await asyncrunapp(
                "git",
                "describe",
                "--all",
                "--long",
                stdout=asyncPIPE,
                stderr=asyncPIPE,
            )
            stdout, stderr = await ver.communicate()
            verout = str(stdout.decode().strip()) + str(stderr.decode().strip())

            rev = await asyncrunapp(
                "git",
                "rev-list",
                "--all",
                "--count",
                stdout=asyncPIPE,
                stderr=asyncPIPE,
            )
            stdout, stderr = await rev.communicate()
            revout = str(stdout.decode().strip()) + str(stderr.decode().strip())

            await event.edit(
                "**Versi Userbot** : " f"`{verout}" "` \n" "**Revisi** : " f"`{revout}" "`"
            )
        else:
            await event.edit(
                "Sayang sekali Anda tidak memiliki git, Anda tetap menjalankan “v1.beta.4”!"
            )


@register(outgoing=True, pattern=r"^\.pip(?: |$)(.*)")
async def pipcheck(pip):
    """For .pip command, do a pip search."""
    if not pip.text[0].isalpha() and pip.text[0] not in ("/", "#", "@", "!"):
        pipmodule = pip.pattern_match.group(1)
        if pipmodule:
            await pip.edit("`Sedang mencari...`")
            pipc = await asyncrunapp(
                "pip3",
                "search",
                pipmodule,
                stdout=asyncPIPE,
                stderr=asyncPIPE,
            )

            stdout, stderr = await pipc.communicate()
            pipout = str(stdout.decode().strip()) + str(stderr.decode().strip())

            if pipout:
                if len(pipout) > 4096:
                    await pip.edit("`Output terlalu besar, dikirim sebagai file`")
                    file = open("output.txt", "w+")
                    file.write(pipout)
                    file.close()
                    await pip.client.send_file(
                        pip.chat_id,
                        "output.txt",
                        reply_to=pip.id,
                    )
                    remove("output.txt")
                    return
                await pip.edit(
                    "**Pencarian** : \n`"
                    f"pip3 search {pipmodule}"
                    "`\n**Hasil** : \n`"
                    f"{pipout}"
                    "`"
                )
            else:
                await pip.edit(
                    "**Pencarian** : \n`"
                    f"pip3 search {pipmodule}"
                    "`\n**Hasil** : \n`Tidak ada hasil yang dikembalikan/salah`"
                )
        else:
            await pip.edit("`Gunakan “.help pip” untuk melihat contoh`")


@register(outgoing=True, pattern=r"^\.alive$")
async def amireallyalive(alive):
    """For .alive command, check if the bot is running."""
    logo = ALIVE_LOGO
    uptime = await get_readable_time((time.time() - StartTime))
    output = (
        f"❖  **WEEBPROJECT AKTIF - BERJALAN NORMAL**  ❖\n\n"
        f"**⌯  Pengguna** : {DEFAULTUSER}\n"
        f"**⌯  Versi Python** : `{python_version()}`\n"
        f"**⌯  Versi Telethon** : `{version.__version__}`\n"
        f"**⌯  Berjalan di** : `{repo.active_branch.name}`\n"
        f"**⌯  Modul dimuat** : `{len(CMD_HELP)}`\n"
        f"**⌯  Bot aktif sejak** : `{uptime}`\n\n"
        f"**🎖️ [RPL v1.d](https://github.com/BianSepang/WeebProject/blob/master/LICENSE) | 👤 [WeebProject](https://github.com/BianSepang) | 📌 [Repo](https://github.com/BianSepang/WeebProject.git)**\n"
    )
    if ALIVE_LOGO:
        try:
            logo = ALIVE_LOGO
            await bot.send_file(alive.chat_id, logo, caption=output)
            await alive.delete()
        except MediaEmptyError:
            await alive.edit(
                output + "\n\n`Logo yang diberikan tidak valid."
                "\nPastikan tautan diarahkan ke gambar logo`."
            )
    else:
        await alive.edit(output)


@register(outgoing=True, pattern=r"^\.aliveu")
async def amireallyaliveuser(username):
    """For .aliveu command, change the username in the .alive command."""
    message = username.text
    output = ".aliveu [pengguna baru tanpa tanda kurung] juga tidak bisa kosong"
    if not (message == ".aliveu" or message[7:8] != " "):
        newuser = message[8:]
        global DEFAULTUSER
        DEFAULTUSER = newuser
        output = "`Berhasil mengubah pengguna menjadi " + newuser + ".`"
    await username.edit(f"{output}")


@register(outgoing=True, pattern=r"^\.resetalive$")
async def amireallyalivereset(ureset):
    """For .resetalive command, reset the username in the .alive command."""
    global DEFAULTUSER
    DEFAULTUSER = str(ALIVE_NAME) if ALIVE_NAME else uname().node
    await ureset.edit("`Berhasil menyetel ulang pengguna untuk “.alive”`")


CMD_HELP.update(
    {
        "sysd": "`.sysd`"
        "\n➥  Menampilkan informasi sistem menggunakan neofetch.",
        "botver": "`.botver`"
        "\n➥  Menampilkan versi userbot.",
        "pip": "`.pip [modul]`"
        "\n➥  Melakukan pencarian modul pip.",
        "alive": "`.alive`"
        "\n➥  Melihat apakah bot Anda berfungsi atau tidak."
        "\n\n`.aliveu [teks]`"
        "\n➥  Mengubah “Pengguna” di `.alive` menjadi teks yang Anda inginkan."
        "\n\n`.resetalive`"
        "\n➥  Menyetel ulang “Pengguna” ke default.",
    }
)
