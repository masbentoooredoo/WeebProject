# Copyright (C) 2019 The Raphielscape Company LLC.
#
# Licensed under the Raphielscape Public License, Version 1.c (the "License");
# you may not use this file except in compliance with the License.
"""
Userbot module to help you manage a group
"""

from asyncio import sleep
from os import remove

from telethon.errors import (
    BadRequestError,
    ChatAdminRequiredError,
    ImageProcessFailedError,
    PhotoCropSizeSmallError,
    RightForbiddenError,
    UserAdminInvalidError,
)
from telethon.errors.rpcerrorlist import MessageTooLongError, UserIdInvalidError
from telethon.tl.functions.channels import (
    EditAdminRequest,
    EditBannedRequest,
    EditPhotoRequest,
)
from telethon.tl.functions.messages import UpdatePinnedMessageRequest
from telethon.tl.types import (
    ChannelParticipantsAdmins,
    ChannelParticipantsBots,
    ChatAdminRights,
    ChatBannedRights,
    MessageEntityMentionName,
    MessageMediaPhoto,
    PeerChat,
)

from userbot import BOTLOG, BOTLOG_CHATID, CMD_HELP, bot
from userbot.events import register

# =================== CONSTANT ===================
PP_TOO_SMOL = "`Gambar terlalu kecil`"
PP_ERROR = "`Kegagalan saat memproses gambar`"
NO_ADMIN = "`Saya bukan admin!`"
NO_PERM = "`Saya tidak memiliki izin yang memadai!`"
NO_SQL = "`Berjalan di mode Non-SQL!`"

CHAT_PP_CHANGED = "`Gambar obrolan diubah`"
CHAT_PP_ERROR = (
    "`Beberapa masalah saat memperbarui foto,`"
    "`mungkin karena saya bukan admin,`"
    "`atau tidak memiliki cukup hak.`"
)
INVALID_MEDIA = "`Ekstensi tidak valid`"

BANNED_RIGHTS = ChatBannedRights(
    until_date=None,
    view_messages=True,
    send_messages=True,
    send_media=True,
    send_stickers=True,
    send_gifs=True,
    send_games=True,
    send_inline=True,
    embed_links=True,
)

UNBAN_RIGHTS = ChatBannedRights(
    until_date=None,
    send_messages=None,
    send_media=None,
    send_stickers=None,
    send_gifs=None,
    send_games=None,
    send_inline=None,
    embed_links=None,
)

MUTE_RIGHTS = ChatBannedRights(until_date=None, send_messages=True)

UNMUTE_RIGHTS = ChatBannedRights(until_date=None, send_messages=False)
# ================================================


@register(outgoing=True, disable_errors=True, pattern=r"^\.setgpic$")
async def set_group_photo(gpic):
    """For .setgpic command, changes the picture of a group"""
    if not gpic.is_group:
        await gpic.edit("`Saya tidak yakin ini adalah grup.`")
        return
    replymsg = await gpic.get_reply_message()
    chat = await gpic.get_chat()
    admin = chat.admin_rights
    creator = chat.creator
    photo = None

    if not admin and not creator:
        return await gpic.edit(NO_ADMIN)

    if replymsg and replymsg.media:
        if isinstance(replymsg.media, MessageMediaPhoto):
            photo = await gpic.client.download_media(message=replymsg.photo)
        elif "image" in replymsg.media.document.mime_type.split("/"):
            photo = await gpic.client.download_file(replymsg.media.document)
        else:
            await gpic.edit(INVALID_MEDIA)

    if photo:
        try:
            await gpic.client(
                EditPhotoRequest(gpic.chat_id, await gpic.client.upload_file(photo))
            )
            await gpic.edit(CHAT_PP_CHANGED)

        except PhotoCropSizeSmallError:
            await gpic.edit(PP_TOO_SMOL)
        except ImageProcessFailedError:
            await gpic.edit(PP_ERROR)


