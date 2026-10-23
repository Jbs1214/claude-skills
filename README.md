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

## 스킬

- `pre-commit-check` — 커밋 직전에 비밀 정보, 대용량·생성 파일, 캐시 혼입을 점검 (점검만 하고 커밋하지 않음). 호출: `/jbs:pre-commit-check`
