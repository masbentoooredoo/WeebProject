# Copyright (C) 2019 The Raphielscape Company LLC.
#
# Licensed under the Raphielscape Public License, Version 1.c (the "License");
# you may not use this file except in compliance with the License.
#
""" Userbot module containing various scrapers. """

import json
import os
import re
import shutil
import time
from asyncio import get_event_loop, sleep
from glob import glob
from re import findall
from urllib.error import HTTPError
from urllib.parse import quote_plus

from bs4 import BeautifulSoup
from emoji import get_emoji_regexp
from googletrans import LANGUAGES, Translator
from gtts import gTTS
from gtts.lang import tts_langs
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from requests import get
from search_engine_parser import GoogleSearch
from telethon.tl.types import DocumentAttributeAudio, DocumentAttributeVideo
from urbandict import define
from wikipedia import summary
from wikipedia.exceptions import DisambiguationError, PageError
from youtube_dl import YoutubeDL
from youtube_dl.utils import (
    ContentTooShortError,
    DownloadError,
    ExtractorError,
    GeoRestrictedError,
    MaxDownloadsReached,
    PostProcessingError,
    UnavailableVideoError,
    XAttrMetadataError,
)
from youtube_search import YoutubeSearch

from userbot import BOTLOG, BOTLOG_CHATID, CMD_HELP, TEMP_DOWNLOAD_DIRECTORY
from userbot.events import register
from userbot.modules.upload_download import get_video_thumb
from userbot.utils import chrome, googleimagesdownload, progress
from userbot.utils.FastTelethon import upload_file

CARBONLANG = "auto"


@register(outgoing=True, pattern=r"^\.crblang (.*)")
async def setlang(prog):
    global CARBONLANG
    CARBONLANG = prog.pattern_match.group(1)
    await prog.edit(f"Bahasa untuk  **carbon.now.sh**  diatur ke {CARBONLANG}")


@register(outgoing=True, pattern=r"^\.carbon")
async def carbon_api(e):
    """ A Wrapper for carbon.now.sh """
    await e.edit("**Sedang memproses...**")
    CARBON = "https://carbon.now.sh/?l={lang}&code={code}"
    global CARBONLANG
    textx = await e.get_reply_message()
    pcode = e.text
    if pcode[8:]:
        pcode = str(pcode[8:])
    elif textx:
        pcode = str(textx.message)  # Importing message to module
    code = quote_plus(pcode)  # Converting to urlencoded
    await e.edit("**Memproses...\n25%**")
    file_path = TEMP_DOWNLOAD_DIRECTORY + "carbon.png"
    if os.path.isfile(file_path):
        os.remove(file_path)
    url = CARBON.format(code=code, lang=CARBONLANG)
    driver = await chrome()
    driver.get(url)
    await e.edit("**Memproses...\n50%**")
    driver.find_element_by_css_selector('[data-cy="quick-export-button"]').click()
    await e.edit("**Memproses...\n75%**")
    # Waiting for downloading
    while not os.path.isfile(file_path):
        await sleep(0.5)
    await e.edit("**Memproses...\n100%**")
    await e.edit("**Mengunggah...**")
    await e.client.send_file(
        e.chat_id,
        file_path,
        caption=(
            "Dibuat menggunakan [Carbon](https://carbon.now.sh/about/)"
            "\nsebuah proyek oleh [Dawn Labs](https://dawnlabs.io/)"
        ),
        force_document=True,
        reply_to=e.message.reply_to_msg_id,
    )

    os.remove(file_path)
    driver.quit()
    # Removing carbon.png after uploading
    await e.delete()  # Deleting msg


