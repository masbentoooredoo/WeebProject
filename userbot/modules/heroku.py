# Copyright (C) 2020 Adek Maulana.
# All rights reserved.
"""
   fallback for main userbot
"""
import os
import asyncio
import requests
import math
import codecs
import shutil

from operator import itemgetter

from userbot import heroku, fallback, HEROKU_APP_NAME, HEROKU_API_KEY, HEROKU_API_KEY_FALLBACK
from userbot.events import register


heroku_api = "https://api.heroku.com"
useragent = (
    "Mozilla/5.0 (Linux; Android 10; SM-G975F) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/81.0.4044.117 Mobile Safari/537.36"
)

@register(outgoing=True, pattern=r"^\.dyno on(?: |$)(.*)")
async def dyno_manage(dyno):
    await dyno.edit("`Mengirim informasi...`")
    exe = dyno.pattern_match.group(1)
    if not exe:
        await dyno.edit(f"`App Heroku tidak ditemukan.\nCoba ketik` `“.dyno on [nama app Anda]”`")
        return
    else:
        HEROKU_APP_NAME = exe
        app = heroku.app(HEROKU_APP_NAME)
        try:
            Dyno = app.dynos()[0]
        except IndexError:
            app.scale_formation_process("worker", 1)
            text = f"`Memulai`  ⬢**{HEROKU_APP_NAME}**"
            sleep = 1
            dot = "."
            await dyno.edit(text)
            while (sleep <= 24):
                await dyno.edit(text + f"`{dot}`")
                await asyncio.sleep(1)
                if len(dot) == 3:
                    dot = "."
                else:
                    dot += "."
                sleep += 1
            state = Dyno.state
            if state == "up":
                await dyno.respond(f"⬢**{HEROKU_APP_NAME}**  `up...`")
            elif state == "crashed":
                await dyno.respond(f"⬢**{HEROKU_APP_NAME}**  `ngadat...`")
            await dyno.delete()
            return True
        else:
            await dyno.edit(f"⬢**{HEROKU_APP_NAME}**  `sudah aktif...`")
            return False


@register(outgoing=True,
           pattern=r"^\.dyno restart(?: |$)(.*)")
async def dyno_manage(dyno):
    await dyno.edit("`Mengirim informasi...`")
    exe = dyno.pattern_match.group(1)
    if not exe:
        await dyno.edit(f"`App Heroku tidak ditemukan.\nCoba ketik` `“.dyno restart [nama app Anda]”`")
        return
    else:
        HEROKU_APP_NAME = exe
        app = heroku.app(HEROKU_APP_NAME)
        try:
            Dyno = app.dynos()[0]
        except IndexError:
            """
               Tell user if main app dyno is not on
            """
            await dyno.respond(f"⬢**{HEROKU_APP_NAME}**  `tidak aktif...`")
            return False
        else:
            text = f"`Memulai ulang`  ⬢**{HEROKU_APP_NAME}**"
            Dyno.restart()
            sleep = 1
            dot = "."
            await dyno.edit(text)
            while (sleep <= 24):
                await dyno.edit(text + f"`{dot}`")
                await asyncio.sleep(1)
                if len(dot) == 3:
                    dot = "."
                else:
                    dot += "."
                sleep += 1
            state = Dyno.state
            if state == "up":
                await dyno.respond(f"⬢**{HEROKU_APP_NAME}**  `dimulai ulang...`")
            elif state == "crashed":
                await dyno.respond(f"⬢**{HEROKU_APP_NAME}**  `ngadat...`")
            await dyno.delete()
            return True


@register(outgoing=True,
           pattern=r"^\.dyno off(?: |$)(.*)")
async def dyno_manage(dyno):
    await dyno.edit("`Mengirim informasi...`")
    exe = dyno.pattern_match.group(1)
    if not exe:
        await dyno.edit(f"`App Heroku tidak ditemukan.\nCoba ketik` `“.dyno off [nama app Anda]”`")
        return
    else:
        HEROKU_APP_NAME = exe
        app = heroku.app(HEROKU_APP_NAME)
        """
           Complete shutdown
        """
        app.scale_formation_process("worker", 0)
        text = f"`Menonaktifkan`  ⬢**{HEROKU_APP_NAME}**"
        sleep = 1
        dot = "."
        while (sleep <= 3):
            await dyno.edit(text + f"`{dot}`")
            await asyncio.sleep(1)
            dot += "."
            sleep += 1
        await dyno.respond(f"⬢**{HEROKU_APP_NAME}**  `dinonaktifkan...`")
        await dyno.delete()
        return True


