# Scriptbook 发布流程

完成新功能后的代码整理和发布步骤。

## 版本规则

- **主版本 (x.0.0)**: 不兼容修改
- **次版本 (x.y.0)**: 新功能（向后兼容）
- **修订版本 (x.y.z)**: 问题修正

## 1. 更新版本号

需要修改 2 个文件：
- `pyproject.toml` → `version = "x.y.z"`
- `src/scriptbook/__init__.py` → `__version__ = "x.y.z"`

## 2. 更新文档

### README.md
- 顶部功能特性列表添加新功能
- 版本信息更新为当前版本
- 更新日志顶部添加新条目

### README_en.md
- 与中文版同步更新

### CHANGELOG.md
- 顶部添加新版本条目
- 包含：新增功能、错误修复、测试增强等

### CLAUDE.md
- 目录结构

## 3. 代码清理

### 删除临时文件
```bash
docs/testing/test-*.html
docs/testing/*FIX*.md
*.log *.tmp
```

### 清理调试代码
- 删除临时注释
- 清理缓存：`find . -name "*.pyc" -delete`

## 4. 测试验证

```bash
# JavaScript测试
npm test

# Python测试
pytest src/ -v
```

## 5. 提交

```bash
git add .
git commit -m "feat: release v1.x.x - 功能描述"
git push
```

## 6. 发布到PyPI

```bash
# 构建包
python -m build

# 上传到PyPI
twine upload dist/*
```

---

**确保：版本号一致 | 测试通过 | 文档完整 | PyPI发布成功**

