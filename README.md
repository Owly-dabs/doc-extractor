# Documentation Extractor

## 🛠 Setup Instructions

This project uses [`uv`](https://github.com/astral-sh/uv) for dependency and virtual environment management.

### 1. Install `uv`

Install `uv` globally (if you haven’t already):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Or with Homebrew (macOS):

```bash
brew install astral-sh/uv/uv
```

---

### 2. Clone the repository

```bash
git clone https://github.com/yourusername/your-repo.git
cd your-repo
```

---

### 3. Create a virtual environment

```bash
uv venv
```

This creates a `.venv/` folder in the project directory.

---

### 4. Activate the environment

```bash
source .venv/bin/activate      # macOS/Linux
.venv\Scripts\activate         # Windows (PowerShell or CMD)
```

---

### 5. Install dependencies

```bash
uv pip sync
```

This installs dependencies from the `uv.lock` file, ensuring the environment exactly matches the locked versions.