@register(outgoing=True, disable_errors=True, pattern=r"^\.promote(?: |$)(.*)")
async def promote(promt):
    """For .promote command, promotes the replied/tagged person"""
    # Get targeted chat
    chat = await promt.get_chat()
    # Grab admin status or creator in a chat
    admin = chat.admin_rights
    creator = chat.creator

    # If not admin and not creator, also return
    if not admin and not creator:
        return await promt.edit(NO_ADMIN)

    new_rights = ChatAdminRights(
        add_admins=False,
        invite_users=True,
        change_info=False,
        ban_users=True,
        delete_messages=True,
        pin_messages=True,
    )

    await promt.edit("`Mempromosikan...`")
    user, rank = await get_user_from_event(promt)
    if not rank:
        rank = "Administrator"  # Just in case.
    if user:
        pass
    else:
        return

    # Try to promote if current user is admin or creator
    try:
        await promt.client(EditAdminRequest(promt.chat_id, user.id, new_rights, rank))
        await promt.edit("`Berhasil dipromosikan!`")
    except RightForbiddenError:
        return await promt.edit(NO_PERM)

    # If Telethon spit BadRequestError, assume
    # we don't have Promote permission
    except BadRequestError:
        return await promt.edit(NO_PERM)

    # Announce to the logging group if we have promoted successfully
    if BOTLOG:
        await promt.client.send_message(
            BOTLOG_CHATID,
            "#PROMOTE\n"
            f"PENGGUNA : [{user.first_name}](tg://user?id={user.id})\n"
            f"OBROLAN : {promt.chat.title}(`{promt.chat_id}`)",
        )


@register(outgoing=True, disable_errors=True, pattern=r"^\.demote(?: |$)(.*)")
async def demote(dmod):
    """For .demote command, demotes the replied/tagged person"""
    # Admin right check
    chat = await dmod.get_chat()
    admin = chat.admin_rights
    creator = chat.creator

    if not admin and not creator:
        return await dmod.edit(NO_ADMIN)

    # If passing, declare that we're going to demote
    await dmod.edit("`Menurunkan jabatan...`")
    rank = "admeme"  # dummy rank, lol.
    user = await get_user_from_event(dmod)
    user = user[0]
    if user:
        pass
    else:
        return

    # New rights after demotion
    newrights = ChatAdminRights(
        add_admins=None,
        invite_users=None,
        change_info=None,
        ban_users=None,
        delete_messages=None,
        pin_messages=None,
    )
    # Edit Admin Permission
    try:
        await dmod.client(EditAdminRequest(dmod.chat_id, user.id, newrights, rank))

    # If we catch BadRequestError from Telethon
    # Assume we don't have permission to demote
    except BadRequestError:
        return await dmod.edit(NO_PERM)
    await dmod.edit("`Berhasil menurunkan jabatan!`")

    # Announce to the logging group if we have demoted successfully
    if BOTLOG:
        await dmod.client.send_message(
            BOTLOG_CHATID,
            "#DEMOTE\n"
            f"PENGGUNA : [{user.first_name}](tg://user?id={user.id})\n"
            f"OBROLAN : {dmod.chat.title}(`{dmod.chat_id}`)",
        )


@register(outgoing=True, disable_errors=True, pattern=r"^\.ban(?: |$)(.*)")
async def ban(bon):
    """For .ban command, bans the replied/tagged person"""
    # Here laying the sanity check
    chat = await bon.get_chat()
    admin = chat.admin_rights
    creator = chat.creator

    # Well
    if not admin and not creator:
        return await bon.edit(NO_ADMIN)

    user, reason = await get_user_from_event(bon)
    if user:
        pass
    else:
        return

    # Announce that we're going to whack the pest
    await bon.edit("`Ada yang melakukan hal ceroboh!`")

    try:
        await bon.client(EditBannedRequest(bon.chat_id, user.id, BANNED_RIGHTS))
    except BadRequestError:
        return await bon.edit(NO_PERM)
    # Helps ban group join spammers more easily
    try:
        reply = await bon.get_reply_message()
        if reply:
            await reply.delete()
    except BadRequestError:
        return await bon.edit(
            "`Saya tidak memiliki izin yang memadai!\nTapi tetap saja dia diblokir(banned)!`"
        )
    # Delete message and then tell that the command
    # is done gracefully
    # Shout out the ID, so that fedadmins can fban later
    if reason:
        await bon.edit(f"{str(user.id)} diblokir(banned)!\n**Alasan** : {reason}")
    else:
        await bon.edit(f"{str(user.id)} diblokir(banned)!")
    # Announce to the logging group if we have banned the person
    # successfully!
    if BOTLOG:
        await bon.client.send_message(
            BOTLOG_CHATID,
            "#BAN\n"
            f"PENGGUNA : [{user.first_name}](tg://user?id={user.id})\n"
            f"OBROLAN : {bon.chat.title}(`{bon.chat_id}`)",
        )


