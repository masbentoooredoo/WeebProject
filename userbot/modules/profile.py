# Copyright (C) 2019 The Raphielscape Company LLC.
#
# Licensed under the Raphielscape Public License, Version 1.c (the "License");
# you may not use this file except in compliance with the License.
#
""" Userbot module for changing your Telegram profile details. """

import os

from telethon.errors import ImageProcessFailedError, PhotoCropSizeSmallError
from telethon.errors.rpcerrorlist import PhotoExtInvalidError, UsernameOccupiedError
from telethon.tl.functions.account import UpdateProfileRequest, UpdateUsernameRequest
from telethon.tl.functions.channels import GetAdminedPublicChannelsRequest
from telethon.tl.functions.photos import (
    DeletePhotosRequest,
    GetUserPhotosRequest,
    UploadProfilePhotoRequest,
)
from telethon.tl.types import Channel, Chat, InputPhoto, MessageMediaPhoto, User

from userbot import CMD_HELP, bot
from userbot.events import register

# ====================== CONSTANT ===============================
INVALID_MEDIA = "`Ekstensi entitas media tidak valid.`"
PP_CHANGED = "`Foto profil berhasil diubah.`"
PP_TOO_SMOL = "`Gambar ini terlalu kecil, gunakan gambar yang lebih besar.`"
PP_ERROR = "`Kegagalan terjadi saat memproses gambar.`"

BIO_SUCCESS = "`Bio berhasil diubah.`"

NAME_OK = "`Nama Anda berhasil diubah.`"
USERNAME_SUCCESS = "`Nama pengguna Anda berhasil diubah.`"
USERNAME_TAKEN = "`Nama pengguna ini sudah dipakai.`"
# ===============================================================


@register(outgoing=True, pattern=r"^\.reserved$")
async def mine(event):
    """ For .reserved command, get a list of your reserved usernames. """
    result = await bot(GetAdminedPublicChannelsRequest())
    output_str = ""
    for channel_obj in result.chats:
        output_str += f"{channel_obj.title}\n@{channel_obj.username}\n\n"
    await event.edit(output_str)


@register(outgoing=True, pattern=r"^\.name")
async def update_name(name):
    """ For .name command, change your name in Telegram. """
    newname = name.text[6:]
    if " " not in newname:
        firstname = newname
        lastname = ""
    else:
        namesplit = newname.split(" ", 1)
        firstname = namesplit[0]
        lastname = namesplit[1]

    await name.client(UpdateProfileRequest(first_name=firstname, last_name=lastname))
    await name.edit(NAME_OK)


@register(outgoing=True, pattern=r"^\.setpfp$")
async def set_profilepic(propic):
    """ For .profilepic command, change your profile picture in Telegram. """
    replymsg = await propic.get_reply_message()
    photo = None
    if replymsg.media:
        if isinstance(replymsg.media, MessageMediaPhoto):
            photo = await propic.client.download_media(message=replymsg.photo)
        elif "image" in replymsg.media.document.mime_type.split("/"):
            photo = await propic.client.download_file(replymsg.media.document)
        else:
            await propic.edit(INVALID_MEDIA)

    if photo:
        try:
            await propic.client(
                UploadProfilePhotoRequest(await propic.client.upload_file(photo))
            )
            os.remove(photo)
            await propic.edit(PP_CHANGED)
        except PhotoCropSizeSmallError:
            await propic.edit(PP_TOO_SMOL)
        except ImageProcessFailedError:
            await propic.edit(PP_ERROR)
        except PhotoExtInvalidError:
            await propic.edit(INVALID_MEDIA)


@register(outgoing=True, pattern=r"^\.setbio (.*)")
async def set_biograph(setbio):
    """ For .setbio command, set a new bio for your profile in Telegram. """
    newbio = setbio.pattern_match.group(1)
    await setbio.client(UpdateProfileRequest(about=newbio))
    await setbio.edit(BIO_SUCCESS)


@register(outgoing=True, pattern=r"^\.username (.*)")
async def update_username(username):
    """ For .username command, set a new username in Telegram. """
    newusername = username.pattern_match.group(1)
    try:
        await username.client(UpdateUsernameRequest(newusername))
        await username.edit(USERNAME_SUCCESS)
    except UsernameOccupiedError:
        await username.edit(USERNAME_TAKEN)


@register(outgoing=True, pattern=r"^\.count$")
async def count(event):
    """ For .count command, get profile stats. """
    u = 0
    g = 0
    c = 0
    bc = 0
    b = 0
    result = ""
    await event.edit("`Sedang memproses...`")
    dialogs = await bot.get_dialogs(limit=None, ignore_migrated=True)
    for d in dialogs:
        currrent_entity = d.entity
        if isinstance(currrent_entity, User):
            if currrent_entity.bot:
                b += 1
            else:
                u += 1
        elif isinstance(currrent_entity, Chat):
            g += 1
        elif isinstance(currrent_entity, Channel):
            if currrent_entity.broadcast:
                bc += 1
            else:
                c += 1
        else:
            print(d)

    result += f"**Pengguna** : \t**{u}**\n"
    result += f"**Grup** : \t**{g}**\n"
    result += f"**Super Grup** : \t**{c}**\n"
    result += f"**Saluran** : \t**{bc}**\n"
    result += f"**Bot** : \t**{b}**"

    await event.edit(result)


@register(outgoing=True, pattern=r"^\.delpfp")
async def remove_profilepic(delpfp):
    """ For .delpfp command, delete your current profile picture in Telegram. """
    group = delpfp.text[8:]
    if group == "all":
        lim = 0
    elif group.isdigit():
        lim = int(group)
    else:
        lim = 1

    pfplist = await delpfp.client(
        GetUserPhotosRequest(user_id=delpfp.from_id, offset=0, max_id=0, limit=lim)
    )
    input_photos = []
    for sep in pfplist.photos:
        input_photos.append(
            InputPhoto(
                id=sep.id,
                access_hash=sep.access_hash,
                file_reference=sep.file_reference,
            )
        )
    await delpfp.client(DeletePhotosRequest(id=input_photos))
    await delpfp.edit(f"`Berhasil menghapus`  **{len(input_photos)}**  `foto profil.`")


CMD_HELP.update(
    {
        "profile": "`.username [nama pengguna baru]`"
        "\n➥  Ubah nama pengguna Telegram Anda."
        "\n\n`.name [nama depan]`\n`.name [nama depan] [nama belakang]`"
        "\n➥  Ubah nama Telegram Anda. (Nama depan dan belakang akan dipisahkan oleh spasi pertama)"
        "\n\n`.setpfp`"
        "\n➥  Balas dengan `.setpfp` ke gambar untuk mengubah gambar profil telegram Anda."
        "\n\n`.setbio [bio baru]`"
        "\n➥  Ubah bio Telegram Anda."
        "\n\n`.delpfp` / `.delpfp [nomor/semua]`"
        "\n➥  Menghapus gambar profil Telegram Anda."
        "\n\n`.reserved`"
        "\n➥  Menampilkan nama pengguna yang dipesan oleh Anda."
        "\n\n`.count`"
        "\n➥  Menghitung grup Anda, obrolan, bot, dll..."
    }
)
