#!/usr/bin/env python3
"""Mirror iQTele .deb/.dylib attachments from a Telegram channel to GitHub Releases.

Requires TELEGRAM_API_ID, TELEGRAM_API_HASH and TELEGRAM_SESSION secrets.
The session is a Telethon StringSession; never commit it to the repository.
"""
import asyncio
import os
import re
import subprocess
import tempfile
from pathlib import Path

from telethon import TelegramClient
from telethon.sessions import StringSession

CHANNEL = os.getenv("IQTELE_CHANNEL", "iQTweakiPA")
MAX_MESSAGES = int(os.getenv("IQTELE_SCAN_LIMIT", "150"))
REPO = os.environ["GITHUB_REPOSITORY"]
API_ID = int(os.environ["TELEGRAM_API_ID"])
API_HASH = os.environ["TELEGRAM_API_HASH"]
SESSION = os.environ["TELEGRAM_SESSION"]

ALLOWED_EXTENSIONS = {".deb", ".dylib"}
SAFE_NAME = re.compile(r"[^A-Za-z0-9._+-]+")


def gh(*args, check=True):
    return subprocess.run(
        ["gh", *args, "--repo", REPO],
        check=check, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )


async def main():
    client = TelegramClient(StringSession(SESSION), API_ID, API_HASH)
    await client.start()
    entity = await client.get_entity(CHANNEL)
    downloaded = 0

    with tempfile.TemporaryDirectory(prefix="iqtele-") as temp:
        temp_path = Path(temp)
        async for message in client.iter_messages(entity, limit=MAX_MESSAGES):
            if not message.document:
                continue
            original_name = None
            for attr in message.document.attributes:
                if getattr(attr, "file_name", None):
                    original_name = attr.file_name
                    break
            if not original_name:
                continue
            ext = Path(original_name).suffix.lower()
            if ext not in ALLOWED_EXTENSIONS:
                continue
            if "iq" not in original_name.lower() and "tele" not in original_name.lower():
                continue

            safe_name = SAFE_NAME.sub("_", Path(original_name).name).strip("._")
            if not safe_name:
                continue
            tag = f"iqtele-source-{message.id}"

            existing = gh("release", "view", tag, check=False)
            if existing.returncode == 0:
                continue

            target = temp_path / safe_name
            await client.download_media(message, file=str(target))
            if not target.is_file() or target.stat().st_size == 0:
                raise RuntimeError(f"Download failed or empty: {safe_name}")

            title = f"iQTele source attachment · Telegram post {message.id}"
            notes = (
                f"Mirrored attachment from https://t.me/{CHANNEL}/{message.id}\n"
                f"Original filename: {original_name}\n"
                "This release is an automated mirror; verify compatibility and licensing before use."
            )
            gh("release", "create", tag, str(target), "--title", title, "--notes", notes, "--prerelease")
            print(f"Published {safe_name} from Telegram post {message.id}")
            downloaded += 1

    await client.disconnect()
    print(f"Finished; published {downloaded} new attachment(s).")


if __name__ == "__main__":
    asyncio.run(main())
