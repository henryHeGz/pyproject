# 国家税务总局留言公开页面爬虫

这是一个使用 Playwright 开发的爬虫工具，用于从国家税务总局留言公开页面提取用户留言数据。

## 功能特性

✅ **自动提取留言数据**：提取留言问题、日期和链接地址
✅ **MD5去重**：使用 `MD5(留言问题+日期+链接地址)` 作为唯一ID，自动去重
✅ **自动翻页**：自动遍历所有页面，直到提取完所有留言
✅ **页面范围控制**：支持指定起始页和最大页数，灵活控制爬取范围
✅ **下载详情内容**：自动下载每条留言的详细问答内容
✅ **智能状态管理**：自动标记下载状态，支持断点续传
✅ **CSV存储**：结构化存储，包含字段：id、留言问题、日期、链接地址、是否下载、问、答
✅ **增量更新**：支持断点续爬，重复运行时只添加新记录

## 安装依赖

```bash
pip install playwright
playwright install chromium
```

## 使用方法

### 方式一：一步完成（推荐）

使用 `--auto-download` 参数，爬取列表后自动下载详情内容：

```bash
# 爬取所有页面并自动下载详情（一步完成）
python chinatax_comments_scraper.py --auto-download

# 爬取前5页并自动下载详情
python chinatax_comments_scraper.py --max-pages 5 --auto-download

# 从第3页开始爬取10页并自动下载详情
python chinatax_comments_scraper.py --start-page 3 --max-pages 10 --auto-download
```

### 方式二：分步执行

#### 第一步：爬取留言列表

```bash
# 爬取所有页面（默认）
python chinatax_comments_scraper.py

# 指定输出文件
python chinatax_comments_scraper.py --csv output.csv

# 使用有头模式（显示浏览器窗口，便于调试）
python chinatax_comments_scraper.py --headed
```

#### 第二步：下载详情内容

爬取完列表后，使用 `--download-content` 下载每条留言的详细问答内容：

```bash
# 下载所有未下载记录的详情内容
python chinatax_comments_scraper.py --download-content

# 下载前10条未下载的记录（测试）
python chinatax_comments_scraper.py --download-content --max-downloads 10

# 使用有头模式下载（可以看到浏览器操作）
python chinatax_comments_scraper.py --download-content --headed
```

### 完整工作流示例

```bash
# 方式1：一步完成（最简单）
python chinatax_comments_scraper.py --max-pages 5 --auto-download

# 方式2：分步执行（更灵活）
# 1. 爬取前5页的留言列表
python chinatax_comments_scraper.py --max-pages 5

# 2. 下载前3条记录的详情内容（测试）
python chinatax_comments_scraper.py --download-content --max-downloads 3

# 3. 下载所有剩余未下载的详情内容
python chinatax_comments_scraper.py --download-content
```

### 页面范围控制

```bash
# 只爬取前10页
python chinatax_comments_scraper.py --max-pages 10

# 从第5页开始爬取所有后续页面
python chinatax_comments_scraper.py --start-page 5

# 从第3页开始爬取5页（爬取第3-7页）
python chinatax_comments_scraper.py --start-page 3 --max-pages 5

# 爬取单独一页（例如第10页）
python chinatax_comments_scraper.py --start-page 10 --max-pages 1

# 组合使用所有参数
python chinatax_comments_scraper.py --csv data.csv --start-page 10 --max-pages 20 --headed
```

### 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--csv PATH` | 路径 | `chinatax_comments.csv` | CSV输出文件路径 |
| `--headed` | 标志 | False | 使用有头模式运行浏览器 |
| `--start-page N` | 整数 | 1 | 起始页码，从第N页开始爬取 |
| `--max-pages N` | 整数 | 无限制 | 最多爬取N页 |
| `--auto-download` | 标志 | False | 爬取列表后自动下载详情内容（推荐） |
| `--download-content` | 标志 | False | 仅下载CSV中未下载记录的详情内容 |
| `--max-downloads N` | 整数 | 无限制 | 最多下载N条记录的内容 |

**提示**：
- `--auto-download` 和 `--download-content` 不能同时使用
- 查看完整帮助信息使用 `python chinatax_comments_scraper.py --help`

## 输出格式

CSV文件包含以下字段：

| 字段 | 说明 | 示例 |
|------|------|------|
| id | MD5哈希值，用于去重 | `405729a2ffcdfe3884f07c44712b0b43` |
| 留言问题 | 用户留言的问题标题 | `我公司是一般纳税人，销售...` |
| 日期 | 留言公开日期 | `2025-10-11` |
| 链接地址 | 留言详情页链接 | `http://www.chinatax.gov.cn/...` |
| 是否下载 | Y表示已下载详情，N表示未下载 | `N` 或 `Y` |
| 问 | 留言详情中的"问"内容 | `我公司是一般纳税人，销售商品...` |
| 答 | 留言详情中的"答"内容 | `根据《中华人民共和国增值税暂行条例》...` |