@register(outgoing=True, disable_errors=True, pattern=r"^\.unban(?: |$)(.*)")
async def nothanos(unbon):
    """For .unban command, unbans the replied/tagged person"""
    # Here laying the sanity check
    chat = await unbon.get_chat()
    admin = chat.admin_rights
    creator = chat.creator

    # Well
    if not admin and not creator:
        return await unbon.edit(NO_ADMIN)

    # If everything goes well...
    await unbon.edit("`Menghapus blokir(unbanning)...`")

    user = await get_user_from_event(unbon)
    user = user[0]
    if user:
        pass
    else:
        return

    try:
        await unbon.client(EditBannedRequest(unbon.chat_id, user.id, UNBAN_RIGHTS))
        await unbon.edit("`Menghapus blokir(unbanning) berhasil.`")

        if BOTLOG:
            await unbon.client.send_message(
                BOTLOG_CHATID,
                "#UNBAN\n"
                f"PENGGUNA : [{user.first_name}](tg://user?id={user.id})\n"
                f"OBROLAN : {unbon.chat.title}(`{unbon.chat_id}`)",
            )
    except UserIdInvalidError:
        await unbon.edit("`Logika unban saya rusak!`")


@register(outgoing=True, pattern=r"^\.mute(?: |$)(.*)")
async def spider(spdr):
    """
    This function is basically muting peeps
    """
    # Check if the function running under SQL mode
    try:
        from userbot.modules.sql_helper.spam_mute_sql import mute
    except AttributeError:
        return await spdr.edit(NO_SQL)

    # Admin or creator check
    chat = await spdr.get_chat()
    admin = chat.admin_rights
    creator = chat.creator

    # If not admin and not creator, return
    if not admin and not creator:
        return await spdr.edit(NO_ADMIN)

    user, reason = await get_user_from_event(spdr)
    if user:
        pass
    else:
        return

    self_user = await spdr.client.get_me()

    if user.id == self_user.id:
        return await spdr.edit(
            "`Saya tidak bisa membisukan!`"
        )

    # If everything goes well, do announcing and mute
    await spdr.edit("`Dapatkan rekamannya!`")
    if mute(spdr.chat_id, user.id) is False:
        return await spdr.edit(f"**Kesalahan** : [{user.first_name}](tg://user?id={user.id}) mungkin sudah dibisukan.")
    else:
        try:
            await spdr.client(EditBannedRequest(spdr.chat_id, user.id, MUTE_RIGHTS))

            # Announce that the function is done
            if reason:
                await spdr.edit(f"`Direkam dengan aman!`\n**Alasan** : {reason}")
            else:
                await spdr.edit("`Direkam dengan aman!`")

            # Announce to logging group
            if BOTLOG:
                await spdr.client.send_message(
                    BOTLOG_CHATID,
                    "#MUTE\n"
                    f"PENGGUNA : [{user.first_name}](tg://user?id={user.id})\n"
                    f"OBROLAN : {spdr.chat.title}(`{spdr.chat_id}`)",
                )
        except UserIdInvalidError:
            return await spdr.edit("`Logika saya untuk membisukan rusak!`")
        except UserAdminInvalidError:
            pass


