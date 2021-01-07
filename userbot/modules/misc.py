# Copyright (C) 2019 The Raphielscape Company LLC.
#
# Licensed under the Raphielscape Public License, Version 1.c (the "License");
# you may not use this file except in compliance with the License.
#
# You can find misc modules, which dont fit in anything xD
""" Userbot module for other small commands. """

import asyncio
import io
import sys
from os import execl
from random import randint
from time import sleep

from userbot import BOTLOG, BOTLOG_CHATID, CMD_HELP, bot
from userbot.events import register
from userbot.utils import time_formatter


@register(outgoing=True, pattern=r"^\.random")
async def randomise(items):
    """ For .random command, get a random item from the list of items. """
    itemo = (items.text[8:]).split()
    if len(itemo) < 2:
        return await items.edit(
            "`2 item atau lebih diperlukan! Periksa .help acak untuk info lebih lanjut.`"
        )
    index = randint(1, len(itemo) - 1)
    await items.edit(
        "**Kueri** : \n`" + items.text[8:] + "`\n**Hasil** : \n`" + itemo[index] + "`"
    )


@register(outgoing=True, pattern=r"^\.sleep ([0-9]+)$")
async def sleepybot(time):
    """ For .sleep command, let the userbot snooze for a few second. """
    counter = int(time.pattern_match.group(1))
    await time.edit("`Bot tidur!\nSaya merajuk dan tertidur...`")
    if BOTLOG:
        str_counter = time_formatter(counter)
        await time.client.send_message(
            BOTLOG_CHATID,
            f"Anda meletakkan bot untuk tidur {str_counter}.",
        )
    sleep(counter)
    await time.edit("`Oke, saya sudah bangun sekarang.`")


@register(outgoing=True, pattern=r"^\.shutdown$")
async def killthebot(event):
    """ For .shutdown command, shut the bot down."""
    await event.edit("`Menonaktifkan bot!\nSelamat tinggal...`")
    if BOTLOG:
        await event.client.send_message(BOTLOG_CHATID, "#SHUTDOWN \n" "Bot dinonaktifkan")
    await bot.disconnect()


@register(outgoing=True, pattern=r"^\.restart$")
async def killdabot(event):
    await event.edit("`Mulai ulang bot!\nSaya akan kembali sebentar lagi`")
    if BOTLOG:
        await event.client.send_message(BOTLOG_CHATID, "#RESTART \n" "Bot dimulai ulang")
    await bot.disconnect()
    # Spin a new instance of bot
    execl(sys.executable, sys.executable, *sys.argv)
    # Shut the existing one down
    exit()


@register(outgoing=True, pattern=r"^\.readme$")
async def reedme(e):
    await e.edit(
        "Di sini sesuatu untuk Anda baca :\n"
        "\n[WeebProject's README.md file](https://github.com/BianSepang/WeebProject/blob/master/README.md)"
        "\n[Setup Guide - Basic](https://telegra.ph/How-to-host-a-Telegram-Userbot-11-02)"
        "\n[Setup Guide - Google Drive](https://telegra.ph/How-To-Setup-Google-Drive-04-03)"
        "\n[Setup Guide - LastFM Module](https://telegra.ph/How-to-set-up-LastFM-module-for-Paperplane-userbot-11-02)"
        "\n[Setup Guide - How to get Deezer ARL TOKEN](https://notabug.org/RemixDevs/DeezloaderRemix/wiki/Login+via+userToken)"
        "\n[Special - Note](https://telegra.ph/Special-Note-11-02)"
    )


# Copyright (c) Gegham Zakaryan | 2019
@register(outgoing=True, pattern=r"^\.repeat (.*)")
async def repeat(rep):
    cnt, txt = rep.pattern_match.group(1).split(" ", 1)
    replyCount = int(cnt)
    toBeRepeated = txt

    replyText = toBeRepeated + "\n"

    for i in range(0, replyCount - 1):
        replyText += toBeRepeated + "\n"

    await rep.edit(replyText)


@register(outgoing=True, pattern=r"^\.repo$")
async def repo_is_here(wannasee):
    """ For .repo command, just returns the repo URL. """
    await wannasee.edit("Klik [disini](https://github.com/BianSepang/WeebProject) untuk melihat Repo yang saya gunakan atau Klik [disini](https://github.com/masbentoooredoo/WeebProject) untuk melihat fork Repo saya.")
    await asyncio.sleep(30)
    await wannasee.delete()


@register(outgoing=True, pattern=r"^\.raw$")
async def raw(event):
    the_real_message = None
    reply_to_id = None
    if event.reply_to_msg_id:
        previous_message = await event.get_reply_message()
        the_real_message = previous_message.stringify()
        reply_to_id = event.reply_to_msg_id
    else:
        the_real_message = event.stringify()
        reply_to_id = event.message.id
    with io.BytesIO(str.encode(the_real_message)) as out_file:
        out_file.name = "raw_message_data.txt"
        await event.edit("`Periksa log userbot untuk data pesan yang diterjemahkan!`")
        await event.client.send_file(
            BOTLOG_CHATID,
            out_file,
            force_document=True,
            allow_cache=False,
            reply_to=reply_to_id,
            caption="Berikut data yang diterjemahkan!",
        )


CMD_HELP.update(
    {
        "random": "`.random [item1] [item2] ... [itemN]`"
        "\n➥  Dapatkan item acak dari daftar item.",
        "sleep": "`.sleep [detik]`" "\n➥  Biarkan bot Anda tidur selama beberapa detik.",
        "shutdown": "`.shutdown`" "\n➥  Matikan bot.",
        "repo": "`.repo`" "\n➥  Github Repo asli dari bot ini.",
        "readme": "`.readme`"
        "\n➥  Berikan tautan untuk menyiapkan userbot dan modulnya.",
        "repeat": "`.repeat [no] [teks]`"
        "\n➥  Ulangi teks tersebut beberapa kali. Jangan bingung karena ini adalah spam.",
        "restart": "`.restart`" "\n➥  Mulai ulang bot.",
        "raw": "`.raw`"
        "\n➥  Dapatkan data berformat seperti JSON mendetail tentang pesan yang dibalas.",
    }
)
