import os
from dotenv import load_dotenv

def load_env():
    load_dotenv()
    env = {
        "FEED_URL": os.getenv("FEED_URL"),
        "WEB_API_ID": os.getenv("WEB_API_ID"),
        "WEB_API_KEY": os.getenv("WEB_API_KEY"),
        "WEB_API_SECRET": os.getenv("WEB_API_SECRET"),
    }
    missing = [k for k, v in env.items() if not v]
    if missing:
        raise RuntimeError(f"Не найдены в .env: {', '.join(missing)}")
    return env
