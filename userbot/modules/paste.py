# Copyright (C) 2019 The Raphielscape Company LLC.
#
# Licensed under the Raphielscape Public License, Version 1.d (the "License");
# you may not use this file except in compliance with the License.
#
"""Userbot module containing commands for interacting with dogbin(https://del.dog)."""
import os

import aiohttp
from aiofile import async_open

from userbot import CMD_HELP, TEMP_DOWNLOAD_DIRECTORY
from userbot.events import register

DOGBIN_URL = "https://del.dog/"
NEKOBIN_URL = "https://nekobin.com/"


@register(outgoing=True, pattern=r"^\.paste( d)?([\s\S]*)")
async def paste(pstl):
    """For .paste command, pastes the text directly to nekobin/dogbin"""
    url_type = pstl.pattern_match.group(1)
    match = pstl.pattern_match.group(2).strip()
    replied = await pstl.get_reply_message()
    f_ext = ".txt"

    if not match and not pstl.is_reply:
        return await pstl.edit("`Apa yang harus saya tempel?`")

    if match:
        message = match
    elif replied:
        if replied.media:
            downloaded_file_name = await pstl.client.download_media(
                replied,
                TEMP_DOWNLOAD_DIRECTORY,
            )
            f_ext = os.path.splitext(downloaded_file_name)[-1]
            async with async_open(downloaded_file_name, "r") as fd:
                try:
                    message = await fd.read()
                except UnicodeDecodeError:
                    return await pstl.edit("`Tidak dapat menempelkan file ini.`")
            os.remove(downloaded_file_name)
        else:
            message = replied.message

    async with aiohttp.ClientSession() as ses:
        if not url_type:
            await pstl.edit("`Menempelkan ke Nekobin...`")
            async with ses.post(
                NEKOBIN_URL + "api/documents", json={"content": message}
            ) as resp:
                if resp.status == 201:
                    response = await resp.json()
                    key = response["result"]["key"]
                    nekobin_final_url = NEKOBIN_URL + key + f_ext
                    reply_text = (
                        "`Berhasil ditempel!`\n\n"
                        f"[URL Nekobin]({nekobin_final_url})\n"
                        f"[Lihat RAW]({NEKOBIN_URL}raw/{key})"
                    )
                else:
                    reply_text = "`Gagal mencapai Nekobin.`"
        else:
            await pstl.edit("`Menempelkan ke Dogbin...`")
            async with ses.post(
                DOGBIN_URL + "documents", data=message.encode("utf-8")
            ) as resp:
                if resp.status == 200:
                    response = await resp.json()
                    key = response["key"]
                    dogbin_final_url = DOGBIN_URL + key + f_ext

                    if response["isUrl"]:
                        reply_text = (
                            "`Berhasil ditempel!`\n\n"
                            f"[URL dipersingkat]({dogbin_final_url})\n\n"
                            "`URL Asli`\n"
                            f"[URL Dogbin]({DOGBIN_URL}v/{key})\n"
                            f"[Lihat RAW]({DOGBIN_URL}raw/{key})"
                        )
                    else:
                        reply_text = (
                            "`Berhasil ditempel!`\n\n"
                            f"[URL Dogbin]({dogbin_final_url})\n"
                            f"[Lihat RAW]({DOGBIN_URL}raw/{key})"
                        )
                else:
                    reply_text = "`Gagal mencapai Dogbin.`"

    await pstl.edit(reply_text)


@register(outgoing=True, pattern=r"^\.getpaste(?: |$)(.*)")
async def get_dogbin_content(dog_url):
    """For .getpaste command, fetches the content of a dogbin URL."""
    textx = await dog_url.get_reply_message()
    message = dog_url.pattern_match.group(1)
    await dog_url.edit("`Mendapatkan konten Dogbin...`")

    if textx:
        message = str(textx.message)

    format_normal = f"{DOGBIN_URL}"
    format_view = f"{DOGBIN_URL}v/"

    if message.startswith(format_view):
        message = message[len(format_view) :]
    elif message.startswith(format_normal):
        message = message[len(format_normal) :]
    elif message.startswith("del.dog/"):
        message = message[len("del.dog/") :]
    else:
        return await dog_url.edit("`Apakah itu URL Dogbin?`")

    async with aiohttp.ClientSession(raise_for_status=True) as ses:
        try:
            async with ses.get(f"{DOGBIN_URL}raw/{message}") as resp:
                paste_content = await resp.text()
        except aiohttp.ClientResponseError as err:
            return await dog_url.edit(
                f"`Permintaan mengembalikan kode status tidak berhasil.`\n\n`{str(err)}`"
            )
        except aiohttp.ServerTimeoutError as err:
            return await dog_url.edit(f"`Permintaan waktu habis.`\n\n`{str(err)}`")
        except aiohttp.TooManyRedirects as err:
            return await dog_url.edit(
                f"`Pemintaan melebihi jumlah pengalihan maksimum yang dikonfigurasikan.`\n\n`{str(err)}`"
            )
        reply_text = (
            f"`Berhasil mengambil konten Dogbin!`\n\n`Konten :`\n`{paste_content}`"
        )

    await dog_url.edit(reply_text)


CMD_HELP.update(
    {
        "paste": "`.paste / .paste d [teks/balas]`"
        "\n➥  Menempelkan teks ke Nekobin atau Dogbin."
        "\n\n`.getpaste`"
        "\n➥  Mendapatkan konten teks atau url yang dipersingkat dari Dogbin (https://del.dog/)"
    }
)
