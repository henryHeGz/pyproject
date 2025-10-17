# CSV文件名和任务日志功能实现总结

## 完成的功能

### 1. 已完成任务显示CSV文件名

在已完成任务卡片中，如果任务生成了CSV文件，会显示一个蓝色背景的信息框：

```
📊 CSV文件: export_法律法规_251017084235_k7m3.csv
```

**实现逻辑：**
- 从数据库的 `tasks` 表中读取 `csv_path` 字段
- 提取文件名（只显示文件名，不显示完整路径）
- 只在有CSV文件时显示此信息框

### 2. 查看任务日志按钮

每个已完成的任务都有一个"查看日志"按钮（橙色）：

**功能特性：**
- 点击按钮打开模态弹窗
- 异步加载日志内容
- 使用深色主题显示日志（类似VSCode终端）
- 自动高亮不同级别的日志：
  - `[INFO]` - 青色
  - `[WARNING]` - 黄色
  - `[ERROR]` - 红色

### 3. 日志查看弹窗

**弹窗特性：**
- 居中显示，最大宽度900px
- 最大高度80vh，内容超出可滚动
- 支持三种关闭方式：
  1. 点击×按钮
  2. 点击弹窗外部灰色区域
  3. 按ESC键
- 深色主题，模拟终端效果
- 等宽字体显示，保持格式

## 前端代码修改

### HTML结构

添加了日志弹窗HTML：

```html
<div id="logModal" class="modal">
    <div class="modal-content">
        <div class="modal-header">
            <h3>📋 任务执行日志</h3>
            <button class="modal-close" onclick="closeLogModal()">&times;</button>
        </div>
        <div class="modal-body">
            <div id="logContent" class="log-content">
                <!-- 日志内容 -->
            </div>
        </div>
    </div>
</div>
```

### CSS样式

新增样式类：
- `.modal` - 弹窗容器（全屏遮罩）
- `.modal.show` - 显示弹窗
- `.modal-content` - 弹窗主体
- `.modal-header` - 弹窗头部
- `.modal-close` - 关闭按钮
- `.modal-body` - 弹窗内容区
- `.log-content` - 日志显示区（深色主题）
- `.log-info` / `.log-warning` / `.log-error` - 日志级别颜色

### JavaScript函数

新增函数：

```javascript
async function viewTaskLog(taskId) {
    // 显示弹窗
    // 调用 /api/tasks/{taskId}/log 获取日志
    // 高亮显示日志内容
}

function closeLogModal() {
    // 关闭弹窗
}
```

## 任务卡片示例

### 完整的任务卡片HTML

```html
<div class="task-item completed">
    <div class="task-header">
        <span class="task-type">留言爬虫 [留言公开]</span>
        <span class="task-status completed">✅ 完成</span>
    </div>
    <div class="task-message">任务完成！新增 0 条记录</div>
    <div class="task-time">
        开始: 2025/10/17 09:10:13
        | 结束: 2025/10/17 01:10:18
    </div>
    <!-- CSV文件信息（如果有） -->
    <div style="margin-top: 8px; padding: 8px; background: #e6f7ff; border-radius: 4px; font-size: 13px;">
        📊 CSV文件: <code>export_留言公开_251017091018_x9k1.csv</code>
    </div>
    <!-- 操作按钮 -->
    <div class="file-actions" style="margin-top: 10px;">
        <button class="button" onclick="previewTaskData('...')">预览数据</button>
        <button class="button secondary" onclick="exportTaskData('...')">导出CSV</button>
        <button class="button tertiary" onclick="viewTaskLog('...')">查看日志</button>
    </div>
</div>
```

## API接口

### GET /api/tasks/{task_id}/log

获取任务执行日志

**请求：**
```
GET /api/tasks/flfg_20251017_091811/log
```

**响应：**
```json
{
  "task_id": "flfg_20251017_091811",
  "log_content": "2025-10-17 09:18:11 - [INFO] - ============================================================\n2025-10-17 09:18:11 - [INFO] - 任务开始: 法律法规爬虫\n...",
  "log_file": "/path/to/task_logs/flfg_20251017_091811.log"
}
```

## 数据库字段

### tasks表相关字段

