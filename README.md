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

### Docs

```bash
mkdocs serve
```