"""OpenWeatherMap API로 현재 날씨를 받아 와 '날씨 메모'로 보여 주는 모듈."""
import os
import queue
import threading

import requests
from dotenv import load_dotenv

from memo import Memo

API_URL = "https://api.openweathermap.org/data/2.5/weather"
REFRESH_MS = 10 * 60 * 1000  # 10분마다 자동 갱신
TIMEOUT_SEC = 5
PREFIX = "[날씨] "


def fetch_weather(api_key, city):
    """현재 날씨를 받아 메모에 적을 한 줄 문자열로 돌려준다. 실패해도 예외 대신 이유를 돌려준다."""
    if not api_key:
        return PREFIX + "API 키 없음 (.env 확인)"
    params = {"q": city, "appid": api_key, "units": "metric", "lang": "kr"}
    try:
        res = requests.get(API_URL, params=params, timeout=TIMEOUT_SEC)
    except requests.RequestException:
        return PREFIX + "연결 실패"
    if res.status_code == 401:
        return PREFIX + "키 오류(401)"
    if res.status_code == 404:
        return PREFIX + f"도시 없음: {city}"
    if res.status_code != 200:
        return PREFIX + f"오류({res.status_code})"
    try:
        data = res.json()
        desc = data["weather"][0]["description"]
        temp = round(data["main"]["temp"])
        feels = round(data["main"]["feels_like"])
        name = data.get("name") or city
    except (ValueError, KeyError, IndexError, TypeError):
        return PREFIX + "응답 형식 오류"
    return PREFIX + f"{name} {desc} {temp}°C\n(체감 {feels}°C)"


class WeatherMemo:
    """날씨 메모 하나를 관리한다. 요청은 스레드에서, 화면 갱신은 poll()에서 메인 스레드로."""

    def __init__(self, app):
        load_dotenv()
        self.app = app
        self.api_key = os.getenv("OPENWEATHER_API_KEY", "").strip()
        self.city = os.getenv("WEATHER_CITY", "").strip() or "Seoul"
        self.memo = None
        self.results = queue.Queue()
        self.loading = False
        self.timer = None

    def refresh(self):
        """날씨를 다시 받아 온다. 이미 받아 오는 중이면 무시한다."""
        if self.loading:
            return
        self.loading = True
        if self.memo is not None:
            self.memo.set_text(PREFIX + "불러오는 중...")
        if self.timer is not None:
            self.app.root.after_cancel(self.timer)
        self.timer = self.app.root.after(REFRESH_MS, self._auto_refresh)
        threading.Thread(target=self._worker, daemon=True).start()

    def _auto_refresh(self):
        self.timer = None
        self.refresh()

    def _worker(self):
        self.results.put(fetch_weather(self.api_key, self.city))

    def poll(self):
        """게임 루프에서 매번 호출: 스레드가 넣어 둔 결과가 있으면 메모에 반영한다."""
        try:
            text = self.results.get_nowait()
        except queue.Empty:
            return
        self.loading = False
        if self.memo is None:
            self.memo = self.app.add_memo(text, on_click=self.refresh)
            self.memo.set_outline("#ffffff")
        else:
            self.memo.set_text(text)
