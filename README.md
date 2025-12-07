# DeepSeek Commit Tool

基于 DeepSeek API 的 Git 提交信息自动生成工具。

## 快速开始

```bash
# 1. 配置 API Key
dsc.exe --api-key sk-xxxx

# 2. 生成提交信息
dsc.exe run
```

## 常用命令

```bash
# 查看帮助
dsc.exe

# 设置提交风格
dsc.exe --commit-style conventional|simple|emoji

# 设置语言
dsc.exe --language zh-CN|en

# 查看配置
dsc.exe --show-config
```

## SourceTree 集成

SourceTree → `工具` → `选项` → `自定义操作` → 添加

- 菜单文本: `DeepSeek Commit`
- 脚本运行: `C:\path\to\dsc.exe` <dsc path>
- 参数: `run $REPO`

## 使用流程

1. 在 SourceTree 中暂存需要提交的文件
2. 右键菜单 → `DeepSeek Commit` - 生成提交信息
3. 复制生成的提交信息，在 SourceTree 中提交代码

## 编码设置

程序默认使用 UTF-8 编码输出。如果遇到中文乱码问题，可以：
```bash
# 使用 UTF-8 编码（默认）
dsc.exe run --encoding utf-8

# 使用 GBK 编码
dsc.exe run --encoding gbk
```

在 SourceTree 的自定义操作参数中添加编码选项：
```
run $REPO --encoding utf-8
```
