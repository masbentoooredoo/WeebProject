# Copyright (C) 2019 The Raphielscape Company LLC.
#
# Licensed under the Raphielscape Public License, Version 1.c (the "License");
# you may not use this file except in compliance with the License.
#
""" Userbot module for executing code and terminal commands from Telegram. """

import asyncio
import re
from os import remove
from sys import executable

from userbot import BOTLOG, BOTLOG_CHATID, CMD_HELP, TERM_ALIAS
from userbot.events import register


@register(outgoing=True, pattern=r"^\.eval(?: |$|\n)(.*)")
async def evaluate(query):
    """ For .eval command, evaluates the given Python expression. """
    if query.is_channel and not query.is_group:
        return await query.edit("`Mengevaluasi tidak diizinkan di saluran.`")

    if query.pattern_match.group(1):
        expression = query.pattern_match.group(1)
    else:
        return await query.edit("`Berikan ekspresi untuk dievaluasi.`")

    for i in ("userbot.session", "env"):
        if expression.find(i) != -1:
            return await query.edit("`Itu tindakan yang berbahaya!\nTidak diperbolehkan!`")

    if not re.search(r"echo[ \-\w]*\$\w+", expression) is None:
        return await expression.edit("`Itu tindakan yang berbahaya!\nTidak diperbolehkan!`")

    try:
        evaluation = str(eval(expression))
        if evaluation:
            if isinstance(evaluation, str):
                if len(evaluation) >= 4096:
                    file = open("output.txt", "w+")
                    file.write(evaluation)
                    file.close()
                    await query.client.send_file(
                        query.chat_id,
                        "output.txt",
                        reply_to=query.id,
                        caption="`Output terlalu besar, dikirim sebagai file.`",
                    )
                    remove("output.txt")
                    return
                await query.edit(
                    "**Kueri** : \n`"
                    f"{expression}"
                    "`\n**Hasil** : \n`"
                    f"{evaluation}"
                    "`"
                )
        else:
            await query.edit(
                "**Kueri** : \n`"
                f"{expression}"
                "`\n**Hasil : **\n`Tidak ada hasil yang dikembalikan/salah.`"
            )
    except Exception as err:
        await query.edit(
            "**Kueri** : \n`" f"{expression}" "`\n**Pengecualian** : \n" f"`{err}`"
        )

    if BOTLOG:
        await query.client.send_message(
            BOTLOG_CHATID, f"`Permintaan evaluasi`  **{expression}**  `berhasil dijalankan.`"
        )


@register(outgoing=True, pattern=r"^\.exec(?: |$|\n)([\s\S]*)")
async def run(run_q):
    """ For .exec command, which executes the dynamically created program """
    code = run_q.pattern_match.group(1)

    if run_q.is_channel and not run_q.is_group:
        return await run_q.edit("`Eksekusi tidak diizinkan di saluran!`")

    if not code:
        return await run_q.edit(
            "`Setidaknya variabel diperlukan untuk "
            "dieksekusi.`\n`Gunakan “.help exec” sebagai contoh.`"
        )

    if code in ("userbot.session", "config.env"):
        return await run_q.edit("`Itu tindakan yang berbahaya!\nTidak diperbolehkan!`")

    if len(code.splitlines()) <= 5:
        codepre = code
    else:
        clines = code.splitlines()
        codepre = (
            clines[0] + "\n" + clines[1] + "\n" + clines[2] + "\n" + clines[3] + "..."
        )

    command = "".join(f"\n {l}" for l in code.split("\n.strip()"))
    process = await asyncio.create_subprocess_exec(
        executable,
        "-c",
        command.strip(),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()
    result = str(stdout.decode().strip()) + str(stderr.decode().strip())

    if result:
        if len(result) > 4096:
            file = open("output.txt", "w+")
            file.write(result)
            file.close()
            await run_q.client.send_file(
                run_q.chat_id,
                "output.txt",
                reply_to=run_q.id,
                caption="`Output terlalu besar, dikirim sebagai file`",
            )
            remove("output.txt")
            return
        await run_q.edit(
            "**Kueri** : \n`" f"{codepre}" "`\n**Hasil** : \n`" f"{result}" "`"
        )
    else:
        await run_q.edit(
            "**Kueri** : \n`" f"{codepre}" "`\n**Hasil** : \n`Tidak ada hasil yang dikembalikan/salah.`"
        )

    if BOTLOG:
        await run_q.client.send_message(
            BOTLOG_CHATID, "Kueri eksekusi " + codepre + " berhasil dieksekusi."
        )


@register(outgoing=True, pattern=r"^\.term(?: |$|\n)(.*)")
async def terminal_runner(term):
    """ For .term command, runs bash commands and scripts on your server. """
    curruser = TERM_ALIAS
    command = term.pattern_match.group(1)
    try:
        from os import geteuid

        uid = geteuid()
    except ImportError:
        uid = "Ini bukan kepala!"

    if term.is_channel and not term.is_group:
        return await term.edit("`Perintah istilah tidak diizinkan di saluran!`")

    if not command:
        return await term.edit(
            "`Berikan perintah atau gunakan` `“.help term”` `sebagai contoh.`"
        )

    for i in ("userbot.session", "env"):
        if command.find(i) != -1:
            return await term.edit("`Itu tindakan yang berbahaya!\nTidak diperbolehkan!`")

    if not re.search(r"echo[ \-\w]*\$\w+", command) is None:
        return await term.edit("`Itu tindakan yang berbahaya!\nTidak diperbolehkan!`")

    process = await asyncio.create_subprocess_shell(
        command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    result = str(stdout.decode().strip()) + str(stderr.decode().strip())

    if len(result) > 4096:
        output = open("output.txt", "w+")
        output.write(result)
        output.close()
        await term.client.send_file(
            term.chat_id,
            "output.txt",
            reply_to=term.id,
            caption="`Output terlalu besar, dikirm sebagai file.`",
        )
        remove("output.txt")
        return

    if uid == 0:
        await term.edit("`" f"{curruser}:~# {command}" f"\n{result}" "`")
    else:
        await term.edit("`" f"{curruser}:~$ {command}" f"\n{result}" "`")

    if BOTLOG:
        await term.client.send_message(
            BOTLOG_CHATID,
            "Perintah terminal " + command + " berhasil dieksekusi.",
        )


CMD_HELP.update(
    {
        "eval": "`.eval 2 + 3`" "\n➥  Evaluasi ekspresi mini.",
        "exec": "`.exec print(hello)`" "\n➥  Jalankan skrip python kecil.",
        "term": "`.term [cmd]`"
        "\n➥  Jalankan perintah dan skrip bash di server Anda.",
    }
)
