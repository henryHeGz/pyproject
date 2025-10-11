# 国家税务总局数据采集工具集

这是一个使用 [Playwright](https://playwright.dev/python/) 开发的数据采集工具集，用于从国家税务总局网站采集法律法规和留言公开数据。

## 项目结构

```
pyproject/
├── flfg_scraper/          # 法规库采集工具
│   ├── chinatax_scraper.py              # 列表采集
│   ├── chinatax_document_downloader.py   # 文档下载
│   ├── chinatax_scheduler.py            # 调度器
│   ├── chinatax_content_to_md.py        # 内容转Markdown
│   └── README.md                         # 详细文档
│
├── comments_scraper/      # 留言公开采集工具
│   ├── chinatax_comments_scraper.py     # 留言采集
│   └── README.md                         # 详细文档
│
└── tests/                 # 测试文件
```

## 功能概述

### 1. 法规库采集工具 ([flfg_scraper/](flfg_scraper/))

采集国家税务总局法规库的法律法规数据：

- **列表采集**：提取标题、发文字号、成文日期、链接等信息
- **文档下载**：下载法规正文和附件
- **批量处理**：调度器支持批量下载和断点续传
- **格式转换**：将内容转换为 Markdown 格式

📖 [查看详细文档](flfg_scraper/README.md)

### 2. 留言公开采集工具 ([comments_scraper/](comments_scraper/))

采集国家税务总局留言公开页面的用户留言：

- **留言列表**：提取留言问题、日期、链接
- **详情下载**：自动下载问答详情内容
- **去重管理**：MD5 去重，避免重复采集
- **断点续传**：支持中断后继续采集

📖 [查看详细文档](comments_scraper/README.md)

## 快速开始

### 安装依赖

```bash
pip install .
playwright install
```

### 使用示例

#### 法规库采集

```bash
# 1. 采集列表数据
cd flfg_scraper
python chinatax_scraper.py

# 2. 批量下载文档
python chinatax_scheduler.py --not-downloaded --output-dir ./documents
```

#### 留言公开采集

```bash
# 一步完成：采集列表并下载详情
cd comments_scraper
python chinatax_comments_scraper.py --auto-download
```

## 注意事项

- 初次使用需要运行 `playwright install` 安装浏览器驱动
- 建议配置合适的网络环境以访问目标网站
- 生成的 CSV 文件使用 UTF-8-BOM 编码，可在 Excel 中正常打开
- 所有工具都支持断点续传，中断后可以继续运行

## 开发文档

- [项目指南 (CLAUDE.md)](CLAUDE.md) - 针对 Claude Code 的开发指南
- [快速入门 (QUICKSTART.md)](QUICKSTART.md) - 快速上手指南
- [Excel 兼容性 (EXCEL_COMPATIBILITY.md)](EXCEL_COMPATIBILITY.md) - CSV 编码说明

## 许可证

MIT License