@register(outgoing=True, pattern=r"^\.img (.*)")
async def img_sampler(event):
    """ For .img command, search and return images matching the query. """
    await event.edit("`Sedang memproses...`")
    query = event.pattern_match.group(1)
    lim = findall(r"lim=\d+", query)
    try:
        lim = lim[0]
        lim = lim.replace("lim=", "")
        query = query.replace("lim=" + lim[0], "")
    except IndexError:
        lim = 7
    response = googleimagesdownload()

    # creating list of arguments
    arguments = {
        "keywords": query,
        "limit": lim,
        "format": "jpg",
        "no_directory": "no_directory",
    }

    # passing the arguments to the function
    paths = response.download(arguments)
    lst = paths[0][query]
    await event.client.send_file(
        await event.client.get_input_entity(event.chat_id), lst
    )
    shutil.rmtree(os.path.dirname(os.path.abspath(lst[0])))
    await event.delete()


@register(outgoing=True, pattern=r"^\.currency (.*)")
async def moni(event):
    input_str = event.pattern_match.group(1)
    input_sgra = input_str.split(" ")
    if len(input_sgra) == 3:
        try:
            number = float(input_sgra[0])
            currency_from = input_sgra[1].upper()
            currency_to = input_sgra[2].upper()
            request_url = f"https://api.ratesapi.io/api/latest?base={currency_from}"
            current_response = get(request_url).json()
            if currency_to in current_response["rates"]:
                current_rate = float(current_response["rates"][currency_to])
                rebmun = round(number * current_rate, 2)
                await event.edit(
                    "{} {} = {} {}".format(number, currency_from, rebmun, currency_to)
                )
            else:
                await event.edit(
                    "`Ini sepertinya mata uang asing, yang tidak dapat saya konversi sekarang.`"
                )
        except Exception as e:
            await event.edit(str(e))
    else:
        return await event.edit("`Sintaks tidak valid.`")


@register(outgoing=True, pattern=r"^\.google (.*)")
async def gsearch(q_event):
    """ For .google command, do a Google search. """
    match = q_event.pattern_match.group(1)
    page = findall(r"page=\d+", match)
    try:
        page = page[0]
        page = page.replace("page=", "")
        match = match.replace("page=" + page[0], "")
    except IndexError:
        page = 1
    try:
        search_args = (str(match), int(page))
        gsearch = GoogleSearch()
        gresults = await gsearch.async_search(*search_args)
        msg = ""
        for i in range(7):
            try:
                title = gresults["titles"][i]
                link = gresults["links"][i]
                desc = gresults["descriptions"][i]
                msg += f"[{title}]({link})\n`{desc}`\n\n"
            except IndexError:
                break
    except BaseException as g_e:
        return await q_event.edit(f"**Kesalahan :** `{g_e}`")
    await q_event.edit(
        "**Kueri Pencarian :**\n`" + match + "`\n\n**Hasil :**\n" + msg, link_preview=False
    )

    if BOTLOG:
        await q_event.client.send_message(
            BOTLOG_CHATID,
            "Permintaan pencarian Google `" + match + "` berhasil dilakukan.",
        )


@register(outgoing=True, pattern=r"^\.wiki (.*)")
async def wiki(wiki_q):
    """ For .wiki command, fetch content from Wikipedia. """
    match = wiki_q.pattern_match.group(1)
    try:
        summary(match)
    except DisambiguationError as error:
        return await wiki_q.edit(f"Ditemukan halaman yang tidak ambigu.\n\n{error}")
    except PageError as pageerror:
        return await wiki_q.edit(f"Halaman tidak ditemukan.\n\n{pageerror}")
    result = summary(match)
    if len(result) >= 4096:
        file = open("output.txt", "w+")
        file.write(result)
        file.close()
        await wiki_q.client.send_file(
            wiki_q.chat_id,
            "output.txt",
            reply_to=wiki_q.id,
            caption="`Output terlalu besar, dikirim sebagai file`",
        )
        if os.path.exists("output.txt"):
            return os.remove("output.txt")
    await wiki_q.edit("**Pencarian :**\n`" + match + "`\n\n**Hasil :**\n" + result)
    if BOTLOG:
        await wiki_q.client.send_message(
            BOTLOG_CHATID, f"Kueri pencarian Wiki `{match}` berhasil dilakukan."
        )


