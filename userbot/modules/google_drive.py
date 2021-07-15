# Copyright (C) 2020 Adek Maulana
#
# SPDX-License-Identifier: GPL-3.0-or-later
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


""" - ProjectBish Google Drive managers - """
import asyncio
import base64
import io
import json
import logging
import math
import os
import pickle
import re
import time
from mimetypes import guess_type
from os.path import getctime, isdir, isfile, join
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from telethon import events

import userbot.modules.sql_helper.google_drive_sql as helper
from userbot import (
    BOTLOG_CHATID,
    CMD_HELP,
    G_DRIVE_CLIENT_ID,
    G_DRIVE_CLIENT_SECRET,
    G_DRIVE_DATA,
    G_DRIVE_FOLDER_ID,
    G_DRIVE_INDEX_URL,
    LOGS,
    TEMP_DOWNLOAD_DIRECTORY,
)
from userbot.events import register
from userbot.modules.aria import aria2, check_metadata
from userbot.utils import human_to_bytes, humanbytes, progress, time_formatter
from userbot.utils.exceptions import CancelProcess

# =========================================================== #
#                          STATIC                             #
# =========================================================== #
GOOGLE_AUTH_URI = "https://accounts.google.com/o/oauth2/auth"
GOOGLE_TOKEN_URI = "https://oauth2.googleapis.com/token"
G_DRIVE_DIR_MIME_TYPE = "application/vnd.google-apps.folder"
SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/drive.metadata",
]
REDIRECT_URI = "urn:ietf:wg:oauth:2.0:oob"
# =========================================================== #
#      STATIC CASE FOR G_DRIVE_FOLDER_ID IF VALUE IS URL      #
# =========================================================== #
__ = G_DRIVE_FOLDER_ID
if __ is not None:
    if "uc?id=" in G_DRIVE_FOLDER_ID:
        LOGS.info("G_DRIVE_FOLDER_ID bukan URL folder yang valid...")
        G_DRIVE_FOLDER_ID = None
    try:
        G_DRIVE_FOLDER_ID = __.split("folders/")[1]
    except IndexError:
        try:
            G_DRIVE_FOLDER_ID = __.split("open?id=")[1]
        except IndexError:
            if "/view" in __:
                G_DRIVE_FOLDER_ID = __.split("/")[-2]
            else:
                try:
                    G_DRIVE_FOLDER_ID = __.split("folderview?id=")[1]
                except IndexError:
                    if "http://" not in __ or "https://" not in __:
                        if any(map(str.isdigit, __)):
                            _1 = True
                        else:
                            _1 = False
                        if "-" in __ or "_" in __:
                            _2 = True
                        else:
                            _2 = False
                        if True in [_1 or _2]:
                            pass
                        else:
                            LOGS.info("G_DRIVE_FOLDER_ID bukan ID yang valid...")
                            G_DRIVE_FOLDER_ID = None
                    else:
                        LOGS.info("G_DRIVE_FOLDER_ID bukan URL yang valid...")
                        G_DRIVE_FOLDER_ID = None
# =========================================================== #
#                           LOG                               #
# =========================================================== #
logger = logging.getLogger("googleapiclient.discovery")
logger.setLevel(logging.ERROR)
# =========================================================== #
#                                                             #
# =========================================================== #


@register(pattern=r"^\.gdauth(?: |$)", outgoing=True)
async def generate_credentials(gdrive):
    """- Only generate once for long run -"""
    if helper.get_credentials(str(gdrive.sender_id)) is not None:
        await gdrive.edit("`Anda sudah mengotorisasi token...`")
        await asyncio.sleep(1.5)
        await gdrive.delete()
        return False
    """ - Generate credentials - """
    if G_DRIVE_DATA is not None:
        try:
            configs = json.loads(G_DRIVE_DATA)
        except json.JSONDecodeError:
            await gdrive.edit(
                "`[KESALAHAN - OTENTIKASI]`\n\n"
                "`Status :` **BURUK**\n"
                "`Alasan :` **G_DRIVE_DATA**  entitas tidak valid!"
            )
            return False
    else:
        """- Only for old user -"""
        if G_DRIVE_CLIENT_ID is None and G_DRIVE_CLIENT_SECRET is None:
            await gdrive.edit(
                "`[KESALAHAN - OTENTIKASI]`\n\n"
                "`Status :` **BURUK**\n"
                "`Alasan :` tolong dapatkan  **G_DRIVE_DATA**  Anda "
                "[disini](https://telegra.ph/How-To-Setup-Google-Drive-04-03)"
            )
            return False
        configs = {
            "installed": {
                "client_id": G_DRIVE_CLIENT_ID,
                "client_secret": G_DRIVE_CLIENT_SECRET,
                "auth_uri": GOOGLE_AUTH_URI,
                "token_uri": GOOGLE_TOKEN_URI,
            }
        }
    await gdrive.edit("`Membuat kredensial...`")
    flow = InstalledAppFlow.from_client_config(
        configs, SCOPES, redirect_uri=REDIRECT_URI
    )
    auth_url, _ = flow.authorization_url(access_type="offline", prompt="consent")
    msg = await gdrive.respond("`Buka grup BOTLOG Anda untuk mengotentikasi token!`")
    async with gdrive.client.conversation(BOTLOG_CHATID) as conv:
        url_msg = await conv.send_message(
            "Silahkan buka URL ini :\n\n" f"{auth_url}\n\n otorisasi lalu balas kodenya."
        )
        r = conv.wait_event(events.NewMessage(outgoing=True, chats=BOTLOG_CHATID))
        r = await r
        code = r.message.message.strip()
        flow.fetch_token(code=code)
        creds = flow.credentials
        await asyncio.sleep(3.5)
        await gdrive.client.delete_messages(gdrive.chat_id, msg.id)
        await gdrive.client.delete_messages(BOTLOG_CHATID, [url_msg.id, r.id])
        """ - Unpack credential objects into strings - """
        creds = base64.b64encode(pickle.dumps(creds)).decode()
        await gdrive.edit("`Kredensial dibuat...`")
    helper.save_credentials(str(gdrive.sender_id), creds)
    await gdrive.delete()
    return


async def create_app(gdrive):
    """- Create google drive service app -"""
    creds = helper.get_credentials(str(gdrive.sender_id))
    if creds is not None:
        """- Repack credential objects from strings -"""
        creds = pickle.loads(base64.b64decode(creds.encode()))
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            await gdrive.edit("`Menyegarkan kredensial...`")
            """ - Refresh credentials - """
            creds.refresh(Request())
            helper.save_credentials(
                str(gdrive.sender_id), base64.b64encode(pickle.dumps(creds)).decode()
            )
        else:
            await gdrive.edit("`Kredensial kosong, silahkan buat...`")
            return False
    service = build("drive", "v3", credentials=creds, cache_discovery=False)
    return service


