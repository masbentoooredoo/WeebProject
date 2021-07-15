# Ported by Aidil Aryanto

import os
from asyncio.exceptions import TimeoutError as TOError

from telethon.errors.rpcerrorlist import YouBlockedUserError

from userbot import CMD_HELP, TEMP_DOWNLOAD_DIRECTORY, bot
from userbot.events import register


@register(outgoing=True, pattern=r"^\.spotnow( s$|$)(.*)")
async def _(event):
    if event.fwd_from:
        return
    input_str = event.pattern_match.group(1).strip()
    chat = "@SpotifyNowBot"
    now = f"/now"
    await event.edit("`Memproses...`")
    try:
        async with event.client.conversation(chat) as conv:
            try:
                msg = await conv.send_message(now)
                response = await conv.get_response()
                """don't spam notif"""
                await bot.send_read_acknowledge(conv.chat_id)
            except YouBlockedUserError:
                await event.reply("`Harap buka blokir`  **@SpotifyNowBot**`...`")
                return
            if response.text.startswith("You're"):
                await event.edit(
                    "`Anda tidak mendengarkan apapun di Spotify saat ini.`"
                )
                await event.client.delete_messages(conv.chat_id, [msg.id, response.id])
                return
            if response.text.startswith("Ads."):
                await event.edit("`Anda mendengarkan iklan yang mengganggu.`")
                await event.client.delete_messages(conv.chat_id, [msg.id, response.id])
                return
            else:
                if input_str == "s":
                    downloaded_file_name = await event.client.download_media(
                        response.media, TEMP_DOWNLOAD_DIRECTORY + "spot.webp"
                    )
                    link = response.reply_markup.rows[0].buttons[0].url
                    spot = await event.client.send_file(
                        event.chat_id,
                        downloaded_file_name,
                        force_document=False,
                    )
                    await event.respond(
                        f"[Putar di Spotify]({link})", reply_to=spot, link_preview=False
                    )
                elif not input_str:
                    downloaded_file_name = await event.client.download_media(
                        response.media, TEMP_DOWNLOAD_DIRECTORY
                    )
                    link = response.reply_markup.rows[0].buttons[0].url
                    await event.client.send_file(
                        event.chat_id,
                        downloaded_file_name,
                        force_document=False,
                        caption=f"[Putar di Spotify]({link})",
                    )
                """cleanup chat after completed"""
                await event.client.delete_messages(conv.chat_id, [msg.id, response.id])
        await event.delete()
        return os.remove(downloaded_file_name)
    except TOError:
        return await event.edit("**Kesalahan :**\n**@SpotifyNowBot**  `tidak menanggapi!`")


CMD_HELP.update(
    {
        "spotifynow": "`.spotnow`"
        "\n➥  Menampilkan apa yang Anda dengarkan di Spotify."
        "\n\n`.spotnow s`"
        "\n➥  Sama seperti “.spotnow”, tetapi dikirim sebagai stiker."
        "\n**@SpotifyNowBot**"
    }
)