@register(outgoing=True, disable_errors=True, pattern=r"^\.unmute(?: |$)(.*)")
async def unmoot(unmot):
    """For .unmute command, unmute the replied/tagged person"""
    # Admin or creator check
    chat = await unmot.get_chat()
    admin = chat.admin_rights
    creator = chat.creator

    # If not admin and not creator, return
    if not admin and not creator:
        return await unmot.edit(NO_ADMIN)

    # Check if the function running under SQL mode
    try:
        from userbot.modules.sql_helper.spam_mute_sql import unmute
    except AttributeError:
        return await unmot.edit(NO_SQL)

    # If admin or creator, inform the user and start unmuting
    await unmot.edit("`Menyuarakan kembali...`")
    user = await get_user_from_event(unmot)
    user = user[0]
    if user:
        pass
    else:
        return

    if unmute(unmot.chat_id, user.id) is False:
        return await unmot.edit(f"**Kesalahan** : [{user.first_name}](tg://user?id={user.id}) mungkin sudah tidak dibisukan.")
    else:

        try:
            await unmot.client(EditBannedRequest(unmot.chat_id, user.id, UNBAN_RIGHTS))
            await unmot.edit("`Berhasil disuarakan`")
        except UserIdInvalidError:
            return await unmot.edit("`Logika saya untuk menyuarakan rusak!`")
        except UserAdminInvalidError:
            pass

        if BOTLOG:
            await unmot.client.send_message(
                BOTLOG_CHATID,
                "#UNMUTE\n"
                f"PENGGUNA : [{user.first_name}](tg://user?id={user.id})\n"
                f"OBROLAN : {unmot.chat.title}(`{unmot.chat_id}`)",
            )


@register(incoming=True, disable_errors=True)
async def muter(moot):
    """Used for deleting the messages of muted people"""
    try:
        from userbot.modules.sql_helper.gmute_sql import is_gmuted
        from userbot.modules.sql_helper.spam_mute_sql import is_muted
    except AttributeError:
        return
    muted = is_muted(moot.chat_id)
    gmuted = is_gmuted(moot.sender_id)
    rights = ChatBannedRights(
        until_date=None,
        send_messages=True,
        send_media=True,
        send_stickers=True,
        send_gifs=True,
        send_games=True,
        send_inline=True,
        embed_links=True,
    )
    if muted:
        for i in muted:
            if str(i.sender) == str(moot.sender_id):
                try:
                    await moot.delete()
                    await moot.client(
                        EditBannedRequest(moot.chat_id, moot.sender_id, rights)
                    )
                except (
                    BadRequestError,
                    UserAdminInvalidError,
                    ChatAdminRequiredError,
                    UserIdInvalidError,
                ):
                    await moot.client.send_read_acknowledge(moot.chat_id, moot.id)
    for i in gmuted:
        if i.sender == str(moot.sender_id):
            await moot.delete()


@register(outgoing=True, disable_errors=True, pattern=r"^\.ungmute(?: |$)(.*)")
async def ungmoot(un_gmute):
    """For .ungmute command, ungmutes the target in the userbot"""
    # Admin or creator check
    chat = await un_gmute.get_chat()
    admin = chat.admin_rights
    creator = chat.creator

    # If not admin and not creator, return
    if not admin and not creator:
        await un_gmute.edit(NO_ADMIN)
        return

    # Check if the function running under SQL mode
    try:
        from userbot.modules.sql_helper.gmute_sql import ungmute
    except AttributeError:
        await un_gmute.edit(NO_SQL)
        return

    user = await get_user_from_event(un_gmute)
    user = user[0]
    if not user:
        return

    # If pass, inform and start ungmuting
    await un_gmute.edit("`Menyuarakan kembali(ungmuting)...`")

    if ungmute(user.id) is False:
        await un_gmute.edit(f"**Kesalahan** : [{user.first_name}](tg://user?id={user.id}) mungkin sudah tidak dibisukan dari grup(ungmute)")
    else:
        # Inform about success
        await un_gmute.edit("`Berhasil disuarakan(ungmuted)`")
        await sleep(3)
        await un_gmute.delete()

        if BOTLOG:
            await un_gmute.client.send_message(
                BOTLOG_CHATID,
                "#UNGMUTE\n"
                f"PENGGUNA : [{user.first_name}](tg://user?id={user.id})\n"
                f"OBROLAN : {un_gmute.chat.title}(`{un_gmute.chat_id}`)",
            )


