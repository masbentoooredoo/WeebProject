# Copyright (C) 2019 The Raphielscape Company LLC.
#
# Licensed under the Raphielscape Public License, Version 1.c (the "License");
# you may not use this file except in compliance with the License.
#
""" Userbot module for filter commands """

from asyncio import sleep
from re import IGNORECASE, escape, search

from userbot import BOTLOG, BOTLOG_CHATID, CMD_HELP
from userbot.events import register


@register(incoming=True, disable_edited=True, disable_errors=True)
async def filter_incoming_handler(handler):
    """Checks if the incoming message contains handler of a filter"""
    try:
        if not (await handler.get_sender()).bot:
            try:
                from userbot.modules.sql_helper.filter_sql import get_filters
            except AttributeError:
                await handler.edit("`Berjalan di mode NON-SQL!`")
                return
            name = handler.raw_text
            filters = get_filters(handler.chat_id)
            if not filters:
                return
            for trigger in filters:
                pattern = r"( |^|[^\w])" + escape(trigger.keyword) + r"( |$|[^\w])"
                pro = search(pattern, name, flags=IGNORECASE)
                if pro and trigger.f_mesg_id:
                    msg_o = await handler.client.get_messages(
                        entity=BOTLOG_CHATID, ids=int(trigger.f_mesg_id)
                    )
                    await handler.reply(msg_o.message, file=msg_o.media)
                elif pro and trigger.reply:
                    await handler.reply(trigger.reply)
    except AttributeError:
        pass


@register(outgoing=True, pattern=r"^\.filter (.*)")
async def add_new_filter(new_handler):
    """For .filter command, allows adding new filters in a chat"""
    try:
        from userbot.modules.sql_helper.filter_sql import add_filter
    except AttributeError:
        await new_handler.edit("`Berjalan di mode NON-SQL!`")
        return
    value = new_handler.pattern_match.group(1).split(None, 1)
    """ - The first words after .filter(space) is the keyword - """
    keyword = value[0]
    try:
        string = value[1]
    except IndexError:
        string = None
    msg = await new_handler.get_reply_message()
    msg_id = None
    if msg and msg.media and not string:
        if BOTLOG_CHATID:
            await new_handler.client.send_message(
                BOTLOG_CHATID,
                f"#FILTER\nID OBROLAN: {new_handler.chat_id}\nPEMICU: {keyword}"
                "\n\nPesan berikut disimpan sebagai balasan filter obrolan, tolong jangan dihapus!!!",
            )
            msg_o = await new_handler.client.forward_messages(
                entity=BOTLOG_CHATID,
                messages=msg,
                from_peer=new_handler.chat_id,
                silent=True,
            )
            msg_id = msg_o.id
        else:
            return await new_handler.edit(
                "`Menyimpan media sebagai balasan ke filter memerlukan BOTLOG_CHATID untuk disetel.`"
            )
    elif new_handler.reply_to_msg_id and not string:
        rep_msg = await new_handler.get_reply_message()
        string = rep_msg.text
    success = "`Filter`  **{}**  `berhasil {}`."
    if add_filter(str(new_handler.chat_id), keyword, string, msg_id) is True:
        await new_handler.edit(success.format(keyword, "ditambahkan"))
    else:
        await new_handler.edit(success.format(keyword, "diperbarui"))


@register(outgoing=True, pattern=r"^\.stop (.*)")
async def remove_a_filter(r_handler):
    """For .stop command, allows you to remove a filter from a chat."""
    try:
        from userbot.modules.sql_helper.filter_sql import remove_filter
    except AttributeError:
        return await r_handler.edit("`Berjalan di mode NON-SQL!`")
    filt = r_handler.pattern_match.group(1)
    if not remove_filter(r_handler.chat_id, filt):
        await r_handler.edit(f"`Filter`  **{filt}**  `tidak ada`.")
    else:
        await r_handler.edit(f"`Filter`  **{filt}**  `berhasil dihapus`.")


@register(outgoing=True, pattern=r"^\.rmbotfilters (.*)")
async def kick_marie_filter(event):
    """ For .rmfilters command, allows you to kick all \
        Marie(or her clones) filters from a chat. """
    bot_type = event.pattern_match.group(1).lower()
    if bot_type not in ["marie", "rose"]:
        return await event.edit("`Bot itu belum didukung!`")
    await event.edit("`Akan menghapus semua filter!`")
    await sleep(3)
    resp = await event.get_reply_message()
    filters = resp.text.split("-")[1:]
    for i in filters:
        if bot_type.lower() == "marie":
            await event.reply(f"/stop {i.strip()}")
        if bot_type.lower() == "rose":
            i = i.replace("`", "")
            await event.reply(f"/stop {i.strip()}")
        await sleep(0.3)
    await event.respond("`Filter bot berhasil dibersihkan!`")
    if BOTLOG:
        await event.client.send_message(
            BOTLOG_CHATID, "Saya membersihkan semua filter di " + str(event.chat_id)
        )


@register(outgoing=True, pattern=r"^\.filters$")
async def filters_active(event):
    """For .filters command, lists all of the active filters in a chat."""
    try:
        from userbot.modules.sql_helper.filter_sql import get_filters
    except AttributeError:
        return await event.edit("`Berjalan di mode NON-SQL!`")
    transact = "`Tidak ada filter dalam obrolan ini.`"
    filters = get_filters(event.chat_id)
    for filt in filters:
        if transact == "`Tidak ada filter dalam obrolan ini.`":
            transact = "Filter aktif dalam obrolan ini:\n"
            transact += f"`{filt.keyword}`\n"
        else:
            transact += f"`{filt.keyword}`\n"

    await event.edit(transact)


CMD_HELP.update(
    {
        "filter": "`.filters`"
        "\n➥  Menampilkan semua daftar filter userbot yang aktif dalam obrolan."
        "\n\n`.filter [kata kunci] [balas teks]` `atau balas pesan dengan`\n`.filter [kata kunci]`"
        "\n➥  Menyimpan pesan balasan sebagai balasan untuk “kata kunci”."
        "\nBot akan membalas pesan setiap kali “kata kunci” disebutkan."
        "\nBekerja dengan segala hal mulai dari file hingga stiker."
        "\n\n`.stop [filter]`"
        "\n➥  Menghentikan filter yang ditentukan."
        "\n\n`.rmbotfilters [marie/rose]`"
        "\n➥  Menghapus semua filter bot admin di obrolan.\nSaat ini didukung : Marie, Rose, dan klonnya."
    }
)
