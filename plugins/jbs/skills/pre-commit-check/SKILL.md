---
name: pre-commit-check
description: 커밋 직전에 스테이징된 변경에 비밀 정보, 대용량·생성 파일, 캐시, 의도치 않은 파일이 섞였는지 점검한다. "커밋 전 점검", "커밋해도 돼?", "올리기 전에 확인", "/pre-commit-check" 요청이나 사용자가 커밋·push를 요청해 실행하기 직전에 사용. 커밋 자체는 하지 않는다.
---

# pre-commit-check

커밋 전에 **올라가면 되돌리기 어려운 것**을 걸러낸다. 점검만 하고, 커밋·push·파일 삭제는 하지 않는다.

## 1. 대상 파악

```
git status --short
git diff --cached --stat
```

- 점검 대상은 **스테이징된 파일**(`git diff --cached`). 스테이징이 비어 있으면 그 사실을 알리고, 커밋 예정 파일을 사용자에게 확인한다.
- 추적되지 않은 파일(`??`)과 스테이징 안 된 변경도 목록으로 보여 줘서 빠진 파일·불필요한 파일을 알아볼 수 있게 한다.

## 2. 비밀 정보

스테이징된 내용에서 **대소문자 무시(`-i`)**로 찾고, `파일:줄번호`가 나오도록 `git grep --cached`를 쓴다. 값은 출력 단계에서 가린다.

```
git grep --cached -nIiE '(api_?key|secret|token|passw(or)?d|credential)[^=:]*[=:]|sk-[A-Za-z0-9]{10,}|ghp_|github_pat_|AKIA|xox[bap]-|AIza|BEGIN .*PRIVATE KEY|://[^/ ]+:[^@ ]+@' | sed -E 's/^([^:]+:[0-9]+:).*/\1 ***/'
```

- `git grep --cached`는 스테이징된 파일 **전체**를 본다(이번 변경이 아닌 기존 줄 포함). 기존 줄이면 그렇게 구분해 보고한다.

| 패턴 | 예 |
|------|-----|
| 키 이름 | `api_key`, `secret`, `token`, `password`, `passwd`, `credential` 뒤에 값 대입 |
| 알려진 접두사 | `sk-`, `ghp_`, `github_pat_`, `AKIA`, `xox[bap]-`, `AIza` |
| 개인키 | `-----BEGIN ... PRIVATE KEY-----` |
| 연결 문자열 | `://user:password@host` |
| 파일 | `.env`, `.env.*`(`.env.example` 제외), `*.pem`, `*.key`, `id_rsa*`, `credentials*.json` |

- **값은 절대 출력하지 않는다.** `파일:줄번호`와 종류만 보고하고 값은 `***`로 가린다.
- 이미 커밋된 기록까지는 보지 않는다. 필요하면 별도로 요청받아 확인한다.

## 3. 대용량·생성 파일

```
git diff --cached --name-only --diff-filter=AM
```

각 파일 크기를 확인한다(`ls -l` 또는 `wc -c`).

- **5MB 초과** 파일을 경고한다. 기준값은 기본값이며 프로젝트에 맞게 조정 가능.
- 확장자로 의심: 모델 가중치(`.pt`, `.pth`, `.ckpt`, `.safetensors`, `.onnx`, `.bin`), 데이터(`.csv`/`.parquet`/`.zip`/`.tar*`가 큰 경우), 영상·이미지 묶음, 빌드 산출물.
- `.gitattributes`에 LFS 설정이 있으면 해당 파일은 LFS 대상인지 함께 본다.

## 4. 캐시·의도치 않은 파일

경로에 다음이 있으면 경고한다.

`__pycache__/`, `*.pyc`, `node_modules/`, `.venv/`, `venv/`, `dist/`, `build/`, `.ipynb_checkpoints/`, `.idea/`, `.vscode/`(공유 설정이 아니면), `.DS_Store`, `Thumbs.db`, `*.log`, `*.tmp`

- `.gitignore`에 해당 항목이 있는지 확인하고, 없으면 추가를 **제안**한다.
- 이미 추적 중이면 `git rm --cached`가 필요하다고 안내만 한다.

## 5. 내용 점검

- 디버그 흔적: `print(`/`console.log` 임시 출력, `TODO`/`FIXME`/`XXX` 새로 추가된 것, `breakpoint()`, `debugger`.
- 충돌 마커: `<<<<<<<`, `=======`, `>>>>>>>`.
- 변경 범위: 요청과 무관해 보이는 파일(포맷팅만 바뀐 파일 등)이 섞였는지.

## 6. 보고

항목별로 한 줄씩. 문제가 있으면 **차단 / 경고**로 나눈다.

- 차단: 비밀 정보, 충돌 마커 → 커밋하지 말 것을 권고.
- 경고: 대용량, 캐시, 디버그 흔적 → 사용자가 판단.

형식:

```
점검 결과: 차단 N / 경고 M
- [차단] config.py:12 — api_key 값 의심 (***)
- [경고] model.pt — 120MB
확인 못 한 항목: (있으면)
```

- 문제가 없으면 "문제 없음"과 점검한 범위(스테이징 N개 파일)를 알린다.
- 확인하지 못한 항목은 숨기지 않고 적는다.
- 수정(unstage, 삭제, `.gitignore` 편집)은 제안만 하고 사용자가 승인하면 한다.