@register(outgoing=True, disable_errors=True, pattern=r"^\.gmute(?: |$)(.*)")
async def gspider(gspdr):
    """For .gmute command, globally mutes the replied/tagged person"""
    # Admin or creator check
    chat = await gspdr.get_chat()
    admin = chat.admin_rights
    creator = chat.creator

    # If not admin and not creator, return
    if not admin and not creator:
        await gspdr.edit(NO_ADMIN)
        return

    # Check if the function running under SQL mode
    try:
        from userbot.modules.sql_helper.gmute_sql import gmute
    except AttributeError:
        await gspdr.edit(NO_SQL)
        return

    user, reason = await get_user_from_event(gspdr)
    if not user:
        return

    # If pass, inform and start gmuting
    await gspdr.edit("`Shhh... Diam sekarang!`")
    if gmute(user.id) is False:
        await gspdr.edit(f"**Kesalahan** : [{user.first_name}](tg://user?id={user.id}) mungkin sudah dibisukan(gmute)")
    else:
        if reason:
            await gspdr.edit(f"`Direkam secara global!`\n**Alasan** : {reason}")
        else:
            await gspdr.edit("`Direkam secara global!`")

        if BOTLOG:
            await gspdr.client.send_message(
                BOTLOG_CHATID,
                "#GMUTE\n"
                f"PENGGUNA : [{user.first_name}](tg://user?id={user.id})\n"
                f"OBROLAN : {gspdr.chat.title}(`{gspdr.chat_id}`)",
            )


@register(outgoing=True, pattern=r"^\.all$")
async def tagaso(event):
    """For .all command, mention all of the member in the group chat"""
    if event.fwd_from:
        return
    await event.delete()
    mentions = "@all"
    chat = await event.get_input_chat()
    async for user in bot.iter_participants(chat, 500):
        mentions += f"[\u2063](tg://user?id={user.id})"
    await bot.send_message(chat, mentions, reply_to=event.message.reply_to_msg_id)


@register(outgoing=True, pattern=r"^\.zombies(?: |$)(.*)", groups_only=False)
async def rm_deletedacc(show):
    """For .zombies command, list all the ghost/deleted/zombie accounts in a chat."""

    con = show.pattern_match.group(1).lower()
    del_u = 0
    del_status = "`Tidak ada akun yang dihapus ditemukan, grup bersih`"

    if con != "clean":
        await show.edit("`Mencari akun hantu/dihapus/zombie...`")
        async for user in show.client.iter_participants(show.chat_id):

            if user.deleted:
                del_u += 1
                await sleep(1)
        if del_u > 0:
            del_status = (
                f"`Menemukan`  **{del_u}**  `akun hantu/dihapus/zombie di grup ini.`"
                "\n`Bersihkan dengan menggunakan .zombies clean`"
            )
        return await show.edit(del_status)

    # Here laying the sanity check
    chat = await show.get_chat()
    admin = chat.admin_rights
    creator = chat.creator

    # Well
    if not admin and not creator:
        return await show.edit("`Saya bukan admin disini!`")

    await show.edit("`Menghapus akun yang dihapus...\nApa saya bisa melakukan itu?`")
    del_u = 0
    del_a = 0

    async for user in show.client.iter_participants(show.chat_id):
        if user.deleted:
            try:
                await show.client(
                    EditBannedRequest(show.chat_id, user.id, BANNED_RIGHTS)
                )
            except ChatAdminRequiredError:
                return await show.edit("`Saya tidak punya hak melarang(ban) di grup ini`")
            except UserAdminInvalidError:
                del_u -= 1
                del_a += 1
            await show.client(EditBannedRequest(show.chat_id, user.id, UNBAN_RIGHTS))
            del_u += 1

    if del_u > 0:
        del_status = f"`Membersihkan`  **{del_u}**  `akun yang dihapus`"

    if del_a > 0:
        del_status = (
            f"`Membersihkan`  **{del_u}**  `akun yang dihapus` "
            f"\n**{del_a}**  `akun yang dihapus admin tidak dihapus`"
        )
    await show.edit(del_status)
    await sleep(2)
    await show.delete()

    if BOTLOG:
        await show.client.send_message(
            BOTLOG_CHATID,
            "#CLEANUP\n"
            f"Membersihkan **{del_u}** akun yang dihapus."
            f"\nOBROLAN : {show.chat.title}(`{show.chat_id}`)",
        )


