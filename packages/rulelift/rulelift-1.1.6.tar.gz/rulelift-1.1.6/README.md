# rulelift - 信用风险规则有效性分析工具

## 项目概述

rulelift 是一个用于信用风险管理中策略规则自动挖掘、有效性分析及监控的 Python 工具包。它帮助风控团队评估规则的实际效果，识别冗余规则，优化策略组合，提高风险控制能力。

## 核心价值

在风控领域，规则系统因其配置便利和强解释性而广泛应用，但面临规则效果监控难、优化难的挑战。rulelift 提供了全面的解决方案：

- **规则评估**：解决规则拦截样本无标签的问题，借助客户评级分布差异，推算逾期率、召回率、精确率、lift 值等核心指标
- **实时监控**：支持基于生产数据的规则效果分析
- **规则挖掘**：自动从数据中挖掘有效的风控规则
- **策略优化**：评估策略组合效果，计算两两规则间的增益
- **可视化展示**：直观呈现规则效果和关系
- **成本效益高**：无需分流测试，基于规则命中用户记录即可评估规则效果

## 安装方法

### 使用 pip 安装（推荐）

```bash
pip install rulelift
```

### 从源码安装

```bash
git clone https://github.com/aialgorithm/rulelift.git
cd rulelift
pip install -e .
```

## 快速开始

### 1. 基本导入

```python
from rulelift import (
    load_example_data, analyze_rules, analyze_rule_correlation,
    calculate_strategy_gain, DecisionTreeRuleExtractor, VariableAnalyzer
)
```

### 2. 加载示例数据

利用规则拦截前后客户评级分布差异估算规则有效性。

#### 规则评估的示例数据结构
支持传入客户评级及对应坏账率 或者 实际逾期情况两种方式评估规则效果

| 字段名 | 描述 | 类型 | 示例值 |
|--------|------|------|--------|
| RULE | 规则名称 | 字符串 | 人行近3个月申请>10 |
| USER_ID | 用户唯一标识 | 字符串 | ID20221115003665 |
| HIT_DATE | 规则命中日期 | 日期 | 2022-10-01 |
| USER_LEVEL | 用户风险评级 | 整数 | 1 |
| USER_LEVEL_BADRATE | 评级对应坏账率 | 数值 | 0.2 |
| USER_TARGET | 实际逾期情况 | 整数 | 1（逾期）/ 0（未逾期） |
## 核心功能

### 1. 规则效度分析

```python
result = analyze_rules(
    df, 
    rule_col='RULE',              # 规则字段名
    user_target_col='user_level_badrate', # 用户评级情况或者实际逾期字段
    hit_date_col='HIT_DATE'        # 命中日期字段（可选，用于命中率监控）
)
```

### 2. 规则相关性分析

```python
correlation_matrix, max_correlation = analyze_rule_correlation(df)
print("\n=== 规则相关性矩阵 ===")
print(correlation_matrix.head())
```

### 3. 策略增益计算

```python
# 定义两个策略组
strategy1 = ['rule1', 'rule2']
strategy2 = ['rule1', 'rule2', 'rule3']

# 计算策略增益（strategy1 到 strategy2 的额外价值）
gain = calculate_strategy_gain(df, strategy1, strategy2, user_target_col='USER_TARGET')
print(f"\n策略增益: {gain:.4f}")
```

### 4. 规则挖掘
#### 规则挖掘数据示例
| 字段名 | 描述 | 类型 | 示例值 |
|--------|------|------|--------|
| feature | 特征 | 字符串 | 人行近3个月申请>10 |
| target_col | 用户标签 | bool | 0或1 |

#### 单特征规则挖掘

```python
from rulelift import SingleFeatureRuleMiner

# 初始化单特征规则挖掘器
sf_miner = SingleFeatureRuleMiner(min_coverage=0.05, min_badrate=0.1)

# 挖掘规则
sf_rules = sf_miner.fit_predict(X, y)
print(f"\n=== 单特征规则挖掘结果 ===")
for rule in sf_rules[:3]:
    print(f"特征: {rule['feature']}, 条件: {rule['condition']}, Badrate: {rule['badrate']:.4f}")
```

#### 多特征规则交叉分析

