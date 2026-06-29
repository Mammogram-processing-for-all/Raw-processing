# Viewer 실행 준비

루트 프로젝트는 단일 패키지이며, 뷰어/엔진 의존성(PySide6, numpy,
opencv-python-headless, pydicom)이 모두 루트 `pyproject.toml` 에 들어있다.

```bash
# 저장소 루트에서
uv sync
uv run python viewer/app.py
```

`viewer/app.py` 는 `engine/` 디렉터리를 `sys.path` 에 추가해
`from main import basic_pipeline` 으로 엔진을 가져다 쓴다. 별도의 엔진 설치
(`pip install -e ../engine`)는 필요 없다.