@register(outgoing=True, disable_errors=True, pattern=r"^\.admins$")
async def get_admin(show):
    """For .admins command, list all of the admins of the chat."""
    info = await show.client.get_entity(show.chat_id)
    title = info.title if info.title else "this chat"
    mentions = f"<b>🔰 Admin di {title} 🔰</b>\n\n"
    try:
        async for user in show.client.iter_participants(
            show.chat_id, filter=ChannelParticipantsAdmins
        ):
            if not user.deleted:
                link = f'<a href="tg://user?id={user.id}">{user.first_name}</a>'
                mentions += f"\n{link}"
            else:
                mentions += f"\nAkun yg dihapus <code>{user.id}</code>"
    except ChatAdminRequiredError as err:
        mentions += " " + str(err) + "\n"
    await show.edit(mentions, parse_mode="html")


@register(outgoing=True, disable_errors=True, pattern=r"^\.pin(?: |$)(.*)")
async def pin(msg):
    """For .pin command, pins the replied/tagged message on the top the chat."""
    # Admin or creator check
    chat = await msg.get_chat()
    admin = chat.admin_rights
    creator = chat.creator

    # If not admin and not creator, return
    if not admin and not creator:
        return await msg.edit(NO_ADMIN)

    to_pin = msg.reply_to_msg_id

    if not to_pin:
        return await msg.edit("`Balas pesan untuk menyematkan!`")

    options = msg.pattern_match.group(1)

    is_silent = True

    if options.lower() == "loud":
        is_silent = False

    try:
        await msg.client(UpdatePinnedMessageRequest(msg.to_id, to_pin, is_silent))
    except BadRequestError:
        return await msg.edit(NO_PERM)

    await msg.edit("`Berhasil disematkan!`")

    user = await get_user_from_id(msg.sender_id, msg)

    if BOTLOG:
        await msg.client.send_message(
            BOTLOG_CHATID,
            "#PIN\n"
            f"ADMIN : [{user.first_name}](tg://user?id={user.id})\n"
            f"OBROLAN : {msg.chat.title}(`{msg.chat_id}`)\n"
            f"KERAS : {not is_silent}",
        )


@register(outgoing=True, disable_errors=True, pattern=r"^\.kick(?: |$)(.*)")
async def kick(usr):
    """For .kick command, kicks the replied/tagged person from the group."""
    # Admin or creator check
    chat = await usr.get_chat()
    admin = chat.admin_rights
    creator = chat.creator

    # If not admin and not creator, return
    if not admin and not creator:
        return await usr.edit(NO_ADMIN)

    user, reason = await get_user_from_event(usr)
    if not user:
        return await usr.edit("`Tidak dapat mengambil pengguna`")

    await usr.edit("`Mengeluarkan...`")

    try:
        await usr.client.kick_participant(usr.chat_id, user.id)
        await sleep(0.5)
    except Exception as e:
        return await usr.edit(NO_PERM + f"\n{str(e)}")

    if reason:
        await usr.edit(
            f"[{user.first_name}](tg://user?id={user.id}) dikeluarkan!\n**Alasan** : {reason}"
        )
    else:
        await usr.edit(f"[{user.first_name}](tg://user?id={user.id}) dikeluarkan!")

    if BOTLOG:
        await usr.client.send_message(
            BOTLOG_CHATID,
            "#KICK\n"
            f"PENGGUNA : [{user.first_name}](tg://user?id={user.id})\n"
            f"OBROLAN : {usr.chat.title}(`{usr.chat_id}`)\n",
        )


@register(outgoing=True, disable_errors=True, pattern=r"^\.users ?(.*)")
async def get_users(show):
    """For .users command, list all of the users in a chat."""
    info = await show.client.get_entity(show.chat_id)
    title = info.title if info.title else "this chat"
    mentions = "<b>👤 Anggota di {} 👤</b>\n\n".format(title)
    try:
        if not show.pattern_match.group(1):
            async for user in show.client.iter_participants(show.chat_id):
                if not user.deleted:
                    mentions += (
                        f"\n[{user.first_name}](tg://user?id={user.id}) `{user.id}`"
                    )
                else:
                    mentions += f"\nAkun yg dihapus `{user.id}`"
        else:
            searchq = show.pattern_match.group(1)
            async for user in show.client.iter_participants(
                show.chat_id, search=f"{searchq}"
            ):
                if not user.deleted:
                    mentions += (
                        f"\n[{user.first_name}](tg://user?id={user.id}) `{user.id}`"
                    )
                else:
                    mentions += f"\nAkun yg dihapus `{user.id}`"
    except ChatAdminRequiredError as err:
        mentions += " " + str(err) + "\n"
    try:
        await show.edit(mentions)
    except MessageTooLongError:
        await show.edit("`Ini grup yang sangat besar\nMengungggah daftar anggota sebagai file`")
        file = open("userslist.txt", "w+")
        file.write(mentions)
        file.close()
        await show.client.send_file(
            show.chat_id,
            "userslist.txt",
            caption="Anggota di {}".format(title),
            reply_to=show.id,
        )
        remove("userslist.txt")


