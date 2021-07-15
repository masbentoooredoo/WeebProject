# Credits to Userge for Remove and Rename

import io
import os
import os.path
import shutil
import time
from datetime import datetime
from os.path import basename, dirname, exists, isdir, isfile, join, relpath, splitext
from shutil import rmtree
from tarfile import TarFile, is_tarfile
from zipfile import ZIP_DEFLATED, BadZipFile, ZipFile, is_zipfile

from natsort import os_sorted
from py7zr import Bad7zFile, SevenZipFile, is_7zfile
from rarfile import BadRarFile, RarFile, is_rarfile

from userbot import CMD_HELP, TEMP_DOWNLOAD_DIRECTORY
from userbot.events import register
from userbot.utils import humanbytes

MAX_MESSAGE_SIZE_LIMIT = 4095


@register(outgoing=True, pattern=r"^\.ls(?: |$)(.*)")
async def lst(event):
    if event.fwd_from:
        return
    cat = event.pattern_match.group(1)
    path = cat if cat else os.getcwd()
    if not exists(path):
        await event.edit(
            f"`Tidak ada direktori atau file seperti itu dengan nama “{cat}” periksa lagi!`"
        )
        return
    if isdir(path):
        if cat:
            msg = f"Folder dan file di  **{path}** :\n\n"
        else:
            msg = "Folder dan file di direktori saat ini :\n\n"
        lists = os.listdir(path)
        files = ""
        folders = ""
        for contents in os_sorted(lists):
            catpath = path + "/" + contents
            if not isdir(catpath):
                size = os.stat(catpath).st_size
                if contents.endswith((".mp3", ".flac", ".wav", ".m4a")):
                    files += "🎵 "
                elif contents.endswith(".opus"):
                    files += "🎙 "
                elif contents.endswith(
                    (".mkv", ".mp4", ".webm", ".avi", ".mov", ".flv")
                ):
                    files += "🎞 "
                elif contents.endswith(
                    (".zip", ".tar", ".tar.gz", ".rar", ".7z", ".xz")
                ):
                    files += "🗜 "
                elif contents.endswith(
                    (".jpg", ".jpeg", ".png", ".gif", ".bmp", ".ico", ".webp")
                ):
                    files += "🖼 "
                elif contents.endswith((".exe", ".deb")):
                    files += "⚙️ "
                elif contents.endswith((".iso", ".img")):
                    files += "💿 "
                elif contents.endswith((".apk", ".xapk")):
                    files += "📱 "
                elif contents.endswith(".py"):
                    files += "🐍 "
                else:
                    files += "📄 "
                files += f"`{contents}` (__{humanbytes(size)}__)\n"
            else:
                folders += f"📁 `{contents}`\n"
        msg = msg + folders + files if files or folders else msg + "__empty path__"
    else:
        size = os.stat(path).st_size
        msg = "The details of given file :\n\n"
        if path.endswith((".mp3", ".flac", ".wav", ".m4a")):
            mode = "🎵 "
        elif path.endswith(".opus"):
            mode = "🎙 "
        elif path.endswith((".mkv", ".mp4", ".webm", ".avi", ".mov", ".flv")):
            mode = "🎞 "
        elif path.endswith((".zip", ".tar", ".tar.gz", ".rar", ".7z", ".xz")):
            mode = "🗜 "
        elif path.endswith((".jpg", ".jpeg", ".png", ".gif", ".bmp", ".ico", ".webp")):
            mode = "🖼 "
        elif path.endswith((".exe", ".deb")):
            mode = "⚙️ "
        elif path.endswith((".iso", ".img")):
            mode = "💿 "
        elif path.endswith((".apk", ".xapk")):
            mode = "📱 "
        elif path.endswith(".py"):
            mode = "🐍 "
        else:
            mode = "📄 "
        time.ctime(os.path.getctime(path))
        time2 = time.ctime(os.path.getmtime(path))
        time3 = time.ctime(os.path.getatime(path))
        msg += f"**Lokasi :** `{path}`\n"
        msg += f"**Ikon :** `{mode}`\n"
        msg += f"**Ukuran :** `{humanbytes(size)}`\n"
        msg += f"**Waktu modifikasi terakhir:** `{time2}`\n"
        msg += f"**Waktu terakhir diakses:** `{time3}`"

    if len(msg) > MAX_MESSAGE_SIZE_LIMIT:
        with io.BytesIO(str.encode(msg)) as out_file:
            out_file.name = "ls.txt"
            await event.client.send_file(
                event.chat_id,
                out_file,
                force_document=True,
                allow_cache=False,
                caption=path,
            )
            await event.delete()
    else:
        await event.edit(msg)


@register(outgoing=True, pattern=r"^\.rm(?: |$)(.*)")
async def rmove(event):
    """Removing Directory/File"""
    cat = event.pattern_match.group(1)
    if not cat:
        await event.edit("`Jalur file tidak ada!`")
        return
    if not exists(cat):
        await event.edit("`Jalur file tidak ada!`")
        return
    if isfile(cat):
        os.remove(cat)
    else:
        rmtree(cat)
    await event.edit(f"`“{cat}” dihapus.`")