@register(pattern=r"^\.gdreset(?: |$)", outgoing=True)
async def reset_credentials(gdrive):
    """- Reset credentials or change account -"""
    await gdrive.edit("`Mengatur ulang informasi...`")
    helper.clear_credentials(str(gdrive.sender_id))
    await gdrive.edit("`Selesai...`")
    await asyncio.sleep(1)
    await gdrive.delete()
    return


async def get_raw_name(file_path):
    """- Get file_name from file_path -"""
    return file_path.split("/")[-1]


async def get_mimeType(name):
    """- Check mimeType given file -"""
    mimeType = guess_type(name)[0]
    if not mimeType:
        mimeType = "text/plain"
    return mimeType


async def download(gdrive, service, uri=None):
    global is_cancelled
    reply = ""
    """ - Download files to local then upload - """
    if not isdir(TEMP_DOWNLOAD_DIRECTORY):
        os.makedirs(TEMP_DOWNLOAD_DIRECTORY)
        required_file_name = None
    if uri:
        full_path = os.getcwd() + TEMP_DOWNLOAD_DIRECTORY.strip(".")
        if isfile(uri) and uri.endswith(".torrent"):
            downloads = aria2.add_torrent(
                uri, uris=None, options={"dir": full_path}, position=None
            )
        else:
            uri = [uri]
            downloads = aria2.add_uris(uri, options={"dir": full_path}, position=None)
        gid = downloads.gid
        await check_progress_for_dl(gdrive, gid, previous=None)
        file = aria2.get_download(gid)
        filename = file.name
        if file.followed_by_ids:
            new_gid = await check_metadata(gid)
            await check_progress_for_dl(gdrive, new_gid, previous=None)
        try:
            required_file_name = TEMP_DOWNLOAD_DIRECTORY + filenames
        except Exception:
            required_file_name = TEMP_DOWNLOAD_DIRECTORY + filename
    else:
        try:
            current_time = time.time()
            is_cancelled = False
            downloaded_file_name = await gdrive.client.download_media(
                await gdrive.get_reply_message(),
                TEMP_DOWNLOAD_DIRECTORY,
                progress_callback=lambda d, t: asyncio.get_event_loop().create_task(
                    progress(
                        d,
                        t,
                        gdrive,
                        current_time,
                        "[FILE - UNDUH]",
                        is_cancelled=is_cancelled,
                    )
                ),
            )
        except CancelProcess:
            names = []
            for name in os.listdir(TEMP_DOWNLOAD_DIRECTORY):
                names.append(join(TEMP_DOWNLOAD_DIRECTORY, name))
            """ asumming newest files are the cancelled one """
            newest = max(names, key=getctime)
            os.remove(newest)
            reply += (
                "`[FILE - DIBATALKAN]`\n\n"
                "`Status` : **OK** - sinyal yang diterima dibatalkan."
            )
            return reply
        else:
            required_file_name = downloaded_file_name
    try:
        file_name = await get_raw_name(required_file_name)
    except AttributeError:
        reply += "`[KESALAHAN - MASUK]`\n\n" "`Status` : **BURUK**\n"
        return reply
    mimeType = await get_mimeType(required_file_name)
    try:
        if isfile(required_file_name):
            try:
                result = await upload(
                    gdrive, service, required_file_name, file_name, mimeType
                )
            except CancelProcess:
                reply += (
                    "`[FILE - DIBATALKAN]`\n\n"
                    "`Status` : **OK** - sinyal yang diterima dibatalkan."
                )
                return reply
            else:
                reply += f"**GDrive Unggah**\n\n📄 [{file_name}]({result[1]})"
                if G_DRIVE_INDEX_URL:
                    index_url = G_DRIVE_INDEX_URL.rstrip("/") + "/" + quote(file_name)
                    reply += f"\n👥 [Index URL]({index_url})"
                reply += f"\n__Ukuran : {humanbytes(result[0])}__"
                return reply
        else:
            global parent_Id
            folder = await create_dir(service, file_name)
            parent_Id = folder.get("id")
            webViewURL = "https://drive.google.com/drive/folders/" + parent_Id
            try:
                await task_directory(gdrive, service, required_file_name)
            except CancelProcess:
                reply += (
                    "`[FOLDER - DIBATALKAN]`\n\n"
                    "`Status` : **OK** - sinyal yang diterima dibatalkan."
                )
                await reset_parentId()
                return reply
            except Exception:
                await reset_parentId()
            else:
                folder_size = await count_dir_size(service, parent_Id)
                reply += f"**GDrive Unggah**\n\n📁 [{file_name}]({webViewURL})"
                if G_DRIVE_INDEX_URL:
                    index_url = (
                        G_DRIVE_INDEX_URL.rstrip("/") + "/" + quote(file_name) + "/"
                    )
                    reply += f"\n👥 [Index URL]({index_url})"
                reply += f"\n__Ukuran : {humanbytes(folder_size)}__"
                await reset_parentId()
                return reply
    except Exception as e:
        reply += f"`[KESALAHAN]`\n\n" "`Status :` **Gagal**\n" f"`Alasan :` `{str(e)}`\n\n"
        return reply
    return


