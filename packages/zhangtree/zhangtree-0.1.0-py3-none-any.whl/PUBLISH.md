# 发布指南 - 如何上传到 PyPI 并安装使用

本指南将详细说明如何将 `zhangtree` 打包并发布到 PyPI。

## 前置准备

### 1. 注册 PyPI 账号

1. 访问 [PyPI](https://pypi.org/) 注册账号
2. 访问 [TestPyPI](https://test.pypi.org/) 注册测试账号（用于测试发布）

### 2. 安装必要的工具

```bash
# 安装构建工具
pip install build twine

# 或者使用 uv（如果已安装）
uv pip install build twine
```

### 3. 配置 PyPI 凭据

创建 `~/.pypirc` 文件（Windows: `C:\Users\你的用户名\.pypirc`）：

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-你的API令牌

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-你的测试API令牌
```

**获取 API 令牌：**
1. 登录 PyPI → Account settings → API tokens
2. 创建新令牌（Scope: Entire account）
3. 复制令牌（只显示一次，请妥善保存）

## 发布步骤

### 步骤 1: 更新版本号

在 `pyproject.toml` 中更新版本号：

```toml
version = "0.1.0"  # 改为新版本，如 "0.1.1"
```

### 步骤 2: 更新项目信息（可选）

在 `pyproject.toml` 中更新作者信息：

```toml
authors = [
    {name = "你的名字", email = "你的邮箱@example.com"}
]
```

更新 `README.md` 中的 GitHub 链接（如果有的话）。

### 步骤 3: 清理旧的构建文件

```bash
# Windows PowerShell
Remove-Item -Recurse -Force dist, build, *.egg-info -ErrorAction SilentlyContinue

# 或者手动删除 dist/、build/、*.egg-info 文件夹
```

### 步骤 4: 构建分发包

```bash
# 使用 build 工具构建
python -m build

# 或者使用 uv
uv build
```

这将创建：
- `dist/zhangtree-0.1.0.tar.gz` (源码分发包)
- `dist/zhangtree-0.1.0-py3-none-any.whl` (wheel 分发包)

### 步骤 5: 检查分发包（可选但推荐）

```bash
# 检查分发包
twine check dist/*
```

### 步骤 6: 测试发布到 TestPyPI

**强烈建议先发布到 TestPyPI 进行测试！**

```bash
# 上传到 TestPyPI
twine upload --repository testpypi dist/*

# 如果配置了 .pypirc，可以简化为：
twine upload --repository testpypi dist/*
```

### 步骤 7: 从 TestPyPI 测试安装

```bash
# 从 TestPyPI 安装测试
pip install --index-url https://test.pypi.org/simple/ zhangtree

# 测试命令是否可用
tree --help
```

### 步骤 8: 发布到正式 PyPI

测试成功后，发布到正式 PyPI：

```bash
# 上传到 PyPI
twine upload dist/*

# 如果配置了 .pypirc，会自动使用 pypi 配置
```

### 步骤 9: 验证发布

```bash
# 等待几分钟让 PyPI 索引更新，然后安装
pip install zhangtree

# 测试命令
tree --help
tree
```

## 安装使用

### 方法 1: 从 PyPI 安装（推荐）

```bash
pip install zhangtree
```

### 方法 2: 从源码安装

```bash
# 克隆仓库
git clone https://github.com/yourusername/zhangtree.git
cd zhangtree

# 安装
pip install .
```

### 方法 3: 开发模式安装

```bash
# 克隆仓库
git clone https://github.com/yourusername/zhangtree.git
cd zhangtree

# 开发模式安装（可编辑模式）
pip install -e .
```

## 使用示例

安装后，可以直接使用 `tree` 命令：

```bash
# 显示当前目录结构
tree

# 显示指定目录
tree C:\Users

# 限制深度
tree -L 2

# 显示文件大小和时间
tree -s -t

# 保存到文件
tree -o tree.txt
```

## 更新版本

当需要发布新版本时：

1. 更新 `pyproject.toml` 中的版本号
2. 更新 `README.md` 中的变更日志（如果有）
3. 重新构建：`python -m build`
4. 上传：`twine upload dist/*`

## 常见问题

### Q: 上传时提示 "File already exists"
A: 该版本已存在，需要更新版本号。

### Q: 上传失败，提示认证错误
A: 检查 `.pypirc` 文件配置，或使用环境变量：
```bash
# Windows PowerShell
$env:TWINE_USERNAME="__token__"
$env:TWINE_PASSWORD="你的API令牌"
twine upload dist/*
```

### Q: 安装后命令不可用
A: 检查 Python 的 Scripts 目录是否在 PATH 中：
```bash
# Windows
where tree

# 应该显示类似：C:\Users\你的用户名\AppData\Local\Programs\Python\Python3x\Scripts\tree.exe
```

### Q: 如何卸载
```bash
pip uninstall zhangtree
```

## 完整发布命令序列

```bash
# 1. 清理
Remove-Item -Recurse -Force dist, build, *.egg-info -ErrorAction SilentlyContinue

# 2. 构建
python -m build

# 3. 检查
twine check dist/*

# 4. 测试发布（可选）
twine upload --repository testpypi dist/*

# 5. 正式发布
twine upload dist/*

# 6. 安装测试
pip install --upgrade zhangtree
tree --help
```

## 注意事项

1. **版本号规范**：遵循 [语义化版本](https://semver.org/) (major.minor.patch)
2. **测试先行**：建议先发布到 TestPyPI 测试
3. **API 令牌安全**：不要将 `.pypirc` 文件提交到 Git
4. **README 格式**：确保 README.md 格式正确，PyPI 会显示它
5. **许可证**：确保有 LICENSE 文件（可选但推荐）

## 相关链接

- [PyPI 官网](https://pypi.org/)
- [TestPyPI 官网](https://test.pypi.org/)
- [Python 打包指南](https://packaging.python.org/)
- [Twine 文档](https://twine.readthedocs.io/)

