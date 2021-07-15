# Copyright (C) 2020 Aidil Aryanto.
# All rights reserved.

import asyncio
import glob
import os
import shutil
import subprocess
import time

import deezloader
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from pylast import User
from telethon import events
from telethon.errors.rpcerrorlist import YouBlockedUserError
from telethon.tl.types import DocumentAttributeAudio, DocumentAttributeVideo

from userbot import (
    CMD_HELP,
    DEEZER_ARL_TOKEN,
    LASTFM_USERNAME,
    TEMP_DOWNLOAD_DIRECTORY,
    bot,
    lastfm,
)
from userbot.events import register
from userbot.utils import chrome, progress
from userbot.utils.FastTelethon import upload_file


async def getmusic(cat):
    video_link = ""
    search = cat
    driver = await chrome()
    driver.get("https://www.youtube.com/results?search_query=" + search)
    user_data = driver.find_elements_by_xpath('//*[@id="video-title"]')
    for i in user_data:
        video_link = i.get_attribute("href")
        break
    command = f"youtube-dl -x --add-metadata --embed-thumbnail --audio-format mp3 {video_link}"
    os.system(command)
    return video_link


async def getmusicvideo(cat):
    video_link = ""
    search = cat
    driver = await chrome()
    driver.get("https://www.youtube.com/results?search_query=" + search)
    user_data = driver.find_elements_by_xpath('//*[@id="video-title"]')
    for i in user_data:
        video_link = i.get_attribute("href")
        break
    command = 'youtube-dl -f "[filesize<50M]" --merge-output-format mp4 ' + video_link
    os.system(command)


@register(outgoing=True, pattern=r"^\.song (.*)")
async def _(event):
    reply_to_id = event.message.id
    if event.reply_to_msg_id:
        reply_to_id = event.reply_to_msg_id
    reply = await event.get_reply_message()
    if event.pattern_match.group(1):
        query = event.pattern_match.group(1)
        await event.edit("`Tunggu...! Saya menemukan lagu Anda...`")
    elif reply.message:
        query = reply.message
        await event.edit("`Tunggu...! Saya menemukan lagu Anda...`")
    else:
        await event.edit("`Apa yang harus saya temukan?`")
        return

    video_link = await getmusic(str(query))
    loa = glob.glob("*.mp3")[0]
    await event.edit("`Mengunggah lagu Anda...`")
    c_time = time.time()
    with open(loa, "rb") as f:
        result = await upload_file(
            client=event.client,
            file=f,
            name=loa,
            progress_callback=lambda d, t: asyncio.get_event_loop().create_task(
                progress(d, t, event, c_time, "[UNGGAH]", loa)
            ),
        )
    await event.client.send_file(
        event.chat_id,
        result,
        allow_cache=False,
        caption=f"[{query}]({video_link})",
        reply_to=reply_to_id,
    )
    await event.delete()
    os.system("rm -rf *.mp3")
    subprocess.check_output("rm -rf *.mp3", shell=True)