@register(outgoing=True, pattern=r"^\.ud (.*)")
async def urban_dict(ud_e):
    """ For .ud command, fetch content from Urban Dictionary. """
    await ud_e.edit("`Sedang memproses...`")
    query = ud_e.pattern_match.group(1)
    try:
        define(query)
    except HTTPError:
        return await ud_e.edit(f"Maaf, tidak dapat menemukan hasil apa pun untuk : **{query}**")
    mean = define(query)
    deflen = sum(len(i) for i in mean[0]["def"])
    exalen = sum(len(i) for i in mean[0]["example"])
    meanlen = deflen + exalen
    if int(meanlen) >= 0:
        if int(meanlen) >= 4096:
            await ud_e.edit("`Output terlalu besar, dikirim sebagai file.`")
            file = open("output.txt", "w+")
            file.write(
                "Teks : "
                + query
                + "\n\nArti : "
                + mean[0]["def"]
                + "\n\n"
                + "Contoh : \n"
                + mean[0]["example"]
            )
            file.close()
            await ud_e.client.send_file(
                ud_e.chat_id,
                "output.txt",
                caption="`Output terlalu besar, dikirim sebagai file.`",
            )
            if os.path.exists("output.txt"):
                os.remove("output.txt")
            return await ud_e.delete()
        await ud_e.edit(
            "Teks : **"
            + query
            + "**\n\nArti : **"
            + mean[0]["def"]
            + "**\n\n"
            + "Contoh : \n__"
            + mean[0]["example"]
            + "__"
        )
        if BOTLOG:
            await ud_e.client.send_message(
                BOTLOG_CHATID, "Kueri pencarian UD `" + query + "` berhasil dilakukan."
            )
    else:
        await ud_e.edit("Tidak ada hasil untuk **" + query + "**")


@register(outgoing=True, pattern=r"^\.tts(?: |$)([\s\S]*)")
async def text_to_speech(query):
    """ For .tts command, a wrapper for Google Text-to-Speech. """
    textx = await query.get_reply_message()
    message = query.pattern_match.group(1)
    if message:
        pass
    elif textx:
        message = textx.text
    else:
        return await query.edit(
            "`Berikan teks atau balas pesan untuk Text-to-Speech!`"
        )

    try:
        from userbot.modules.sql_helper.globals import gvarstatus
    except AttributeError:
        return await query.edit("`Berjalan di mode Non-SQL!`")

    if gvarstatus("tts_lang") is not None:
        target_lang = str(gvarstatus("tts_lang"))
    else:
        target_lang = "en"

    try:
        gTTS(message, lang=target_lang)
    except AssertionError:
        return await query.edit(
            "Teks kosong.\n"
            "Tidak ada yang tersisa untuk dibicarakan setelah pra-pemrosesan, tokenisasi, dan pembersihan."
        )
    except ValueError:
        return await query.edit("`Bahasa tidak didukung.`")
    except RuntimeError:
        return await query.edit("`Terjadi kesalahan saat memuat kamus bahasa.`")
    tts = gTTS(message, lang=target_lang)
    tts.save("k.mp3")
    with open("k.mp3", "rb") as audio:
        linelist = list(audio)
        linecount = len(linelist)
    if linecount == 1:
        tts = gTTS(message, lang=target_lang)
        tts.save("k.mp3")
    with open("k.mp3", "r"):
        await query.client.send_file(query.chat_id, "k.mp3", voice_note=True)
        os.remove("k.mp3")
        if BOTLOG:
            await query.client.send_message(
                BOTLOG_CHATID, "Text to Speech berhasil dilakukan."
            )
        await query.delete()


