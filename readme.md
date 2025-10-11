# Chinatax Playwright Scraper

该项目提供了一个使用 [Playwright](https://playwright.dev/python/) 编写的命令行工具，用于采集 “国家税务总局-法律法规” 列表页面的数据。

## 功能概述

- 采集列表中的序号、标题、发文字号、成文日期。
- 将数据保存至本地 CSV 文件。
- 启动时读取既有 CSV 数据并进行去重，仅追加未采集过的记录。
- 自动翻页直至没有下一页。

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

2. 运行采集脚本：

   ```bash
   python chinatax_scraper.py
   ```

   或者安装后使用命令行入口：

   ```bash
   chinatax-scraper
   ```

3. 可选参数：

   - `--csv PATH`：指定保存 CSV 的路径（默认 `chinatax_flfg.csv`）。
   - `--headed`：以有界面模式运行浏览器，便于调试。

运行结束后，终端会输出新增记录数及保存位置。

## 注意事项

- 初次使用 Playwright 需执行 `playwright install` 安装浏览器内核。
- 建议为请求配置合适的代理或网络环境，确保可以访问目标网站。
