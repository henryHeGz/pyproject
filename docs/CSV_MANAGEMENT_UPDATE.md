# CSV文件管理系统更新

## 变更摘要

项目现在使用集中式CSV文件管理系统，所有CSV导出文件统一存放在 `csv_exports/` 目录中，每个文件使用唯一的命名格式。

## 主要变更

### 1. 新增文件

- **[csv_manager.py](csv_manager.py)** - CSV文件管理核心模块
  - 提供 `get_csv_path()` 生成唯一CSV路径
  - 提供 `list_csv_files()` 列出所有CSV文件
  - 提供 `get_latest_csv()` 获取最新CSV文件
  - 统一管理 `csv_exports/` 目录

- **[csv_exports/README.md](csv_exports/README.md)** - CSV目录说明文档

- **[.gitignore](.gitignore)** - Git忽略规则（包含csv_exports/）

- **[migrate_csv_files.py](migrate_csv_files.py)** - CSV迁移工具（已执行）

### 2. 修改文件

- **[web_app.py](web_app.py)** - 更新所有CSV相关功能
  - 导入 `csv_manager` 模块
  - `/api/files` 现在读取 `csv_exports/` 目录
  - `/api/files/{filename}/preview` 使用 `CSV_EXPORTS_DIR`
  - `/api/files/{filename}/download` 使用 `CSV_EXPORTS_DIR`
  - `/api/tasks/{task_id}/export` 使用 `get_csv_path()` 生成唯一文件名

- **[CLAUDE.md](CLAUDE.md)** - 更新项目文档
  - 添加CSV导出系统说明
  - 添加文件命名规范
  - 添加使用示例

### 3. 目录结构变更

**之前：**
```
pyproject/
├── chinatax_comments.csv          # ❌ 根目录杂乱
├── chinatax_flfg.csv              # ❌
├── export_comments_xxx.csv        # ❌
└── web_app.py
```

**现在：**
```
pyproject/
├── csv_exports/                   # ✅ 专门的CSV目录
│   ├── README.md                  # 说明文档
│   ├── flfg_251017083045_a3f2.csv
│   └── comments_251017083512_x9k1.csv
├── csv_manager.py                 # ✅ 统一管理
├── web_app.py
└── .gitignore                     # ✅ 排除csv_exports/
```

## CSV文件命名规范

### 格式
```
{task_name}_{YYMMDDHHmmss}_{4位随机数}.csv
```

### 组成部分
- **task_name**: 任务名称（如 `flfg`, `comments`, `export_法律法规`）
- **YYMMDDHHmmss**: 时间戳（年月日时分秒）
- **4位随机数**: 小写字母+数字组合（防止冲突）

### 示例
```
flfg_251017083045_a3f2.csv
comments_251017083512_x9k1.csv
export_法律法规_251017084235_k7m3.csv
```

## 使用方法

### 在代码中使用

```python
from csv_manager import get_csv_path, list_csv_files, get_latest_csv

# 生成新的CSV路径（自动创建csv_exports目录）
csv_path = get_csv_path("my_task")
# 返回: csv_exports/my_task_251017083045_x7a2.csv

# 写入CSV
with open(csv_path, 'w', encoding='utf-8-sig', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['列1', '列2'])
    writer.writerow(['数据1', '数据2'])

# 列出所有CSV文件（按修改时间倒序）
files = list_csv_files()
for file in files:
    print(f"文件: {file.name}, 大小: {file.stat().st_size} bytes")

# 获取特定任务的最新CSV文件
latest = get_latest_csv("flfg")
if latest:
    print(f"最新的flfg文件: {latest.name}")
```

### 在Web界面使用

1. 访问 http://localhost:8000
2. 执行爬虫任务
3. 在"文件列表"中查看和下载CSV文件
4. 每次导出都会生成新的唯一文件

## 优势

✅ **不再污染根目录** - 所有CSV文件集中管理
✅ **自动去重** - 时间戳+随机数保证文件名唯一
✅ **易于追踪** - 文件名包含任务名和时间信息
✅ **便于清理** - 可以安全删除整个csv_exports目录
✅ **版本控制友好** - csv_exports/被.gitignore排除

## 迁移已完成

已执行 `migrate_csv_files.py` 将根目录的4个旧CSV文件移动到 `csv_exports/` 目录：

- `chinatax_comments.csv` → `chinatax_comments_251017090738_s463.csv`
- `chinatax_comments2015.csv` → `chinatax_comments2015_251017090738_9nuc.csv`
- `chinatax_flfg.csv` → `chinatax_flfg_251017090738_66fz.csv`
- `export_comments_20251017_083512.csv` → `export_comments_20251017_083512_251017090738_68oe.csv`

## 测试验证

```bash
# 测试CSV管理器
python csv_manager.py

# 启动Web应用
python web_app.py

# 访问 http://localhost:8000 验证文件列表
```

## 向后兼容性

- 数据库存储**不受影响** - 所有爬虫仍然将数据存入数据库
- Web API接口**保持兼容** - 端点路径未变，只是内部实现改变
- 旧的CSV文件已迁移到新目录

## 注意事项

⚠️ **重要**:
- 不要手动在根目录创建CSV文件
- 始终使用 `csv_manager.get_csv_path()` 生成路径
- CSV文件仅用于导出，主数据存储在数据库中