async def download_gdrive(gdrive, service, uri):
    reply = ""
    global is_cancelled
    """ - remove drivesdk and export=download from link - """
    if not isdir(TEMP_DOWNLOAD_DIRECTORY):
        os.mkdir(TEMP_DOWNLOAD_DIRECTORY)
    if "&export=download" in uri:
        uri = uri.split("&export=download")[0]
    elif "file/d/" in uri and "/view" in uri:
        uri = uri.split("?usp=drivesdk")[0]
    try:
        file_Id = uri.split("uc?id=")[1]
    except IndexError:
        try:
            file_Id = uri.split("open?id=")[1]
        except IndexError:
            if "/view" in uri:
                file_Id = uri.split("/")[-2]
            else:
                try:
                    file_Id = uri.split("uc?export=download&confirm=")[1].split("id=")[
                        1
                    ]
                except IndexError:
                    """- if error parse in url, assume given value is Id -"""
                    file_Id = uri
    try:
        file = await get_information(service, file_Id)
        await gdrive.edit("`Mengunduh dari GD...`")
    except HttpError as e:
        if "404" in str(e):
            drive = "https://drive.google.com"
            url = f"{drive}/uc?export=download&id={file_Id}"

            session = requests.session()
            download = session.get(url, stream=True)

            try:
                download.headers["Content-Disposition"]
            except KeyError:
                page = BeautifulSoup(download.content, "lxml")
                try:
                    export = drive + page.find("a", {"id": "uc-download-link"}).get(
                        "href"
                    )
                except AttributeError:
                    try:
                        error = (
                            page.find("p", {"class": "uc-error-caption"}).text
                            + "\n"
                            + page.find("p", {"class": "uc-error-subcaption"}).text
                        )
                    except Exception:
                        reply += (
                            "`[FILE - KESALAHAN]`\n\n"
                            "`Status :` **BURUK** - gagal mengunduh.\n"
                            "`Alasan :` kesalahan tidak tertangkap."
                        )
                    else:
                        reply += (
                            "`[FILE - KESALAHAN]`\n\n"
                            "`Status :` **BURUK** - gagal mengunduh.\n"
                            f"`Alasan :` {error}"
                        )
                    return reply
                download = session.get(export, stream=True)
                file_size = human_to_bytes(
                    page.find("span", {"class": "uc-name-size"})
                    .text.split()[-1]
                    .strip("()")
                )
            else:
                file_size = int(download.headers["Content-Length"])

            file_name = re.search(
                'filename="(.*)"', download.headers["Content-Disposition"]
            ).group(1)
            file_path = TEMP_DOWNLOAD_DIRECTORY + file_name
            with io.FileIO(file_path, "wb") as files:
                CHUNK_SIZE = None
                current_time = time.time()
                display_message = None
                first = True
                is_cancelled = False
                for chunk in download.iter_content(CHUNK_SIZE):
                    if is_cancelled is True:
                        raise CancelProcess

                    if not chunk:
                        break

                    diff = time.time() - current_time
                    if first is True:
                        downloaded = len(chunk)
                        first = False
                    else:
                        downloaded += len(chunk)
                    percentage = downloaded / file_size * 100
                    speed = round(downloaded / diff, 2)
                    eta = round((file_size - downloaded) / speed)
                    prog_str = "**Mengunduh** | [{}{}] `{}%`".format(
                        "".join(["■" for i in range(math.floor(percentage / 10))]),
                        "".join(["▨" for i in range(10 - math.floor(percentage / 10))]),
                        round(percentage, 2),
                    )
                    current_message = (
                        "`[FILE - UNDUH]`\n\n"
                        f"`{file_name}`\n"
                        f"`Status`\n{prog_str}\n"
                        f"`{humanbytes(downloaded)} dari {humanbytes(file_size)}"
                        f" @ {humanbytes(speed)}`\n"
                        f"`Perkiraan` -> {time_formatter(eta)}"
                    )
                    if (
                        round(diff % 15.00) == 0
                        and (display_message != current_message)
                        or (downloaded == file_size)
                    ):
                        await gdrive.edit(current_message)
                        display_message = current_message
                    files.write(chunk)
    else:
        file_name = file.get("name")
        mimeType = file.get("mimeType")
        if mimeType == "application/vnd.google-apps.folder":
            await gdrive.edit("`Dibatalkan, folder unduhan tidak mendukung...`")
            return False
        file_path = TEMP_DOWNLOAD_DIRECTORY + file_name
        request = service.files().get_media(fileId=file_Id, supportsAllDrives=True)
        with io.FileIO(file_path, "wb") as df:
            downloader = MediaIoBaseDownload(df, request)
            complete = False
            is_cancelled = False
            current_time = time.time()
            display_message = None
            while complete is False:
                if is_cancelled is True:
                    raise CancelProcess

                status, complete = downloader.next_chunk()
                if status:
                    file_size = status.total_size
                    diff = time.time() - current_time
                    downloaded = status.resumable_progress
                    percentage = downloaded / file_size * 100
                    speed = round(downloaded / diff, 2)
                    eta = round((file_size - downloaded) / speed)
                    prog_str = "**Mengunduh** | [{}{}] `{}%`".format(
                        "".join(["■" for i in range(math.floor(percentage / 10))]),
                        "".join(["▨" for i in range(10 - math.floor(percentage / 10))]),
                        round(percentage, 2),
                    )
                    current_message = (
                        "`[FILE - UNDUH]`\n\n"
                        f"`{file_name}`\n"
                        f"`Status`\n{prog_str}\n"
                        f"`{humanbytes(downloaded)} dari {humanbytes(file_size)}"
                        f" @ {humanbytes(speed)}`\n"
                        f"`Perkiraan` -> {time_formatter(eta)}"
                    )
                    if (
                        round(diff % 15.00) == 0
                        and (display_message != current_message)
                        or (downloaded == file_size)
                    ):
                        await gdrive.edit(current_message)
                        display_message = current_message
    await gdrive.edit(
        "`[FILE - UNDUH]`\n\n"
        f"`Nama   :` `{file_name}`\n"
        f"`Ukuran :` `{humanbytes(file_size)}`\n"
        f"`Jalur  :` `{file_path}`\n"
        "`Status :` **OK** - Berhasil diunduh."
    )
    msg = await gdrive.respond("`Jawab pertanyaan di grup BOTLOD Anda`")
    async with gdrive.client.conversation(BOTLOG_CHATID) as conv:
        ask = await conv.send_message("`Lanjutkan proses? [Y/N]`")
        try:
            r = conv.wait_event(events.NewMessage(outgoing=True, chats=BOTLOG_CHATID))
            r = await r
        except Exception:
            ans = "N"
        else:
            ans = r.message.message.strip()
            await gdrive.client.delete_messages(BOTLOG_CHATID, r.id)
        await gdrive.client.delete_messages(gdrive.chat_id, msg.id)
        await gdrive.client.delete_messages(BOTLOG_CHATID, ask.id)
    if ans.capitalize() == "N":
        return reply
    elif ans.capitalize() == "Y":
        try:
            result = await upload(gdrive, service, file_path, file_name, mimeType)
        except CancelProcess:
            reply += (
                "`[FILE - DIBATALKAN]`\n\n"
                "`Status :` **OK** - sinyal yang diterima dibatalkan."
            )
        else:
            reply += (
                "`[FILE - UNGGAH]`\n\n"
                f"`Nama   :` `{file_name}`\n"
                f"`Ukuran :` `{humanbytes(result[0])}`\n"
                f"`Tautan :` [{file_name}]({result[1]})\n"
                "`Status :` **OK**\n\n"
            )
        return reply
    else:
        await gdrive.client.send_message(
            BOTLOG_CHATID, "`Jawaban tidak valid, hanya [Y/N]`"
        )
        return reply


