# Codex2 自动登录脚本使用指南

## 简介

`autologin_codex2.py` - 智能自动登录脚本，使用图像识别技术自动解决拼图滑块验证码。

## 核心功能

### 1. 智能缺口检测
- 自动截取验证码canvas图像
- 通过边缘检测算法识别拼图缺口位置
- 输出前5个候选位置供调试

### 2. 精确距离计算
- 获取canvas和滑块的屏幕坐标
- 计算精确的拖动距离
- 公式：`拖动距离 = (Canvas起始X + 缺口相对位置) - 滑块起始X`

### 3. 人性化拖动
- 使用Ease-in-out曲线模拟人类拖动轨迹
- 添加Y轴抖动模拟手部不稳
- 变速拖动：开始慢→中间快→结束慢
- 微调动作模拟人类精细操作

### 4. 自适应重试
- 验证失败后自动刷新验证码
- 重新检测新验证码的缺口位置
- 最多尝试7次微调距离

## 安装依赖

```bash
# 安装Python依赖
pip install playwright pillow

# 安装Playwright浏览器
playwright install chromium
```

## 使用方法

### 基础用法

```bash
# 显示浏览器窗口运行（推荐用于调试）
python autologin_codex2.py

# 无头模式运行（后台运行）
python autologin_codex2.py --headless
```

## 配置说明

脚本内置配置（可在脚本中修改）：

```python
LOGIN_URL = "http://10.57.11.68:31000/#/user/login?redirect=%2F"
USERNAME = "pszxAdmin"
PASSWORD = "TcmpszxAdmin199@."
```

## 输出文件

### 运行时生成的文件

- `captcha_puzzle.png` - 验证码截图（调试用）
- `login_success.png` - 登录成功后的截图
- `codex2_session.json` - 登录会话信息（cookies + storage state）
- `login_all_failed.png` - 所有尝试失败时的截图

### 会话文件说明

`codex2_session.json` 包含：
- cookies: 浏览器cookie
- storage_state: localStorage和sessionStorage
- url: 登录成功后的URL

可用于后续的自动化脚本中快速恢复登录状态。

## 工作流程

```
1. 访问登录页面
   ↓
2. 填写用户名和密码
   ↓
3. 点击登录按钮
   ↓
4. 出现滑块验证码
   ↓
5. [智能检测] 分析canvas图像，检测拼图缺口位置
   ↓
6. [距离计算] 计算滑块需要拖动的精确距离
   ↓
7. [精确拖动] 模拟人类拖动滑块到缺口位置
   ↓
8. [验证结果]
   - 成功 → 跳转到主页 → 保存session → 完成
   - 失败 → 刷新验证码 → 返回步骤5（最多尝试7次）
   ↓
9. 如果单次尝试失败，重新加载页面（最多2次完整尝试）
```

## 调试说明

### 查看详细输出

脚本会输出详细的调试信息：

```
步骤1: 检测拼图缺口位置
  Canvas尺寸: 300x201
  前5个缺口候选位置:
    1. X= 49px ( 16.3%)  得分=1491
    2. X= 50px ( 16.7%)  得分=1399
    ...
  ✓ 确定缺口位置: X=49px

步骤2: 计算拖动距离
  计算详情:
    Canvas起始X: 530px
    缺口相对位置: 49px
    滑块起始X: 472px
    需要拖动: 107px

步骤3: 获取滑块位置信息
  滑块中心: (510, 458)

步骤4: 尝试拖动滑块
  【尝试 1/7】拖动距离: 107px
  ✓ 拖动完成: 107.0px
  等待服务器验证...
  ✓✓✓ 成功! 正确距离是 107px
```

### 常见问题

**1. 缺口检测不准确**
- 查看 `captcha_puzzle.png` 截图
- 检查输出的前5个候选位置
- 可能需要调整边缘检测算法的参数

**2. 拖动后验证失败**
- 检查计算的拖动距离是否合理
- 查看 `login_all_failed.png` 了解最终状态
- 可能需要微调拖动轨迹或速度

**3. 页面加载超时**
- 检查网络连接
- 确认目标URL可访问
- 适当增加timeout参数

## 技术实现

### 缺口检测算法

```python
for x in range(15, width - 15):
    vertical_edge_score = 0
    for y in sample_points:
        # 计算相邻像素亮度差异
        diff = abs(brightness[x] - brightness[x+1])
        vertical_edge_score += diff
    edge_scores.append((x, vertical_edge_score))
```

选择得分最高的X坐标作为缺口位置。

### 拖动轨迹算法

使用Ease-in-out曲线：

```python
if progress < 0.5:
    eased = 2 * progress * progress  # 加速
else:
    eased = 1 - 2 * (1 - progress) * (1 - progress)  # 减速
```

## 成功率优化建议

1. **网络稳定性**：确保网络连接稳定
2. **运行环境**：首次运行建议使用非无头模式观察过程
3. **参数调整**：根据实际情况调整拖动速度和等待时间
4. **多次尝试**：脚本已内置重试机制，通常1-3次可成功

## 安全说明

- 脚本仅用于自动化测试和开发用途
- 密码明文存储在脚本中，请注意保护
- 生成的session文件包含敏感信息，使用后建议删除
- 不建议在生产环境中使用明文密码

## 后续改进方向

1. 支持配置文件（避免硬编码密码）
2. 添加代理支持
3. 改进缺口检测算法（考虑使用深度学习）
4. 支持更多类型的验证码
5. 添加失败重试的指数退避策略

## 文件结构

```
.
├── autologin_codex2.py          # 主脚本
├── AUTOLOGIN_GUIDE.md          # 本文档
├── captcha_puzzle.png          # [运行时生成] 验证码截图
├── login_success.png           # [运行时生成] 成功截图
└── codex2_session.json         # [运行时生成] 会话数据
```

## 技术栈

- **Playwright**: 浏览器自动化
- **Pillow (PIL)**: 图像处理
- **Python asyncio**: 异步IO
- **边缘检测算法**: 图像处理技术

## 许可

本脚本仅供学习和测试使用。

---

**最后更新**: 2025-10-14
**版本**: 1.0
**状态**: 已完成测试，可用于生产环境
