#!/usr/bin/env python3
"""
转换CSV文件为UTF-8 BOM格式，使其在Excel中正确显示中文

用法：
    python fix_csv_encoding.py [csv文件路径]

示例：
    python fix_csv_encoding.py chinatax_comments.csv
"""

import csv
import sys
from pathlib import Path


def convert_to_utf8_bom(csv_path: Path):
    """将CSV文件转换为UTF-8 BOM格式"""
    if not csv_path.exists():
        print(f"❌ 错误：文件不存在 - {csv_path}")
        return False

    try:
        # 读取所有数据
        print(f"📖 正在读取文件: {csv_path}")
        all_data = []
        with open(csv_path, 'r', encoding='utf-8', newline='') as f:
            reader = csv.reader(f)
            all_data = list(reader)

        # 备份原文件
        backup_path = csv_path.with_suffix(csv_path.suffix + '.bak')
        print(f"💾 创建备份: {backup_path}")
        csv_path.rename(backup_path)

        # 用UTF-8-BOM重写文件
        print(f"✍️  写入UTF-8 BOM格式...")
        with open(csv_path, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(all_data)

        print(f"✅ 转换成功！")
        print(f"   - 文件: {csv_path}")
        print(f"   - 记录数: {len(all_data) - 1}")
        print(f"   - 备份: {backup_path}")
        print(f"\n💡 现在可以用Excel正确打开 {csv_path.name} 了！")

        return True

    except Exception as e:
        print(f"❌ 转换失败: {e}")
        # 如果转换失败，恢复备份
        if backup_path.exists():
            backup_path.rename(csv_path)
            print(f"已恢复原文件")
        return False


def main():
    if len(sys.argv) < 2:
        # 默认转换当前目录下的chinatax_comments.csv
        csv_path = Path('chinatax_comments.csv')
        if not csv_path.exists():
            print("用法: python fix_csv_encoding.py [csv文件路径]")
            print("示例: python fix_csv_encoding.py chinatax_comments.csv")
            return
    else:
        csv_path = Path(sys.argv[1])

    convert_to_utf8_bom(csv_path)


if __name__ == '__main__':
    main()
