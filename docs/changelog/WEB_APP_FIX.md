# Web 应用修复说明

## 🐛 问题描述

Web 应用在数据库重构后，CSV 文件列表加载失败。

## ✅ 修复内容

### 1. 恢复 CSV 文件列表功能

保留了 `/api/files` 端点用于列出 CSV 文件（向后兼容）：

```http
GET /api/files
```

返回示例：
```json
{
  "files": [
    {
      "name": "chinatax_flfg.csv",
      "path": "/path/to/chinatax_flfg.csv",
      "size": 1024000,
      "size_mb": 1.0,
      "modified": "2025-10-12T10:30:00",
      "rows": 100
    }
  ]
}
```

### 2. 新增数据库统计端点

添加了新的端点获取数据库统计信息：

```http
GET /api/database/stats
```

返回示例：
```json
{
  "database_type": "sqlite",
  "tables": [
    {
      "name": "flfg_records",
      "display_name": "法律法规记录",
      "total_rows": 100,
      "downloaded": 80,
      "not_downloaded": 20
    },
    {
      "name": "comment_records",
      "display_name": "留言记录",
      "total_rows": 50,
      "downloaded": 30,
      "not_downloaded": 20
    }
  ]
}
```

### 3. 保留 CSV 文件预览和下载

```http
GET /api/files/{filename}/preview?limit=10
GET /api/files/{filename}/download
```

### 4. 新增数据库记录预览

```http
GET /api/records/flfg/preview?limit=10
GET /api/records/comments/preview?limit=10
```

## 📡 完整 API 列表

### 任务管理
- `GET /api/tasks` - 获取所有任务状态
- `GET /api/task/{task_id}` - 获取特定任务状态

### 爬虫任务
- `POST /api/flfg/scrape` - 启动法律法规爬虫
- `POST /api/comments/scrape` - 启动留言爬虫
- `POST /api/comments/download` - 下载留言详情
- `POST /api/flfg/download` - 下载法律法规详情

### 数据查询（新）
- `GET /api/database/stats` - 获取数据库统计信息 ⭐ 新增
- `GET /api/records/flfg/preview` - 预览法律法规记录 ⭐ 新增
- `GET /api/records/comments/preview` - 预览留言记录 ⭐ 新增

### 文件管理（兼容旧版）
- `GET /api/files` - 列出 CSV 文件
- `GET /api/files/{filename}/preview` - 预览 CSV 文件
- `GET /api/files/{filename}/download` - 下载 CSV 文件

## 🚀 使用方式

### 启动 Web 服务

```bash
# 确保数据库已初始化
python db_config.py

# 启动 Web 服务
python web_app.py
```

访问地址：
- 管理后台: http://localhost:8000
- API 文档: http://localhost:8000/docs
- ReDoc 文档: http://localhost:8000/redoc

### 示例：获取数据库统计

```bash
curl http://localhost:8000/api/database/stats
```

### 示例：预览法律法规记录

```bash
curl http://localhost:8000/api/records/flfg/preview?limit=5
```

### 示例：列出 CSV 文件

```bash
curl http://localhost:8000/api/files
```

## 🎯 前端建议

如果你的前端之前调用 `/api/files` 获取文件列表，现在依然可以正常工作。

如果你想使用新的数据库功能，可以：

```javascript
// 1. 获取数据库统计（推荐）
fetch('/api/database/stats')
  .then(res => res.json())
  .then(data => {
    console.log('数据库类型:', data.database_type);
    data.tables.forEach(table => {
      console.log(`${table.display_name}: ${table.total_rows} 条记录`);
    });
  });

// 2. 预览数据库记录（推荐）
fetch('/api/records/flfg/preview?limit=10')
  .then(res => res.json())
  .then(data => {
    console.log('法律法规记录:', data.records);
  });

// 3. 兼容：继续使用 CSV 文件列表
fetch('/api/files')
  .then(res => res.json())
  .then(data => {
    console.log('CSV 文件:', data.files);
  });
```

## 🔄 迁移建议

### 推荐做法

1. **新功能使用数据库 API**
   - 使用 `/api/database/stats` 获取统计
   - 使用 `/api/records/*/preview` 预览记录

2. **保持 CSV 文件管理**
   - CSV 文件仍然可以查看、预览、下载
   - 用于数据备份和迁移

3. **逐步迁移**
   - 旧页面继续使用 `/api/files`
   - 新页面使用数据库 API

## 📝 注意事项

1. **数据一致性**
   - 数据库是主要数据源
   - CSV 文件仅用于备份和兼容

2. **性能考虑**
   - 数据库查询比 CSV 文件读取更快
   - 建议优先使用数据库 API

3. **向后兼容**
   - 所有旧的 API 端点保持不变
   - 可以平滑迁移

## 🐛 故障排查

### 问题：API 返回 500 错误

**解决方案：**
```bash
# 检查数据库是否初始化
python db_config.py

# 测试数据库连接
python -c "from db_config import test_connection; print('✅ 成功' if test_connection() else '❌ 失败')"
```

### 问题：CSV 文件列表为空

这是正常的！新版本使用数据库存储，不再生成 CSV 文件。

如果需要导出 CSV：
```bash
# 从数据库导出到 CSV
python migrate_csv_to_db.py --export
```

## 📚 相关文档

- [Web 应用更新说明](WEB_APP_UPDATED.md)
- [快速开始](QUICKSTART.md)
- [数据库配置](DATABASE_GUIDE.md)

---

**修复时间**: 2025-10-12  
**版本**: 2.0.1