```sql
csv_path VARCHAR(255)  -- CSV文件路径（如果任务生成了CSV）
log_file VARCHAR(255)  -- 日志文件路径（每个任务都有）
```

## 用户体验流程

1. 用户启动一个爬虫任务
2. 任务完成后，在"已完成的任务"列表中看到：
   - 任务基本信息（类型、状态、时间）
   - CSV文件名（如果有生成）
   - 三个操作按钮：预览数据、导出CSV、查看日志
3. 点击"查看日志"按钮
4. 弹出日志查看窗口，显示任务执行的详细日志
5. 日志内容包括：
   - 任务开始时间和参数
   - 执行过程中的进度信息
   - 警告和错误信息
   - 任务结束状态和时间
6. 关闭弹窗，返回任务列表

## 特色功能

### 1. 智能显示CSV文件名

- 只在任务实际生成CSV时显示
- 自动提取文件名（不显示完整路径）
- 使用醒目的蓝色背景高亮显示
- 使用 `<code>` 标签显示文件名，提高可读性

### 2. 日志高亮显示

- [INFO] 信息 - 青色 (#4ec9b0)
- [WARNING] 警告 - 黄色 (#dcdcaa)
- [ERROR] 错误 - 红色 (#f48771)
- 深色背景 (#1e1e1e)，模拟终端效果
- 等宽字体，保持格式对齐

### 3. 友好的交互体验

- 弹窗动画流畅
- 多种关闭方式（×按钮、点击外部、ESC键）
- 加载状态提示
- 错误提示清晰明确

## 测试建议

### 1. 启动一个测试任务

```bash
# 启动Web服务
python web_app.py

# 在浏览器访问
http://localhost:8000
```

### 2. 测试CSV显示

- 启动一个会生成CSV的任务（如导出任务）
- 等待任务完成
- 查看"已完成的任务"列表
- 确认CSV文件名正确显示

### 3. 测试日志查看

- 点击"查看日志"按钮
- 确认弹窗正常打开
- 确认日志内容正确加载
- 确认日志高亮显示正常
- 测试三种关闭方式

## 截图示例

### 任务卡片效果

```
┌─────────────────────────────────────────────────┐
│ 留言爬虫 [留言公开]              ✅ 完成        │
├─────────────────────────────────────────────────┤
│ 任务完成！新增 0 条记录                         │
│ 开始: 2025/10/17 09:10:13 | 结束: 2025/10/17... │
├─────────────────────────────────────────────────┤
│ 📊 CSV文件: export_留言公开_251017091018_x9k1.csv │
├─────────────────────────────────────────────────┤
│ [预览数据] [导出CSV] [查看日志]                 │
└─────────────────────────────────────────────────┘
```

### 日志弹窗效果

```
┌────────────────────────────────────────────┐
│  📋 任务执行日志                     ×    │
├────────────────────────────────────────────┤
│ ╔══════════════════════════════════════╗  │
│ ║ 2025-10-17 09:18:11 - [INFO] - 任务  ║  │
│ ║ 开始: 法律法规爬虫                   ║  │
│ ║ 2025-10-17 09:18:11 - [INFO] - 任务  ║  │
│ ║ ID: flfg_20251017_091811            ║  │
│ ║ 2025-10-17 09:18:12 - [WARNING] -   ║  │
│ ║ 发现重复记录                         ║  │
│ ║ 2025-10-17 09:20:45 - [INFO] - 任务  ║  │
│ ║ 结束: COMPLETED                      ║  │
│ ╚══════════════════════════════════════╝  │
└────────────────────────────────────────────┘
```

## 文件清单

修改的文件：
- [templates/index.html](../templates/index.html) - 前端模板

新增内容：
- CSS样式：日志弹窗相关样式
- HTML结构：日志弹窗DOM
- JavaScript函数：`viewTaskLog()`, `closeLogModal()`
- 任务卡片显示：CSV文件名显示区域
- 任务操作按钮：查看日志按钮

## 下一步优化建议

1. **日志实时刷新** - 运行中的任务可以实时查看日志更新
2. **日志下载** - 添加下载日志文件的功能
3. **日志搜索** - 在弹窗中添加搜索功能
4. **日志过滤** - 按级别（INFO/WARNING/ERROR）过滤
5. **性能优化** - 超大日志文件分页加载

## 完成时间

2025年10月17日