```python
from rulelift import MultiFeatureRuleMiner

multi_miner = MultiFeatureRuleMiner(df, target_col='ISBAD')
    
# 生成交叉规则
feature1 = df.columns[2]
feature2 = df.columns[3]
cross_rules = multi_miner.get_cross_rules(feature1, feature2, top_n=5, metric='lift')
print(f"{feature1}和{feature2}的交叉规则top 3:\n{cross_rules[['rule_description', 'lift', 'badrate', 'sample_ratio']]}")

# 绘制交叉热力图
plt = multi_miner.plot_cross_heatmap(feature1, feature2, metric='lift')
plt.savefig('images/cross_feature_heatmap.png', dpi=300, bbox_inches='tight')
plt.close()
```

### 5. 可视化

```python
from rulelift import plot_rule_comparison, plot_decision_tree

# 规则比较图（保存到本地）
plot_rule_comparison(result, metric='actual_lift', save_path='rule_comparison.png')
print("规则比较图已保存到 rule_comparison.png")

# 决策树可视化（保存到本地）
plot_decision_tree(dt_extractor, feature_names=X.columns.tolist(), save_path='decision_tree.png')
print("决策树图已保存到 decision_tree.png")
```

### 6. 变量分析

rulelift 新增了变量分析模块，支持对特征变量进行全面的效度分析和分箱分析，帮助风控团队识别重要变量，优化特征工程。

#### 6.1 变量效度分析

```python
from rulelift import VariableAnalyzer

# 初始化变量分析器
var_analyzer = VariableAnalyzer(df, exclude_cols=['ID', 'CREATE_TIME'], target_col='ISBAD')

# 分析所有变量的效度指标
var_metrics = var_analyzer.analyze_all_variables()
print("\n=== 所有变量效度指标 ===")
print(var_metrics)
```

#### 6.2 单变量分箱分析

```python
# 分析单个变量的分箱情况
feature = 'ALI_FQZSCORE'
bin_analysis = var_analyzer.analyze_single_variable(feature, n_bins=10)
print(f"\n=== {feature} 分箱分析 ===")
print(bin_analysis)

# 可视化变量分箱结果
plt = var_analyzer.plot_variable_bins(feature, n_bins=10)
plt.savefig(f'{feature}_bin_analysis.png', dpi=300, bbox_inches='tight')
print(f"\n{feature} 分箱分析图已保存到 {feature}_bin_analysis.png")
```

## 核心指标说明

### 规则评估指标

| 指标 | 定义 | 最佳范围 | 意义 |
|------|------|----------|------|
| `actual_lift` | 规则命中样本逾期率 / 总样本逾期率 | > 1.0 | 规则的风险区分能力，值越大效果越好 |
| `f1` | 2*(精确率*召回率)/(精确率+召回率) | 0-1 | 综合评估规则的精确率和召回率 |
| `actual_badrate` | 规则命中样本中的逾期比例 | 依业务场景而定 | 规则直接拦截的坏客户比例 |
| `actual_recall` | 规则命中的坏客户 / 总坏客户 | 0-1 | 规则对坏客户的覆盖能力 |
| `hit_rate_cv` | 命中率变异系数 = 标准差/均值 | < 0.2 | 规则命中率的稳定性，值越小越稳定 |
| `max_correlation_value` | 与其他规则的最大相关系数 | < 0.5 | 规则的独立性，值越小独立性越好 |

### 变量分析指标

| 指标 | 定义 | 最佳范围 | 意义 |
|------|------|----------|------|
| `iv` | 信息值(Information Value) | > 0.1 | 变量的预测能力，值越大预测能力越强 |
| `ks` | KS统计量 | > 0.2 | 变量对好坏客户的区分能力，值越大区分能力越强 |
| `auc` | 曲线下面积 | > 0.6 | 变量的整体预测能力，值越大预测能力越强 |
| `badrate` | 分箱中的坏客户比例 | 依业务场景而定 | 分箱的风险水平 |
| `cum_badrate` | 累积坏客户比例 | 依业务场景而定 | 累积分箱的风险水平 |



## 最佳实践

1. **数据准备**：
   - 确保数据包含唯一的用户标识和规则名称
   - 实际逾期字段（USER_TARGET）应为 0/1 格式
   - 评级坏账率字段（USER_LEVEL_BADRATE）应为数值型

2. **分场景使用**：
   - **开发测试阶段**：使用决策树规则提取和单/多特征规则挖掘生成候选规则
   - **生产监控阶段**：使用 analyze_rules 定期评估规则效果，关注 lift 值和命中率稳定性

