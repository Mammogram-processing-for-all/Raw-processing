# 🚨 경고 (CAUTION)

**이 프로젝트는 코드 생성형 AI를 적극적으로 활용하여 제작되었습니다.**  
그 결과 일부 코드나 문서에 부정확하거나 잘못된 내용이 포함되어 있을 수 있습니다.  
사용 전 반드시 직접 검증하시고, **중요한 용도**(특히 임상·의료 관련)로 사용할 경우 각별히 주의하시기 바랍니다.

# Raw-processing

[Mammogram Processing for All](https://mammogram-processing-for-all.github.io/Raw-processing/)

## 1. Install

```bash
git clone https://github.com/Mammogram-processing-for-all/Raw-processing.git
cd Raw-processing
```

### 1.1 Using uv (recommend)

<details>
<summary> Install uv
</summary>

```bash
# Install uv
# https://docs.astral.sh/uv/getting-started/installation/#installing-uv
# Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS & Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

</details>

```bash
uv sync
```

### 1.2 Using pip

```bash
pip install .
```

---

### Viewer

```bash
python viewer/app.py
```

### Docs

Docs tooling lives in the optional `docs` extra:

```bash
uv sync --extra docs   # or: pip install ".[docs]"
```

```bash
mkdocs serve
```

---

## 프로젝트 개요

- **주제**: 가짜연구소(PseudoLab) 시즌 12, 1차 프로젝트
- **기간**: 2026-03 ~ 2026-06
- **참여자**: Youngmin Joo, Injae Ryou, dongguri92, EuijuHeo, Taehyun Lee
- **주요 내용**
  - 유방촬영(mammography) **RAW 영상 처리 엔진** — 강도 선형화, masking, windowing/LUT, 대비 강화(CLAHE·다중스케일) 등 RAW 영상 처리 엔진 알고리즘 개발
  - **Viewer** — 처리 결과를 확인하는 시각화 도구 (`viewer/app.py`)
  - **기술 문서(docs)** — X-ray 물리·디텍터 기초부터 톤 매핑, 품질 지표, 처리 기법, 3-Tier 파이프라인 사례까지 정리한 서베이 문서 ([사이트](https://mammogram-processing-for-all.github.io/Raw-processing/))

## 향후 로드맵

### 1차 프로젝트 마무리

- [ ] 설치/실행 가이드 재정리 및 검증
- [ ] 처리 파이프라인 단계별 모듈화 및 설정 기반 실행 정리
- [ ] 문서와 코드 간 정합성 검증 및 AI 생성 내용 교정
- [ ] 기여 가이드(CONTRIBUTING) 추가
- [ ] V1.0 릴리즈

### Viewer 기능 추가 및 영상 처리 알고리즘 개선

- [ ] Viewer 기능 보강 (비교 보기, 처리 단계별 미리보기)
