# 任务管理功能更新说明

## 更新概述

本次更新为爬虫管理后台添加了完整的任务持久化和管理功能，包括：

1. ✅ **数据库持久化** - 所有任务信息保存到数据库
2. ✅ **任务分类** - 按"法律法规"和"留言公开"分类管理任务
3. ✅ **已完成任务列表** - 独立显示已完成任务，支持分类筛选
4. ✅ **CSV导出和预览** - 可预览和导出每个任务相关的数据

## 数据库变更

### 新增表：tasks

```sql
CREATE TABLE tasks (
    task_id VARCHAR(64) PRIMARY KEY,          -- 任务唯一标识
    task_type VARCHAR(50) NOT NULL,           -- 任务类型（法律法规爬虫/留言爬虫等）
    task_category VARCHAR(50) NOT NULL,       -- 任务分类（法律法规/留言公开）
    status VARCHAR(20) NOT NULL,              -- 任务状态（running/completed/failed）
    params TEXT,                               -- 任务参数（JSON格式）
    message TEXT,                              -- 任务消息
    result TEXT,                               -- 任务结果（JSON格式）
    error TEXT,                                -- 错误信息
    csv_path VARCHAR(255),                     -- CSV文件路径
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**索引：**
- `idx_task_status` - 按状态查询
- `idx_task_category` - 按分类查询
- `idx_task_start_time` - 按开始时间排序

## 后端API更新

### 新增/修改的API端点

#### 1. 获取任务列表（支持筛选）
```
GET /api/tasks?status=running&category=法律法规&limit=50
```

**查询参数：**
- `status` - 任务状态（running/completed/failed）
- `category` - 任务分类（法律法规/留言公开）
- `limit` - 返回数量限制

#### 2. 获取已完成任务
```
GET /api/tasks/completed?category=法律法规&limit=50
```

**查询参数：**
- `category` - 可选，按分类筛选
- `limit` - 可选，默认50条

#### 3. 导出任务数据为CSV
```
GET /api/tasks/{task_id}/export
```

根据任务类型，自动从数据库导出相应的记录到CSV文件并下载。

### 任务创建流程

所有任务创建时都会：
1. 生成唯一的 `task_id`
2. 设置 `task_category`（法律法规/留言公开）
3. 保存到内存（用于快速访问）
4. 持久化到数据库

任务更新时会同时更新内存和数据库。

## 前端界面更新

### 1. 任务列表区域

**运行中的任务（📊）：**
- 只显示状态为 `running` 的任务
- 每3秒自动刷新
- 显示任务类型和分类标签

**已完成的任务（✅）：**
- 显示所有 `completed` 状态的任务
- 支持按分类筛选（全部/法律法规/留言公开）
- 每10秒自动刷新
- 每个任务提供两个按钮：
  - **预览数据** - 查看前10条记录
  - **导出CSV** - 下载完整CSV文件

### 2. 任务卡片显示格式

```
┌─────────────────────────────────────────┐
│ 法律法规爬虫 [法律法规]         ✅ 完成  │
│ 任务完成！新增 150 条记录                │
│ 开始: 2025-01-15 10:30:00               │
│ 结束: 2025-01-15 10:35:00               │
│ [预览数据]  [导出CSV]                   │
└─────────────────────────────────────────┘
```

## 使用指南

### 初始化数据库

如果是首次使用或需要重新初始化：

```bash
python db_config.py
```

### 启动Web应用

```bash
python web_app.py
```

或使用启动脚本：

```bash
bash start_web.sh
```

访问：http://localhost:8000

### 查看已完成的任务

1. 在前端页面滚动到"已完成的任务"区域
2. 使用下拉菜单选择分类（可选）
3. 点击"预览数据"查看前10条记录
4. 点击"导出CSV"下载完整数据

### 任务分类说明

| 分类 | 包含的任务类型 |
|------|---------------|
| 法律法规 | 法律法规爬虫、下载法律法规详情 |
| 留言公开 | 留言爬虫、下载留言详情 |

## 技术细节

### 数据持久化策略

1. **双存储机制**：
   - 内存存储（`task_status`）- 用于快速访问运行中的任务
   - 数据库存储 - 持久化所有任务历史

2. **自动同步**：
   - 任务创建时同步到数据库
   - 任务状态更新时同步到数据库
   - 前端优先从数据库加载历史任务

3. **时间戳管理**：
   - SQLite使用触发器自动更新 `end_time`
   - MySQL使用 `ON UPDATE` 自动更新

### CSV导出逻辑

导出时根据任务的 `category` 字段决定导出哪个表：
- **法律法规** → `flfg_records` 表
- **留言公开** → `comment_records` 表

导出文件命名格式：`export_{task_id}.csv`

## 数据库兼容性

支持两种数据库：
- **SQLite**（默认）- 适合单机部署
- **MySQL** - 适合生产环境

切换方式：设置环境变量 `DB_TYPE=mysql`

## 测试检查清单

- [x] 数据库表创建成功
- [x] Web应用导入无错误
- [x] 任务持久化到数据库
- [x] 已完成任务列表加载
- [x] 分类筛选功能
- [x] CSV导出功能
- [x] 数据预览功能
- [x] 前端页面更新

## 后续优化建议

1. 添加任务删除功能
2. 支持任务搜索（按关键词、日期范围）
3. 添加任务统计图表
4. 支持导出为Excel格式
5. 添加任务失败重试功能
6. 增加任务执行日志记录

## 文件变更清单

### 修改的文件
- `db_config.py` - 添加tasks表定义和辅助函数
- `web_app.py` - 添加任务持久化逻辑和新API端点
- `templates/index.html` - 更新前端界面

### 新增的文件
- `TASK_MANAGEMENT_UPDATE.md` - 本说明文档

---

**更新时间：** 2025-10-12
**版本：** v2.0.0