# kanged from Blank-x ;---;
@register(outgoing=True, pattern=r"^\.imdb (.*)")
async def imdb(e):
    try:
        movie_name = e.pattern_match.group(1)
        remove_space = movie_name.split(" ")
        final_name = "+".join(remove_space)
        page = get("https://www.imdb.com/find?ref_=nv_sr_fn&q=" + final_name + "&s=all")
        soup = BeautifulSoup(page.content, "lxml")
        odds = soup.findAll("tr", "odd")
        mov_title = odds[0].findNext("td").findNext("td").text
        mov_link = (
            "http://www.imdb.com/" + odds[0].findNext("td").findNext("td").a["href"]
        )
        page1 = get(mov_link)
        soup = BeautifulSoup(page1.content, "lxml")
        if soup.find("div", "poster"):
            poster = soup.find("div", "poster").img["src"]
        else:
            poster = ""
        if soup.find("div", "title_wrapper"):
            pg = soup.find("div", "title_wrapper").findNext("div").text
            mov_details = re.sub(r"\s+", " ", pg)
        else:
            mov_details = ""
        credits = soup.findAll("div", "credit_summary_item")
        if len(credits) == 1:
            director = credits[0].a.text
            writer = "Tidak diketahui"
            stars = "Tidak diketahui"
        elif len(credits) > 2:
            director = credits[0].a.text
            writer = credits[1].a.text
            actors = []
            for x in credits[2].findAll("a"):
                actors.append(x.text)
            actors.pop()
            stars = actors[0] + "," + actors[1] + "," + actors[2]
        else:
            director = credits[0].a.text
            writer = "Tidak diketahui"
            actors = []
            for x in credits[1].findAll("a"):
                actors.append(x.text)
            actors.pop()
            stars = actors[0] + "," + actors[1] + "," + actors[2]
        if soup.find("div", "inline canwrap"):
            story_line = soup.find("div", "inline canwrap").findAll("p")[0].text
        else:
            story_line = "Tidak tersedia"
        info = soup.findAll("div", "txt-block")
        if info:
            mov_country = []
            mov_language = []
            for node in info:
                a = node.findAll("a")
                for i in a:
                    if "country_of_origin" in i["href"]:
                        mov_country.append(i.text)
                    elif "primary_language" in i["href"]:
                        mov_language.append(i.text)
        if soup.findAll("div", "ratingValue"):
            for r in soup.findAll("div", "ratingValue"):
                mov_rating = r.strong["title"]
        else:
            mov_rating = "Tidak tersedia"
        await e.edit(
            "<a href=" + poster + ">&#8203;</a>"
            "<b>Judul : </b><code>"
            + mov_title
            + "</code>\n<code>"
            + mov_details
            + "</code>\n<b>Peringkat : </b><code>"
            + mov_rating
            + "</code>\n<b>Negara : </b><code>"
            + mov_country[0]
            + "</code>\n<b>Bahasa : </b><code>"
            + mov_language[0]
            + "</code>\n<b>Direktur : </b><code>"
            + director
            + "</code>\n<b>Penulis : </b><code>"
            + writer
            + "</code>\n<b>Bintang : </b><code>"
            + stars
            + "</code>\n<b>Url IMDB : </b>"
            + mov_link
            + "\n<b>Alur Cerita : </b>"
            + story_line,
            link_preview=True,
            parse_mode="HTML",
        )
    except IndexError:
        await e.edit("Plox masukkan **Nama film yang valid**")


@register(outgoing=True, pattern=r"^\.trt(?: |$)([\s\S]*)")
async def translateme(trans):
    """ For .trt command, translate the given text using Google Translate. """
    translator = Translator()
    textx = await trans.get_reply_message()
    message = trans.pattern_match.group(1)
    if message:
        pass
    elif textx:
        message = textx.text
    else:
        return await trans.edit("`Berikan teks atau balas pesan untuk diterjemahkan!`")

    try:
        from userbot.modules.sql_helper.globals import gvarstatus
    except AttributeError:
        return await trans.edit("`Berjalan di mode Non-SQL!`")

    if gvarstatus("trt_lang") is not None:
        target_lang = str(gvarstatus("trt_lang"))
    else:
        target_lang = "en"

    try:
        reply_text = translator.translate(deEmojify(message), dest=target_lang)
    except ValueError:
        return await trans.edit("Bahasa tujuan tidak valid.")

    source_lan = LANGUAGES[f"{reply_text.src.lower()}"]
    transl_lan = LANGUAGES[f"{reply_text.dest.lower()}"]
    reply_text = f"Dari  **{source_lan.title()}**\nKe  **{transl_lan.title()} :**\n\n{reply_text.text}"

    await trans.edit(reply_text)
    if BOTLOG:
        await trans.client.send_message(
            BOTLOG_CHATID,
            f"Menerjemahkan beberapa {source_lan.title()} hal ke {transl_lan.title()} sekarang.",
        )


