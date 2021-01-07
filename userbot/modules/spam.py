# Copyright (C) 2019 The Raphielscape Company LLC.
#
# Licensed under the Raphielscape Public License, Version 1.c (the "License");
# you may not use this file except in compliance with the License.

import asyncio
from asyncio import sleep

from userbot import BOTLOG, BOTLOG_CHATID, CMD_HELP
from userbot.events import register


@register(outgoing=True, pattern=r"^\.cspam (.*)")
async def tmeme(e):
    cspam = str(e.pattern_match.group(1))
    message = cspam.replace(" ", "")
    await e.delete()
    for letter in message:
        await e.respond(letter)
    if BOTLOG:
        await e.client.send_message(
            BOTLOG_CHATID, "#CSPAM\n" "TSpam berhasil dijalankan."
        )


@register(outgoing=True, pattern=r"^\.wspam (.*)")
async def t_meme(e):
    wspam = str(e.pattern_match.group(1))
    message = wspam.split()
    await e.delete()
    for word in message:
        await e.respond(word)
    if BOTLOG:
        await e.client.send_message(
            BOTLOG_CHATID, "#WSPAM\n" "WSpam berhasil dijalankan."
        )


@register(outgoing=True, pattern=r"^\.spam (.*)")
async def spammers(e):
    counter = int(e.pattern_match.group(1).split(" ", 1)[0])
    spam_message = str(e.pattern_match.group(1).split(" ", 1)[1])
    await e.delete()
    await asyncio.wait([e.respond(spam_message) for i in range(counter)])
    if BOTLOG:
        await e.client.send_message(
            BOTLOG_CHATID, "#SPAM\n" "Spam berhasil dijalankan."
        )


@register(outgoing=True, pattern=r"^\.picspam")
async def tiny_pic_spam(e):
    message = e.text
    text = message.split()
    counter = int(text[1])
    link = str(text[2])
    await e.delete()
    for i in range(1, counter):
        await e.client.send_file(e.chat_id, link)
    if BOTLOG:
        await e.client.send_message(
            BOTLOG_CHATID, "#PICSPAM\n" "Spam gambar berhasil dijalankan."
        )


@register(outgoing=True, pattern=r"^\.delayspam (.*)")
async def spammer(e):
    spamDelay = float(e.pattern_match.group(1).split(" ", 2)[0])
    counter = int(e.pattern_match.group(1).split(" ", 2)[1])
    spam_message = str(e.pattern_match.group(1).split(" ", 2)[2])
    await e.delete()
    for i in range(1, counter):
        await e.respond(spam_message)
        await sleep(spamDelay)
    if BOTLOG:
        await e.client.send_message(
            BOTLOG_CHATID, "#DELAYSPAM\n" "Spam tunda berhasil dijalankan."
        )


CMD_HELP.update(
    {
        "spam": "`.cspam [teks]`"
        "\n➥  Spam teks huruf demi huruf."
        "\n\n`.spam [jumlah] [teks]`"
        "\n➥  Spam teks dalam obrolan sebanyak [jumlah]."
        "\n\n`.wspam [teks]`"
        "\n➥  Spam teks kata demi kata."
        "\n\n`.picspam [jumlah] [tautan ke gambar/gif]`"
        "\n➥  Spam gambar/gif.\nMemangnya spam teks tidak cukup?!"
        "\n\n`.delayspam [tunda] [jumlah] [teks]`"
        "\n➥  Spam besar tetapi dengan penundaan khusus."
        "\n\n**CATATAN :** Resiko Anda tanggung sendiri...!!!"
    }
)
