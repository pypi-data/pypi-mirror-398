# db.py: db연결 담당
import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()


def get_supabase():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

    if not url or not key:
        raise ValueError("❌ .env 파일에 SUPABASE_URL 또는 SUPABASE_KEY가 없습니다!")

    return create_client(url, key)
