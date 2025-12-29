# ESN Tool

一个用于管理多个 Git 项目的命令行工具，支持批量 Git 操作和 AI 自动生成提交信息。

## 功能

- **esntool acm** - 自动生成符合 Conventional Commits 规范的提交信息
- **esntool git** - 批量对多个 Git 项目执行相同命令
- **esntool config** - 配置 AI 接口

## 安装

需要 Python 3.12+ 和 [uv](https://docs.astral.sh/uv/)。

```bash
# 安装 uv (如果还没安装)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 安装 esn-tool
uv tool install esn-tool
```

## 快速开始

### 1. 配置 AI 接口

```bash
esntool config
```

### 2. 自动生成提交信息

```bash
# 进入项目父目录
cd /path/to/projects

# 自动提交
esntool acm
```

### 3. 批量 Git 操作

```bash
# 拉取所有项目
esntool git pull

# 查看所有项目状态
esntool git status
```

## 文档

详细使用说明请查看 [docs/usage.md](docs/usage.md)。

## License

MIT
