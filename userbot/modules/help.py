# Copyright (C) 2019 The Raphielscape Company LLC.
#
# Licensed under the Raphielscape Public License, Version 1.c (the "License");
# you may not use this file except in compliance with the License.
#
"""Userbot help command"""

from userbot import CMD_HELP
from userbot.events import register


@register(outgoing=True, pattern=r"^\.help(?: |$)(.*)")
async def help_handler(event):
    """For .help command."""
    args = event.pattern_match.group(1).lower()
    if args:
        if args in CMD_HELP:
            await event.edit(str(CMD_HELP[args]))
        else:
            await event.edit(f"**“{args}”**  bukan nama modul yang valid.")
    else:
        head = "Harap tentukan modul mana yang Anda inginkan untuk bantuan!"
        head2 = f"Modul yang dimuat : `{len(CMD_HELP)} modul`"
        head3 = "Gunakan : `.help [nama modul]`"
        head4 = "Daftar untuk semua perintah tersedia dibawah ini : "
        string = ""
        sep1 = "`---------------------------------------------------`"
        for i in sorted(CMD_HELP):
            string += "`" + str(i)
            string += "`  ❖  "
        await event.edit(
            f"{head}\
              \n{head2}\
              \n{head3}\
              \n{head4}\
              \n\n{sep1}\
              \n{string}\
              \n{sep1}"
        )
