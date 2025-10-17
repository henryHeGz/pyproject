# 📚 文档索引

欢迎来到国家税务总局数据采集系统的完整文档库。

## 🚀 快速开始

| 文档 | 说明 | 适用人群 |
|------|------|----------|
| [README.md](../readme.md) | 项目主页，功能概览 | 所有用户 |
| [QUICKSTART.md](../QUICKSTART.md) | 5分钟快速上手 | 新用户 |
| [CLAUDE.md](../CLAUDE.md) | Claude Code 开发指南 | AI 辅助开发 |

## 📖 使用指南

### 数据库配置
- [DATABASE_GUIDE.md](guides/DATABASE_GUIDE.md) - SQLite 和 MySQL 详细配置指南
  - 环境变量配置
  - 数据库切换
  - 备份与恢复
  - 性能优化

### Web 管理界面
- [WEB_GUIDE.md](guides/WEB_GUIDE.md) - Web 管理后台使用指南
  - 启动 Web 服务
  - 爬虫任务管理
  - 文件管理
  - API 接口说明

### 文档下载功能
- [FLFG_DOWNLOAD_GUIDE.md](guides/FLFG_DOWNLOAD_GUIDE.md) - 法律法规文档下载指南
  - 下载流程
  - 参数说明
  - 状态管理
  - 常见问题

### 自动登录工具
- [AUTOLOGIN_GUIDE.md](guides/AUTOLOGIN_GUIDE.md) - Codex2 自动登录使用指南
  - 安装配置
  - 使用方法
  - 工作原理
  - 调试技巧

## 🔄 迁移与升级

### 数据库迁移
- [DATABASE_MIGRATION.md](migration/DATABASE_MIGRATION.md) - 从 CSV 迁移到数据库
  - 迁移步骤
  - 数据转换
  - 向后兼容
  - 故障排查

### 重构总结
- [REFACTORING_SUMMARY.md](migration/REFACTORING_SUMMARY.md) - v2.0 重构技术总结
  - 重构目标
  - 架构变更
  - 性能对比
  - 迁移路径

## 🔧 技术文档

### 自动登录技术
- [AUTOLOGIN_PROJECT_SUMMARY.md](technical/AUTOLOGIN_PROJECT_SUMMARY.md) - 自动登录项目技术总结
  - 图像识别算法
  - 滑块拖动模拟
  - 自适应重试
  - 开发历程

### 任务管理
- [TASK_MANAGEMENT_UPDATE.md](technical/TASK_MANAGEMENT_UPDATE.md) - 任务管理功能更新
  - 数据库设计
  - API 变更
  - 前端更新
  - 使用指南

### Excel 兼容性
- [EXCEL_COMPATIBILITY.md](technical/EXCEL_COMPATIBILITY.md) - CSV 文件 Excel 兼容性说明
  - UTF-8 BOM 处理
  - 编码转换
  - 兼容性验证

## 📝 更新日志

### Bug 修复
- [BUGFIX_CSV_BOM.md](changelog/BUGFIX_CSV_BOM.md) - CSV BOM 编码问题修复记录

### Web 应用更新
- [WEB_APP_FIX.md](changelog/WEB_APP_FIX.md) - Web 应用数据库重构适配修复
- [WEB_APP_UPDATED.md](changelog/WEB_APP_UPDATED.md) - Web 应用 v2.0 更新说明

## 📦 模块文档

### 法律法规爬虫
- [flfg_scraper/README.md](../flfg_scraper/README.md) - 法律法规爬虫模块说明
  - 列表采集
  - 文档下载
  - 调度器使用

### 留言爬虫
- [comments_scraper/README.md](../comments_scraper/README.md) - 留言爬虫模块说明
  - 列表爬取
  - 详情下载
  - 自动化流程

## 🗂️ 文档结构

```
docs/
├── INDEX.md                          # 本文档索引
├── guides/                           # 使用指南
│   ├── DATABASE_GUIDE.md
│   ├── WEB_GUIDE.md
│   ├── FLFG_DOWNLOAD_GUIDE.md
│   └── AUTOLOGIN_GUIDE.md
├── migration/                        # 迁移与升级
│   ├── DATABASE_MIGRATION.md
│   └── REFACTORING_SUMMARY.md
├── technical/                        # 技术文档
│   ├── AUTOLOGIN_PROJECT_SUMMARY.md
│   ├── TASK_MANAGEMENT_UPDATE.md
│   └── EXCEL_COMPATIBILITY.md
└── changelog/                        # 更新日志
    ├── BUGFIX_CSV_BOM.md
    ├── WEB_APP_FIX.md
    └── WEB_APP_UPDATED.md
```

## 💡 文档使用建议

### 新用户路径
1. 阅读 [README.md](../readme.md) 了解项目
2. 按照 [QUICKSTART.md](../QUICKSTART.md) 快速上手
3. 根据需要查阅 [guides/](guides/) 目录下的具体指南

### 开发者路径
1. 阅读 [CLAUDE.md](../CLAUDE.md) 了解项目架构
2. 查看 [technical/](technical/) 目录下的技术文档
3. 参考 [migration/REFACTORING_SUMMARY.md](migration/REFACTORING_SUMMARY.md) 了解设计决策

### 运维人员路径
1. 参考 [guides/DATABASE_GUIDE.md](guides/DATABASE_GUIDE.md) 配置数据库
2. 使用 [guides/WEB_GUIDE.md](guides/WEB_GUIDE.md) 管理系统
3. 遇到问题查阅 [changelog/](changelog/) 目录

## 🔍 查找信息

### 按主题查找

| 主题 | 相关文档 |
|------|----------|
| 数据库 | DATABASE_GUIDE, DATABASE_MIGRATION |
| Web 界面 | WEB_GUIDE, WEB_APP_FIX, WEB_APP_UPDATED |
| 爬虫 | flfg_scraper/README, comments_scraper/README |
| 下载 | FLFG_DOWNLOAD_GUIDE |
| 自动登录 | AUTOLOGIN_GUIDE, AUTOLOGIN_PROJECT_SUMMARY |
| 迁移升级 | DATABASE_MIGRATION, REFACTORING_SUMMARY |
| Bug 修复 | BUGFIX_CSV_BOM, WEB_APP_FIX |

### 按任务查找

| 任务 | 推荐文档 |
|------|----------|
| 首次安装 | QUICKSTART.md |
| 配置数据库 | DATABASE_GUIDE.md |
| 启动 Web 界面 | WEB_GUIDE.md |
| 爬取数据 | README.md, flfg_scraper/README.md |
| 下载文档 | FLFG_DOWNLOAD_GUIDE.md |
| 自动登录 | AUTOLOGIN_GUIDE.md |
| CSV 迁移 | DATABASE_MIGRATION.md |
| 问题排查 | DATABASE_GUIDE.md, WEB_APP_FIX.md |

## 📞 获取帮助

- 查看各文档中的"故障排查"章节
- 参考 [changelog/](changelog/) 了解已知问题和修复
- 查阅模块级 README 了解具体功能

---

**最后更新**: 2025-10-14
**文档版本**: 2.0
**项目版本**: 2.0.0
