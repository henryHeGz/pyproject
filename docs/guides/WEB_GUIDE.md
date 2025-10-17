# Web管理后台使用指南

## 功能概览

Web管理后台提供了一个友好的界面来管理两个爬虫任务：
1. **法律法规爬虫** - 爬取国家税务总局法规库的法律法规列表
2. **留言公开爬虫** - 爬取国家税务总局的留言公开数据
3. **下载留言详情** - 下载留言的详细问答内容

## 快速开始

### 1. 安装依赖

```bash
# 安装项目依赖
pip install -e .

# 安装Playwright浏览器
playwright install
```

### 2. 启动Web服务

有两种方式启动：

**方式一：使用启动脚本**
```bash
./start_web.sh
```

**方式二：直接运行Python**
```bash
python3 web_app.py
```

**方式三：使用命令行工具**
```bash
chinatax-web
```

### 3. 访问界面

服务启动后，在浏览器中访问：
- 主界面: http://localhost:8000
- API文档: http://localhost:8000/docs

## 使用说明

### 法律法规爬虫

**参数说明：**
- **CSV文件路径**: 保存数据的CSV文件名（默认：chinatax_flfg.csv）
- **起始页码**: 从第几页开始爬取（默认：1）
- **抓取页数**: 抓取多少页，留空表示抓取到最后一页或遇到重复记录
- **无头模式**: 勾选后浏览器在后台运行不显示窗口

**使用场景：**
- 首次使用：使用默认设置，点击"开始爬取"
- 增量更新：运行时会自动跳过已存在的记录
- 断点续传：设置起始页码，从指定页开始爬取

### 留言公开爬虫

**参数说明：**
- **CSV文件路径**: 保存数据的CSV文件名（默认：chinatax_comments.csv）
- **起始页码**: 从第几页开始爬取
- **最多抓取页数**: 最多爬取多少页，留空表示全部爬取
- **无头模式**: 浏览器是否在后台运行
- **自动下载详情内容**: 勾选后会在爬取列表完成后自动下载每条留言的详细问答

**使用场景：**
- 快速爬取列表：不勾选"自动下载详情"，只获取标题和链接
- 完整爬取：勾选"自动下载详情"，一次性获取列表和详情
- 限制爬取量：设置"最多抓取页数"，比如只爬取前10页

### 下载留言详情

**参数说明：**
- **CSV文件路径**: 包含留言列表的CSV文件
- **最多下载数量**: 最多下载多少条，留空表示下载所有未下载的
- **无头模式**: 浏览器是否在后台运行

**使用场景：**
- 补充下载：之前只爬取了列表，现在补充下载详情内容
- 限量下载：设置"最多下载数量"，比如每次下载50条
- 断点续传：程序会自动跳过已下载的记录（"是否下载"列为"Y"）

## 任务状态监控

任务提交后，界面会自动显示任务状态：

- **🔄 运行中**: 任务正在执行
- **✅ 完成**: 任务成功完成
- **❌ 失败**: 任务执行失败

状态每3秒自动刷新，实时显示任务进度。

## 文件管理

**文件列表功能：**
- 显示所有CSV文件及其信息（行数、大小、修改时间）
- **预览**: 查看文件前10行内容
- **下载**: 下载CSV文件到本地

文件列表每10秒自动刷新。

## API接口

如果需要程序化调用，可以使用以下API接口：

### 启动法律法规爬虫
```bash
curl -X POST "http://localhost:8000/api/flfg/scrape" \
  -H "Content-Type: application/json" \
  -d '{
    "csv_path": "chinatax_flfg.csv",
    "start_page": 1,
    "page_count": null,
    "headless": true
  }'
```

### 启动留言爬虫
```bash
curl -X POST "http://localhost:8000/api/comments/scrape" \
  -H "Content-Type: application/json" \
  -d '{
    "csv_path": "chinatax_comments.csv",
    "start_page": 1,
    "max_pages": null,
    "headless": true,
    "auto_download": false
  }'
```

### 下载留言详情
```bash
curl -X POST "http://localhost:8000/api/comments/download" \
  -H "Content-Type: application/json" \
  -d '{
    "csv_path": "chinatax_comments.csv",
    "max_downloads": null,
    "headless": true
  }'
```

### 查询任务状态
```bash
# 获取所有任务
curl "http://localhost:8000/api/tasks"

# 获取特定任务
curl "http://localhost:8000/api/task/{task_id}"
```

### 文件操作
```bash
# 列出所有CSV文件
curl "http://localhost:8000/api/files"

# 预览文件
curl "http://localhost:8000/api/files/chinatax_flfg.csv/preview?limit=10"

# 下载文件
curl -O "http://localhost:8000/api/files/chinatax_flfg.csv/download"
```

## 常见问题

**Q: 爬虫运行很慢怎么办？**
A: 可以设置页数限制，分批次爬取，比如每次爬取10页。

**Q: 任务失败了怎么办？**
A: 查看任务状态中的错误信息，常见问题包括网络超时、网站结构变化等。可以尝试重新运行。

**Q: 如何停止正在运行的任务？**
A: 当前版本不支持中途停止任务，如需停止请重启Web服务。后续版本会添加此功能。

**Q: CSV文件保存在哪里？**
A: 默认保存在项目根目录下，可以在"文件列表"中查看和下载。

**Q: 可以同时运行多个任务吗？**
A: 可以，任务会在后台并行执行，但建议不要同时运行太多任务以免占用过多资源。

## 技术架构

- **后端框架**: FastAPI
- **Web服务器**: Uvicorn
- **模板引擎**: Jinja2
- **前端**: 原生HTML/CSS/JavaScript
- **爬虫引擎**: Playwright

## 注意事项

1. 首次使用需要安装Playwright浏览器：`playwright install`
2. 爬虫运行时会占用一定的CPU和内存资源
3. 请合理设置爬取频率，避免对目标网站造成过大压力
4. 任务状态存储在内存中，重启服务后会清空历史记录
5. 生产环境建议使用进程管理工具（如supervisor、systemd）来管理服务

## 未来改进

- [ ] 添加任务取消功能
- [ ] 持久化任务状态到数据库
- [ ] 添加用户认证和权限管理
- [ ] 支持定时任务和自动调度
- [ ] 添加数据统计和可视化图表
- [ ] 支持导出为多种格式（Excel, JSON等）