async def change_permission(service, Id):
    permission = {"role": "reader", "type": "anyone"}
    try:
        service.permissions().create(fileId=Id, body=permission).execute()
    except HttpError as e:
        """it's not possible to change permission per file for teamdrive"""
        if f'"File not found: {Id}."' in str(e) or (
            '"Sharing folders that are inside a shared drive is not supported."'
            in str(e)
        ):
            return
        else:
            raise e
    return


async def get_information(service, Id):
    r = (
        service.files()
        .get(
            fileId=Id,
            fields="name, id, size, mimeType, "
            "webViewLink, webContentLink,"
            "description",
            supportsAllDrives=True,
        )
        .execute()
    )
    return r


async def create_dir(service, folder_name):
    metadata = {
        "name": folder_name,
        "mimeType": "application/vnd.google-apps.folder",
    }
    try:
        if parent_Id is not None:
            pass
    except NameError:
        """- Fallback to G_DRIVE_FOLDER_ID else root dir -"""
        if G_DRIVE_FOLDER_ID is not None:
            metadata["parents"] = [G_DRIVE_FOLDER_ID]
    else:
        """- Override G_DRIVE_FOLDER_ID because parent_Id not empty -"""
        metadata["parents"] = [parent_Id]
    folder = (
        service.files()
        .create(body=metadata, fields="id, webViewLink", supportsAllDrives=True)
        .execute()
    )
    await change_permission(service, folder.get("id"))
    return folder


async def upload(gdrive, service, file_path, file_name, mimeType):
    try:
        await gdrive.edit("`Memproses unggahan...`")
    except Exception:
        pass
    body = {
        "name": file_name,
        "description": "Diunggah menggunakan WeebProject userbot.",
        "mimeType": mimeType,
    }
    try:
        if parent_Id is not None:
            pass
    except NameError:
        """- Fallback to G_DRIVE_FOLDER_ID else root dir -"""
        if G_DRIVE_FOLDER_ID is not None:
            body["parents"] = [G_DRIVE_FOLDER_ID]
    else:
        """- Override G_DRIVE_FOLDER_ID because parent_Id not empty -"""
        body["parents"] = [parent_Id]
    media_body = MediaFileUpload(file_path, mimetype=mimeType, resumable=True)
    """ - Start upload process - """
    file = service.files().create(
        body=body,
        media_body=media_body,
        fields="id, size, webContentLink",
        supportsAllDrives=True,
    )
    global is_cancelled
    current_time = time.time()
    response = None
    display_message = None
    is_cancelled = False
    while response is None:
        if is_cancelled is True:
            raise CancelProcess

        status, response = file.next_chunk()
        if status:
            file_size = status.total_size
            diff = time.time() - current_time
            uploaded = status.resumable_progress
            percentage = uploaded / file_size * 100
            speed = round(uploaded / diff, 2)
            eta = round((file_size - uploaded) / speed)
            prog_str = "**Mengunggah** | [{}{}] `{}%`".format(
                "".join(["■" for i in range(math.floor(percentage / 10))]),
                "".join(["▨" for i in range(10 - math.floor(percentage / 10))]),
                round(percentage, 2),
            )
            current_message = (
                "`[FILE - UNGGAH]`\n\n"
                f"`{file_name}`\n"
                f"`Status`\n{prog_str}\n"
                f"`{humanbytes(uploaded)} dari {humanbytes(file_size)} "
                f"@ {humanbytes(speed)}`\n"
                f"`Perkiraan` -> {time_formatter(eta)}"
            )
            if (
                round(diff % 15.00) == 0
                and (display_message != current_message)
                or (uploaded == file_size)
            ):
                await gdrive.edit(current_message)
                display_message = current_message
    file_id = response.get("id")
    file_size = response.get("size")
    downloadURL = response.get("webContentLink")
    """ - Change permission - """
    await change_permission(service, file_id)
    return int(file_size), downloadURL


async def task_directory(gdrive, service, folder_path):
    global parent_Id
    global is_cancelled
    is_cancelled = False
    lists = os.listdir(folder_path)
    if len(lists) == 0:
        return parent_Id
    root_parent_Id = None
    for f in lists:
        if is_cancelled is True:
            raise CancelProcess

        current_f_name = join(folder_path, f)
        if isdir(current_f_name):
            folder = await create_dir(service, f)
            parent_Id = folder.get("id")
            root_parent_Id = await task_directory(gdrive, service, current_f_name)
        else:
            file_name = await get_raw_name(current_f_name)
            mimeType = await get_mimeType(current_f_name)
            await upload(gdrive, service, current_f_name, file_name, mimeType)
            root_parent_Id = parent_Id
    return root_parent_Id


async def reset_parentId():
    global parent_Id
    try:
        if parent_Id is not None:
            pass
    except NameError:
        if G_DRIVE_FOLDER_ID is not None:
            parent_Id = G_DRIVE_FOLDER_ID
    else:
        del parent_Id
    return


@register(pattern=r"^\.gdlist(?: |$)(-l \d+)?(?: |$)?(.*)?(?: |$)", outgoing=True)
async def lists(gdrive):
    await gdrive.edit("`Mendapatkan informasi...`")
    checker = gdrive.pattern_match.group(1)
    if checker is not None:
        page_size = int(gdrive.pattern_match.group(1).strip("-l "))
        if page_size > 1000:
            await gdrive.edit(
                "`[DAFTAR - GDRIVE]`\n\n"
                "`Status :` **BAD**\n"
                "`Alasan :` Tidak bisa mendapatkan daftar jika batas lebih dari 1000."
            )
            return
    else:
        page_size = 25  # default page_size is 25
    checker = gdrive.pattern_match.group(2)
    if checker != "":
        if checker.startswith("-p"):
            parents = checker.split(None, 2)[1]
            try:
                name = checker.split(None, 2)[2]
            except IndexError:
                query = f"'{parents}' in parents and (name contains '*')"
            else:
                query = f"'{parents}' in parents and (name contains '{name}')"
        else:
            if re.search("-p (.*)", checker):
                parents = re.search("-p (.*)", checker).group(1)
                name = checker.split("-p")[0].strip()
                query = f"'{parents}' in parents and (name contains '{name}')"
            else:
                name = checker
                query = f"name contains '{name}'"
    else:
        query = ""
    service = await create_app(gdrive)
    if service is False:
        return False
    message = ""
    fields = (
        "nextPageToken, files(name, size, id, " "mimeType, webViewLink, webContentLink)"
    )
    page_token = None
    result = []
    while True:
        try:
            response = (
                service.files()
                .list(
                    supportsAllDrives=True,
                    includeTeamDriveItems=True,
                    q=query,
                    spaces="drive",
                    corpora="allDrives",
                    fields=fields,
                    pageSize=page_size,
                    orderBy="modifiedTime desc, folder",
                    pageToken=page_token,
                )
                .execute()
            )
        except HttpError as e:
            await gdrive.edit(
                "`[DAFTAR - GDRIVE]`\n\n" "`Status :` **BURUK**\n" f"`Alasan :` {str(e)}"
            )
            return
        for files in response.get("files", []):
            if len(result) >= page_size:
                break

            file_name = files.get("name")
            file_size = files.get("size", 0)
            if files.get("mimeType") == "application/vnd.google-apps.folder":
                link = files.get("webViewLink")
                message += f"📁️ • [{file_name}]({link})\n"
            else:
                link = files.get("webContentLink")
                message += (
                    f"📄️ • [{file_name}]({link}) - __{humanbytes(int(file_size))}__\n"
                )
            result.append(files)
        if len(result) >= page_size:
            break

        page_token = response.get("nextPageToken", None)
        if page_token is None:
            break

    del result
    if query == "":
        query = "Tidak ditentukan"
    if len(message) > 4096:
        await gdrive.edit("`Hasil terlalu besar, dikirim sebagai file...`")
        with open("result.txt", "w") as r:
            r.write(f"**Pencarian Google Drive :**\n{query}\n\n**Hasil :**\n\n{message}")
        await gdrive.client.send_file(
            gdrive.chat_id, "result.txt", caption="Pencarian Daftar Google Drive."
        )
    else:
        await gdrive.edit(
            "**Pencarian Google Drive :**\n" f"`{query}`\n\n**Hasil :**\n\n{message}"
        )
    return


