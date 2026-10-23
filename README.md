# claude-skills

Claude Code 플러그인 마켓플레이스. 범용 스킬 모음.

## 설치

Claude Code에서 아래 명령을 한 줄씩 따로 실행한다.

1. 마켓플레이스 추가

   ```
   /plugin marketplace add Jbs1214/claude-skills
   ```

2. 플러그인 설치

   ```
   /plugin install jbs@jbs-skills
   ```

설치 후 새 세션에서 사용한다.

## 훅

플러그인 설치 시 `git commit` 직전 점검 훅이 함께 켜진다. Python 3이 필요하다.

- 차단: 개인키, 토큰 접두사(`ghp_`, `AKIA` 등), `.env`·`*.pem` 같은 비밀 파일, 충돌 마커, 100MB 초과 파일
- 확인 요청: 키·비밀번호 변수에 값을 대입한 줄, `user:pw@host` 연결 문자열
- 한 번만 건너뛰기: 명령 앞에 `SKIP_PRECOMMIT_CHECK=1` (예: `SKIP_PRECOMMIT_CHECK=1 git commit -m "..."`)

## 스킬

- `pre-commit-check` — 커밋 직전에 비밀 정보, 대용량·생성 파일, 캐시 혼입을 점검 (점검만 하고 커밋하지 않음). 호출: `/jbs:pre-commit-check`