@register(pattern=".lang (trt|tts) (.*)", outgoing=True)
async def lang(value):
    """ For .lang command, change the default langauge of userbot scrapers. """
    util = value.pattern_match.group(1).lower()

    try:
        from userbot.modules.sql_helper.globals import addgvar, delgvar, gvarstatus
    except AttributeError:
        return await lang.edit("`Berjalan di mode Non-SQL!`")

    if util == "trt":
        scraper = "Penerjemah"
        arg = value.pattern_match.group(2).lower()

        if arg not in LANGUAGES:
            return await value.edit(
                f"**Kode bahasa tidak valid!**\n**Kode bahasa yang tersedia untuk TRT :**\n\n`“{LANGUAGES}”  `"
            )

        if gvarstatus("trt_lang"):
            delgvar("trt_lang")
        addgvar("trt_lang", arg)
        LANG = LANGUAGES[arg]

    elif util == "tts":
        scraper = "Text to Speech"
        arg = value.pattern_match.group(2).lower()

        if arg not in tts_langs():
            return await value.edit(
                f"**Kode bahasa tidak valid!**\n**Kode bahasa yang tersedia untuk TTS :**\n\n`“{tts_langs()}”  `"
            )

        if gvarstatus("tts_lang"):
            delgvar("tts_lang")
        addgvar("tts_lang", arg)
        LANG = tts_langs()[arg]

    await value.edit(f"**Bahasa untuk {scraper} diubah menjadi {LANG.title()}.**")
    if BOTLOG:
        await value.client.send_message(
            BOTLOG_CHATID, f"Bahasa untuk  **{scraper}**  diubah menjadi {LANG.title()}."
        )


@register(outgoing=True, pattern=r"^\.yt (\d*) *(.*)")
async def yt_search(event):
    """For .yt command, do a YouTube search from Telegram."""

    if event.pattern_match.group(1) != "":
        counter = int(event.pattern_match.group(1))
        if counter > 10:
            counter = int(10)
        if counter <= 0:
            counter = int(1)
    else:
        counter = int(3)

    query = event.pattern_match.group(2)

    if not query:
        return await event.edit("`Masukkan kueri untuk dicari!`")
    await event.edit("`Sedang memproses...`")

    try:
        results = json.loads(YoutubeSearch(query, max_results=counter).to_json())
    except KeyError:
        return await event.edit(
            "`Pencarian YouTube menjadi lambat.\nTidak dapat menelusuri kueri ini!`"
        )

    output = f"**Kueri Pencarian :**\n`{query}`\n\n**Hasil :**\n"

    for i in results["videos"]:
        try:
            title = i["title"]
            link = "https://youtube.com" + i["url_suffix"]
            channel = i["channel"]
            duration = i["duration"]
            views = i["views"]
            output += f"[{title}]({link})\n**Saluran :** `{channel}`\n**Durasi :** {duration} | {views}\n\n"
        except IndexError:
            break

    await event.edit(output, link_preview=False)


