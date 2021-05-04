# Copyright (C) 2019 The Raphielscape Company LLC.
#
# Licensed under the Raphielscape Public License, Version 1.c (the "License");
# you may not use this file except in compliance with the License.
#
""" Userbot module for getting the date
    and time of any country or the userbot server.  """


import asyncio

from datetime import datetime as dt

from pytz import country_names as c_n
from pytz import country_timezones as c_tz
from pytz import timezone as tz

from userbot import CMD_HELP, COUNTRY, TZ_NUMBER
from userbot.events import register


async def get_tz(con):
    """Get time zone of the given country."""
    if "(Uk)" in con:
        con = con.replace("Uk", "UK")
    if "(Us)" in con:
        con = con.replace("Us", "US")
    if " Of " in con:
        con = con.replace(" Of ", " of ")
    if "(Western)" in con:
        con = con.replace("(Western)", "(western)")
    if "Minor Outlying Islands" in con:
        con = con.replace("Minor Outlying Islands", "minor outlying islands")
    if "Nl" in con:
        con = con.replace("Nl", "NL")

    for c_code in c_n:
        if con == c_n[c_code]:
            return c_tz[c_code]
    try:
        if c_n[con]:
            return c_tz[con]
    except KeyError:
        return


@register(outgoing=True, pattern=r"^\.time(?: |$)(.*)(?<![0-9])(?: |$)([0-9]+)?")
async def time_func(tdata):
    """For .time command, return the time of
    1. The country passed as an argument,
    2. The default userbot country(set it by using .settime),
    3. The server where the userbot runs.
    """
    con = tdata.pattern_match.group(1).title()
    tz_num = tdata.pattern_match.group(2)

    t_form = "%H:%M:%S"
    c_name = None

    if len(con) > 4:
        try:
            c_name = c_n[con]
        except KeyError:
            c_name = con
        timezones = await get_tz(con)
    elif COUNTRY:
        c_name = COUNTRY
        tz_num = TZ_NUMBER
        timezones = await get_tz(COUNTRY)
    else:
        return await tdata.edit(f"`Sekarang jam`  **{dt.now().strftime(t_form)}**")

    if not timezones:
        return await tdata.edit("`Negara tidak valid!`")

    if len(timezones) == 1:
        time_zone = timezones[0]
    elif len(timezones) > 1:
        if tz_num:
            tz_num = int(tz_num)
            time_zone = timezones[tz_num - 1]
        else:
            return_str = f"`{c_name} memiliki banyak zona waktu :`\n\n"

            for i, item in enumerate(timezones):
                return_str += f"`{i+1}. {item}`\n"

            return_str += "\n`Pilih salah satu dengan mengetik nomornya"
            return_str += "\ndalam perintah.`\n"
            return_str += f"`Contoh : .time {c_name} 2`"

            return await tdata.edit(return_str)

    dtnow = dt.now(tz(time_zone)).strftime(t_form)

    if c_name != COUNTRY:
        return await tdata.edit(
            f"`Sekarang jam`  **{dtnow}**  `zona waktu di {c_name}({time_zone}).`"
        )
    elif COUNTRY:
        return await tdata.edit(
            f"`Sekarang jam`  **{dtnow}**  `zona waktu di {COUNTRY}" f"({time_zone}).`"
        )
        await asyncio.sleep(60)
        await tdata.delete()


@register(outgoing=True, pattern=r"^\.date(?: |$)(.*)(?<![0-9])(?: |$)([0-9]+)?")
async def date_func(dat):
    """For .date command, return the date of
    1. The country passed as an argument,
    2. The default userbot country(set it by using .settime),
    3. The server where the userbot runs.
    """
    con = dat.pattern_match.group(1).title()
    tz_num = dat.pattern_match.group(2)

    d_form = "%d-%m-%y - %A"
    c_name = ""

    if len(con) > 4:
        try:
            c_name = c_n[con]
        except KeyError:
            c_name = con
        timezones = await get_tz(con)
    elif COUNTRY:
        c_name = COUNTRY
        tz_num = TZ_NUMBER
        timezones = await get_tz(COUNTRY)
    else:
        return await dat.edit(f"`Sekarang`  **{dt.now().strftime(d_form)}**.")

    if not timezones:
        return await dat.edit("`Negara tidak valid!`")

    if len(timezones) == 1:
        time_zone = timezones[0]
    elif len(timezones) > 1:
        if tz_num:
            tz_num = int(tz_num)
            time_zone = timezones[tz_num - 1]
        else:
            return_str = f"`{c_name} memiliki banyak zona waktu :`\n"

            for i, item in enumerate(timezones):
                return_str += f"`{i+1}. {item}`\n"

            return_str += "\n`Pilih salah satu dengan mengetik nomornya"
            return_str += "\ndalam perintah.`\n"
            return_str += f"`Contoh : .date {c_name} 2`"

            return await dat.edit(return_str)

    dtnow = dt.now(tz(time_zone)).strftime(d_form)

    if c_name != COUNTRY:
        return await dat.edit(
            f"`Sekarang`  **{dtnow}**  `zona waktu di {c_name}({time_zone}).`"
        )
    elif COUNTRY:
        return await dat.edit(
            f"`Sekarang`  **{dtnow}**  `zona waktu di {COUNTRY}" f"({time_zone}).`"
        )
        await asyncio.sleep(60)
        await dat.delete()


CMD_HELP.update(
    {
        "time": "`.time [kode/nama negara] [nomor zona waktu]`"
        "\n➥  Dapatkan waktu sebuah negara. Jika suatu negara memiliki "
        "beberapa zona waktu, itu akan mencantumkan semuanya dan silahkan Anda memilih salah satu.",
        "date": "`.date [kode/nama negara] [nomor zona waktu]`"
        "\n➥  Dapatkan tanggal sebuah negara. Jika suatu negara memiliki "
        "beberapa zona waktu, itu akan mencantumkan semuanya dan silahkan Anda memilih salah satu.",
    }
)
