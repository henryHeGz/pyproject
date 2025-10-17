# 任务日志系统实现总结

## 概述

为项目添加了完整的任务执行日志系统，每个任务都有独立的日志文件，数据库只存储文件路径引用。

## 新增文件

### 1. [log_manager.py](../log_manager.py)
任务日志管理核心模块

**主要功能：**
- `create_task_logger()` - 为任务创建专用日志记录器
- `read_task_log()` - 读取任务日志内容
- `get_log_file_path()` - 获取日志文件路径
- `finish_task_log()` - 完成任务日志记录
- `list_log_files()` - 列出所有日志文件
- `get_log_file_info()` - 获取日志文件详细信息

### 2. [task_logs/](../task_logs/)
任务日志文件存储目录

**命名格式：** `{task_id}.log`

**示例：**
- `flfg_20251017_091811.log`
- `comments_20251017_093512.log`
- `download_20251017_101030.log`

### 3. [migrate_add_log_file.py](../migrate_add_log_file.py)
数据库迁移脚本 - 添加 `log_file` 字段到 `tasks` 表

## 数据库变更

###  tasks 表新增字段

```sql
ALTER TABLE tasks ADD COLUMN log_file VARCHAR(255);
```

此字段存储日志文件的完整路径，例如：
```
/Users/henry.he/project/py/pyproject/task_logs/flfg_20251017_091811.log
```

## Web API 新增接口

### GET /api/tasks/{task_id}/log

获取任务执行日志

**请求示例：**
```bash
curl http://localhost:8000/api/tasks/flfg_20251017_091811/log
```

**响应示例：**
```json
{
  "task_id": "flfg_20251017_091811",
  "log_content": "2025-10-17 09:18:11 - [INFO] - 任务开始...",
  "log_file": "/path/to/task_logs/flfg_20251017_091811.log"
}
```

## 修改的文件

### [web_app.py](../web_app.py)

**主要变更：**

1. **导入日志管理模块**
   ```python
   from log_manager import create_task_logger, finish_task_log, read_task_log, get_log_file_path
   ```

2. **任务创建时生成日志文件路径**
   ```python
   log_file_path = str(get_log_file_path(task_id))
   task_data["log_file"] = log_file_path
   ```

3. **后台任务函数集成日志记录**
   ```python
   async def run_flfg_scraper(task_id: str, params: FlfgScraperRequest):
       logger = create_task_logger(task_id, "法律法规爬虫")
       try:
           logger.info("开始爬取数据...")
           # ... 任务执行
           logger.info("爬取完成！")
           finish_task_log(logger, task_id, "completed")
       except Exception as e:
           logger.error(f"任务失败: {e}")
           finish_task_log(logger, task_id, "failed")
   ```

4. **数据库操作函数更新**
   - `save_task_to_db()` - 保存 log_file 字段
   - `update_task_in_db()` - 支持更新 log_file
   - `load_tasks_from_db()` - 查询返回 log_file

### [.gitignore](../.gitignore)

新增排除规则：
```gitignore
# Task logs - all task execution logs go here
task_logs/
```

## 日志格式

每个任务的日志文件包含：

```
============================================================
任务开始: {任务类型}
任务ID: {task_id}
开始时间: {timestamp}
============================================================
任务参数: {parameters}
{执行过程日志...}
============================================================
任务结束: {COMPLETED|FAILED}
结束时间: {timestamp}
============================================================
```

## 使用示例

### Python代码

```python
from log_manager import create_task_logger, finish_task_log

# 创建日志记录器
logger = create_task_logger("my_task_001", "数据处理任务")

# 记录日志
logger.info("开始处理数据...")
logger.warning("发现异常数据")
logger.error("处理失败")

# 完成日志
finish_task_log(logger, "my_task_001", "completed")

# 读取日志
from log_manager import read_task_log
content = read_task_log("my_task_001")
print(content)
```

### Web界面

1. 启动任务后，任务列表会显示"查看日志"按钮
2. 点击按钮查看实时日志内容
3. 日志显示在弹窗或独立页面中

## 优势

✅ **日志文件独立** - 不占用数据库空间
✅ **易于查看** - 可直接用文本编辑器打开
✅ **便于调试** - 支持tail -f实时查看
✅ **易于清理** - 可批量删除旧日志
✅ **可导出分享** - 日志文件可直接发送给他人

## 注意事项

⚠️ **重要：**
- 日志文件自动生成，不要手动编辑
- task_logs/目录已被git ignore
- 日志文件与任务一一对应，通过task_id关联
- 删除日志文件不影响数据库中的任务记录

## 下一步

- [ ] 前端模板添加"查看日志"按钮
- [ ] 实现日志实时查看功能
- [ ] 添加日志文件自动清理功能（可选）
- [ ] 支持日志下载功能

## 测试

```bash
# 测试日志管理器
python log_manager.py

# 测试数据库迁移
python migrate_add_log_file.py

# 查看生成的日志
ls -lh task_logs/
cat task_logs/test_task_20251017_001.log
```