@register(outgoing=True, pattern=r".rip(audio|video( \d{0,4})?) (.*)")
async def download_video(v_url):
    """ For .rip command, download media from YouTube and many other sites. """
    dl_type = v_url.pattern_match.group(1).lower()
    reso = v_url.pattern_match.group(2)
    reso = reso.strip() if reso else None
    url = v_url.pattern_match.group(3)

    await v_url.edit("`Bersiap untuk mengunduh...`")
    s_time = time.time()
    video = False
    audio = False

    if "audio" in dl_type:
        opts = {
            "format": "bestaudio",
            "addmetadata": True,
            "key": "FFmpegMetadata",
            "writethumbnail": True,
            "prefer_ffmpeg": True,
            "geo_bypass": True,
            "nocheckcertificate": True,
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "320",
                }
            ],
            "outtmpl": "%(id)s.%(ext)s",
            "quiet": True,
            "logtostderr": False,
        }
        audio = True

    elif "video" in dl_type:
        quality = (
            f"bestvideo[height<={reso}]+bestaudio/best[height<={reso}]"
            if reso
            else "bestvideo+bestaudio/best"
        )
        opts = {
            "format": quality,
            "addmetadata": True,
            "key": "FFmpegMetadata",
            "prefer_ffmpeg": True,
            "geo_bypass": True,
            "nocheckcertificate": True,
            "outtmpl": os.path.join(
                TEMP_DOWNLOAD_DIRECTORY, str(s_time), "%(title)s.%(ext)s"
            ),
            "logtostderr": False,
            "quiet": True,
        }
        video = True

    try:
        await v_url.edit("`Mengambil data.\nTunggu sebentar...`")
        with YoutubeDL(opts) as rip:
            rip_data = rip.extract_info(url)
    except DownloadError as DE:
        return await v_url.edit(f"`{str(DE)}`")
    except ContentTooShortError:
        return await v_url.edit("`Konten unduhan terlalu pendek.`")
    except GeoRestrictedError:
        return await v_url.edit(
            "`Video tidak tersedia dari lokasi geografis Anda "
            "karena batasan geografis yang diberlakukan oleh situs web.`"
        )
    except MaxDownloadsReached:
        return await v_url.edit("`Batas unduhan maksimal telah tercapai.`")
    except PostProcessingError:
        return await v_url.edit("`Ada kesalahan selama pemrosesan posting.`")
    except UnavailableVideoError:
        return await v_url.edit("`Media tidak tersedia dalam format yang diminta.`")
    except XAttrMetadataError as XAME:
        return await v_url.edit(f"`{XAME.code}: {XAME.msg}\n{XAME.reason}`")
    except ExtractorError:
        return await v_url.edit("`Terjadi kesalahan selama mengekstrak info.`")
    except Exception as e:
        return await v_url.edit(f"{str(type(e)): {str(e)}}")
    c_time = time.time()
    if audio:
        await v_url.edit(
            f"`Bersiap mengunggah lagu :`\n**{rip_data.get('title')}**"
            f"\noleh **{rip_data.get('uploader')}**"
        )
        f_name = rip_data.get("id") + ".mp3"
        with open(f_name, "rb") as f:
            result = await upload_file(
                client=v_url.client,
                file=f,
                name=f_name,
                progress_callback=lambda d, t: get_event_loop().create_task(
                    progress(
                        d, t, v_url, c_time, "Uploading...", f"{rip_data['title']}.mp3"
                    )
                ),
            )
        img_extensions = ["jpg", "jpeg", "webp"]
        img_filenames = [
            fn_img
            for fn_img in os.listdir()
            if any(fn_img.endswith(ext_img) for ext_img in img_extensions)
        ]
        thumb_image = img_filenames[0]
        metadata = extractMetadata(createParser(f_name))
        duration = 0
        if metadata.has("duration"):
            duration = metadata.get("duration").seconds
        await v_url.client.send_file(
            v_url.chat_id,
            result,
            supports_streaming=True,
            attributes=[
                DocumentAttributeAudio(
                    duration=duration,
                    title=rip_data.get("title"),
                    performer=rip_data.get("uploader"),
                )
            ],
            thumb=thumb_image,
        )
        os.remove(thumb_image)
        os.remove(f_name)
        await v_url.delete()
    elif video:
        await v_url.edit(
            f"`Bersiap mengunggah video :`\n**{rip_data.get('title')}**"
            f"\noleh **{rip_data.get('uploader')}**"
        )
        f_path = glob(os.path.join(TEMP_DOWNLOAD_DIRECTORY, str(s_time), "*"))[0]
        # Noob way to convert from .mkv to .mp4
        if f_path.endswith(".mkv"):
            base = os.path.splitext(f_path)[0]
            os.rename(f_path, base + ".mp4")
            f_path = glob(os.path.join(TEMP_DOWNLOAD_DIRECTORY, str(s_time), "*"))[0]
        f_name = os.path.basename(f_path)
        with open(f_path, "rb") as f:
            result = await upload_file(
                client=v_url.client,
                file=f,
                name=f_name,
                progress_callback=lambda d, t: get_event_loop().create_task(
                    progress(d, t, v_url, c_time, "Uploading...", f_name)
                ),
            )
        thumb_image = await get_video_thumb(f_path, "thumb.png")
        metadata = extractMetadata(createParser(f_path))
        duration = 0
        width = 0
        height = 0
        if metadata.has("duration"):
            duration = metadata.get("duration").seconds
        if metadata.has("width"):
            width = metadata.get("width")
        if metadata.has("height"):
            height = metadata.get("height")
        await v_url.client.send_file(
            v_url.chat_id,
            result,
            thumb=thumb_image,
            attributes=[
                DocumentAttributeVideo(
                    duration=duration,
                    w=width,
                    h=height,
                    supports_streaming=True,
                )
            ],
            caption=f"[{rip.data.get('title')}]({url})",
        )
        shutil.rmtree(os.path.join(TEMP_DOWNLOAD_DIRECTORY, str(s_time)))
        os.remove(thumb_image)
        await v_url.delete()


