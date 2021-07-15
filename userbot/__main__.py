# Copyright (C) 2019 The Raphielscape Company LLC.
#
# Licensed under the Raphielscape Public License, Version 1.c (the "License");
# you may not use this file except in compliance with the License.
#
""" Userbot start point """

from importlib import import_module

from telethon.errors.rpcerrorlist import PhoneNumberInvalidError

from userbot import LOGS, bot
from userbot.modules import ALL_MODULES

INVALID_PH = (
    "\nKESALAHAN: Nomor telepon yang dimasukkan TIDAK VALID"
    "\n Tip: Gunakan kode negara bersama dengan nomor"
    "\n atau periksa nomor telepon Anda dan coba lagi!"
)

try:
    bot.start()
except PhoneNumberInvalidError:
    print(INVALID_PH)
    exit(1)

for module_name in ALL_MODULES:
    imported_module = import_module("userbot.modules." + module_name)

LOGS.info("Anda menjalankan WeebProject Userbot")

bot.run_until_disconnected()
