# Amazon Suspicious Error-Deal Alert Bot

Python 기반 Amazon 오류딜 의심 알림 봇입니다. 이 프로젝트의 목적은 자동구매가 아니라, 관심 카테고리의 가격 이상 징후를 사람이 직접 확인할 수 있도록 Telegram으로 알림을 보내는 것입니다.

> 현재 MVP 단계에서는 **mock 데이터만 사용**합니다. 실제 Amazon 페이지 크롤링, 로그인 자동화, 장바구니 테스트, 쿠폰 클릭, CAPTCHA 우회, 자동구매 기능은 만들지 않습니다.

## 핵심 원칙

- 자동구매 기능을 만들지 않습니다.
- Amazon 로그인 자동화 기능을 만들지 않습니다.
- 장바구니 자동 테스트 또는 add-to-cart 자동화를 만들지 않습니다.
- 쿠폰 자동 클릭 기능을 만들지 않습니다.
- CAPTCHA 우회, 프록시 회피, 봇 탐지 우회 기능을 만들지 않습니다.
- 대량 크롤링 또는 서비스 약관을 침해할 수 있는 수집 방식을 만들지 않습니다.
- 첫 MVP는 mock 데이터로만 동작합니다.
- 실제 데이터 소스는 추후 `Keepa API` → `Slickdeals RSS` → `Reddit API` 순서로 추가합니다.
- 알림은 Telegram Bot으로 보냅니다.
- SQLite에 알림 이력을 저장해 중복 알림을 방지합니다.
- 환경변수는 `.env`로 관리하고, 실제 API 키나 토큰은 코드에 하드코딩하지 않습니다.

## 관심 카테고리

- 가전제품
- 컴퓨터 부품
- 컴퓨터 주변기기

## 관심 키워드

초기 필터링 및 스코어링 대상 키워드는 다음과 같습니다.

```text
monitor, gaming monitor, OLED monitor, SSD, NVMe, RAM, DDR4, DDR5,
keyboard, mechanical keyboard, mouse, wireless mouse, headset,
docking station, USB hub, robot vacuum, air purifier, coffee machine,
TV, soundbar
```

## MVP 목표

초기 버전은 다음 기능을 목표로 합니다.

1. Mock deal 데이터 로드.
2. 관심 카테고리 및 키워드 기반 필터링.
3. 단순한 오류딜 의심 스코어링.
4. SQLite 기반 알림 이력 저장.
5. 이미 알림을 보낸 deal 중복 방지.
6. Telegram Bot 알림 발송.
7. `.env` 기반 설정 관리.

## 제외 범위

MVP뿐 아니라 장기적으로도 다음 기능은 이 프로젝트 범위에서 제외합니다.

- 자동구매.
- 자동 체크아웃.
- Amazon 계정 로그인 자동화.
- 장바구니 삽입 또는 장바구니 가격 검증 자동화.
- 쿠폰 자동 클릭.
- CAPTCHA 우회.
- 대량 크롤링.
- 우회 목적의 프록시/세션/브라우저 자동화.

## 향후 데이터 소스 계획

실제 데이터 연동은 아래 순서로 진행합니다.

### 1. Keepa API

- 가격 이력, 할인율, 카테고리 정보를 활용할 수 있는 1차 후보입니다.
- API 키는 `.env`로만 주입합니다.

### 2. Slickdeals RSS

- 공개 RSS 기반으로 deal 후보를 수집하는 2차 후보입니다.
- RSS 파서 모듈은 Keepa adapter와 분리합니다.

### 3. Reddit API

- deal 관련 subreddit의 게시글을 보조 신호로 활용하는 3차 후보입니다.
- Reddit API credential 역시 `.env`로만 주입합니다.

## 현재 MVP 구조

현재 구현된 파일 구조는 다음과 같습니다. 실제 데이터 소스 adapter는 아직 추가하지 않았고, mock 데이터 소스만 사용합니다.

```text
amazon-deal-alert-bot/
├── main.py
├── requirements.txt
├── .env.example
├── AGENTS.md
├── README.md
└── src/
    └── deal_alert_bot/
        ├── __init__.py
        ├── config.py          # .env 및 환경변수 로딩
        ├── models.py          # Deal, ScoreResult 도메인 모델
        ├── scoring.py         # 오류딜 의심 점수 계산
        ├── storage.py         # SQLite 알림 이력 저장 및 중복 방지
        ├── notifier.py        # Telegram 알림 또는 콘솔 fallback
        └── sources/
            ├── __init__.py
            └── mock.py        # MVP용 mock 데이터 소스
```

## 환경변수 계획

구현 시 다음 환경변수를 사용할 예정입니다. 실제 값은 `.env`에만 저장하고 커밋하지 않습니다.

```env
TELEGRAM_BOT_TOKEN=replace-with-your-telegram-bot-token
TELEGRAM_CHAT_ID=replace-with-your-chat-id
SQLITE_DB_PATH=./data/alerts.sqlite3
ALERT_SCORE_THRESHOLD=70
LOG_LEVEL=INFO

# Future integrations
KEEPA_API_KEY=replace-later
REDDIT_CLIENT_ID=replace-later
REDDIT_CLIENT_SECRET=replace-later
REDDIT_USER_AGENT=amazon-deal-alert-bot/0.1
```

## 빠른 시작

```bash
pip install -r requirements.txt
cp .env.example .env  # 선택 사항: Telegram 설정을 넣고 싶을 때만 사용
python main.py
python main.py  # 두 번째 실행에서는 동일 deal_id 중복 알림이 차단됩니다
```

