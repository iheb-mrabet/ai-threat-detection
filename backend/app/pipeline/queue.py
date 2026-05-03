import asyncio

raw_queue = asyncio.Queue()
parsed_queue = asyncio.Queue()
feature_queue = asyncio.Queue()
detection_queue = asyncio.Queue()
