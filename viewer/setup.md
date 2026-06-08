# Viewer 실행 준비

```bash
cd viewer
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install PySide6              # 뷰어 GUI
pip install -e ../engine         # 엔진 + 의존성(numpy, opencv-python-headless, pydicom) 자동 설치

python app.py
```

`pip install -e ../engine` 는 `engine/pyproject.toml` 을 읽어 `processing` 패키지와
`main`(basic_pipeline) 모듈을 editable 로 설치하고, 필요한 영상처리 의존성까지 함께
설치한다. 따라서 뷰어는 별도 경로 설정 없이 `from main import basic_pipeline` 으로
엔진을 가져다 쓸 수 있다.
