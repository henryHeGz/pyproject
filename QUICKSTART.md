# 快速开始指南

## 最简单的用法（一步完成）

```bash
# 爬取前5页并自动下载所有详情内容
python chinatax_comments_scraper.py --max-pages 5 --auto-download
```

这一条命令会：
1. ✅ 爬取前5页的留言列表
2. ✅ 自动下载每条留言的详细问答内容
3. ✅ 保存到 `chinatax_comments.csv`，包含完整的"问"和"答"

## 其他常用命令

```bash
# 爬取所有页面并自动下载详情（可能需要很长时间）
python chinatax_comments_scraper.py --auto-download

# 仅爬取列表，不下载详情
python chinatax_comments_scraper.py --max-pages 10

# 稍后单独下载详情（下载CSV中未下载的记录）
python chinatax_comments_scraper.py --download-content

# 测试：下载前3条记录的详情
python chinatax_comments_scraper.py --download-content --max-downloads 3

# 显示浏览器窗口（调试用）
python chinatax_comments_scraper.py --max-pages 2 --auto-download --headed
```

## 输出示例

CSV文件包含以下字段：

| id | 留言问题 | 日期 | 链接地址 | 是否下载 | 问 | 答 |
|----|---------|------|---------|----------|----|----|
| abc123... | 关于增值税... | 2025-10-11 | http://... | Y | 详细问题内容... | 详细答复内容... |

## 注意事项

- 使用 `--auto-download` 时，下载详情需要较长时间（每条记录约1.5秒）
- 可以随时中断（Ctrl+C），下次运行会自动跳过已下载的记录
- 建议先用 `--max-pages 5` 测试，确认正常后再爬取所有页面
