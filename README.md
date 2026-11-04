# 메모 화면보호기 + 날씨 API

기존의 화면보호기에 **OpenWeatherMap API**를 붙였다. 현재 날씨가 적힌 **날씨 메모**(흰 테두리, `[날씨]`로 시작)가 다른 메모들과 함께 돌아다닌다.

아래에서는 이번에 **새로 추가한 코드만** 설명한다. (새 파일 `weather.py`, 그리고 `main.py`·`memo.py`에서 바뀐 부분)

## 실행 방법

API 키는 프로젝트 폴더의 `.env` 파일에 아래 형식으로 넣는다. (`.env`는 `.gitignore`에 들어 있어서 GitHub에 올라가지 않는다.) 따라서 다른 폴더에서 실행하기 위해선 `.env`파일을 하나 직접 만들어야 한다.

```dotenv
OPENWEATHER_API_KEY=발급받은_32자리_키
WEATHER_CITY=Seoul
```
키 관리를 위해 이런 식으로 빼서 쓰는 것 같다.

---

## 1. 시작 흐름

1. **`.env`에서 키 읽기**:
   `__init__`에서 `self.weather = WeatherMemo(self)`(`main.py:39`)로 날씨 메모 관리자를 만든다. `WeatherMemo`는 만들어질 때 `load_dotenv()`(`weather.py:47`)로 `.env` 파일을 읽고, `os.getenv("OPENWEATHER_API_KEY")`로 키를, `os.getenv("WEATHER_CITY")`로 도시를 꺼내 둔다. 도시가 비어 있으면 서울을 기본값으로 쓴다.(`or "Seoul"`)
2. **날씨 요청을 뒤에서 시작**:
   바로 이어서 `self.weather.refresh()`(`main.py:40`)를 부른다. `refresh`는 날씨 요청을 **별도 스레드**에 맡긴다. 스레드는 작업자로 이해하면 될 것 같다.
   ```python
   threading.Thread(target=self._worker, daemon=True).start()   # weather.py:66
   ```
   스레드는 `fetch_weather()`로 인터넷에서 날씨를 받아 오고, 결과 문자열을 `self.results`라는 큐(queue, 선입선출 방식의 자료구조)에 넣어 둔다. 동시에 `root.after`로 10분 뒤 자동 갱신 타이머도 걸어 둔다.
3. **화면은 기다리지 않고 진행**:
   날씨가 오기 전에 `self.show_input(first=True)`로 첫 메모 입력창을 띄우고, `self.game_loop()`로 애니메이션을 시작한다. 날씨 요청은 다른 작업자에게 맡겼기 때문에 인터넷이 느려도 화면이 멈추지 않는다.
4. **날씨가 도착하면 날씨 메모 생성**:
   30밀리초마다 도는 `game_loop`가 맨 처음에 `self.weather.poll()`(`main.py:182`)을 부른다. `poll`은 큐에 결과가 들어왔는지 확인하고, 처음 온 결과라면 날씨 메모를 만든다(`weather.py:75~86`).
   > **왜 큐를 쓰나?** tkinter 화면은 메인 스레드에서만 건드려야 안전하다. 그래서 "날씨 받아 오기"는 스레드가, "화면에 그리기"는 메인 스레드가 하도록 나누고, 그 사이를 큐로 이어 주었다.(자료구조로 소통하기?)

## 2. 상호작용 흐름

1. **W 키로 날씨 새로고침**:
   - `NORMAL` 모드에서 W 키를 누르면 `on_global_key`가 `self.weather.refresh()`를 부른다. N 키처럼 한글 입력 상태의 `"ㅈ"`과 `event.keycode == 87`도 함께 검사한다.
   - `refresh`는 이미 요청 중(`self.loading`이 참)이면 바로 끝나서, W를 여러 번 눌러도 요청이 겹치지 않는다.
   - 요청 중에는 날씨 메모 글이 `"[날씨] 불러오는 중..."`으로 바뀌고, 결과가 오면 `poll`이 `self.memo.set_text(text)`로 새 날씨로 바꾼다.
