# Credits to Userge for Remove and Rename

import io
import os
import os.path
import shutil
import time
from os.path import dirname, exists, isdir, isfile, join
from shutil import rmtree

from userbot import CMD_HELP
from userbot.events import register
from userbot.utils import humanbytes

MAX_MESSAGE_SIZE_LIMIT = 4095


@register(outgoing=True, pattern=r"^\.ls ?(.*)")
async def lst(event):
    if event.fwd_from:
        return
    cat = event.pattern_match.group(1)
    path = cat if cat else os.getcwd()
    if not exists(path):
        await event.edit(
            f"`Tidak ada direktori atau file seperti itu dengan nama`  **{cat}**, `periksa lagi!`"
        )
        return
    if isdir(path):
        if cat:
            msg = "`Folder dan file di `{}` :\n\n".format(path)
        else:
            msg = "`Folder dan file di direktori saat ini` :\n\n"
        lists = os.listdir(path)
        files = ""
        folders = ""
        for contents in sorted(lists):
            catpath = path + "/" + contents
            if not isdir(catpath):
                size = os.stat(catpath).st_size
                if contents.endswith((".mp3", ".flac", ".wav", ".m4a")):
                    files += "🎵 "
                elif contents.endswith((".opus")):
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
                elif contents.endswith((".py")):
                    files += "🐍 "
                else:
                    files += "📄 "
                files += f"`{contents}`  - __{humanbytes(size)}__\n"
            else:
                folders += f"📁 `{contents}`\n"
        msg = msg + folders + files if files or folders else msg + "__direktori kosong__"
    else:
        size = os.stat(path).st_size
        msg = "The details of given file :\n\n"
        if path.endswith((".mp3", ".flac", ".wav", ".m4a")):
            mode = "🎵 "
        elif path.endswith((".opus")):
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
        elif path.endswith((".py")):
            mode = "🐍 "
        else:
            mode = "📄 "
        time.ctime(os.path.getctime(path))
        time2 = time.ctime(os.path.getmtime(path))
        time3 = time.ctime(os.path.getatime(path))
        msg += f"**Lokasi** : `{path}`\n"
        msg += f"**Ikon** : `{mode}`\n"
        msg += f"**Ukuran** : `{humanbytes(size)}`\n"
        msg += f"**Waktu terakhir diubah** : `{time2}`\n"
        msg += f"**Waktu terakhir diakses** : `{time3}`"

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


@register(outgoing=True, pattern=r"^\.rm ?(.*)")
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
    await event.edit(f"**{cat}**  `dihapus!`")


@register(outgoing=True, pattern=r"^\.rn ([^|]+)\|([^|]+)")
async def rname(event):
    """Renaming Directory/File"""
    cat = str(event.pattern_match.group(1)).strip()
    new_name = str(event.pattern_match.group(2)).strip()
    if not exists(cat):
        await event.edit(f"`Jalur file` : **{cat}**  `tidak ada!`")
        return
    new_path = join(dirname(cat), new_name)
    shutil.move(cat, new_path)
    await event.edit(f"`Nama diganti dari`  **{cat}**  `menjadi`  **{new_path}**")


CMD_HELP.update(
    {
        "file": "`.ls [direktori]`"
        "\n➥  Dapatkan daftar file di dalam direktori."
        "\n\n`.rm [direktori/file]`"
        "\n➥  Hapus file atau direktori."
        "\n\n`.rn [direktori/file] | [nama baru]`"
        "\n➥  Mengubah nama file atau direktori."
    }
)
