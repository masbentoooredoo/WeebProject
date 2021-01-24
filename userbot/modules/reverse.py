# Copyright (C) 2019 The Raphielscape Company LLC.
#
# Thanks to @kandnub, for this awesome module !!
#
# Licensed under the Raphielscape Public License, Version 1.c (the "License");
# you may not use this file except in compliance with the License.
#
""" Userbot module for reverse searching stickers and images on Google """

import io
import os
import re
import urllib

import requests
from bs4 import BeautifulSoup
from PIL import Image

from userbot import CMD_HELP, bot
from userbot.events import register

opener = urllib.request.build_opener()
useragent = (
    "Mozilla/5.0 (Linux; Android 10; SM-G975F) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/80.0.3987.149 Mobile Safari/537.36"
)
opener.addheaders = [("User-agent", useragent)]


@register(outgoing=True, pattern=r"^\.reverse(?: |$)(\d*)")
async def okgoogle(img):
    """ For .reverse command, Google search images and stickers. """
    if os.path.isfile("okgoogle.png"):
        os.remove("okgoogle.png")

    message = await img.get_reply_message()

    if not message or not message.media:
        return await img.edit("`Balas foto atau stiker!`")

    photo = io.BytesIO()
    await bot.download_media(message, photo)
    if not photo:
        return await img.edit("`Tidak dapat mengunduh gambar.`")

    await img.edit("`Sedang memproses...`")

    try:
        image = Image.open(photo)
    except OSError:
        return await img.edit("`Kemungkinan besar yang berkaitan seksual tidak didukung.`")

    name = "okgoogle.png"
    image.save(name, "PNG")
    image.close()

    # https://stackoverflow.com/questions/23270175/google-reverse-image-search-using-post-request#28792943
    searchUrl = "https://www.google.com/searchbyimage/upload"
    multipart = {"encoded_image": (name, open(name, "rb")), "image_content": ""}
    response = requests.post(searchUrl, files=multipart, allow_redirects=False)
    fetchUrl = response.headers["Location"]

    if response == 400:
        return await img.edit("`Google menyuruhku pergi.`")

    await img.edit(
        "`Gambar berhasil diunggah ke Google, mungkin.`"
        "\n`Mengurai sumber sekarang, mungkin.`"
    )
    os.remove(name)
    match = await ParseSauce(fetchUrl + "&preferences?hl=en&fg=1#languages")
    guess = match["best_guess"]
    imgspage = match["similar_images"]

    if not guess and not imgspage:
        return await img.edit("`Tidak dapat menemukan apa pun!`")

    try:
        lim = int(img.pattern_match.group(1))
    except BaseException:
        lim = int(3)
    lim = int(10) if lim > 10 else lim
    lim = int(3) if lim < 0 else lim

    if lim == 0:
        return await img.edit(
            f"**Kecocokan terbaik :** `{guess}`"
            "\n\n[Gambar mirip secara visual]({fetchUrl})"
            "\n\n[Hasil untuk {guess}]({imgspage})"
        )

    await img.edit(
        f"**Kecocokan terbaik :** `{guess}`"
        "\n\n[Gambar mirip secara visual]({fetchUrl})"
        "\n\n[Hasil untuk {guess}]({imgspage})"
        "\n\n`Mengambil gambar...`"
    )

    images = await scam(match, lim)
    yeet = []

    for i in images:
        k = requests.get(i)
        yeet.append(k.content)

    try:
        await img.client.send_file(
            entity=img.chat_id,
            file=yeet,
            reply_to=img,
        )
    except BaseException:
        return await img.edit(
            f"**Kecocokan terbaik :** `{guess}`"
            "\n\n[Gambar mirip secara visual]({fetchUrl})"
            "\n\n[Hasil untuk {guess}]({imgspage})"
            "\n\n**Terjadi kesalahan saat mengunggah gambar!**"
        )

    await img.edit(
        f"**Kecocokan terbaik :** `{guess}`"
        "\n\n[Gambar mirip secara visual]({fetchUrl})"
        "\n\n[Hasil untuk {guess}]({imgspage})"
    )


async def ParseSauce(googleurl):
    """Parse/Scrape the HTML code for the info we want."""

    source = opener.open(googleurl).read()
    soup = BeautifulSoup(source, "html.parser")
    results = {"similar_images": "", "best_guess": ""}

    try:
        for similar_image in soup.findAll("input", {"class": "gLFyf"}):
            url = "https://www.google.com/search?tbm=isch&q=" + urllib.parse.quote_plus(
                similar_image.get("value")
            )
            results["similar_images"] = url
    except BaseException:
        pass

    for best_guess in soup.findAll("div", attrs={"class": "r5a77d"}):
        results["best_guess"] = best_guess.get_text()

    results["best_guess"] = results["best_guess"][12:]
    return results


async def scam(results, lim):
    single = opener.open(results["similar_images"]).read()
    decoded = single.decode("utf-8")

    pattern = r"^,\[\"(.*[.png|.jpg|.jpeg])\",[0-9]+,[0-9]+\]$"
    oboi = re.findall(pattern, decoded, re.I | re.M)

    imglinks = []
    counter = int(0)

    for imglink in oboi:
        if counter < lim:
            imglinks.append(imglink)
            counter += 1
        else:
            break

    return imglinks


CMD_HELP.update(
    {
        "reverse": "`.reverse [jumlah] <opsional>`"
        "\n➥  Balas gambar / stiker untuk melakukan pencarian terbalik di Gambar Google."
        "\nJumlah hasil pencarian dapat ditentukan, defaultnya 3."
        " Jika [jumlah] pencarian 0, hanya info dan tautan yang akan diberikan."
        "\n\n**CATATAN** : Bot mungkin akan gagal mengunggah gambar, jika meminta hasil gambar berkualitas tinggi."
    }
)
