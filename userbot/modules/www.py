# Copyright (C) 2019 The Raphielscape Company LLC.
#
# Licensed under the Raphielscape Public License, Version 1.c (the "License");
# you may not use this file except in compliance with the License.
#
""" Userbot module containing commands related to the \
    Information Superhighway (yes, Internet). """

from datetime import datetime

from speedtest import Speedtest
from telethon import functions

from userbot import CMD_HELP
from userbot.events import register
from userbot.utils import humanbytes


@register(outgoing=True, pattern=r"^\.speedtest$")
async def speedtst(spd):
    """ For .speed command, use SpeedTest to check server speeds. """
    await spd.edit("`Tes kecepatan. . .`")
    
    test = Speedtest()
    test.get_best_server()
    test.download()
    test.upload()
    test.results.share()
    result = test.results.dict()

    msg = (
        f"**Dimulai pada {result['timestamp']}** \n\n"
        "**Klien**\n"
        f"**ISP :** `{result['client']['isp']}`\n"
        f"**Negara :** `{result['client']['country']}`\n\n"
        "**Server**\n"
        f"**Nama :** `{result['server']['name']}`\n"
        f"**Negara :** `{result['server']['country']}`\n"
        f"**Sponsor :** `{result['server']['sponsor']}`\n"
        f"**Ping :** `{result['ping']}`\n"
        f"**Unggah :** `{humanbytes(result['upload'])}/s`\n"
        f"**Unduh :** `{humanbytes(result['download'])}/s`\n"
    )
    
    await spd.delete()
    await spd.client.send_file(
        spd.chat_id,
        result["share"],
        caption=msg,
        force_document=False,
    )


@register(outgoing=True, pattern=r"^\.dc$")
async def neardc(event):
    """ For .dc command, get the nearest datacenter information. """
    result = await event.client(functions.help.GetNearestDcRequest())
    await event.edit(
        f"**Negara** : `{result.country}`\n"
        f"**Pusat Data Terdekat** : `{result.nearest_dc}`\n"
        f"**Pusat Data ini** : `{result.this_dc}`"
    )


@register(outgoing=True, pattern=r"^\.ping$")
async def pingme(pong):
    """ For .ping command, ping the userbot from any chat.  """
    start = datetime.now()
    await pong.edit("**Pong!**")
    end = datetime.now()
    duration = (end - start).microseconds / 1000
    await pong.edit("**Pong!**\n**%sms**" % (duration))


CMD_HELP.update(
    {
        "speedtest": "`.speedtest`" "\n➥  Melakukan tes kecepatan dan menunjukkan hasilnya.",
        "dc": "`.dc`" "\n➥  Menemukan pusat data terdekat dari server Anda.",
        "ping": "`.ping`" "\n➥  Menunjukkan berapa lama waktu yang dibutuhkan untuk melakukan ping bot Anda.",
    }
)
