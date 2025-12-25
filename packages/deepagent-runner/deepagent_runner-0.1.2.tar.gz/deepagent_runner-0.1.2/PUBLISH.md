# Hướng dẫn Publish Package lên PyPI

## Cách 1: Publish lên PyPI (Public)

### Bước 1: Cài đặt build tools

```bash
# Cài đặt build và twine
pip install build twine
# hoặc với uv
uv pip install build twine
```

### Bước 2: Build package

```bash
# Build source distribution và wheel
python -m build
# hoặc
uv build
```

Sẽ tạo ra 2 files trong thư mục `dist/`:
- `deepagent-runner-0.1.0.tar.gz` (source distribution)
- `deepagent-runner-0.1.0-py3-none-any.whl` (wheel)

### Bước 3: Kiểm tra package

```bash
# Kiểm tra package trước khi upload
twine check dist/*
```

### Bước 4: Upload lên PyPI

**TestPyPI (để test trước):**
```bash
# Tạo account tại https://test.pypi.org/account/register/
# Tạo API token tại https://test.pypi.org/manage/account/token/

twine upload --repository testpypi dist/*
```

**PyPI chính thức:**
```bash
# Tạo account tại https://pypi.org/account/register/
# Tạo API token tại https://pypi.org/manage/account/token/

twine upload dist/*
```

Khi được hỏi username, dùng: `__token__`
Khi được hỏi password, dùng: API token của bạn (bắt đầu với `pypi-`)

### Bước 5: Cài đặt từ PyPI

Sau khi publish, người dùng có thể cài đặt dễ dàng:

```bash
# Cài đặt từ PyPI
pip install deepagent-runner
# hoặc với uv
uv pip install deepagent-runner

# Cài với optional dependencies
pip install "deepagent-runner[tavily]"
```

## Cách 2: Publish lên Private Repository

### Sử dụng GitLab/GitHub Packages

Có thể publish lên GitLab Package Registry hoặc GitHub Packages:

```bash
# GitLab
twine upload --repository-url https://gitlab.com/api/v4/projects/<project-id>/packages/pypi dist/*

# GitHub
twine upload --repository-url https://upload.pypi.org/legacy/ dist/*
```

## Cách 3: Cài đặt từ Git Repository (không cần PyPI)

Nếu không muốn publish lên PyPI, có thể cài trực tiếp từ Git:

```bash
# Cài từ Git repo
pip install git+https://github.com/yourusername/CodeAgent.git
# hoặc với uv
uv pip install git+https://github.com/yourusername/CodeAgent.git

# Cài từ branch cụ thể
pip install git+https://github.com/yourusername/CodeAgent.git@main

# Cài từ tag
pip install git+https://github.com/yourusername/CodeAgent.git@v0.1.0
```

## Cách 4: Cài đặt từ Local Wheel

Nếu muốn chia sẻ file `.whl` trực tiếp:

```bash
# Build wheel
python -m build --wheel

# Chia sẻ file dist/deepagent-runner-0.1.0-py3-none-any.whl
# Người nhận cài đặt:
pip install deepagent-runner-0.1.0-py3-none-any.whl
```

## Cập nhật Version

Khi cần publish version mới:

1. Cập nhật version trong `pyproject.toml`:
```toml
version = "0.1.1"
```

2. Cập nhật version trong `src/deepagent_runner/__init__.py`:
```python
__version__ = "0.1.1"
```

3. Build và upload lại:
```bash
python -m build
twine upload dist/*
```

## Lưu ý

- **Version number**: Phải tăng version mỗi lần publish
- **API tokens**: Không commit tokens vào Git
- **Test trước**: Nên test trên TestPyPI trước khi publish lên PyPI chính thức
- **Dependencies**: Đảm bảo tất cả dependencies đã có trên PyPI

