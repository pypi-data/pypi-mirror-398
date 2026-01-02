# Web Manage MCP Server 部署指南

## 🚀 通过 uvx 快速部署

### 1. 本地测试

```bash
# 测试入口点
python -c "from web_manage_mcp_server.main import main; print('Entry point test successful')"

# 直接运行（无需安装）
uvx run .

# 测试包模块
python -m web_manage_mcp_server
```

### 2. 发布到 PyPI

```bash
# 构建包
uv build

# 发布到 PyPI（需要配置 PyPI 凭据）
uv publish

# 或发布到测试 PyPI
uv publish --repository testpypi
```

### 3. 用户安装和使用

```bash
# 方式1: 直接运行（推荐）
uvx run web-manage-mcp

# 方式2: 安装后使用
uvx install web-manage-mcp
web-manage-mcp

# 方式3: 从 Git 仓库安装
uvx install git+https://github.com/yourusername/web-manage-mcp.git
```

## 🔧 MCP 客户端配置

### 自动配置

```bash
# 下载并运行安装脚本
curl -sSL https://raw.githubusercontent.com/yourusername/web-manage-mcp/main/install.py | python

# 或本地运行
python install.py --configure
```

### 手动配置

#### Claude Desktop

配置文件位置：
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Linux**: `~/.config/claude/claude_desktop_config.json`

配置内容：
```json
{
  "mcpServers": {
    "web-manage-mcp": {
      "command": "uvx",
      "args": ["web-manage-mcp"],
      "env": {}
    }
  }
}
```

#### Cursor IDE

在 Cursor 设置中添加：
```json
{
  "mcpServers": {
    "web-manage-mcp": {
      "command": "uvx",
      "args": ["web-manage-mcp"],
      "env": {}
    }
  }
}
```

## 📦 分发选项

### 1. PyPI 分发（推荐）

**优点**：
- 用户可以通过 `uvx run web-manage-mcp` 直接使用
- 自动处理依赖
- 版本管理简单

**步骤**：
1. 更新 `pyproject.toml` 中的版本号
2. 运行 `uv build` 构建包
3. 运行 `uv publish` 发布到 PyPI

### 2. GitHub Releases

**优点**：
- 免费托管
- 版本控制集成
- 支持预发布版本

**步骤**：
1. 创建 Git tag: `git tag v0.1.0`
2. 推送 tag: `git push origin v0.1.0`
3. 在 GitHub 创建 Release

用户安装：
```bash
uvx install git+https://github.com/yourusername/web-manage-mcp.git@v0.1.0
```

### 3. 私有分发

对于企业内部使用：

```bash
# 构建 wheel 文件
uv build

# 分发 wheel 文件
# 用户安装：uvx install ./dist/web_manage_mcp-0.1.0-py3-none-any.whl
```

## 🔄 持续集成/持续部署 (CI/CD)

### GitHub Actions 示例

创建 `.github/workflows/release.yml`：

```yaml
name: Release

on:
  push:
    tags:
      - 'v*'

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: Install uv
      uses: astral-sh/setup-uv@v3
      with:
        version: "latest"
    
    - name: Set up Python
      run: uv python install 3.11
    
    - name: Build package
      run: uv build
    
    - name: Publish to PyPI
      run: uv publish
      env:
        UV_PUBLISH_TOKEN: ${{ secrets.PYPI_API_TOKEN }}
    
    - name: Create GitHub Release
      uses: actions/create-release@v1
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      with:
        tag_name: ${{ github.ref }}
        release_name: Release ${{ github.ref }}
        draft: false
        prerelease: false
```

## 🛠️ 开发者设置

### 本地开发

```bash
# 克隆仓库
git clone https://github.com/yourusername/web-manage-mcp.git
cd web-manage-mcp

# 安装开发依赖
uv sync --dev

# 以开发模式安装
uv pip install -e .

# 运行测试
uv run pytest
```

### 版本发布流程

1. **更新版本号**：
   ```bash
   # 在 pyproject.toml 中更新版本
   version = "0.2.0"
   ```

2. **更新 CHANGELOG**：
   记录新功能和修复

3. **创建 Git tag**：
   ```bash
   git tag v0.2.0
   git push origin v0.2.0
   ```

4. **自动发布**：
   GitHub Actions 会自动构建和发布

## 📋 部署检查清单

- [ ] 测试入口点：`python -c "from web_manage_mcp_server.main import main; print('OK')"`
- [ ] 测试 uvx 运行：`uvx run .`
- [ ] 更新版本号在 `pyproject.toml`
- [ ] 更新 README.md 和文档
- [ ] 运行测试套件
- [ ] 构建包：`uv build`
- [ ] 测试构建的包：`uvx run dist/web_manage_mcp-*.whl`
- [ ] 发布到 PyPI：`uv publish`
- [ ] 创建 GitHub Release
- [ ] 更新 MCP 客户端配置文档

## 🐛 故障排除

### 常见问题

1. **uvx 找不到命令**
   ```bash
   # 确保 uvx 已安装
   pip install uv
   ```

2. **入口点错误**
   ```bash
   # 检查 pyproject.toml 中的 scripts 配置
   [project.scripts]
   web-manage-mcp = "web_manage_mcp_server.main:main"
   ```

3. **依赖冲突**
   ```bash
   # 清理并重新安装
   uv cache clean
   uv sync
   ```

4. **MCP 连接失败**
   - 检查配置文件路径
   - 确认 uvx 在 PATH 中
   - 重启 MCP 客户端

### 调试模式

```bash
# 启用详细日志
export MCP_DEBUG=1
uvx run web-manage-mcp
```

## 📞 支持

- **Issues**: https://github.com/yourusername/web-manage-mcp/issues
- **Discussions**: https://github.com/yourusername/web-manage-mcp/discussions
- **Email**: your.email@example.com