async def get_user_from_event(event):
    """Get the user from argument or replied message."""
    args = event.pattern_match.group(1).split(" ", 1)
    extra = None
    if event.reply_to_msg_id and not len(args) == 2:
        previous_message = await event.get_reply_message()
        user_obj = await event.client.get_entity(previous_message.sender_id)
        extra = event.pattern_match.group(1)
    elif args:
        user = args[0]
        if len(args) == 2:
            extra = args[1]

        if user.isnumeric():
            user = int(user)

        if not user:
            return await event.edit("`Berikan nama pengguna, id atau balas pesan!`")

        if event.message.entities is not None:
            probable_user_mention_entity = event.message.entities[0]

            if isinstance(probable_user_mention_entity, MessageEntityMentionName):
                user_id = probable_user_mention_entity.user_id
                user_obj = await event.client.get_entity(user_id)
                return user_obj
        try:
            user_obj = await event.client.get_entity(user)
        except (TypeError, ValueError) as err:
            return await event.edit(str(err))

    return user_obj, extra


async def get_user_from_id(user, event):
    if isinstance(user, str):
        user = int(user)

    try:
        user_obj = await event.client.get_entity(user)
    except (TypeError, ValueError) as err:
        return await event.edit(str(err))

    return user_obj


@register(outgoing=True, disable_errors=True, pattern=r"^\.usersdel ?(.*)")
async def get_usersdel(show):
    """For .usersdel command, list all of the deleted users in a chat."""
    info = await show.client.get_entity(show.chat_id)
    title = info.title if info.title else "this chat"
    mentions = "<b>💀 Pengguna yg dihapus di {} 💀</b>\n\n".format(title)
    try:
        if not show.pattern_match.group(1):
            async for user in show.client.iter_participants(show.chat_id):
                if not user.deleted:
                    mentions += (
                        f"\n[{user.first_name}](tg://user?id={user.id}) `{user.id}`"
                    )
        #       else:
        #                mentions += f"\nDeleted Account `{user.id}`"
        else:
            searchq = show.pattern_match.group(1)
            async for user in show.client.iter_participants(
                show.chat_id, search=f"{searchq}"
            ):
                if not user.deleted:
                    mentions += (
                        f"\n[{user.first_name}](tg://user?id={user.id}) `{user.id}`"
                    )
        #       else:
    #              mentions += f"\nDeleted Account `{user.id}`"
    except ChatAdminRequiredError as err:
        mentions += " " + str(err) + "\n"
    try:
        await show.edit(mentions)
    except MessageTooLongError:
        await show.edit(
            "`Ini grup yang sangat besar\nMengunggah daftar pengguna yg dihapus sebagai file`"
        )
        file = open("userslist.txt", "w+")
        file.write(mentions)
        file.close()
        await show.client.send_file(
            show.chat_id,
            "deleteduserslist.txt",
            caption="Pengguna di {}".format(title),
            reply_to=show.id,
        )
        remove("deleteduserslist.txt")


async def get_userdel_from_event(event):
    """Get the deleted user from argument or replied message."""
    args = event.pattern_match.group(1).split(" ", 1)
    extra = None
    if event.reply_to_msg_id and not len(args) == 2:
        previous_message = await event.get_reply_message()
        user_obj = await event.client.get_entity(previous_message.sender_id)
        extra = event.pattern_match.group(1)
    elif args:
        user = args[0]
        if len(args) == 2:
            extra = args[1]

        if user.isnumeric():
            user = int(user)

        if not user:
            return await event.edit("`Berikan nama pengguna, id atau balas pesan pengguna yg dihapus!`")

        if event.message.entities is not None:
            probable_user_mention_entity = event.message.entities[0]

            if isinstance(probable_user_mention_entity, MessageEntityMentionName):
                user_id = probable_user_mention_entity.user_id
                user_obj = await event.client.get_entity(user_id)
                return user_obj
        try:
            user_obj = await event.client.get_entity(user)
        except (TypeError, ValueError) as err:
            return await event.edit(str(err))

    return user_obj, extra


