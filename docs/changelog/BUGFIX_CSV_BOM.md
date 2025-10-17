# Bug修复记录

## 问题描述
在Web界面使用"下载法律法规详情"功能时，出现错误：
```
任务失败: CSV 文件缺少必要的列: 序号
```

## 根本原因
1. CSV文件使用`utf-8-sig`编码写入（包含BOM字符）
2. `chinatax_scheduler.py`中的`load_csv_records()`函数使用普通`utf-8`编码读取
3. 导致第一个列名前面包含不可见的BOM字符（`\ufeff序号`），与预期的"序号"不匹配

## 修复方案
修改 `flfg_scraper/chinatax_scheduler.py` 文件中的两个函数：

### 1. `load_csv_records()` 函数
- 将编码从 `utf-8` 改为 `utf-8-sig`
- 添加列名清理逻辑（去除空格和特殊字符）

### 2. `update_csv_record()` 函数
- 读取时使用 `utf-8-sig` 编码
- 写入时也使用 `utf-8-sig` 编码，保持一致性

## 测试验证
```bash
# 测试1: 验证CSV读取
python3 -c "
from pathlib import Path
import sys
sys.path.insert(0, 'flfg_scraper')
from chinatax_scheduler import load_csv_records
records = load_csv_records(Path('chinatax_flfg.csv'))
print(f'✅ 成功读取 {len(records)} 条记录')
"

# 测试2: 验证列名正确
python3 -c "
from pathlib import Path
import sys
sys.path.insert(0, 'flfg_scraper')
from chinatax_scheduler import load_csv_records
records = load_csv_records(Path('chinatax_flfg.csv'))
print(f'列名: {list(records[0].keys())}')
print('✅ 包含序号列' if '序号' in records[0] else '❌ 缺少序号列')
"
```

## 影响范围
- ✅ Web界面的"下载法律法规详情"功能现在可以正常工作
- ✅ 命令行工具 `chinatax_scheduler.py` 也已修复
- ✅ 与Excel的兼容性得到保持（BOM帮助Excel正确识别UTF-8）

## 预防措施
建议在所有CSV读写操作中统一使用 `utf-8-sig` 编码：
- 写入CSV时使用 `encoding="utf-8-sig"` （已在爬虫中使用）
- 读取CSV时也使用 `encoding="utf-8-sig"` （已修复）

## 修复时间
2025-10-12

## 修复文件
- `flfg_scraper/chinatax_scheduler.py`
