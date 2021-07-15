# Copyright (C) 2019 The Raphielscape Company LLC.
#
# Licensed under the Raphielscape Public License, Version 1.c (the "License");
# you may not use this file except in compliance with the License.
#
# The entire source code is OSSRPL except 'whois' which is MPL
# License: MPL and OSSRPL
""" Userbot module for getting info about any user on Telegram(including you!). """

import os

from telethon.tl.functions.photos import GetUserPhotosRequest
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.types import MessageEntityMentionName
from telethon.utils import get_input_location

from userbot import CMD_HELP, TEMP_DOWNLOAD_DIRECTORY
from userbot.events import register


@register(pattern=r"^\.whois(?: |$)(.*)", outgoing=True)
async def who(event):

    await event.edit(
        "`Harap tunggu sementara saya mengambil beberapa data dari`  **Zona Jaringan Global**`...`"
    )

    if not os.path.isdir(TEMP_DOWNLOAD_DIRECTORY):
        os.makedirs(TEMP_DOWNLOAD_DIRECTORY)

    replied_user = await get_user(event)
    if replied_user is None:
        await event.edit(
            "`Ini adalah admin anonim di grup ini.\nTidak dapat mengambil info.`"
        )
        return

    try:
        photo, caption = await fetch_info(replied_user, event)
    except AttributeError:
        await event.edit("`Tidak dapat mengambil info dari pengguna ini.`")
        return

    message_id_to_reply = event.message.reply_to_msg_id

    if not message_id_to_reply:
        message_id_to_reply = None

    try:
        await event.client.send_file(
            event.chat_id,
            photo,
            caption=caption,
            link_preview=False,
            force_document=False,
            reply_to=message_id_to_reply,
            parse_mode="html",
        )

        if not photo.startswith("http"):
            os.remove(photo)
        await event.delete()

    except TypeError:
        await event.edit(caption, parse_mode="html")


async def get_user(event):
    """Get the user from argument or replied message."""
    if event.reply_to_msg_id and not event.pattern_match.group(1):
        previous_message = await event.get_reply_message()
        if previous_message.sender_id is None and not event.is_private:
            return None
        replied_user = await event.client(
            GetFullUserRequest(previous_message.sender_id)
        )
    else:
        user = event.pattern_match.group(1)

        if user.isnumeric():
            user = int(user)

        if not user:
            self_user = await event.client.get_me()
            user = self_user.id

        if event.message.entities is not None:
            probable_user_mention_entity = event.message.entities[0]

            if isinstance(probable_user_mention_entity, MessageEntityMentionName):
                user_id = probable_user_mention_entity.user_id
                replied_user = await event.client(GetFullUserRequest(user_id))
                return replied_user
        try:
            user_object = await event.client.get_entity(user)
            replied_user = await event.client(GetFullUserRequest(user_object.id))
        except (TypeError, ValueError) as err:
            return await event.edit(str(err))

    return replied_user


async def fetch_info(replied_user, event):
    """Get details from the User object."""
    replied_user_profile_photos = await event.client(
        GetUserPhotosRequest(
            user_id=replied_user.user.id, offset=42, max_id=0, limit=80
        )
    )
    replied_user_profile_photos_count = (
        "Seseorang membutuhkan bantuan dengan mengunggah foto profil."
    )
    try:
        replied_user_profile_photos_count = replied_user_profile_photos.count
    except AttributeError:
        pass
    user_id = replied_user.user.id
    first_name = replied_user.user.first_name
    last_name = replied_user.user.last_name
    try:
        dc_id, _ = get_input_location(replied_user.profile_photo)
    except Exception as e:
        dc_id = "Tidak dapat mengambil ID Pusat Data!"
        str(e)
    common_chat = replied_user.common_chats_count
    username = replied_user.user.username
    user_bio = replied_user.about
    is_bot = replied_user.user.bot
    restricted = replied_user.user.restricted
    verified = replied_user.user.verified
    photo = await event.client.download_profile_photo(
        user_id, TEMP_DOWNLOAD_DIRECTORY + str(user_id) + ".jpg", download_big=True
    )
    first_name = (
        first_name.replace("\u2060", "")
        if first_name
        else ("Orang ini tidak memiliki nama depan")
    )
    last_name = (
        last_name.replace("\u2060", "") if last_name else ("Orang ini tidak memiliki nama belakang")
    )
    username = f"@{username}" if username else ("Orang ini tidak memiliki nama pengguna")
    user_bio = "Orang ini tidak memiliki bio" if not user_bio else user_bio

    caption = "<b>INFO</b>\n\n"
    caption += f"<b>Nama Depan</b> : {first_name}\n"
    caption += f"<b>Nama Belakang</b> : {last_name}\n"
    caption += f"<b>Nama Pengguna</b> : {username}\n"
    caption += f"<b>ID Pusat Data</b> : {dc_id}\n"
    caption += f"<b>Jumlah Foto Profil</b> : {replied_user_profile_photos_count}\n"
    caption += f"<b>Apakah Bot</b> : {is_bot}\n"
    caption += f"<b>Apakah Dibatasi</b> : {restricted}\n"
    caption += f"<b>Diverifikasi oleh Telegram</b> : {verified}\n"
    caption += f"<b>ID</b> : <code>{user_id}</code>\n\n"
    caption += f"<b>BIO</b> \n<code>{user_bio}</code>\n\n"
    caption += f"<b>Obrolan Umum dengan Pengguna</b> : {common_chat}\n"
    caption += f"<b>Tautan Permanen ke Profil</b> : "
    caption += f'<a href="tg://user?id={user_id}">{first_name}</a>'

    return photo, caption


CMD_HELP.update(
    {
        "whois": "`.whois [nama pengguna/balas pesan seseorang]`"
        "\n➥  Dapatkan info seseorang."
    }
)
