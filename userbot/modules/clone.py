# Ported from Userge-Plugins

import asyncio
import os

from telethon.tl.functions.account import UpdateProfileRequest
from telethon.tl.functions.photos import DeletePhotosRequest, UploadProfilePhotoRequest
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.types import InputPhoto

from userbot import CMD_HELP, TEMP_DOWNLOAD_DIRECTORY
from userbot.events import register

PHOTO = TEMP_DOWNLOAD_DIRECTORY + "profile_pic.jpg"
USER_DATA = {}


@register(pattern=r"^\.clone(?: |$)(.*)", outgoing=True)
async def clone(cloner):
    """ Clone first name, last name, bio and profile picture """
    reply_message = cloner.reply_to_msg_id
    message = await cloner.get_reply_message()
    if reply_message:
        input_ = message.sender.id
    else:
        input_ = cloner.pattern_match.group(1)

    if not input_:
        await cloner.edit("`Harap balas ke pungguna atau masukkan nama pengguna`")
        await asyncio.sleep(5)
        await cloner.delete()
        return

    await cloner.edit("`Kloning...`")

    try:
        user = await cloner.client(GetFullUserRequest(input_))
    except ValueError:
        await cloner.edit("`Nama pengguna tidak valid!`")
        await asyncio.sleep(2)
        await cloner.delete()
        return
    me = await cloner.client.get_me()

    if USER_DATA or os.path.exists(PHOTO):
        await cloner.edit("`Kembalikan dulu!`")
        await asyncio.sleep(2)
        await cloner.delete()
        return
    mychat = await cloner.client(GetFullUserRequest(me.id))
    USER_DATA.update(
        {
            "first_name": mychat.user.first_name or "",
            "last_name": mychat.user.last_name or "",
            "about": mychat.about or "",
        }
    )
    await cloner.client(
        UpdateProfileRequest(
            first_name=user.user.first_name or "",
            last_name=user.user.last_name or "",
            about=user.about or "",
        )
    )
    if not user.profile_photo:
        await cloner.edit("`Pengguna tidak memiliki foto profil.\nKloning nama dan bio...`")
        await asyncio.sleep(5)
        await cloner.delete()
        return
    await cloner.client.download_profile_photo(user.user.id, PHOTO)
    await cloner.client(
        UploadProfilePhotoRequest(file=await cloner.client.upload_file(PHOTO))
    )
    await cloner.edit("`Profil berhasil di-klon!`")
    await asyncio.sleep(3)
    await cloner.delete()


@register(pattern=r"^\.revert(?: |$)(.*)", outgoing=True)
async def revert_(reverter):
    """ Returns Original Profile """
    if not (USER_DATA or os.path.exists(PHOTO)):
        await reverter.edit("`Sudah dikembalikan!`")
        await asyncio.sleep(2)
        await reverter.delete()
        return
    if USER_DATA:
        await reverter.client(UpdateProfileRequest(**USER_DATA))
        USER_DATA.clear()
    if os.path.exists(PHOTO):
        me = await reverter.client.get_me()
        photo = (await reverter.client.get_profile_photos(me.id, limit=1))[0]
        await reverter.client(
            DeletePhotosRequest(
                id=[
                    InputPhoto(
                        id=photo.id,
                        access_hash=photo.access_hash,
                        file_reference=photo.file_reference,
                    )
                ]
            )
        )
        os.remove(PHOTO)
    await reverter.edit("`Profil berhasil dikembalikan!`")
    await asyncio.sleep(3)
    await reverter.delete()


CMD_HELP.update(
    {
        "clone": "`.clone [balas/nama pengguna]`"
        "\n➥  Mengkloning nama seseorang, foto profil dan bio."
        "\n\n`.revert`"
        "\n➥  Kembali ke profil Anda."
    }
)
