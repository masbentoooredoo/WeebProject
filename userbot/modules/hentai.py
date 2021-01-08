# Copyright (C) 2021 Bian Sepang
# All Rights Reserved.
#

import nekos

from userbot import CMD_HELP
from userbot.events import register


@register(pattern=r"^\.hentai$", outgoing=True)
async def _(event):
    """Gets random hentai gif from nekos.py."""
    await event.edit("`Mengambil data dari nekos...`")
    pic = nekos.img("random_hentai_gif")
    await event.client.send_file(
        event.chat_id,
        pic,
        caption=f"[Sumber]({pic})",
    )
    await event.delete()


@register(pattern=r"^\.pussy$", outgoing=True)
async def _(event):
    """Gets anime pussy gif from nekos.py."""
    await event.edit("`Mengambil data dari nekos...`")
    pic = nekos.img("pussy")
    await event.client.send_file(
        event.chat_id,
        pic,
        caption=f"[Sumber]({pic})",
    )
    await event.delete()


@register(pattern=r"^\.cum$", outgoing=True)
async def _(event):
    """Gets anime cum gif from nekos.py."""
    await event.edit("`Mengambil data dari nekos...`")
    pic = nekos.img("cum")
    await event.client.send_file(
        event.chat_id,
        pic,
        caption=f"[Sumber]({pic})",
    )
    await event.delete()


@register(pattern=r"^\.nsfwneko$", outgoing=True)
async def _(event):
    """Gets nsfw neko gif from nekos.py."""
    await event.edit("`Mengambil data dari nekos...`")
    pic = nekos.img("nsfw_neko_gif")
    await event.client.send_file(
        event.chat_id,
        pic,
        caption=f"[Sumber]({pic})",
    )
    await event.delete()


CMD_HELP.update(
    {
        "hentai": "`.hentai`"
        "\n➥  Dapatkan gif hentai acak dari nekos."
        "\n\n`.pussy`"
        "\n➥  Dapatkan gif anime “miss v” dari nekos."
        "\n\n`.cum`"
        "\n➥  Dapatkan gif anime cum dari nekos."
        "\n\n`.nsfwneko`"
        "\n➥  Dapatkan gif nsfw neko dari nekos."
    }
)