2. **날씨 메모 클릭**:
   - `add_memo`에 새로 `on_click` 옵션을 만들었다. 이 값이 있으면 클릭했을 때 삭제 확인창 대신 그 함수를 부른다(`(lambda e: self.mode == "NORMAL" and on_click()) if on_click`). 이때 쓰인 `lambda e`함수는 `e`가 이벤트 정보를 받는 자리이며, 정보가 오면 실행하는 함수이다.
   - 날씨 메모는 `on_click=self.refresh`로 만들어졌으므로, 클릭하면 W 키와 똑같이 새로고침된다.
1. **10분마다 자동 갱신**:
   - `refresh` 안에서 `root.after(REFRESH_MS, self._auto_refresh)`로 타이머를 건다. 10분이 지나면 `_auto_refresh`가 다시 `refresh`를 부르고, 그때 또 다음 10분 타이머를 건다.
   - W 키로 수동 갱신하면 기존 타이머를 `after_cancel`로 취소하고 새로 건다.
4. **날씨 글이 바뀔 때 메모 크기 맞추기**:
   - `memo.py`에 `set_text`를 새로 만들었다. 글을 바꾼 뒤, 새 글의 크기에 맞춰 배경 사각형 좌표를 다시 잡고, 화면 밖으로 나가지 않게 `_clamp_into_bounds()`로 보정한다.
1. **날씨를 못 받아 왔을 때**:
   - `fetch_weather`는 문제가 생겨도 에러를 내지 않고 이유를 글로 돌려준다. 그 글이 그대로 날씨 메모에 적히므로 프로그램은 꺼지지 않는다.
     - 키가 없음 → `[날씨] API 키 없음 (.env 확인)`
     - 키가 틀림 (응답 코드 401) → `[날씨] 키 오류(401)`
     - 도시 이름이 틀림 (404) → `[날씨] 도시 없음: ...`
     - 인터넷 끊김 / 5초 안에 응답 없음 → `[날씨] 연결 실패`
6. **입력 중일 때 / 종료할 때**:
   - 메모 입력창이나 삭제 확인창이 떠 있으면 `mode`가 `NORMAL`이 아니므로 W 키도, 날씨 메모 클릭도 아무 일을 하지 않는다.
   - Esc로 `root.destroy()`가 불리면, 요청 스레드는 `daemon=True`로 만들었기 때문에 프로그램과 함께 끝난다.

## 3. 패키지의 역할

`uv add requests python-dotenv`로 두 패키지를 추가했다.

1. **requests — 인터넷에서 날씨 받아 오기**:
   - `fetch_weather` 안에서 OpenWeatherMap 주소로 요청을 보낸다.
     ```python
     params = {"q": city, "appid": api_key, "units": "metric", "lang": "kr"}   # weather.py:21
     res = requests.get(API_URL, params=params, timeout=TIMEOUT_SEC)          # weather.py:23
     ```
     `params`는 주소 뒤에 `?q=Seoul&appid=키&units=metric&lang=kr`처럼 붙는다. `units=metric`은 섭씨, `lang=kr`은 한국어 날씨 설명을 뜻한다.
   - `res.status_code`로 성공(200)인지 401·404 같은 오류인지 확인하고, `res.json()`으로 응답을 파이썬 딕셔너리로 바꿔 도시·날씨·기온을 꺼낸다.
   - `except requests.RequestException`으로 인터넷이 끊긴 경우를 잡는다.
   - **빼면?** `main.py`가 `weather.py`를 불러오는데, `import requests`에서 에러가 나서 **프로그램이 아예 켜지지 않는다.**
1. **python-dotenv — `.env` 파일에서 키 읽기**:
   - `WeatherMemo.__init__`의 `load_dotenv()`(`weather.py:47`)가 `.env` 파일을 읽어서 그 안의 값을 환경 변수로 등록한다. 그래야 바로 아래 `os.getenv("OPENWEATHER_API_KEY")`가 키를 찾을 수 있다.
   - 덕분에 키를 코드에 직접 쓰지 않아도 되고, `.env`만 GitHub에 안 올리면 키가 공개되지 않는다.
   - **빼면?** 마찬가지로 `import`에서 에러가 나서 프로그램이 켜지지 않는다. `load_dotenv()` 한 줄만 지우면 프로그램은 켜지지만 `.env`를 못 읽어서 날씨 메모에 `[날씨] API 키 없음 (.env 확인)`만 뜬다.