3. **规则优化建议**：
   - 保留 lift 值 > 1.2 的规则
   - 移除命中率变异系数 > 0.5 的不稳定规则
   - 合并或移除相关系数 > 0.8 的冗余规则
   - 综合考虑 f1 分数，平衡精确率和召回率

4. **策略组合**：
   - 使用 calculate_strategy_gain 评估不同策略组合的效果
   - 优先添加 lift 值高且与现有规则相关性低的规则
   - 定期评估策略整体效果，及时调整规则组合

## API 文档

### analyze_rules

```python
def analyze_rules(rule_score, rule_col='RULE', user_id_col='USER_ID', 
                 user_level_badrate_col=None, user_target_col=None,
                 hit_date_col=None)
```

**参数**：
- `rule_score`: DataFrame，包含规则拦截客户信息
- `rule_col`: str，规则名字段名，默认 'RULE'
- `user_id_col`: str，用户编号字段名，默认 'USER_ID'
- `user_level_badrate_col`: str，用户评级坏账率字段名，可选
- `user_target_col`: str，用户实际逾期字段名，可选
- `hit_date_col`: str，命中日期字段名，可选（用于命中率监控）

**返回值**：
- DataFrame，包含所有规则的评估指标

### DecisionTreeRuleExtractor

```python
class DecisionTreeRuleExtractor:
    def __init__(self, max_depth=3, min_samples_leaf=5, criterion='gini')
    def fit(self, X, y)
    def extract_rules(self)
```

**参数**：
- `max_depth`: int，决策树最大深度
- `min_samples_leaf`: int，叶子节点最小样本数
- `criterion`: str，分裂标准，可选 'gini' 或 'entropy'

**方法**：
- `fit(X, y)`: 拟合决策树模型
- `extract_rules()`: 提取规则，返回规则列表

### calculate_strategy_gain

```python
def calculate_strategy_gain(df, strategy1, strategy2, 
                           rule_col='RULE', user_id_col='USER_ID',
                           user_target_col=None, user_level_badrate_col=None)
```

**参数**：
- `df`: DataFrame，规则拦截客户信息
- `strategy1`: list，基础策略规则列表
- `strategy2`: list，增强策略规则列表
- `user_target_col`: str，用户实际逾期字段名，可选
- `user_level_badrate_col`: str，用户评级坏账率字段名，可选

**返回值**：
- float，策略2相对策略1的增益值

### VariableAnalyzer

```python
class VariableAnalyzer:
    def __init__(self, df, exclude_cols=None, target_col='ISBAD')
    def analyze_all_variables(self)
    def analyze_single_variable(self, variable, n_bins=10)
    def plot_variable_bins(self, variable, n_bins=10)
```

**参数**：
- `df`: DataFrame，输入的数据集
- `exclude_cols`: list，排除的字段名列表，可选
- `target_col`: str，目标字段名，默认 'ISBAD'
- `variable`: str，要分析的变量名
- `n_bins`: int，分箱数量，默认 10

**方法**：
- `analyze_all_variables()`: 分析所有变量的效度指标，返回包含所有变量指标的DataFrame
- `analyze_single_variable(variable, n_bins=10)`: 分析单个变量的分箱情况，返回包含各分箱统计信息的DataFrame
- `plot_variable_bins(variable, n_bins=10)`: 可视化变量分箱结果，返回matplotlib.pyplot对象

## 版本信息

当前版本：1.1.1

## 更新日志

### v1.1.2 (2025-12-23)
- 新增变量分析模块，支持IV、KS、AUC等指标计算
- 实现单变量等频分箱分析功能
- 新增策略自动挖掘功能
- 优化决策树规则显示，加入 lift 值和拦截用户数等指标
- 新增两两策略增益计算功能
- 优化代码质量，修复所有已知问题

### v0.3.0 (2025-12-17)
- 新增命中率变异系数（hit_rate_cv）用于监控规则稳定性
- 新增 F1 分数计算，综合评估规则效果
- 优化规则相关性分析，新增最大相关性指标
- 改进命中率计算逻辑
- 完善文档，新增技术原理和缺陷分析

## 许可证

MIT License

## 项目地址

- GitHub: https://github.com/aialgorithm/rulelift
- PyPI: https://pypi.org/project/rulelift/

## 联系方式

作者: aialgorithm
邮箱: 15880982687@qq.com

## 贡献指南

欢迎提交 Issue 和 Pull Request！如果您有任何建议或问题，请通过 GitHub Issues 反馈。

---

**开始使用 rulelift 优化您的风控规则系统吧！** 🚀