@register(outgoing=True, pattern=r"^\.vsong(?: |$)(.*)")
async def _(event):
    reply_to_id = event.message.id
    if event.reply_to_msg_id:
        reply_to_id = event.reply_to_msg_id
    reply = await event.get_reply_message()
    if event.pattern_match.group(1):
        query = event.pattern_match.group(1)
        await event.edit("`Tunggu...! Saya menemukan lagu video Anda...`")
    elif reply:
        query = str(reply.message)
        await event.edit("`Tunggu...! Saya menemukan lagu video Anda...`")
    else:
        await event.edit("`Apa yang harus saya temukan?`")
        return
    await getmusicvideo(query)
    l = glob.glob("*.mp4") + glob.glob("*.mkv") + glob.glob("*.webm")
    if l:
        await event.edit("`Saya menemukan sesuatu...`")
    else:
        await event.edit(f"`Maaf...! Saya tidak dapat menemukan apa pun untuk`  **{query}**")
        return
    try:
        loa = l[0]
        metadata = extractMetadata(createParser(loa))
        duration = 0
        width = 0
        height = 0
        if metadata.has("duration"):
            duration = metadata.get("duration").seconds
        if metadata.has("width"):
            width = metadata.get("width")
        if metadata.has("height"):
            height = metadata.get("height")
        os.system("cp *mp4 thumb.mp4")
        os.system("ffmpeg -i thumb.mp4 -vframes 1 -an -s 480x360 -ss 5 thumb.jpg")
        thumb_image = "thumb.jpg"
        c_time = time.time()
        with open(loa, "rb") as f:
            result = await upload_file(
                client=event.client,
                file=f,
                name=loa,
                progress_callback=lambda d, t: asyncio.get_event_loop().create_task(
                    progress(d, t, event, c_time, "[UNGGAH]", loa)
                ),
            )
        await event.client.send_file(
            event.chat_id,
            result,
            force_document=False,
            thumb=thumb_image,
            allow_cache=False,
            caption=query,
            supports_streaming=True,
            reply_to=reply_to_id,
            attributes=[
                DocumentAttributeVideo(
                    duration=duration,
                    w=width,
                    h=height,
                    round_message=False,
                    supports_streaming=True,
                )
            ],
        )
        await event.edit(f"**{query}**  `berhasil diunggah!`")
        os.remove(thumb_image)
        os.system("rm *.mkv *.mp4 *.webm")
    except BaseException:
        os.remove(thumb_image)
        os.system("rm *.mkv *.mp4 *.webm")
        return


@register(outgoing=True, pattern=r"^\.smd (?:(now)|(.*) - (.*))")
async def _(event):
    if event.fwd_from:
        return
    if event.pattern_match.group(1) == "now":
        playing = User(LASTFM_USERNAME, lastfm).get_now_playing()
        if playing is None:
            return await event.edit("`Kesalahan: Tidak ada data scrobbling yang ditemukan.`")
        artist = playing.get_artist()
        song = playing.get_title()
    else:
        artist = event.pattern_match.group(2)
        song = event.pattern_match.group(3)
    track = str(artist) + " - " + str(song)
    chat = "@SpotifyMusicDownloaderBot"
    try:
        await event.edit("`Mendapatkan musik Anda...`")
        async with bot.conversation(chat) as conv:
            await asyncio.sleep(2)
            await event.edit("`Mengunduh...`")
            try:
                response = conv.wait_event(
                    events.NewMessage(incoming=True, from_users=752979930)
                )
                msg = await bot.send_message(chat, track)
                respond = await response
                res = conv.wait_event(
                    events.NewMessage(incoming=True, from_users=752979930)
                )
                r = await res
                await bot.send_read_acknowledge(conv.chat_id)
            except YouBlockedUserError:
                await event.reply("`Buka blokir`  **@SpotifyMusicDownloaderBot**  `dan coba lagi!`")
                return
            await bot.forward_messages(event.chat_id, respond.message)
        await event.client.delete_messages(conv.chat_id, [msg.id, r.id, respond.id])
        await event.delete()
    except TimeoutError:
        return await event.edit(
            "`Kesalahan:`  **@SpotifyMusicDownloaderBot**  tidak menanggapi atau Lagu tidak ditemukan!`"
        )


@register(outgoing=True, pattern=r"^\.net (?:(now)|(.*) - (.*))")
async def _(event):
    if event.fwd_from:
        return
    if event.pattern_match.group(1) == "now":
        playing = User(LASTFM_USERNAME, lastfm).get_now_playing()
        if playing is None:
            return await event.edit("`Kesalahan: Tidak ditemukan scrobble saat ini.`")
        artist = playing.get_artist()
        song = playing.get_title()
    else:
        artist = event.pattern_match.group(2)
        song = event.pattern_match.group(3)
    track = str(artist) + " - " + str(song)
    chat = "@WooMaiBot"
    link = f"/netease {track}"
    await event.edit("`Mencari...`")
    try:
        async with bot.conversation(chat) as conv:
            await asyncio.sleep(2)
            await event.edit("`Memproses...\nTunggu sebentar...`")
            try:
                msg = await conv.send_message(link)
                response = await conv.get_response()
                respond = await conv.get_response()
                await bot.send_read_acknowledge(conv.chat_id)
            except YouBlockedUserError:
                await event.reply("`Harap buka blokir`  **@WooMaiBot**  `dan coba lagi!`")
                return
            await event.edit("`Mengirim musik Anda...`")
            await asyncio.sleep(3)
            await bot.send_file(event.chat_id, respond)
        await event.client.delete_messages(
            conv.chat_id, [msg.id, response.id, respond.id]
        )
        await event.delete()
    except TimeoutError:
        return await event.edit(
            "`Kesalahan:`  **@WooMaiBot**  `tidak menanggapi atau Lagu tidak ditemukan!`"
        )


