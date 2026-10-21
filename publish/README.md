## 매주 기본 운영

- 일요일 18:00 SGT: 이 Codex 채팅의 예약 작업이 최신 옵션 자료·한국어 글·영어 초안·한영 원페이저를 준비하고 사이트에 반영합니다.
- 월요일 09:00 SGT: 새 회차 준비 기록을 확인한 뒤 GitHub Actions `draft`로 소유자 개인 채팅에 검토본을 보냅니다.
- 개인 봇: @wenojadaniel_options_bot. 공지방 자동 게시와 X 자동 게시는 하지 않습니다.
- 주말 작업은 `publish/weekly-ready.json`에 준비 시각·커버 기간·전달 날짜·회차 id를 남깁니다. 월요일에는 오늘 회차 및 72시간 이내 준비 여부를 확인하며, 미완성·만료 자료를 보내지 않습니다.
- 예약 콘텐츠 생성은 로컬 Codex 작업이므로 이 Mac과 Codex가 실행 중이어야 합니다. GitHub Actions 전송은 클라우드에서 실행됩니다. 준비 자동화가 실행되지 않으면 최신 콘텐츠도 생성되지 않습니다.
- 첫 준비: 2026-10-25 일요일, 첫 정기 전달: 2026-10-26 월요일. 사이트에는 앞으로 8주 계획을 표시합니다. 달력 수정이 Codex 예약 시각을 바꾸지는 않습니다.

## 현재 운영 방식: 개인 채팅 검토 우선

공지방 자동 게시를 중지했습니다. main에 push해도 preview만 실행됩니다.

Actions의 `draft`는 봇에게 `/start`를 보낸 **공지방 소유자 계정**의 개인 채팅을 확인한 뒤 이미지와 원고를 보냅니다. 봇의 받은 메시지를 수정하는 기능은 없으므로 글을 복사·편집한 뒤 이 채팅에 붙여넣거나 봇에게 새 메시지로 보내 검토할 수 있습니다. 자동 응답·편집본 수집은 아직 동작하지 않습니다.

개인 정보·chat ID는 로그나 저장소에 저장하지 않습니다. 공지방 소유자 ID와 개인 대화를 직접 확인하므로 매주 /start를 반복할 필요가 없습니다. getUpdates나 웹훅 변경은 사용하지 않습니다. 처음 한 번 /start가 필요하고 봇을 차단하면 전송할 수 없습니다.

공지방 게시에는 회차별 승인과 명시적인 `send` 실행이 필요합니다. 아래 기존 안내의 push 자동 게시 설명은 현재 적용되지 않습니다.

# 텔레그램 공지방 자동 게시

이 기능은 공지방에 **한국어 원페이저 사진 → 전체 글**을 차례대로 올립니다. 사진 캡션 길이 제한 때문에 전체 글은 별도 메시지로 게시합니다. 영상 자동 게시는 현재 포함하지 않습니다.

## 처음 한 번 연결

1. 텔레그램 [@BotFather](https://t.me/BotFather)에서 `/newbot`으로 봇을 만듭니다. 이미 있는 봇도 사용할 수 있습니다.
2. **본인이 만든 공지방**의 관리 메뉴에서 봇을 관리자로 추가하고 **메시지 게시** 권한을 켭니다.
공지방 기본 대상은 `@wenojadaniel`로 GitHub Actions Variable `TELEGRAM_CHAT_ID`에 설정되어 있습니다. 같은 이름의 Secret이 있으면 Secret을 우선합니다.

3. [GitHub Actions Secrets](https://github.com/DigitalDanie1/optioncontent/settings/secrets/actions)에 봇 토큰을 추가합니다. 공지방은 이미 Variable에 설정되어 있으며 변경할 때만 chat ID를 등록하면 됩니다.
   - `TELEGRAM_BOT_TOKEN`: BotFather가 발급한 토큰.
   - `TELEGRAM_CHAT_ID`: 공개 공지방이면 `@채널아이디`, 비공개 공지방이면 `-100...` 형태의 숫자 ID.
4. 비공개 공지방의 초대 링크는 chat ID가 아닙니다. 봇을 추가한 뒤 공지방에 새 글을 올리고, 로컬에서 Bot API `getUpdates` 응답의 `channel_post.chat.id`를 확인할 수 있습니다. 다른 서비스가 웹훅/업데이트를 사용 중인 봇이면 수집 방식이 충돌할 수 있으니 별도 봇을 권장합니다. 토큰이 들어가는 API 주소는 브라우저·채팅에 붙이지 마세요.
5. [Actions](https://github.com/DigitalDanie1/optioncontent/actions/workflows/telegram-publish.yml) → **Run workflow → check**로 연결을 확인합니다. `check`는 메시지를 보내지 않습니다.

토큰은 GitHub Secrets에만 저장합니다. 정적 웹사이트나 소스 코드에 입력하지 마세요. `preview`는 토큰 없이도 작동합니다.

## 회차 게시

1. 원페이저와 한국어 글을 검토해 저장소에 반영합니다. 사이트 브라우저에서 수정한 초안은 자동으로 서버에 전달되지 않습니다.
2. `publish/telegram.json`의 `id`를 새 회차의 고유 값으로 바꾸고 `text`, `photo`, `caption` 경로·내용을 지정합니다.
3. 자료 기준일을 확인해 `validUntil`을 게시 가능한 만료 시각으로 설정합니다. `approved: true`는 **이 회차를 공지방에 게시하라는 승인**입니다.
4. 설정 파일을 main에 push하면 미리보기만 실행합니다. 확정 후 공지방 게시에는 Actions에서 `send`를 선택합니다.

현재 W42는 과거 자료이므로 **approved: false**, 만료 상태로 둡니다. 최신 회차로 갱신하기 전에는 발송하지 않습니다. 매주 고정 시각 예약은 아직 설정하지 않았습니다. 요일·시간이 정해지면 workflow에 예약 트리거를 추가할 수 있습니다. 수집·작성·이미지 갱신은 이 게시 도구와 별개입니다.

## 중복과 실패

- `telegram-state` 브랜치에 회차·채널별 전송 이력을 저장합니다. 채널은 해시로 식별하며 토큰·글·공지방 이름은 저장하지 않습니다. 성공한 사진이나 글은 같은 회차 재실행 시 건너뜁니다.
- 각 요청 전에 `sending` 기록을 저장합니다. 네트워크가 끊겨 성공 여부가 모호하면 자동 재발송하지 않습니다. 공지방을 확인한 후 해당 회차의 receipt를 수동으로 정리해야 합니다. 이미 게시됐다면 `sent`와 실제 `message_id`를 기록하고, 게시되지 않은 것을 확인했다면 해당 step을 삭제한 뒤 재실행합니다.
- 실제 전송은 Telegram과 Git 사이에서 원자적으로 처리되지 않습니다. 실패 시 사진만 게시되고 글이 누락될 수 있습니다. 같은 회차로 재실행하면 성공한 단계는 건너뛰고, 불명확한 단계는 정지합니다.
- 이미 보낸 회차의 내용을 바꾸면 차단합니다. 이 도구는 기존 메시지 편집·삭제를 하지 않습니다.

검증: `node --test scripts/telegram-publish.test.mjs` (모의 API, 실제 발송 없음).

공식 참고: [BotFather](https://core.telegram.org/bots/features#botfather), [Telegram Bot API](https://core.telegram.org/bots/api).