@register(pattern=r"^\.gdf (mkdir|rm|chck) (.*)", outgoing=True)
async def google_drive_managers(gdrive):
    """- Google Drive folder/file management -"""
    await gdrive.edit("`Mengirim informasi...`")
    service = await create_app(gdrive)
    if service is False:
        return None
    """ - Split name if contains spaces by using ; - """
    f_name = gdrive.pattern_match.group(2).split(";")
    exe = gdrive.pattern_match.group(1)
    reply = ""
    for name_or_id in f_name:
        """- in case given name has a space beetween ; -"""
        name_or_id = name_or_id.strip()
        metadata = {
            "name": name_or_id,
            "mimeType": "application/vnd.google-apps.folder",
        }
        try:
            if parent_Id is not None:
                pass
        except NameError:
            """- Fallback to G_DRIVE_FOLDER_ID else to root dir -"""
            if G_DRIVE_FOLDER_ID is not None:
                metadata["parents"] = [G_DRIVE_FOLDER_ID]
        else:
            """- Override G_DRIVE_FOLDER_ID because parent_Id not empty -"""
            metadata["parents"] = [parent_Id]
        page_token = None
        result = (
            service.files()
            .list(
                q=f'name="{name_or_id}"',
                spaces="drive",
                fields=(
                    "nextPageToken, files(parents, name, id, size, "
                    "mimeType, webViewLink, webContentLink, description)"
                ),
                supportsAllDrives=True,
                pageToken=page_token,
            )
            .execute()
        )
        if exe == "mkdir":
            """
            - Create a directory, abort if exist when parent not given -
            """
            status = "[FOLDER - ADA]"
            try:
                folder = result.get("files", [])[0]
            except IndexError:
                folder = await create_dir(service, name_or_id)
                status = status.replace("ADA]", "DIBUAT]")
            folder_id = folder.get("id")
            webViewURL = folder.get("webViewLink")
            if "DIBUAT" in status:
                """- Change permission -"""
                await change_permission(service, folder_id)
            reply += (
                f"`{status}`\n\n"
                f"`{name_or_id}`\n"
                f"`ID  :` `{folder_id}`\n"
                f"`URL :` [Buka]({webViewURL})\n\n"
            )
        elif exe == "rm":
            """- Permanently delete, skipping the trash -"""
            try:
                """- Try if given value is a name not a folderId/fileId -"""
                f = result.get("files", [])[0]
                f_id = f.get("id")
            except IndexError:
                """- If failed assumming value is folderId/fileId -"""
                f_id = name_or_id
                if "http://" in name_or_id or "https://" in name_or_id:
                    if "id=" in name_or_id:
                        f_id = name_or_id.split("id=")[1]
                        f_id = re.split("[? &]", f_id)[0]
                    elif "folders/" in name_or_id:
                        f_id = name_or_id.split("folders/")[1]
                        f_id = re.split("[? &]", f_id)[0]
                    elif "/view" in name_or_id:
                        f_id = name_or_id.split("/")[-2]
                try:
                    f = await get_information(service, f_id)
                except Exception as e:
                    reply += (
                        f"`[KESALAHAN - FILE/FOLDER]`\n\n"
                        "`Status :` **BURUK**\n"
                        f"`Alasan :` `{str(e)}`\n\n"
                    )
                    continue
            name = f.get("name")
            mimeType = f.get("mimeType")
            if mimeType == "application/vnd.google-apps.folder":
                status = "[HAPUS - FOLDER]"
            else:
                status = "[HAPUS - FILE]"
            try:
                service.files().delete(fileId=f_id, supportsAllDrives=True).execute()
            except HttpError as e:
                status.replace("[HAPUS", "[KESALAHAN")
                reply += (
                    f"`{status}`\n\n" "`Status :` **BURUK**" f"`Alasan :` {str(e)}\n\n"
                )
                continue
            else:
                reply += f"`{status}`\n\n" f"`{name}`\n" "`Status :` **OK**\n\n"
        elif exe == "chck":
            """- Check file/folder if exists -"""
            try:
                f = result.get("files", [])[0]
            except IndexError:
                """- If failed assumming value is folderId/fileId -"""
                f_id = name_or_id
                try:
                    f = await get_information(service, f_id)
                except Exception as e:
                    reply += (
                        "`[KESALAHAN - FILE/FOLDER]`\n\n"
                        "`Status :` **BURUK**\n"
                        f"`Alasan :` `{str(e)}`\n\n"
                    )
                    continue
            """ - If exists parse file/folder information - """
            name_or_id = f.get("name")  # override input value
            f_id = f.get("id")
            f_size = f.get("size")
            mimeType = f.get("mimeType")
            webViewLink = f.get("webViewLink")
            downloadURL = f.get("webContentLink")
            description = f.get("description")
            if mimeType == "application/vnd.google-apps.folder":
                status = "[FOLDER - ADA]"
            else:
                status = "[FILE - ADA]"
            msg = (
                f"`{status}`\n\n" f"`Nama  :` `{name_or_id}`\n" f"`ID    :` `{f_id}`\n"
            )
            if mimeType != "application/vnd.google-apps.folder":
                msg += f"`Ukuran :` `{humanbytes(f_size)}`\n"
                msg += f"`Tautan :` [{name_or_id}]({downloadURL})\n\n"
            else:
                msg += f"`URL    :` [Open]({webViewLink})\n\n"
            if description:
                msg += f"`Tentang:`\n`{description}`\n\n"
            reply += msg
        page_token = result.get("nextPageToken", None)
    await gdrive.edit(reply)
    return