@register(outgoing=True,
          pattern=(
              "^.dyno "
              "(usage|deploy|cancel deploy"
              "|cancel build|get log|help|update)(?: (.*)|$)")
          )
async def dyno_manage(dyno):
    await dyno.edit("`Mengirim informasi...`")
    exe = dyno.pattern_match.group(1)
    app = heroku.app(HEROKU_APP_NAME)
    if exe == "usage":
        """
           Get your account Dyno Usage
        """
        await dyno.edit("`Mendapatkan informasi...`")
        headers = {
            "User-Agent": useragent,
            "Accept": "application/vnd.heroku+json; version=3.account-quotas",
        }
        user_id = []
        user_id.append(heroku.account().id)
        if fallback is not None:
            user_id.append(fallback.account().id)
        msg = ""
        for aydi in user_id:
            if fallback is not None and fallback.account().id == aydi:
                headers["Authorization"] = f"Bearer {HEROKU_API_KEY_FALLBACK}"
            else:
                headers["Authorization"] = f"Bearer {HEROKU_API_KEY}"
            path = "/accounts/" + aydi + "/actions/get-quota"
            r = requests.get(heroku_api + path, headers=headers)
            if r.status_code != 200:
                msg += f"`tidak bisa mendapatkan informasi {aydi}...`\n\n"
                continue
            result = r.json()
            quota = result["account_quota"]
            quota_used = result["quota_used"]

            """
               Quota Limit Left and Used Quota
            """
            remaining_quota = quota - quota_used
            percentage = math.floor(remaining_quota / quota * 100)
            minutes_remaining = remaining_quota / 60
            hours = math.floor(minutes_remaining / 60)
            minutes = math.floor(minutes_remaining % 60)

            """
               Used Quota per/App
            """
            Apps = result["apps"]
            """Sort from larger usage to lower usage"""
            Apps = sorted(Apps, key=itemgetter("quota_used"), reverse=True)
            if fallback is not None and fallback.account().id == aydi:
                apps = fallback.apps()
                msg += "**Penggunaan dyno akun fallback :**\n\n"
            else:
                apps = heroku.apps()
                msg += "**Penggunaan dyno akun utama :**\n\n"
            if len(Apps) == 0:
                for App in apps:
                    msg += (
                        f"**->**  `Penggunaan dyno untuk`  **{App.name}** :\n"
                        f"     •  **0 jam**,  **0 menit**  "
                        f"**–**  **0%**\n\n"
                    )
            else:
                for App in Apps:
                    AppName = '__~~Deleted or transferred app~~__'
                    ID = App.get("app_uuid")

                    AppQuota = App.get("quota_used")
                    AppQuotaUsed = AppQuota / 60
                    AppPercentage = math.floor(AppQuota * 100 / quota)
                    AppHours = math.floor(AppQuotaUsed / 60)
                    AppMinutes = math.floor(AppQuotaUsed % 60)

                    for name in apps:
                        if ID == name.id:
                            AppName = f"**{name.name}**"
                            break

                    msg += (
                        f"**->**  `Penggunaan dyno untuk`  **{AppName}** :\n"
                        f"     •  **{AppHours} jam**,  **{AppMinutes} menit**  "
                        f"**–**  **{AppPercentage}%**\n\n"
                    )

            msg = (
                f"{msg}"
                " **->**  `Sisa dyno bulan ini` :\n"
                f"     •  **{hours} jam**,  **{minutes} menit**  "
                f"**–**  **{percentage}%**\n\n"
            )
        await dyno.edit(msg)
        return
    if exe == "deploy":
        home = os.getcwd()
        if not os.path.isdir("deploy"):
            os.mkdir("deploy")
        txt = (
            "`Oops... deploy userbot tidak bisa dilanjutkan, "
            "terjadi beberapa masalah.`\n\n**JEJAK LOG :**\n"
        )
        heroku_app = None
        apps = heroku.apps()
        for app in apps:
            if app.name == HEROKU_APP_NAME:
                heroku_app = app
                break
        if heroku_app is None:
            await dyno.edit(
                f"{txt}\n"
                "`Kredensial Heroku tidak valid untuk men-deploy dyno userbot.`"
            )
            return
        await dyno.edit(
            "`[HEROKU - UTAMA]"\n'
            "`Deploy userbot dalam proses, tunggu sebentar...`"
        )
        os.chdir("deploy")
        repo = Repo.init()
        origin = repo.create_remote("deploy", UPSTREAM_REPO_URL)
        try:
            origin.pull(MAIN_REPO_BRANCH)
        except GitCommandError:
            await dyno.edit(
                f"{txt}\n"
                f"`Nama branch`  **{MAIN_REPO_BRANCH}**  `tidak valid.`"
            )
            os.remove("deploy")
            return
        heroku_git_url = heroku_app.git_url.replace(
            "https://", "https://api:" + HEROKU_API_KEY + "@")
        remote = repo.create_remote("heroku", heroku_git_url)
        remote.push(refspec="HEAD:refs/heads/master", force=True)
        await dyno.edit("`Berhasil diperbarui!\n"
                        "Mulai ulang, tunggu sebentar...`")
        os.chdir(home)
        shutil.rmtree("deploy")
        return
    elif exe == "cancel deploy" or exe == "cancel build":
        """
           Only cancel 1 recent builds from activity if build.id not supplied
        """
        build_id = dyno.pattern_match.group(2)
        if build_id is None:
            build = app.builds(order_by="created_at", sort="desc")[0]
        else:
            build = app.builds().get(build_id)
            if build is None:
                await dyno.edit(
                    f"`Tidak ada build.id seperti itu` :\n**{build_id}**")
                return False
        if build.status != "pending":
            await dyno.edit("`Nol build aktif untuk dibatalkan...`")
            return False
        headers = {
            "User-Agent": useragent,
            "Authorization": f"Bearer {HEROKU_API_KEY}",
            "Accept": "application/vnd.heroku+json; version=3.cancel-build",
        }
        path = "/apps/" + build.app.id + "/builds/" + build.id
        r = requests.delete(heroku_api + path, headers=headers)
        text = f"`Menghentikan build`  ⬢**{build.app.name}**"
        await dyno.edit(text)
        sleep = 1
        dot = "."
        await asyncio.sleep(2)
        while (sleep <= 3):
            await dyno.edit(text + f"`{dot}`")
            await asyncio.sleep(1)
            dot += "."
            sleep += 1
        await dyno.respond(
            "`[HEROKU]`\n"
            f"Build: ⬢**{build.app.name}**  `dihentikan...`")
        await dyno.delete()
        return True
    elif exe == "get log":
        await dyno.edit("`Getting information...`")
        with open("logs.txt", "w") as log:
            log.write(app.get_log())
        fd = codecs.open("logs.txt", "r", encoding="utf-8")
        data = fd.read()
        key = (requests.post("https://nekobin.com/api/documents",
                             json={"content": data}) .json() .get("result") .get("key"))
        url = f"https://nekobin.com/raw/{key}"
        await dyno.edit(f"`Di sini log heroku dicatat :`\n\nDitempel ke : [Nekobin]({url})")
        os.remove('logs.txt')
        return True
    elif exe == "help":
        await dyno.edit(
            "`.dyno usage`"
            "\n➥  Memeriksa penggunaan dyno bot Anda."
            "\nJika salah satu penggunaan bot Anda kosong, itu tidak akan ditulis dalam keluaran."
            "\n\n`.dyno on [nama app]`"
            "\n➥  Menyalakan dyno bot Anda."
            "\n\n`.dyno restart [nama app]`"
            "\n➥  Memulai ulang dyno bot Anda."
            "\n\n`.dyno off [nama app]`"
            "\n➥  Menonaktifkan dyno sepenuhnya."
            "\n\n`.dyno cancel deploy` / `.dyno cancel build`"
            "\n➥  Batalkan penerapan dari bot utama, "
            "berikan build.id untuk menentukan build yang akan dibatalkan."
            "\n\n`.dyno get log`"
            "\n➥  Dapatkan log dyno terbaru bot Anda."
            "\n\n`.dyno help`"
            "\n➥  Menampilkan bantuan."
        )
        return True
    elif exe == "update":
        await dyno.edit(
            "`.updatef`"
            "\n➥  Periksa fallback jika ada pembaruan."
            "\n\n`.updatef deploy`"
            "\n➥  Jika ada pembaruan, Anda dapat menerapkannya ke fallback."
            "\n\n`.updatef now`"
            "\n➥  Jika ada pembaruan, Anda dapat menerapkannya ke fallback."
            "\n\n"
            "**FAQ :**\n"
            "`Q` : Apa bedanya  `.updatef now`  dan   `.updatef deploy`?\n"
            "`A` : `.updatef now`  untuk memperbarui fallback Anda tanpa menerapkan, "
            "tetapi bot akan kembali ke status terakhir yang berhasil diterapkan jika fallback dimulai ulang.\n"
            "`.updatef deploy`  sama seperti  `.updatef now`  tetapi jika fallback dimulai ulang, bot tidak akan kembali dan tetap di status terakhir/terbaru."
        )
        return True