async def get_userdel_from_id(user, event):
    if isinstance(user, str):
        user = int(user)

    try:
        user_obj = await event.client.get_entity(user)
    except (TypeError, ValueError) as err:
        return await event.edit(str(err))

    return user_obj


@register(outgoing=True, pattern=r"^\.bots$", groups_only=True)
async def get_bots(show):
    """For .bots command, list all of the bots of the chat."""
    info = await show.client.get_entity(show.chat_id)
    title = info.title if info.title else "this chat"
    mentions = f"<b>🤖 Bot di {title} 🤖</b>\n\n"
    try:
        if isinstance(show.to_id, PeerChat):
            return await show.edit("`Saya dengar bahwa hanya Super Grup yang dapat menggunakan bot.`")
        else:
            async for user in show.client.iter_participants(
                show.chat_id, filter=ChannelParticipantsBots
            ):
                if not user.deleted:
                    link = f'<a href="tg://user?id={user.id}">{user.first_name}</a>'
                    userid = f"<code>{user.id}</code>"
                    mentions += f"\n{link} {userid}"
                else:
                    mentions += f"\nBot dihapus <code>{user.id}</code>"
    except ChatAdminRequiredError as err:
        mentions += " " + str(err) + "\n"
    try:
        await show.edit(mentions, parse_mode="html")
    except MessageTooLongError:
        await show.edit("`Terlalu banyak bot disini.\nMengunggah daftar bot sebagai file.`")
        file = open("botlist.txt", "w+")
        file.write(mentions)
        file.close()
        await show.client.send_file(
            show.chat_id,
            "botlist.txt",
            caption="Bot di {}".format(title),
            reply_to=show.id,
        )
        remove("botlist.txt")


CMD_HELP.update(
    {
        "admin": "`.promote [nama penguna/balas] [hak khusus (opsional)]`"
        "\n➥  Memberikan hak admin kepada orang dalam obrolan."
        "\n\n`.demote [nama pengguna/balas]`"
        "\n➥  Mencabut izin admin orang tersebut dalam obrolan."
        "\n\n`.ban [nama pengguna/balas] [alasan (opsional)]`"
        "\n➥  Larang orang tersebut dari obrolan."
        "\n\n`.unban [nama pengguna/balas]`"
        "\n➥  Menghapus larangan orang tersebut dari obrolan."
        "\n\n`.mute [nama pengguna/balas] [alasan (opsional)]`"
        "\n➥  Membisukan orang dalam obrolan, berfungsi juga pada admin."
        "\n\n`.unmute [nama pengguna/balas]`"
        "\n➥  Menghapus orang tersebut dari daftar yang dibisukan."
        "\n\n`.gmute [nama pengguna/balas] [alasan (opsional)]`"
        "\n➥  Membisukan orang di semua grup yang memiliki kesamaan dengan Anda."
        "\n\n`.ungmute [nama pengguna/balas]`"
        "\n➥  Menghapus orang tersebut dari daftar grup yang dibisukan."
        "\n\n`.zombies`"
        "\n➥  Mencari akun yang dihapus dalam grup."
        "\n\n`.zombies clean`"
        "\n➥  Untuk menghapus/membersihkan akun yang dihapus dari grup."
        "\n\n`.all`"
        "\n➥  Tandai semua anggota di obrolan grup."
        "\n\n`.admins`"
        "\n➥  Mengambil daftar admin di grup."
        "\n\n`.bots`"
        "\n➥  Mengambil daftar bot di grup."
        "\n\n`.users` / `.users [nama anggota]`"
        "\n➥  Mengambil semua data (atau menanyakan) pengguna di obrolan."
        "\n\n`.setgpic [balas gambar]`"
        "\n➥  Mengubah gambar tampilan grup."
    }
)
