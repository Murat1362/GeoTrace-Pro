import streamlit as st
import requests
from datetime import datetime, timezone


def log_visit():
    """Ziyarət vaxtını Supabase-də qeydə alır."""

    try:
        url = st.secrets["SUPABASE_URL"].rstrip("/")
        key = st.secrets["SUPABASE_SECRET_KEY"]

        response = requests.post(
            f"{url}/rest/v1/visitor_logs",
            headers={
                "apikey": key,
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
                "Prefer": "return=minimal",
            },
            json={
                "visited_at": datetime.now(timezone.utc).isoformat(),
                "page": "location_app",
            },
            timeout=10,
        )

        return response.status_code in (200, 201, 204)

    except Exception:
        return False
