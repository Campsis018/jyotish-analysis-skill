# 印占体系分析 · Jyotish Analysis Skill

一套中文印度占星分析工作流，将本命、Yoga、分盘、个人指标星和时间预测组织成可复查的完整流程。适用于支持 `SKILL.md` 的AI代理，也可作为手工分析清单使用。

核心方法：**D1结构与行星状态 → Yoga/相位/处置链 → D9/D10及专题分盘 → 个体化专题 → Vimshottari主轴与多层计时复核。**

“完整”指这一套分析流程、输入要求、判断方法和交付模板完整，不表示囊括印度占星所有流派，也不表示内置完整排盘引擎。

## 方法特点

- 继承原始成盘与明确设置，不静默切换岁差、宫制、年长、分盘或指标星算法。
- 分开读取结构资格、Shadbala发力、苦乐果顺阻、宫位承载和跨分盘质量。
- 八星制Chara Karaka全部进入主题判断，保留原软件的双标签与空标签；不只看AK/AmK/DK。
- Vimshottari MD/AD/PD是主时间轴；一套Rashi大运复核环境，出生地TP复核年度，过境与八分点复核触发及顺阻。
- 规则内支持充分就明确结论，发现具体错误才纠正；不制造平衡式反证，不静默推翻旧版。
- 旧报告保留有效坐标和日界，按新证据逐项标记不变、加强、削弱、移期、取消或主题重命名。

这些是本项目采用的口径，尤其八星制、节点相位及TP规则，不代表所有Jyotish流派均如此处理。已有明确用户设置时优先继承并登记差异。

## 目录

| 位置 | 内容 |
| --- | --- |
| `skills/analyze-jyotish/SKILL.md` | 触发描述、核心流程与完成标准 |
| `skills/analyze-jyotish/references/01–10` | 输入口径、D1、Yoga、分盘、指标星、专题、计时、修订、案例、来源 |
| `skills/analyze-jyotish/assets/` | 报告模板、输入JSON模板与合成示例 |
| `skills/analyze-jyotish/scripts/chart_audit.py` | 无网络、标准库数学校核 |
| `tests/test_chart_audit.py` | 数学边界、错误输入、日界与链接测试 |
| `.github/workflows/check.yml` | GitHub Actions自动检查 |

## 使用

将整个 `skills/analyze-jyotish/` 文件夹放入所用代理支持的skill目录，按该代理的加载方式启用。必须保留references、assets和scripts，单独复制SKILL.md会丢失完整方法。

也可直接让支持读取本地文件的AI先读取该SKILL.md，再按其中链接加载需要的参考。以下为示例请求：

> 使用 analyze-jyotish，根据我提供的JHora成盘与大运表做完整五阶段分析。先核对口径，保留原八星制标签，分清成就与成本，给出能追溯到原表的结论。

> 核验我对这条Yoga的判断。先列实际配置和采用定义，成立就确认；若不成立，指出哪项条件不满足。

> 复核旧报告的未来半年窗口。保留正确运期，核对指标角色、D9/D10、TP与触发；给出逐条修订表。

输入以成盘/导出表为优先，尽量包含D1精确度数、D9及相关专题分盘、指标星、力量表、MD/AD/PD边界和设置。没有某项就标缺失；不要为了凑齐报告填猜测值。出生资料或原盘含个人信息时，仅在个人分析会话中提供，不提交到公开仓库。

## 运行校核

Python 3.10及以上，无第三方依赖。从本仓库根目录运行：

```bash
python3 skills/analyze-jyotish/scripts/chart_audit.py skills/analyze-jyotish/assets/synthetic-chart.json
python3 skills/analyze-jyotish/scripts/chart_audit.py skills/analyze-jyotish/assets/synthetic-chart.json --output audit.json
python3 skills/analyze-jyotish/scripts/chart_audit.py --split-start 2030-01-01T00:00:00+00:00 --split-end 2031-01-01T00:00:00+00:00 --lord Jupiter
python3 -m unittest discover -s tests -v
```

脚本仅核对**已提供的恒星黄经**与整宫、标准D9、27宿/Pada、交点对轴、处置链；按完整父运范围做比例分运。不重新分配指标角色，不从出生资料计算星历或大运余额。合成样例不是现实天象，也不对应真实个人。

退出码：`0`为未发现已核对字段冲突（仍可能有缺项警告），`1`为发现冲突，`2`为输入/参数错误。`status=incomplete`不等于数据完整或排盘验证通过；数学一致也不表示现实出生资料正确。

`assets/input-template.json`是空表单，未知值为null。填好后再运行；不应期望空模板通过坐标校核。

## 适用范围

可用于本命、事业、财富、关系、教育、家庭家宅、分盘整合、长期阶段、年度/月度窗口、多人分维度比较与旧报告纠错。

本包不实现Prashna、Muhurta、完整Tajaka、完整出生时间校正、补救法或天文历表。缺少计算引擎时从可靠成盘读取，不用语言补造计算结果。

占星解释未被确立为经现代科学验证的人格测量或事件预测模型。这里的“证据等级”表示传统框架内的支持与计算完整度，不是概率或确定性保证。现实事实与推论分开，不用盘面代替诊断、法律意见或财务判断。

## 分享到GitHub

新建仓库后，上传**这个目录中的文件和文件夹**，保留根目录README、LICENSE、skills、tests和GitHub工作流。无需上传个人出生资料或私人报告。使用命令行的读者也可以在本目录初始化自己的Git仓库后，按GitHub新仓库页面给出的命令上传。

建议仓库名：`jyotish-analysis-skill`；简介：`A Chinese Jyotish analysis skill with traceable chart reasoning, varga synthesis and layered timing.`

提交改进时，附所用规则出处、完整设置、虚构或获得公开授权的最小示例，以及修改前后的具体差异。涉及预测规则须区分方法选择和已验证计算；不要仅凭单次吻合宣称准确率。

## 许可

本仓库原创说明、脚本与模板采用MIT许可，允许复制、修改及再分发，并保留许可声明。第三方书籍、软件、历表与外链资料的权利仍归其权利人；本仓库不打包或再授权它们。
