## humblenode-agent

PyPI 배포명: **`humblenode-agent`**  
파이썬 import 패키지명: **`agent`**  
설치 후 실행 커맨드: **`agent`**

### 설치

```bash
pip install humblenode-agent
```

### 실행

```bash
agent --host 0.0.0.0 --port 8250
```

### 개발(로컬)

```bash
pip install -e .
agent --reload
```

### 배포(PyPI) - uv로 빌드/업로드

사전 준비:

- PyPI 계정 생성 및 **API Token** 발급
- `uv` 설치 (둘 중 하나)

```bash
pip install -U uv
```

또는

```bash
pipx install uv
```

빌드(산출물: `dist/`에 wheel/sdist 생성):

```bash
uv build
```

TestPyPI에 먼저 업로드(권장):

```bash
uv publish --repository testpypi
```

실제 PyPI 업로드:

```bash
uv publish
```

인증(권장 방식):

- Username: `__token__`
- Password: PyPI에서 발급받은 토큰(예: `pypi-...`)

팁(자동화/CI):

- `uv publish` 실행 시 입력이 필요 없게 하려면, 일반적으로 `~/.pypirc` 또는 `TWINE_USERNAME`/`TWINE_PASSWORD` 환경변수를 사용합니다.