@register(outgoing=True, pattern=r"^\.mhb(?: |$)(.*)")
async def _(event):
    if event.fwd_from:
        return
    d_link = event.pattern_match.group(1)
    if ".com" not in d_link:
        await event.edit("`Masukkan tautan yang valid untuk mengunduh.`")
    else:
        await event.edit("`Memproses...`")
    chat = "@MusicsHunterBot"
    try:
        async with bot.conversation(chat) as conv:
            try:
                msg_start = await conv.send_message("/start")
                response = await conv.get_response()
                msg = await conv.send_message(d_link)
                details = await conv.get_response()
                song = await conv.get_response()
                await bot.send_read_acknowledge(conv.chat_id)
            except YouBlockedUserError:
                await event.edit("`Buka blokir`  **@MusicsHunterBot**  `dan coba lagi!`")
                return
            await bot.send_file(event.chat_id, song, caption=details.text)
            await event.client.delete_messages(
                conv.chat_id, [msg_start.id, response.id, msg.id, details.id, song.id]
            )
            await event.delete()
    except TimeoutError:
        return await event.edit(
            "`Kesalahan:`  **@MusicsHunterBot**  `tidak menanggapi atau Lagu tidak ditemukan!`"
        )


@register(
    outgoing=True, pattern=r"^\.deez (now|.+)( FLAC| MP3\_320| MP3\_256| MP3\_128)?"
)
async def _(event):
    """DeezLoader by @An0nimia. Ported for UniBorg by @SpEcHlDe"""
    if event.fwd_from:
        return

    strings = {
        "name": "DeezLoad",
        "arl_token_cfg_doc": "Token ARL untuk Deezer",
        "invalid_arl_token": "silahkan atur variabel yang diperlukan untuk modul ini",
        "wrong_cmd_syntax": "bro, sekarang saya berpikir bagaimana kita harus pergi. Tolong hentikan Sesi saya.",
        "server_error": "Kami mengalami kesulitan teknis.",
        "processing": "`Mengunduh...`",
        "uploading": "`Mengunggah...`",
    }

    ARL_TOKEN = DEEZER_ARL_TOKEN

    if ARL_TOKEN is None:
        await event.edit(strings["invalid_arl_token"])
        return

    try:
        loader = deezloader.Login(ARL_TOKEN)
    except Exception as er:
        await event.edit(str(er))
        return

    temp_dl_path = os.path.join(TEMP_DOWNLOAD_DIRECTORY, str(time.time()))
    if not os.path.exists(temp_dl_path):
        os.makedirs(temp_dl_path)

    required_link = event.pattern_match.group(1)
    required_qty = event.pattern_match.group(2)
    required_qty = required_qty.strip() if required_qty else "MP3_320"

    await event.edit(strings["processing"])

    if "spotify" in required_link:
        if "track" in required_link:
            required_track = loader.download_trackspo(
                required_link,
                output=temp_dl_path,
                quality=required_qty,
                recursive_quality=True,
                recursive_download=True,
                not_interface=True,
            )
            await event.edit(strings["uploading"])
            await upload_track(required_track, event)
            shutil.rmtree(temp_dl_path)
            await event.delete()

        elif "album" in required_link:
            reqd_albums = loader.download_albumspo(
                required_link,
                output=temp_dl_path,
                quality=required_qty,
                recursive_quality=True,
                recursive_download=True,
                not_interface=True,
                zips=False,
            )
            await event.edit(strings["uploading"])
            for required_track in reqd_albums:
                await upload_track(required_track, event)
            shutil.rmtree(temp_dl_path)
            await event.delete()

    elif "deezer" in required_link:
        if "track" in required_link:
            required_track = loader.download_trackdee(
                required_link,
                output=temp_dl_path,
                quality=required_qty,
                recursive_quality=True,
                recursive_download=True,
                not_interface=True,
            )
            await event.edit(strings["uploading"])
            await upload_track(required_track, event)
            shutil.rmtree(temp_dl_path)
            await event.delete()

        elif "album" in required_link:
            reqd_albums = loader.download_albumdee(
                required_link,
                output=temp_dl_path,
                quality=required_qty,
                recursive_quality=True,
                recursive_download=True,
                not_interface=True,
                zips=False,
            )
            await event.edit(strings["uploading"])
            for required_track in reqd_albums:
                await upload_track(required_track, event)
            shutil.rmtree(temp_dl_path)
            await event.delete()

    elif "now" in required_link:
        playing = User(LASTFM_USERNAME, lastfm).get_now_playing()
        artist = str(playing.get_artist())
        song = str(playing.get_title())
        try:
            required_track = loader.download_name(
                artist=artist,
                song=song,
                output=temp_dl_path,
                quality=required_qty,
                recursive_quality=True,
                recursive_download=True,
                not_interface=True,
            )
        except BaseException as err:
            await event.edit(f"**Kesalahan :** {err}")
            await asyncio.sleep(5)
            return
        await event.edit(strings["uploading"])
        await upload_track(required_track, event)
        shutil.rmtree(temp_dl_path)
        await event.delete()

    else:
        await event.edit(strings["wrong_cmd_syntax"])