**Excel兼容性**：CSV文件使用UTF-8 BOM编码，可以直接在Excel中正常打开，中文不会乱码。

## 运行示例

### 示例1：爬取所有页面

```bash
$ python chinatax_comments_scraper.py --csv comments.csv

🚀 开始爬取国家税务总局留言数据...

📂 已加载 0 条现有记录ID
🌐 正在访问: https://www.chinatax.gov.cn/...

📃 正在处理第 1 页...
   找到 20 个列表项
   提取到 20 条留言
   其中 20 条为新记录
✅ 成功翻页

📃 正在处理第 2 页...
   找到 20 个列表项
   提取到 20 条留言
   其中 20 条为新记录
✅ 成功翻页

...

✅ 成功添加 940 条新记录到 comments.csv

🎉 爬取完成！新增 940 条记录
```

### 示例2：从指定页开始爬取

```bash
$ python chinatax_comments_scraper.py --start-page 3 --max-pages 2

🚀 开始爬取国家税务总局留言数据...

📂 已加载 0 条现有记录ID
📄 起始页码：第 3 页
📊 最多爬取：2 页
🌐 正在访问: https://www.chinatax.gov.cn/...

⏩ 正在跳转到第 3 页...
   跳过第 1 页...
✅ 成功翻页
   跳过第 2 页...
✅ 成功翻页
✅ 已到达第 3 页

📃 正在处理第 3 页...
   找到 20 个列表项
   提取到 20 条留言
   其中 20 条为新记录
✅ 成功翻页

📃 正在处理第 4 页...
   找到 20 个列表项
   提取到 20 条留言
   其中 20 条为新记录

✅ 已达到最大页数限制 (2 页)

✅ 成功添加 40 条新记录到 chinatax_comments.csv

🎉 爬取完成！新增 40 条记录
```

## 技术实现

### 核心技术栈
- **Playwright**: 无头浏览器自动化
- **Python 3.7+**: 主要开发语言
- **asyncio**: 异步I/O处理

### 关键实现细节

1. **反检测设置**：通过自定义 User-Agent 和浏览器参数，避免被网站识别为自动化工具
2. **智能等待**：使用 `domcontentloaded` + 固定延迟，确保JavaScript渲染完成
3. **数据去重**：使用MD5哈希实现高效去重，支持增量更新
4. **页面导航**：支持快速跳转到指定起始页，提高分段爬取效率
5. **错误处理**：完善的异常处理机制，确保爬虫稳定运行
6. **内容提取**：使用正则表达式从HTML中提取"问："和"答："部分
7. **状态管理**：自动标记下载状态，支持断点续传，避免重复下载
8. **数据完整性**：下载内容时完全重写CSV，确保数据一致性

### 页面结构

爬虫适配的HTML结构：
```html
<ul class="list">
  <li>
    <a href="链接地址">留言问题</a>
    <span>[日期]</span>
  </li>
  ...
</ul>
```

## 注意事项

1. **运行时间**：完整爬取所有页面可能需要较长时间（取决于总页数）。建议使用 `--max-pages` 限制或分批爬取
2. **下载详情时间**：下载详情内容需要逐条访问详情页，每条记录之间有1.5秒延迟，大量下载需要较长时间
3. **网络环境**：需要能够访问 `www.chinatax.gov.cn`
4. **资源占用**：Chromium浏览器会占用一定的系统资源
5. **合规使用**：请遵守网站使用条款，合理使用爬虫
6. **数据完整性**：下载内容时会重写整个CSV文件，建议先备份重要数据
7. **兼容性**：脚本自动兼容旧版CSV（5列）和新版CSV（7列）

## 使用技巧

### 分批爬取策略

对于大量数据，建议分批爬取以提高稳定性：

```bash
# 爬取第1-10页
python chinatax_comments_scraper.py --max-pages 10

# 继续爬取第11-20页
python chinatax_comments_scraper.py --start-page 11 --max-pages 10

# 继续爬取第21-30页
python chinatax_comments_scraper.py --start-page 21 --max-pages 10
```

由于脚本支持去重，多次运行会自动合并数据到同一CSV文件。

## 故障排除

### 页面加载超时
- 检查网络连接
- 尝试使用 `--headed` 模式查看浏览器行为
- 增加代码中的 `wait_for_timeout` 时间

### 找不到元素
- 网站可能更新了页面结构
- 使用 `--headed` 模式检查页面实际内容

## 文件结构

```
chinatax_comments_scraper.py    # 主爬虫脚本
chinatax_comments.csv           # 默认输出文件（运行后生成）
```

## 许可证

本工具仅供学习和研究使用。