@register(pattern=r"^\.gdabort(?: |$)", outgoing=True)
async def cancel_process(gdrive):
    """
    Abort process for download and upload
    """
    global is_cancelled
    downloads = aria2.get_downloads()
    await gdrive.edit("`Membatalkan...`")
    if len(downloads) != 0:
        aria2.remove_all(force=True)
        aria2.autopurge()
    is_cancelled = True
    await asyncio.sleep(3.5)
    await gdrive.delete()


@register(pattern=r"^\.gd(?: |$)(.*)", outgoing=True)
async def google_drive(gdrive):
    reply = ""
    """ - Parsing all google drive function - """
    value = gdrive.pattern_match.group(1)
    file_path = None
    uri = None
    if not value and not gdrive.reply_to_msg_id:
        return None
    elif value and gdrive.reply_to_msg_id:
        await gdrive.edit(
            "`[KESALAHAN - TIDAK DIKETAHUI]`\n\n"
            "`Status :` **GAGAL**\n"
            "`Alasan :` Bingung mengunggah file atau pesan/media yang dibalas."
        )
        return None
    service = await create_app(gdrive)
    if service is False:
        return None
    if isfile(value):
        file_path = value
        if file_path.endswith(".torrent"):
            uri = [file_path]
            file_path = None
    elif isdir(value):
        folder_path = value
        global parent_Id
        folder_name = await get_raw_name(folder_path)
        folder = await create_dir(service, folder_name)
        parent_Id = folder.get("id")
        webViewURL = "https://drive.google.com/drive/folders/" + parent_Id
        try:
            await task_directory(gdrive, service, folder_path)
        except CancelProcess:
            await gdrive.respond(
                "`[FOLDER - DIBATALKAN]`\n\n"
                "`Status :` **OK** - sinyal yang diterima dibatalkan."
            )
            await reset_parentId()
            await gdrive.delete()
            return True
        except Exception as e:
            await gdrive.edit(
                "`[FOLDER - UNGGAH]`\n\n"
                f"`{folder_name}`\n"
                "`Status :` **BURUK**\n"
                f"`Alasan :` {str(e)}"
            )
            await reset_parentId()
            return False
        else:
            msg = f"**GDrive Unggah**\n\n📁 [{folder_name}]({webViewURL})"
            if G_DRIVE_INDEX_URL:
                index_url = (
                    G_DRIVE_INDEX_URL.rstrip("/") + "/" + quote(folder_name) + "/"
                )
                msg += f"\n👥 [Index URL]({index_url})"
            folder_size = await count_dir_size(service, parent_Id)
            msg += f"\n__Ukuran : {humanbytes(folder_size)}__"
            await gdrive.edit(msg, link_preview=False)
            await reset_parentId()
            return True
    elif not value and gdrive.reply_to_msg_id:
        reply += await download(gdrive, service)
        await gdrive.respond(reply)
        await gdrive.delete()
        return None
    else:
        if re.findall(r"\bhttps?://drive\.google\.com\S+", value):
            """- Link is google drive fallback to download -"""
            value = re.findall(r"\bhttps?://drive\.google\.com\S+", value)
            for uri in value:
                try:
                    reply += await download_gdrive(gdrive, service, uri)
                except CancelProcess:
                    reply += (
                        "`[FILE - DIBATALKAN]`\n\n"
                        "`Status :` **OK** - sinyal yang diterima dibatalkan."
                    )
                    break
                except Exception as e:
                    reply += (
                        "`[KESALAHAN - FILE]`\n\n"
                        "`Status :` **BURUK**\n"
                        f"`Alasan :` {str(e)}\n\n"
                    )
                    continue
            if reply:
                await gdrive.respond(reply, link_preview=False)
                await gdrive.delete()
                return True
            else:
                return None
        elif re.findall(r"\bhttps?://.*\.\S+", value) or "magnet:?" in value:
            uri = value.split()
        else:
            for fileId in value.split():
                if any(map(str.isdigit, fileId)):
                    one = True
                else:
                    one = False
                if "-" in fileId or "_" in fileId:
                    two = True
                else:
                    two = False
                if True in [one or two]:
                    try:
                        reply += await download_gdrive(gdrive, service, fileId)
                    except CancelProcess:
                        reply += (
                            "`[FILE - DIBATALKAN]`\n\n"
                            "`Status :` **OK** - sinyal yang diterima dibatalkan."
                        )
                        break
                    except Exception as e:
                        reply += (
                            "`[KESALAHAN - FILE]`\n\n"
                            "`Status :` **BURUK**\n"
                            f"`Alasan :` {str(e)}\n\n"
                        )
                        continue
            if reply:
                await gdrive.respond(reply, link_preview=False)
                await gdrive.delete()
                return True
            else:
                return None
        if not uri and not gdrive.reply_to_msg_id:
            await gdrive.edit(
                "`[KESALAHAN - VALUE]`\n\n"
                "`Status :` **BURUK**\n"
                "`Alasan :` Nilai yang diberikan bukanlah URL atau jalur file/folder. "
                "Jika menurut Anda ini salah, mungkin Anda menggunakan  **“.gd”**  dengan beberapa "
                "nilai file/folder, cth: **“.gd [nama file1] [nama file2]”**  "
                "untuk mengunggah dari jalur file/folder itu tidak didukung."
            )
            return False
    if uri and not gdrive.reply_to_msg_id:
        for dl in uri:
            try:
                reply += await download(gdrive, service, dl)
            except Exception as e:
                if " not found" in str(e) or "'file'" in str(e):
                    reply += (
                        "`[FILE - DIBATALKAN]`\n\n"
                        "`Status :` **OK** - sinyal yang diterima dibatalkan."
                    )
                    await asyncio.sleep(2.5)
                    break
                else:
                    """- if something bad happened, continue to next uri -"""
                    reply += (
                        "`[KESALAHAN - TIDAK DIKETAHUI]`\n\n"
                        "`Status :` **BURUK**\n"
                        f"`Alasan :` `{dl}` | `{str(e)}`\n\n"
                    )
                    continue
        await gdrive.respond(reply, link_preview=False)
        await gdrive.delete()
        return None
    mimeType = await get_mimeType(file_path)
    file_name = await get_raw_name(file_path)
    try:
        result = await upload(gdrive, service, file_path, file_name, mimeType)
    except CancelProcess:
        gdrive.respond(
            "`[FILE - DIBATALKAN]`\n\n" "`Status :` **OK** - sinyal yang diterima dibatalkan."
        )
    if result:
        msg = f"**GDrive Unggah**\n\n📄 [{file_name}]({result[1]})"
        if G_DRIVE_INDEX_URL:
            index_url = G_DRIVE_INDEX_URL.rstrip("/") + "/" + quote(file_name)
            msg += f"\n👥 [Index URL]({index_url})"
        msg += f"\n__Ukuran : {humanbytes(result[0])}__"
        await gdrive.respond(msg, link_preview=False)
    await gdrive.delete()
    return