async def upload_track(track_location, message):
    metadata = extractMetadata(createParser(track_location))
    duration = 0
    title = ""
    performer = ""
    if metadata.has("duration"):
        duration = metadata.get("duration").seconds
    if metadata.has("title"):
        title = metadata.get("title")
    if metadata.has("artist"):
        performer = metadata.get("artist")
    document_attributes = [
        DocumentAttributeAudio(
            duration=duration,
            voice=False,
            title=title,
            performer=performer,
            waveform=None,
        )
    ]
    supports_streaming = True
    force_document = False
    caption_rts = os.path.basename(track_location)
    c_time = time.time()
    with open(track_location, "rb") as f:
        result = await upload_file(
            client=message.client,
            file=f,
            name=track_location,
            progress_callback=lambda d, t: asyncio.get_event_loop().create_task(
                progress(d, t, message, c_time, "[UNGGAH]", track_location)
            ),
        )
    await message.client.send_file(
        message.chat_id,
        result,
        caption=caption_rts,
        force_document=force_document,
        supports_streaming=supports_streaming,
        allow_cache=False,
        attributes=document_attributes,
    )
    os.remove(track_location)


CMD_HELP.update(
    {
        "getmusic": "`.song [artis - judul]`"
        "\n➥  Menemukan dan mengunggah lagu.\n\n"
        "`.vsong [artis - judul]`"
        "\n➥  Menemukan dan mengunggah klip video.\n\n"
        "`.smd [artis - judul]`"
        "\n➥  Unduh lagu dari spotify menggunakan  **@SpotifyMusicDownloaderBot**.\n\n"
        "`.smd now`"
        "\n➥  Unduh scrobble LastFM saat ini menggunakan  **@SpotifyMusicDownloaderBot**.\n\n"
        "`.net [artis - judul]`"
        "\n➥  Unduh lagu menggunakan  **@WooMaiBot**.\n\n"
        "`.net now`"
        "\n➥  Unduh scrobble LastFM saat ini menggunakan  **@WooMaiBot**.\n\n"
        "`.mhb [spotify/tautan deezer]`"
        "\n➥  Unduh lagu dari Spotify atau Deezer menggunakan  **@MusicsHunterBot**.\n\n"
        "`.deez [spotify/tautan deezer] FORMAT`"
        "\n➥  Unduh lagu dari Deezer atau Spotify.\n\n"
        "`.deez now FORMAT`"
        "\n➥  Unduh scrobble LastFM saat ini menggunakan deezloader."
        "\nFormat (opsional): `FLAC`, `MP3_320`, `MP3_256`, `MP3_128`."
    }
)
