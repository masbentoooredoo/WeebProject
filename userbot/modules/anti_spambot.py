# Copyright (C) 2019 The Raphielscape Company LLC.
#
# Licensed under the Raphielscape Public License, Version 1.c (the "License");
# you may not use this file except in compliance with the License.
#
""" A module for helping ban group join spammers. """

from asyncio import sleep

from requests import get
from telethon.events import ChatAction
from telethon.tl.types import ChannelParticipantsAdmins, Message

from userbot import (
    ANTI_SPAMBOT,
    ANTI_SPAMBOT_SHOUT,
    BOTLOG,
    BOTLOG_CHATID,
    CMD_HELP,
    bot,
)


@bot.on(ChatAction)
async def ANTI_SPAMBOTS(welcm):
    try:
        """Ban a recently joined user if it
        matches the spammer checking algorithm."""
        if not ANTI_SPAMBOT:
            return
        if welcm.user_joined or welcm.user_added:
            adder = None
            ignore = False
            users = None

            if welcm.user_added:
                ignore = False
                try:
                    adder = welcm.action_message.from_id
                except AttributeError:
                    return

            async for admin in bot.iter_participants(
                welcm.chat_id, filter=ChannelParticipantsAdmins
            ):
                if admin.id == adder:
                    ignore = True
                    break

            if ignore:
                return

            elif welcm.user_joined:
                users_list = hasattr(welcm.action_message.action, "users")
                if users_list:
                    users = welcm.action_message.action.users
                else:
                    users = [welcm.action_message.from_id]

            await sleep(5)
            spambot = False

            if not users:
                return

            for user_id in users:
                async for message in bot.iter_messages(
                    welcm.chat_id, from_user=user_id
                ):

                    correct_type = isinstance(message, Message)
                    if not message or not correct_type:
                        break

                    join_time = welcm.action_message.date
                    message_date = message.date

                    if message_date < join_time:
                        continue  # The message was sent before the user joined, thus ignore it

                    check_user = await welcm.client.get_entity(user_id)

                    # DEBUGGING. LEAVING IT HERE FOR SOME TIME ###
                    print(f"**Pengguna Telah Bergabung** : {check_user.first_name} [ID : {check_user.id}]")
                    print(f"**Obrolan** : {welcm.chat.title}")
                    print(f"**Waktu** : {join_time}")
                    print(f"**Pesan Terkirim** : {message.text}\n\n[Waktu : {message_date}]")
                    ##############################################

                    try:
                        cas_url = (
                            f"https://combot.org/api/cas/check?user_id={check_user.id}"
                        )
                        r = get(cas_url, timeout=3)
                        data = r.json()
                    except BaseException:
                        print(
                            "Pemeriksaan CAS gagal, kembali ke perilaku anti_spambot lama."
                        )
                        data = None

                    if data and data["ok"]:
                        reason = f"Dilarang oleh [Combot Anti Spam](https://combot.org/cas/query?u={check_user.id})"
                        spambot = True
                    elif "t.cn/" in message.text:
                        reason = "Cocok di `t.cn` URL"
                        spambot = True
                    elif "t.me/joinchat" in message.text:
                        reason = "Pesan Promosi Potensial"
                        spambot = True
                    elif message.fwd_from:
                        reason = "Pesan yang Diteruskan"
                        spambot = True
                    elif "?start=" in message.text:
                        reason = "Tautan `mulai` bot Telegram"
                        spambot = True
                    elif "bit.ly/" in message.text:
                        reason = "Cocok di `bit.ly` URL"
                        spambot = True
                    else:
                        if check_user.first_name in (
                            "Bitmex",
                            "Promotion",
                            "Information",
                            "Dex",
                            "Announcements",
                            "Info",
                        ):
                            if users.last_name == "Bot":
                                reason = "Spambot diketahui"
                                spambot = True

                    if spambot:
                        print(f"Potensi Pesan Spam : {message.text}")
                        await message.delete()
                        break

                    continue  # Check the next messsage

            if spambot:
                chat = await welcm.get_chat()
                admin = chat.admin_rights
                creator = chat.creator
                if not admin and not creator:
                    if ANTI_SPAMBOT_SHOUT:
                        await welcm.reply(
                            "@admins\n"
                            "#DETEKTOR ANTI SPAMBOT\n"
                            "PENGGUNA INI COCOK DENGAN ALGORITME SAYA SEBAGAI SPAMBOT!"
                            f"**Alasan** : {reason}"
                        )
                        kicked = False
                        reported = True
                else:
                    try:

                        await welcm.reply(
                            "**Potensi spambot terdeteksi!**\n"
                            f"**Alasan** : {reason}\n"
                            "Menendang pergi untuk saat ini, akan mencatat ID untuk tujuan selanjutnya.\n"
                            f"**Pengguna** : [{check_user.first_name}](tg://user?id={check_user.id})"
                        )

                        await welcm.client.kick_participant(
                            welcm.chat_id, check_user.id
                        )
                        kicked = True
                        reported = False

                    except BaseException:
                        if ANTI_SPAMBOT_SHOUT:
                            await welcm.reply(
                                "@admins\n"
                                "DETEKTOR ANTI SPAMBOT\n"
                                "PENGGUNA INI COCOK DENGAN ALGORITME SAYA SEBAGAI SPAMBOT!"
                                f"**Alasan** : {reason}"
                            )
                            kicked = False
                            reported = True

                if BOTLOG:
                    if kicked or reported:
                        await welcm.client.send_message(
                            BOTLOG_CHATID,
                            "#LAPORAN ANTI_SPAMBOT\n"
                            f"Pengguna : [{users.first_name}](tg://user?id={check_user.id})\n"
                            f"ID Pengguna : `{check_user.id}`\n"
                            f"Obrolan : {welcm.chat.title}\n"
                            f"ID Obrolan : `{welcm.chat_id}`\n"
                            f"Alasan : {reason}\n"
                            f"Pesan :\n\n{message.text}",
                        )
    except ValueError:
        pass


CMD_HELP.update(
    {
        "anti_spambot": "Jika diaktifkan di config.env atau env var, "
        "modul ini akan melarang(atau menginformasikan admin grup) terhadap spammer "
        "jika mereka cocok dengan algoritma anti-spam userbot."
    }
)
