# Chinatax Playwright Scraper

该项目提供了一个使用 [Playwright](https://playwright.dev/python/) 编写的命令行工具，用于采集 “国家税务总局-法律法规” 列表页面的数据。

## 功能概述

- **列表采集** ([chinatax_scraper.py](chinatax_scraper.py)): 采集列表中的序号、标题、发文字号、成文日期、链接，将数据保存至 CSV 文件并自动去重。
- **文档下载** ([chinatax_document_downloader.py](chinatax_document_downloader.py)): 根据文档链接下载主文档和附件。
- **调度器** ([chinatax_scheduler.py](chinatax_scheduler.py)): 从 CSV 文件读取记录并批量下载文档。

## 使用方式

1. 安装依赖：

   ```bash
   pip install .
   playwright install
   ```

   > **网络受限环境提示**：若 `pip install playwright` 因代理或 403 错误失败，可尝试：
   >
   > - 预先下载 Playwright wheel 与浏览器驱动离线安装；
   > - 配置具备公网访问权限的代理，并在 `pip` 命令中加入 `--proxy` 参数；
   > - 使用 `pip install --index-url <镜像地址> playwright` 指定可信镜像源。
   >
   > 成功安装 Python 包后，再执行 `playwright install` 下载浏览器内核。

2. 采集列表数据：

   ```bash
   # 直接运行
   python chinatax_scraper.py

   # 或使用命令行入口
   chinatax-scraper

   # 可选参数
   chinatax-scraper --csv output.csv --headed
   ```

   **可选参数：**
   - `--csv PATH`：指定保存 CSV 的路径（默认 `chinatax_flfg.csv`）
   - `--headed`：以有界面模式运行浏览器，便于调试

   运行结束后，终端会输出新增记录数及保存位置。

3. 下载单个文档：

   ```bash
   # 下载指定 URL 的文档及附件
   python chinatax_document_downloader.py "http://..." --output-dir ./downloads

   # 可视化模式运行
   python chinatax_document_downloader.py "http://..." --headed
   ```

   **可选参数：**
   - `--output-dir PATH`：指定输出目录（默认：当前目录）
   - `--headed`：以可视化模式运行浏览器

4. 批量下载文档（调度器）：

   ```bash
   # 下载第一条未下载的记录（默认）
   python chinatax_scheduler.py

   # 下载所有未下载的记录
   python chinatax_scheduler.py --not-downloaded

   # 下载前5条未下载的记录
   python chinatax_scheduler.py --not-downloaded --limit 5

   # 根据ID下载指定记录
   python chinatax_scheduler.py --ids "abc123,def456,ghi789"

   # 指定输出目录
   python chinatax_scheduler.py --output-dir ./downloads --not-downloaded
   ```

   **可选参数：**
   - `--csv PATH`：CSV文件路径（默认：chinatax_flfg.csv）
   - `--output-dir PATH`：输出目录（默认：当前目录）
   - `--ids ID1,ID2,...`：要下载的记录ID列表（逗号分隔）
   - `--not-downloaded`：下载所有未下载的记录（"是否下载"字段为N）
   - `--limit N`：限制下载数量
   - `--fail-on-error`：遇到下载错误时停止
   - `--headed`：以可视化模式运行浏览器

   调度器会自动更新 CSV 文件中的"是否下载"字段，成功下载后标记为"Y"。

## 注意事项

- 初次使用 Playwright 需执行 `playwright install` 安装浏览器内核。
- 建议为请求配置合适的代理或网络环境，确保可以访问目标网站。
- 调度器会自动跟踪下载状态，避免重复下载已完成的文档。

## 工作流程示例

1. **首次使用**：采集列表数据生成 CSV
   ```bash
   python chinatax_scraper.py --csv chinatax_flfg.csv
   ```

2. **批量下载**：使用调度器下载所有未下载的文档
   ```bash
   python chinatax_scheduler.py --csv chinatax_flfg.csv --output-dir ./documents --not-downloaded
   ```

3. **继续下载**：如果中断，再次运行调度器会自动跳过已下载的记录
   ```bash
   python chinatax_scheduler.py --csv chinatax_flfg.csv --output-dir ./documents --not-downloaded
   ```

4. **下载特定文档**：根据 CSV 中的序号（MD5）下载指定记录
   ```bash
   python chinatax_scheduler.py --ids "abc123,def456"
   ```
