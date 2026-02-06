import requests

API_URL = "http://localhost:8000"

def _headers(token=None):
    h = {"Content-Type": "application/json"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


# ---------- AUTH ----------
def register(data):
    return requests.post(f"{API_URL}/auth/register", json=data).json()

def login(data):
    return requests.post(f"{API_URL}/auth/login", json=data).json()

def profile(token):
    return requests.get(f"{API_URL}/auth/profile", headers=_headers(token)).json()


# ---------- INTERVIEWS ----------
def create_interview(token, data):
    return requests.post(
        f"{API_URL}/interviews",
        json=data,
        headers=_headers(token)
    ).json()

def get_interviews(token):
    return requests.get(
        f"{API_URL}/interviews",
        headers=_headers(token)
    ).json()

def start_interview(token, interview_id):
    return requests.post(
        f"{API_URL}/interviews/{interview_id}/start",
        headers=_headers(token)
    ).json()

def interview_chat(token, interview_id, message):
    return requests.post(
        f"{API_URL}/interviews/{interview_id}/chat",
        json={"role": "user", "message": message},
        headers=_headers(token)
    ).json()

def get_chat(token, interview_id):
    return requests.get(
        f"{API_URL}/interviews/{interview_id}/chat",
        headers=_headers(token)
    ).json()


# ---------- SUPPORT ----------
def support_chat(token, message):
    return requests.post(
        f"{API_URL}/support/chats",
        json={"message": message},
        headers=_headers(token)
    ).json()

def get_support(token):
    return requests.get(
        f"{API_URL}/support/chats",
        headers=_headers(token)
    ).json()