@register(pattern=r"^\.gdfset (put|rm)(?: |$)(.*)", outgoing=True)
async def set_upload_folder(gdrive):
    """- Set parents dir for upload/check/makedir/remove -"""
    await gdrive.edit("`Mengirim informasi...`")
    global parent_Id
    exe = gdrive.pattern_match.group(1)
    if exe == "rm":
        if G_DRIVE_FOLDER_ID is not None:
            parent_Id = G_DRIVE_FOLDER_ID
            await gdrive.edit(
                "`[FOLDER - SET]`\n\n"
                "`Status :` **OK** - sekarang menggunakan G_DRIVE_FOLDER_ID."
            )
            return None
        else:
            try:
                del parent_Id
            except NameError:
                await gdrive.edit(
                    "`[FOLDER - SET]`\n\n" "`Status :` **BURUK** - Tidak ada parent_Id yang disetel."
                )
                return False
            else:
                await gdrive.edit(
                    "`[FOLDER - SET]`\n\n"
                    "`Status :` **OK**"
                    " - G_DRIVE_FOLDER_ID kosong, akan menggunakan root."
                )
                return None
    inp = gdrive.pattern_match.group(2)
    if not inp:
        await gdrive.edit("`Gunakan .gdfset put [folderURL/folderID]`")
        return None
    """ - Value for .gdfset (put|rm) can be folderId or folder link - """
    try:
        ext_id = re.findall(r"\bhttps?://drive\.google\.com\S+", inp)[0]
    except IndexError:
        """- if given value isn't folderURL assume it's an Id -"""
        if any(map(str.isdigit, inp)):
            c1 = True
        else:
            c1 = False
        if "-" in inp or "_" in inp:
            c2 = True
        else:
            c2 = False
        if True in [c1 or c2]:
            parent_Id = inp
            await gdrive.edit(
                "`[PARENT - FOLDER]`\n\n" "`Status :` **OK** - Berhasil diubah."
            )
            return None
        else:
            await gdrive.edit(
                "`[PARENT - FOLDER]`\n\n" "`Status :` **PERINGATAN** - penggunaan paksa..."
            )
            parent_Id = inp
    else:
        if "uc?id=" in ext_id:
            await gdrive.edit(
                "`[KESALAHAN - URL]`\n\n" "`Status :` **BURUK** - folderURL tidak valid."
            )
            return None
        try:
            parent_Id = ext_id.split("folders/")[1]
        except IndexError:
            """- Try catch again if URL open?id= -"""
            try:
                parent_Id = ext_id.split("open?id=")[1]
            except IndexError:
                if "/view" in ext_id:
                    parent_Id = ext_id.split("/")[-2]
                else:
                    try:
                        parent_Id = ext_id.split("folderview?id=")[1]
                    except IndexError:
                        await gdrive.edit(
                            "`[KESALAHAN - URL]`\n\n"
                            "`Status :` **BURUK** - folderURL tidak valid."
                        )
                        return None
        await gdrive.edit(
            "`[PARENT - FOLDER]`\n\n" "`Status :` **OK** - Berhasil diubah."
        )
    return


async def check_progress_for_dl(gdrive, gid, previous):
    complete = None
    global is_cancelled
    global filenames
    is_cancelled = False
    while not complete:
        if is_cancelled is True:
            raise CancelProcess

        file = aria2.get_download(gid)
        complete = file.is_complete
        try:
            filenames = file.name
        except IndexError:
            pass
        try:
            if not complete and not file.error_message:
                percentage = int(file.progress)
                downloaded = percentage * int(file.total_length) / 100
                prog_str = "**Mengunduh** | [{}{}] `{}`".format(
                    "".join(["■" for i in range(math.floor(percentage / 10))]),
                    "".join(["▨" for i in range(10 - math.floor(percentage / 10))]),
                    file.progress_string(),
                )
                msg = (
                    "`[URI - UNDUH]`\n\n"
                    f"`{file.name}`\n"
                    f"`Status` -> **{file.status.capitalize()}**\n"
                    f"{prog_str}\n"
                    f"`{humanbytes(downloaded)} dari"
                    f" {file.total_length_string()}"
                    f" @ {file.download_speed_string()}`\n"
                    f"`Perkiraan` -> {file.eta_string()}\n"
                )
                if msg != previous or downloaded == file.total_length_string():
                    await gdrive.edit(msg)
                    msg = previous
            else:
                await gdrive.edit(f"`{msg}`")
            await asyncio.sleep(15)
            await check_progress_for_dl(gdrive, gid, previous)
            file = aria2.get_download(gid)
            complete = file.is_complete
            if complete:
                await gdrive.edit(f"`{file.name}`\n\n" "Berhasil diunduh...")
                return True
        except Exception as e:
            if " depth exceeded" in str(e):
                file.remove(force=True)
                try:
                    await gdrive.edit(
                        "`[URI - UNDUH]`\n\n"
                        f"`{file.name}`\n"
                        "`Status :` **GAGAL**\n"
                        "`Alasan :` Unduhan otomatis dibatalkan, URI/Torrent mati."
                    )
                except Exception:
                    pass


async def list_drive_dir(service, file_id: str) -> list:
    query = f"'{file_id}' in parents and (name contains '*')"
    fields = "nextPageToken, files(id, name, mimeType, size)"
    page_token = None
    page_size = 100
    files = []
    while True:
        response = (
            service.files()
            .list(
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
                q=query,
                spaces="drive",
                fields=fields,
                pageToken=page_token,
                pageSize=page_size,
                corpora="allDrives",
                orderBy="folder, name",
            )
            .execute()
        )
        files.extend(response.get("files", []))
        page_token = response.get("nextPageToken", None)
        if page_token is None:
            break
    return files


