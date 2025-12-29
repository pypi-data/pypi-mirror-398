# LightRFT PyPI 发布指南

本文档提供了将 LightRFT 项目发布到 PyPI 的完整步骤。

## 📋 目录

1. [前置准备](#前置准备)
2. [配置 PyPI 账户](#配置-pypi-账户)
3. [构建和发布流程](#构建和发布流程)
4. [在其他机器上安装](#在其他机器上安装)
5. [常见问题](#常见问题)

---

## 前置准备

### 1. 安装必要的工具

```bash
# 升级 pip
pip install --upgrade pip

# 安装构建和发布工具
pip install --upgrade setuptools wheel build twine
```

### 2. 检查项目文件

确保以下文件存在且配置正确：

- ✅ `setup.py` - 包配置文件
- ✅ `pyproject.toml` - 现代 Python 项目配置文件
- ✅ `MANIFEST.in` - 指定要包含的非 Python 文件
- ✅ `README.md` - 项目说明文档
- ✅ `LICENSE` - 许可证文件
- ✅ `requirements.txt` - 依赖列表

---

## 配置 PyPI 账户

### 1. 注册 PyPI 账户

- **正式 PyPI**: https://pypi.org/account/register/
- **测试 PyPI**: https://test.pypi.org/account/register/ (推荐先使用)

### 2. 创建 API Token

#### 在 PyPI 网站上创建 Token:

1. 登录 PyPI 账户
2. 进入 Account Settings → API tokens
3. 点击 "Add API token"
4. 设置 Token 名称（如 "LightRFT-upload"）
5. 选择作用域（Scope）:
   - 首次发布: 选择 "Entire account"
   - 后续发布: 可以选择特定项目 "Project: LightRFT"
6. 创建后**立即复制 Token**（只显示一次）

#### 配置本地凭据:

创建或编辑 `~/.pypirc` 文件:

```bash
nano ~/.pypirc
```

添加以下内容:

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-AgEIcHlwaS5vcmcCJDxxxxxxxxxxxxxxxxxxxxxxxx

[testpypi]
username = __token__
password = pypi-AgENdGVzdC5weXBpLm9yZxxxxxxxxxxxxxxxxxxxxxx
repository = https://test.pypi.org/legacy/
```

设置文件权限:

```bash
chmod 600 ~/.pypirc
```

---

## 构建和发布流程

### 方法一: 使用提供的脚本（推荐）

#### 1. 仅构建（不上传）

```bash
cd /mnt/shared-storage-user/puyuan/code/LightRFT
./scripts/build_only.sh
```

这将：
- 清理旧的构建文件
- 安装必要的构建工具
- 构建 wheel 和 source 分发包
- 检查分发包的完整性

#### 2. 构建并发布到 TestPyPI（推荐先测试）

```bash
./scripts/build_and_publish.sh test
```

#### 3. 构建并发布到正式 PyPI

```bash
./scripts/build_and_publish.sh prod
```

### 方法二: 手动执行步骤

#### 步骤 1: 清理旧的构建文件

```bash
cd /mnt/shared-storage-user/puyuan/code/LightRFT
rm -rf build/ dist/ *.egg-info
```

#### 步骤 2: 构建分发包

```bash
# 使用 build 工具（推荐）
python -m build

# 或使用传统方式
python setup.py sdist bdist_wheel
```

构建完成后，`dist/` 目录会包含:
- `LightRFT-0.1.0-py3-none-any.whl` (wheel 格式)
- `LightRFT-0.1.0.tar.gz` (source 格式)

#### 步骤 3: 检查分发包

```bash
twine check dist/*
```

确保输出显示 "PASSED"。

#### 步骤 4: 上传到 TestPyPI（测试）

```bash
twine upload --repository testpypi dist/*
```

#### 步骤 5: 测试从 TestPyPI 安装

```bash
# 创建新的虚拟环境测试
python -m venv test_env
source test_env/bin/activate

# 从 TestPyPI 安装
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ LightRFT

# 测试导入
python -c "import lightrft; print('安装成功!')"

# 清理
deactivate
rm -rf test_env
```

#### 步骤 6: 上传到正式 PyPI

确认 TestPyPI 测试无误后:

```bash
twine upload dist/*
```

---

## 在其他机器上安装

### 基础安装

```bash
# 从 PyPI 安装
pip install LightRFT
```

### GPU 环境安装（推荐）

LightRFT 需要 CUDA 支持，建议按以下顺序安装:

```bash
# 1. 先安装 PyTorch（根据你的 CUDA 版本）
# CUDA 12.4 示例:
pip install torch==2.5.1 --index-url https://download.pytorch.org/whl/cu124

# 2. 安装 flash-attention（可选但推荐，需要 GPU）
pip install flash-attn --no-build-isolation

# 3. 安装 LightRFT
pip install LightRFT

# 4. 或者安装所有可选依赖
pip install LightRFT[flash-attn,eval]
```

### 开发模式安装

如果需要修改代码:

```bash
git clone https://github.com/opendilab/LightRFT.git
cd LightRFT
pip install -e .

# 安装开发依赖
pip install -e .[dev]
```

### 验证安装

```bash
python -c "import lightrft; print('LightRFT 安装成功!')"
```

---

## 版本更新流程

当需要发布新版本时:

### 1. 更新版本号

编辑以下文件中的版本号:

- `setup.py`: `version="0.1.1"`
- `pyproject.toml`: `version = "0.1.1"`
- `README.md`: 更新 badge 中的版本号

### 2. 更新 CHANGELOG

编辑 `CHANGELOG.md`:

```markdown
## [0.1.1] - 2025-12-26

### Added
- 新功能描述

### Fixed
- 修复的问题

### Changed
- 变更的内容
```

### 3. 提交变更

```bash
git add .
git commit -m "Bump version to 0.1.1"
git tag v0.1.1
git push origin main --tags
```

### 4. 重新构建和发布

```bash
./scripts/build_and_publish.sh prod
```

---

## 常见问题

### Q1: 上传时提示 "File already exists"

**原因**: PyPI 不允许覆盖已上传的版本。

**解决**: 更新版本号后重新构建和上传。

### Q2: 安装时找不到某些依赖

**原因**: 某些依赖（如 `vllm`, `flash-attn`）可能需要特定的系统环境。

**解决**:
```bash
# 跳过某些依赖先安装
pip install LightRFT --no-deps

# 然后手动安装能安装的依赖
pip install torch transformers deepspeed accelerate datasets wandb peft easydict
```

### Q3: 构建时出现编码错误

**原因**: 文件编码问题。

**解决**: 确保 `setup.py` 中使用 UTF-8 编码读取 README:
```python
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()
```

### Q4: 如何只发布到私有 PyPI 服务器？

编辑 `~/.pypirc` 添加私有仓库:

```ini
[distutils]
index-servers =
    private

[private]
repository = https://your-private-pypi.com
username = your_username
password = your_password
```

上传:
```bash
twine upload --repository private dist/*
```

---

## 安全建议

1. **不要将 `.pypirc` 文件提交到 Git**
   ```bash
   echo ".pypirc" >> ~/.gitignore
   ```

2. **使用 API Token 而不是密码**
   - Token 可以随时撤销
   - 可以限制作用域

3. **定期更新 Token**
   - 建议每 3-6 个月更新一次

4. **使用 2FA（双因素认证）**
   - 在 PyPI 账户设置中启用

---

## 相关链接

- PyPI 官方文档: https://packaging.python.org/
- Twine 文档: https://twine.readthedocs.io/
- setuptools 文档: https://setuptools.pypa.io/
- PyPI: https://pypi.org/
- TestPyPI: https://test.pypi.org/

---

## 快速命令参考

```bash
# 构建
python -m build

# 检查
twine check dist/*

# 上传到 TestPyPI
twine upload --repository testpypi dist/*

# 上传到 PyPI
twine upload dist/*

# 从 TestPyPI 安装
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ LightRFT

# 从 PyPI 安装
pip install LightRFT

# 清理构建文件
rm -rf build/ dist/ *.egg-info
```
