#!/usr/bin/env python3
# (c) https://t.me/TelethonChat/37677 and SpEcHiDe
#
# Licensed under the Raphielscape Public License, Version 1.d (the "License");
# you may not use this file except in compliance with the License.
#

from telethon.sync import TelegramClient
from telethon.sessions import StringSession

print("""Silahkan buka my.telegram.org
Masuk menggunakan akun Telegram Anda
Klik di API Development Tools
Buat aplikasi baru, dengan memasukkan detail yang diperlukan
Periksa bagian pesan tersimpan Telegram Anda untuk menyalin STRING_SESSION""")
API_KEY = input("API_KEY: ")
API_HASH = input("API_HASH: ")

with TelegramClient(StringSession(), API_KEY, API_HASH) as client:
    print("Periksa pesan tersimpan Telegram Anda untuk menyalin kode STRING_SESSION")
    session_string = client.session.save()
    saved_messages_template = """Support: @userbotindo
    
#USERBOT #STRING_SESSION :
	<code>{}</code>
	
⚠️ <i>Harap berhati-hati untuk memberikan kode ini kepada pihak ketiga</i>""".format(session_string)
    client.send_message("me", saved_messages_template, parse_mode="html")