async def create_folder(service, folder_name: str, parent_id: str) -> str:
    metadata = {
        "name": folder_name,
        "mimeType": "application/vnd.google-apps.folder",
    }
    if parent_id is not None:
        metadata["parents"] = [parent_id]
    folder = (
        service.files()
        .create(body=metadata, fields="id", supportsAllDrives=True)
        .execute()
    )
    return folder["id"]


async def copy_file(service, file_id: str, parent_id: str) -> str:
    body = {}
    if parent_id:
        body["parents"] = [parent_id]
    drive_file = (
        service.files()
        .copy(body=body, fileId=file_id, supportsTeamDrives=True)
        .execute()
    )
    return drive_file["id"]


async def copy_dir(service, file_id: str, parent_id: str) -> str:
    files = await list_drive_dir(service, file_id)
    if len(files) == 0:
        return parent_id
    new_id = None
    for file_ in files:
        if file_["mimeType"] == G_DRIVE_DIR_MIME_TYPE:
            dir_id = await create_folder(service, file_["name"], parent_id)
            new_id = await copy_dir(service, file_["id"], dir_id)
        else:
            await copy_file(service, file_["id"], parent_id)
            await asyncio.sleep(0.5)  # due to user rate limits
            new_id = parent_id
    return new_id


async def count_dir_size(service, file_id: str) -> int:
    _size = 0
    files = await list_drive_dir(service, file_id)
    for _file in files:
        try:
            if _file.get("mimeType") == G_DRIVE_DIR_MIME_TYPE:
                dir_id = _file.get("id")
                _size += int(await count_dir_size(service, dir_id))
            else:
                _size += int(_file.get("size"))
        except TypeError:
            pass
    return _size


@register(outgoing=True, pattern=r"^\.gcl(?: |$)(.*)")
async def gdrive_clone(event):
    service = await create_app(event)
    if service is False:
        return None
    input_str = event.pattern_match.group(1)
    if not input_str:
        return await event.edit("`Apa yang harus saya salin?`")
    _file_id = input_str
    await event.edit("`Memproses...`")
    if "https://" or "http://" in input_str:
        if "id=" in input_str:
            _file_id = input_str.split("id=")[1]
            _file_id = re.split("[? &]", _file_id)[0]
        elif "folders/" in input_str:
            _file_id = input_str.split("folders/")[1]
            _file_id = re.split("[? &]", _file_id)[0]
        elif "/view" in input_str:
            _file_id = input_str.split("/")[-2]
    try:
        await get_information(service, _file_id)
    except BaseException as gd_e:
        return await event.edit(
            f"`[KESALAHAN - FILE/FOLDER]`\n\n`Status :` **BURUK**\n`Kesalahan :` `{gd_e}`"
        )
    _drive_file = await get_information(service, _file_id)
    if _drive_file["mimeType"] == G_DRIVE_DIR_MIME_TYPE:
        dir_id = await create_folder(service, _drive_file["name"], G_DRIVE_FOLDER_ID)
        await copy_dir(service, _file_id, dir_id)
        ret_id = dir_id
    else:
        ret_id = await copy_file(service, _file_id, G_DRIVE_FOLDER_ID)
    _drive_meta = await get_information(service, ret_id)
    _name = _drive_meta.get("name")
    if _drive_meta.get("mimeType") == G_DRIVE_DIR_MIME_TYPE:
        _link = _drive_meta.get("webViewLink")
        _size = await count_dir_size(service, _drive_meta.get("id"))
        _icon = "📁️"
    else:
        _link = _drive_meta.get("webContentLink")
        _size = _drive_meta.get("size", 0)
        _icon = "📄️"
    msg = ""
    drive_link = f"{_icon} [{_name}]({_link})"
    msg += f"**Salin GDrive**\n\n**{drive_link}**"
    if G_DRIVE_INDEX_URL:
        index_url = G_DRIVE_INDEX_URL.rstrip("/") + "/" + quote(_name)
        if _drive_meta.get("mimeType") == G_DRIVE_DIR_MIME_TYPE:
            index_url += "/"
        msg += f"\n👤 **[Index URL]({index_url})**"
    msg += f"\n__Ukuran : {humanbytes(int(_size))}__"
    await event.edit(msg)


CMD_HELP.update(
    {
        "gdrive": "`.gdauth`"
        "\n➥  Buat token untuk mengaktifkan semua layanan cmd google drive. "
        "Ini hanya perlu dijalankan sekali seumur hidup."
        "\n\n`.gdreset`"
        "\n➥  Setel ulang token Anda jika terjadi sesuatu yang buruk atau mengubah akun drive."
        "\n\n`.gd`"
        "\n➥  Unggah file dari lokal atau uri/url/tautan drive ke google drive. "
        "Untuk tautan drive, unggah hanya jika Anda menginginkannya."
        "\n\n`.gdabort`"
        "\n➥  Batalkan proses mengunggah atau mengunduh."
        "\n\n`.gdlist`"
        "\n➥  Dapatkan daftar folder dan file dengan ukuran default 50."
        "\nGunakan flags `“-l range[1-1000]”` untuk batas keluaran."
        "\nGunakan flags `“-p parents-folder_id”` untuk daftar folder yang diberikan di gdrive."
        "\n\n`.gdf mkdir`"
        "\n➥  Membuat folder gdrive."
        "\n\n`.gdf chck`"
        "\n➥  Periksa file/folder di gdrive."
        "\n\n`.gdf rm`"
        "\n➥  Hapus files/folders di gdrive. "
        "Tidak bisa dibatalkan, metode ini melewatkan file sampah, jadi hati-hati..."
        "\n\n`.gdfset put`"
        "\n➥  Ubah direktori unggah di gdrive."
        "\n\n`.gdfset rm`"
        "\n➥  Hapus set parentId dari cmd `“.gdfset put”` "
        "ke  **G_DRIVE_FOLDER_ID**  dan jika upload kosong akan masuk ke root."
        "\n\n`.gcl [tautan GDrive publik/ID GDrive]`"
        "\n➥  Salin file atau folder ke drive Anda."
        "\n\n**CATATAN** :"
        "\nUntuk `“.gdlist”` Anda bisa menggabungkan flags `“-l”` dan `“-p”` dengan atau tanpa nama "
        "pada waktu bersamaan, flags `“-l”` itu pasti lebih dahulu sebelum flags `“-p”`."
        "\nDan secara default daftar dari  **modifiedTime**  terbaru dan kemudian folder."
    }
)