Telegram 환경변수가 비어 있으면 실제 Telegram 전송을 시도하지 않고 콘솔 알림으로 fallback합니다. SQLite 알림 이력은 기본적으로 `./data/alerts.sqlite3`에 저장됩니다.

## Telegram Bot 설정

Telegram 알림은 선택 사항입니다. 토큰이나 chat_id가 없으면 MVP는 실제 Telegram API 호출을 하지 않고 콘솔 fallback으로 알림 메시지를 출력합니다.

1. Telegram에서 `@BotFather`를 열고 `/newbot` 명령으로 새 bot을 만듭니다.
2. BotFather가 발급한 bot token을 복사합니다. 이 값은 비밀 정보이므로 코드, README, 이슈, PR, GitHub Actions 로그에 노출하지 않습니다.
3. 생성한 bot에게 Telegram 앱에서 직접 메시지를 1회 보냅니다.
4. `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`를 브라우저나 안전한 로컬 터미널에서 호출해 `chat.id` 값을 확인합니다. 운영 토큰은 공유하지 말고, 확인 후 터미널 기록 관리에도 주의합니다.
5. 로컬 `.env` 파일에 아래처럼 placeholder가 아닌 실제 값을 설정합니다. `.env`는 절대 GitHub에 커밋하지 않습니다.

```env
TELEGRAM_BOT_TOKEN=replace-with-your-real-bot-token
TELEGRAM_CHAT_ID=replace-with-your-real-chat-id
```

토큰 없이 실행하거나 `TELEGRAM_BOT_TOKEN` 또는 `TELEGRAM_CHAT_ID` 중 하나라도 비어 있으면 다음과 같이 콘솔 fallback으로 동작합니다.

```text
CONSOLE ALERT FALLBACK (Telegram is not configured)
```

## 테스트 및 CI

이 프로젝트의 테스트는 현재 MVP 안전 범위에 맞춰 **mock 데이터만** 사용합니다. 실제 Amazon, Keepa, Slickdeals, Reddit 연동이나 자동구매/로그인/장바구니/쿠폰/CAPTCHA 우회 동작은 테스트에도 포함하지 않습니다.

### 로컬 테스트 실행

```bash
python -m py_compile main.py src/deal_alert_bot/*.py src/deal_alert_bot/sources/*.py
pytest
python main.py
```

- `tests/test_scoring.py`: 평균가 대비 할인율, 관심 키워드, 오류딜 의심 signal, `ScoreResult` 내용을 검증합니다.
- `tests/test_storage.py`: 임시 디렉터리의 SQLite 파일로 최초 알림 가능 여부와 중복 알림 차단을 검증하며, 실제 `data/alerts.sqlite3`는 사용하지 않습니다.
- `tests/test_config.py`: 환경변수 기본값, `ALERT_SCORE_THRESHOLD` 정수 파싱, `SQLITE_DB_PATH` override, `python-dotenv` 미설치 fallback을 검증합니다.
- `tests/test_notifier.py`: 알림 메시지 포맷, 사람이 직접 확인해야 할 항목, Telegram 미설정 콘솔 fallback, Telegram 전송 실패 fallback을 mock `requests.post`로 검증합니다.

### GitHub Actions

`.github/workflows/test.yml` 워크플로는 `push`와 `pull_request`에서 실행되며 Python 3.11 및 3.12 조합으로 다음을 수행합니다.

1. `pip install -r requirements.txt`
2. `pytest`
3. Telegram 토큰 없이 콘솔 fallback으로 `python main.py` mock-only smoke test

### GitHub Actions에서 Telegram 수동 테스트

`.github/workflows/telegram-smoke-test.yml` 워크플로는 `workflow_dispatch`로만 실행되는 수동 smoke test입니다. `push` 또는 `pull_request`에서는 자동 실행되지 않습니다. 이 workflow는 기존 MVP와 동일하게 **mock 데이터만 사용**하며, 자동구매, Amazon 접근, 로그인 자동화, 장바구니 테스트, 쿠폰 클릭, CAPTCHA 우회, 크롤링을 수행하지 않습니다.

실제 Telegram 발송을 테스트하려면 GitHub 저장소의 `Settings → Secrets and variables → Actions`에서 아래 GitHub Secrets를 등록합니다.

- `TELEGRAM_BOT_TOKEN`: Telegram BotFather에서 발급받은 bot token
- `TELEGRAM_CHAT_ID`: 알림을 받을 Telegram chat ID

수동 실행 방법은 다음과 같습니다.

1. GitHub 저장소의 `Actions` 탭을 엽니다.
2. `Telegram Smoke Test` workflow를 선택합니다.
3. `Run workflow` 버튼을 클릭합니다.
4. 실행 로그에서 mock-only 알림 처리 결과를 확인합니다.

토큰과 chat ID는 비밀 정보이므로 코드, README, 이슈, PR, GitHub Actions 로그에 출력하지 마세요. workflow는 `TELEGRAM_BOT_TOKEN`과 `TELEGRAM_CHAT_ID`를 GitHub Secrets에서만 읽습니다. 두 secret 중 하나라도 비어 있으면 실제 Telegram API 호출을 하지 않고 콘솔 fallback으로 동작할 수 있습니다.

## 로컬 개발 메모

애플리케이션 MVP 코드가 추가되었습니다. 로컬 실행 시 다음 원칙을 따릅니다.

- `.env`는 git에 커밋하지 않습니다.
- `.env.example`에는 placeholder 값만 둡니다.
- SQLite DB 파일은 로컬 런타임 산출물로 취급합니다.
- Telegram 알림 전송 로직은 테스트 가능하도록 분리합니다.
- mock 데이터 기반 테스트를 먼저 작성합니다.

## 라이선스

아직 라이선스가 정해지지 않았습니다.
