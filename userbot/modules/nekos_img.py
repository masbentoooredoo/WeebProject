# Copyright (C) 2021 Bian Sepang
# All Rights Reserved.
#

from aiohttp import ClientSession

from userbot import CMD_HELP
from userbot.events import register


async def get_nekos_img(args):
    nekos_baseurl = "https://nekos.life/api/v2/img/"
    if args == "random_hentai_gif":
        args = "Random_hentai_gif"
    async with ClientSession() as ses:
        async with ses.get(nekos_baseurl + args) as r:
            result = await r.json()
            return result


@register(outgoing=True, pattern=r"^\.nekos(?: |$)(.*)")
async def nekos_media(event):
    args = event.pattern_match.group(1)
    args_error = "`Ketik “.help nekos” untuk melihat argumen yang tersedia.`"
    if not args:
        return await event.edit(args_error)
    result = await get_nekos_img(args)
    if result.get("msg") == "404":
        return await event.edit(args_error)
    media_url = result.get("url")
    await event.edit("`Mengambil data dari nekos...`")
    await event.client.send_file(
        entity=event.chat_id,
        file=media_url,
        caption=f"[Sumber]({media_url})",
        force_document=False,
        reply_to=event.reply_to_msg_id,
    )
    await event.delete()


CMD_HELP.update(
    {
        "nekos": "`.nekos [argumen]`"
        "\n➥  Untuk mengambil gambar dari nekos"
        "\n\n**Argumen :** `8ball`, `anal`, `avatar`, `baka`, `bj`, "
        "`blowjob`, `boobs`, `classic`, `cuddle`, `cum`, "
        "`cum_jpg`, `ero`, `erofeet`, `erok`, `erokemo`, "
        "`eron`, `eroyuri`, `feed`, `feet`, `feetg`, "
        "`femdom`, `fox_girl`, `futanari`, `gasm`, `gecg`, "
        "`goose`, `hentai`, `holo`, `holoero`, `hololewd`, "
        "`hug`, `kemonomimi`, `keta`, `kiss`, `kuni`, "
        "`les`, `lewd`, `lewdk`, `lewdkemo`, `lizard`, "
        "`neko`, `ngif`, `nsfw_avatar`, `nsfw_neko_gif`, `pat`, "
        "`poke`, `pussy`, `pussy_jpg`, `pwankg`, `random_hentai_gif`, "
        "`slap`, `smallboobs`, `smug`, `solo`, `solog`, "
        "`spank`, `tickle`, `tits`, `trap`, `waifu`, "
        "`wallpaper`, `woof`, `yuri`"
    }
)
