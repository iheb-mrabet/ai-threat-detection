import asyncio
import os

from backend.app.pipeline.queue import raw_queue


LOG_FILE_PATH = os.getenv("LOG_FILE_PATH", "data/access.log")
LOG_TAIL_ENABLED = os.getenv("LOG_TAIL_ENABLED", "false").lower() == "true"


async def tail_log_file():
    if not LOG_TAIL_ENABLED:
        print("[LogTailer] Disabled")
        return

    os.makedirs(os.path.dirname(LOG_FILE_PATH), exist_ok=True)

    if not os.path.exists(LOG_FILE_PATH):
        open(LOG_FILE_PATH, "a").close()

    print(f"[LogTailer] Watching {LOG_FILE_PATH}")

    with open(LOG_FILE_PATH, "r") as f:
        f.seek(0, os.SEEK_END)

        while True:
            line = f.readline()

            if line:
                log_line = line.strip()
                if log_line:
                    await raw_queue.put(log_line)
            else:
                await asyncio.sleep(0.5)


async def start_log_tailer():
    asyncio.create_task(tail_log_file())