@register(outgoing=True, pattern=r"^\.rn ([^|]+)\|([^|]+)")
async def rname(event):
    """Renaming Directory/File"""
    cat = str(event.pattern_match.group(1)).strip()
    new_name = str(event.pattern_match.group(2)).strip()
    if not exists(cat):
        await event.edit(f"`Jalur berkas : “{cat}” tidak ada!`")
        return
    new_path = join(dirname(cat), new_name)
    shutil.move(cat, new_path)
    await event.edit(f"`“{cat}” diubah ke “{new_path}”`")


@register(outgoing=True, pattern=r"^\.zip (.*)")
async def zip_file(event):
    if event.fwd_from:
        return
    if not exists(TEMP_DOWNLOAD_DIRECTORY):
        os.makedirs(TEMP_DOWNLOAD_DIRECTORY)
    input_str = event.pattern_match.group(1)
    path = input_str
    zip_name = ""
    if "|" in input_str:
        path, zip_name = path.split("|")
        path = path.strip()
        zip_name = zip_name.strip()
    if exists(path):
        await event.edit("`Membuat arsip...`")
        start_time = datetime.now()
        if isdir(path):
            dir_path = path.split("/")[-1]
            if path.endswith("/"):
                dir_path = path.split("/")[-2]
            zip_path = join(TEMP_DOWNLOAD_DIRECTORY, dir_path) + ".zip"
            if zip_name:
                zip_path = join(TEMP_DOWNLOAD_DIRECTORY, zip_name)
                if not zip_name.endswith(".zip"):
                    zip_path += ".zip"
            with ZipFile(zip_path, "w", ZIP_DEFLATED) as zip_obj:
                for roots, _, files in os.walk(path):
                    for file in files:
                        files_path = join(roots, file)
                        arc_path = join(dir_path, relpath(files_path, path))
                        zip_obj.write(files_path, arc_path)
            end_time = (datetime.now() - start_time).seconds
            await event.edit(
                f"**{path}**  dibuat zip ke  **{zip_path}**  dalam  **{end_time}**  detik."
            )
        elif isfile(path):
            file_name = basename(path)
            zip_path = join(TEMP_DOWNLOAD_DIRECTORY, file_name) + ".zip"
            if zip_name:
                zip_path = join(TEMP_DOWNLOAD_DIRECTORY, zip_name)
                if not zip_name.endswith(".zip"):
                    zip_path += ".zip"
            with ZipFile(zip_path, "w", ZIP_DEFLATED) as zip_obj:
                zip_obj.write(path, file_name)
            await event.edit(f"**{path}**  dibuat zip ke  **{zip_path}**")
    else:
        await event.edit("`404: Tidak ditemukan.`")


@register(outgoing=True, pattern=r"^\.unzip (.*)")
async def unzip_file(event):
    if event.fwd_from:
        return
    if not exists(TEMP_DOWNLOAD_DIRECTORY):
        os.makedirs(TEMP_DOWNLOAD_DIRECTORY)
    input_str = event.pattern_match.group(1)
    output_path = TEMP_DOWNLOAD_DIRECTORY + basename(splitext(input_str)[0])
    if exists(input_str):
        start_time = datetime.now()
        await event.edit("`Mengekstrak...`")
        if is_zipfile(input_str):
            zip_type = ZipFile
        elif is_rarfile(input_str):
            zip_type = RarFile
        elif is_tarfile(input_str):
            zip_type = TarFile
        elif is_7zfile(input_str):
            zip_type = SevenZipFile
        else:
            return await event.edit(
                "`Tipe file tidak didukung!`\n`Hanya ZIP, TAR, 7z, dan RAR`"
            )
        try:
            with zip_type(input_str, "r") as zip_obj:
                zip_obj.extractall(output_path)
        except BadRarFile:
            return await event.edit("**Kesalahan:** `File RAR rusak`")
        except BadZipFile:
            return await event.edit("**Kesalahan:** `File ZIP rusak`")
        except Bad7zFile:
            return await event.edit("**Kesalahan:** `File 7z rusak`")
        except BaseException as err:
            return await event.edit(f"**Kesalahan:** `{err}`")
        end_time = (datetime.now() - start_time).seconds
        await event.edit(
            f"Mengekstrak  **{input_str}**  ke  **{output_path}**  dalam  **{end_time}**  detik."
        )
    else:
        await event.edit("`404: Not Found`")


CMD_HELP.update(
    {
        "file": "`.ls [direktori]`"
        "\n➥  Dapatkan daftar file di dalam direktori."
        "\n\n`.rm [direktori/file]`"
        "\n➥  Hapus file atau direktori."
        "\n\n`.rn [direktori/file] | [nama baru]`"
        "\n➥  Mengubah nama file atau direktori."
        "\n\n>`.zip [file/jalur folder] | [nama zip] (opsional)`"
        "\n➥  Untuk membuat file atau folder menjadi arsip."
        "\n\n`.unzip [jalur ke file zip]`"
        "\n➥  Untuk mengekstrak file arsip."
        "\n**Catatan :** Hanya didukung file ZIP, TAR, 7z, dan RAR!"
    }
)
