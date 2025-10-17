# Web 应用更新说明

## 📋 更新内容

Web 应用（web_app.py）已更新以支持新的数据库架构。

### ✅ 主要变更

1. **移除 CSV 依赖**
   - ❌ 删除所有 CSV 文件路径参数
   - ✅ 直接使用数据库读取和写入

2. **更新 API 接口**
   - `/api/files` → 返回数据库统计信息（替代 CSV 文件列表）
   - `/api/records/flfg/preview` → 预览法律法规记录
   - `/api/records/comments/preview` → 预览留言记录

3. **更新请求参数**
   - 移除所有 `csv_path` 参数
   - 保留其他功能参数（headless, start_page 等）

4. **数据库集成**
   - 使用 `get_db_cursor()` 读取数据
   - 使用 `update_record_status()` 更新状态
   - 支持 SQLite 和 MySQL（通过 DB_TYPE 环境变量）

## 🚀 启动 Web 应用

```bash
# 确保数据库已初始化
python db_config.py

# 启动 Web 服务
python web_app.py
```

访问地址：http://localhost:8000

## 📡 API 变更对照

### 获取数据统计

**旧版（CSV）:**
```http
GET /api/files
返回: CSV 文件列表
```

**新版（数据库）:**
```http
GET /api/files
返回: {
  "database_type": "sqlite",
  "tables": [
    {
      "name": "flfg_records",
      "display_name": "法律法规记录",
      "total_rows": 100,
      "downloaded": 80,
      "not_downloaded": 20
    },
    ...
  ]
}
```

### 预览数据

**新增接口:**
```http
GET /api/records/flfg/preview?limit=10
GET /api/records/comments/preview?limit=10
```

### 启动爬虫任务

**旧版:**
```json
POST /api/flfg/scrape
{
  "csv_path": "chinatax_flfg.csv",
  "start_page": 1,
  "page_count": 10,
  "headless": true
}
```

**新版:**
```json
POST /api/flfg/scrape
{
  "start_page": 1,
  "page_count": 10,
  "headless": true
}
```

## 🔧 前端适配建议

如果你有自定义前端，需要更新以下部分：

### 1. 文件列表显示

```javascript
// 旧代码
fetch('/api/files')
  .then(res => res.json())
  .then(data => {
    // data.files 是 CSV 文件列表
  });

// 新代码
fetch('/api/files')
  .then(res => res.json())
  .then(data => {
    // data.tables 是数据库表统计
    data.tables.forEach(table => {
      console.log(`${table.display_name}: ${table.total_rows} 条记录`);
    });
  });
```

### 2. 启动爬虫任务

```javascript
// 旧代码
fetch('/api/flfg/scrape', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    csv_path: 'chinatax_flfg.csv',  // ❌ 移除此参数
    start_page: 1,
    headless: true
  })
});

// 新代码
fetch('/api/flfg/scrape', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    start_page: 1,
    headless: true
  })
});
```

### 3. 预览数据

```javascript
// 新增功能：预览法律法规记录
fetch('/api/records/flfg/preview?limit=10')
  .then(res => res.json())
  .then(data => {
    console.log(`预览 ${data.count} 条记录`);
    data.records.forEach(record => {
      console.log(record);
    });
  });

// 新增功能：预览留言记录
fetch('/api/records/comments/preview?limit=10')
  .then(res => res.json())
  .then(data => {
    console.log(`预览 ${data.count} 条记录`);
  });
```

## 📄 完整 API 列表

### 任务管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/tasks` | 获取所有任务状态 |
| GET | `/api/task/{task_id}` | 获取特定任务状态 |

### 爬虫任务

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/flfg/scrape` | 启动法律法规爬虫 |
| POST | `/api/comments/scrape` | 启动留言爬虫 |
| POST | `/api/comments/download` | 下载留言详情 |
| POST | `/api/flfg/download` | 下载法律法规详情 |

### 数据查询

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/files` | 获取数据库统计 |
| GET | `/api/records/flfg/preview` | 预览法律法规记录 |
| GET | `/api/records/comments/preview` | 预览留言记录 |

## 🐛 常见问题

### Q: Web 应用无法启动

**A:** 确保已初始化数据库
```bash
python db_config.py
```

### Q: API 返回 500 错误

**A:** 检查数据库连接
```bash
# 测试数据库连接
python -c "from db_config import test_connection; print('成功' if test_connection() else '失败')"
```

### Q: 如何切换数据库类型？

**A:** 设置环境变量后重启 Web 应用
```bash
# 使用 MySQL
export DB_TYPE=mysql
export MYSQL_HOST=localhost
export MYSQL_USER=root
export MYSQL_PASSWORD=password
export MYSQL_DATABASE=chinatax

# 重启 Web 应用
python web_app.py
```

## 📚 相关文档

- [快速开始](QUICKSTART.md)
- [数据库配置](DATABASE_GUIDE.md)
- [API 文档](http://localhost:8000/docs) - 启动后访问

---

**最后更新**: 2025-10-12  
**版本**: 2.0.0
