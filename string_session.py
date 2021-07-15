#!/usr/bin/env python3
# (c) https://t.me/TelethonChat/37677 and SpEcHiDe
#
# Licensed under the Raphielscape Public License, Version 1.d (the "License");
# you may not use this file except in compliance with the License.
#

from telethon.sessions import StringSession
from telethon.sync import TelegramClient

print(
    """Silakan masuk ke my.telegram.org
Masuk menggunakan akun Telegram Anda
Klik pada Alat Pengembangan API
Buat aplikasi baru, dengan memasukkan detail yang diperlukan
Periksa bagian pesan tersimpan Telegram Anda untuk menyalin STRING_SESSION"""
)
API_KEY = int(input("Masukkan API_KEY di sini: "))
API_HASH = input("Masukkan API_HASH di sini: ")

with TelegramClient(StringSession(), API_KEY, API_HASH) as client:
    print("Periksa Pesan Tersimpan Telegram Anda untuk menyalin kode STRING_SESSION")
    session_string = client.session.save()
    saved_messages_template = """Support: @userbotindo

<code>STRING_SESSION</code>: <code>{}</code>

⚠️ <i>Harap berhati-hati untuk memberikan kode ini kepada pihak ketiga</i>""".format(
        session_string
    )
    client.send_message("me", saved_messages_template, parse_mode="html")