def deEmojify(inputString):
    """ Remove emojis and other non-safe characters from string """
    return get_emoji_regexp().sub("", inputString)


CMD_HELP.update(
    {
        "img": "`.img [kueri pencarian]`"
        "\n➥  Melakukan pencarian gambar di Google dan menampilkan 5 gambar.",
        "currency": "`.currency [jumlah] [dari] [untuk]`"
        "\n➥  Mengkonversi berbagai mata uang.",
        "carbon": "`.carbon [teks/balas pesan]`"
        "\n➥  Percantik kode Anda menggunakan  **carbon.now.sh**\n"
        "Gunakan perintah `.crblang [teks]` untuk mengatur kode bahasa Anda.",
        "google": "`.google [kueri]`" "\n➥  Melakukan pencarian di Google.",
        "wiki": "`.wiki [kueri]`" "\n➥  Melakukan pencarian di Wikipedia.",
        "ud": "`.ud [kueri]`" "\n➥  Melakukan pencarian di Kamus Urban.",
        "tts": "`.tts [teks/balas pesan]`"
        "\n➥  Menerjemahkan teks ucapan untuk bahasa yang diatur."
        "\nGunakan perintah `.lang tts [kode bahasa]` untuk mengatur bahasa untuk TTS. (Default-nya bahasa Inggris)",
        "trt": "`.trt [teks/balas pesan]`"
        "\n➥  Menerjemahkan teks ke bahasa yang diatur."
        "\nGunakan perintah `.lang trt [kode bahasa]` untuk mengatur bahasa untuk TRT. (Default-nya bahasa Inggris )",
        "yt": "`.yt [jumlah] [kueri]`"
        "\n➥  Melakukan pencarian YouTube."
        "\nJuga dapat menentukan jumlah hasil (default-nya 3 dan maksimal 10).",
        "imdb": "`.imdb [nama film]`" "\n➥  Menampilkan info film dan hal lainnya.",
        "rip": "`.ripaudio [url]`"
        "\n➥  Unduh video dari YouTube dan ubah menjadi audio "
        "\n`.ripvideo [kualitas] [url] (kualitas opsional)`"
        "\n**Contoh Kualitas :** `144` `240` `360` `480` `720` `1080` `2160`"
        "\n➥  Unduh video dari YouTube "
        "dan [banyak situs lainnya](https://ytdl-org.github.io/youtube-dl/supportedsites.html)",
    }
)
