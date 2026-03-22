"""
GRADE 证据质量分级系统
来源: GRADE Working Group
将证据质量分为 High / Moderate / Low / Very Low 四级
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class GRADEResult:
    """GRADE 评估结果"""
    outcome: str                  # 具体结局指标
    study_design: str = "RCT"     # RCT 或观察性研究

    # 升级因素
    dose_response: bool = False   # 剂量-效应关系
    large_magnitude: bool = False  # 效应量大
    confounders: bool = False      # 残余混杂因素会增加效应估计

    # 降级因素
    risk_of_bias: bool = False    # 偏倚风险
    inconsistency: bool = False   # 异质性
    indirectness: bool = False    # 间接性
    imprecision: bool = False      # 不精确性
    publication_bias: bool = False # 发表偏倚

    # 输出
    quality: str = "Unknown"      # High / Moderate / Low / Very Low
    certainty: str = "Unknown"    # 同 quality
    justification: str = ""        # 判断依据

    def to_markdown(self) -> str:
        quality_map = {
            'High': '🟢 High',
            'Moderate': '🟡 Moderate',
            'Low': '🟠 Low',
            'Very Low': '🔴 Very Low',
        }

        lines = [
            f"## GRADE 证据质量评估",
            "",
            f"**结局指标**: {self.outcome}",
            f"**研究设计**: {self.study_design}",
            "",
            "### 影响因素",
            "",
            f"| 因素 | 状态 | 影响 |",
            f"|------|------|------|",
            f"| 偏倚风险 (RoB) | {'⚠️ 存在' if self.risk_of_bias else '✅ 无明显问题'} | {'↓ 降级' if self.risk_of_bias else '-'} |",
            f"| 异质性 (I²) | {'⚠️ 显著' if self.inconsistency else '✅ 无明显问题'} | {'↓ 降级' if self.inconsistency else '-'} |",
            f"| 间接性 | {'⚠️ 存在' if self.indirectness else '✅ 无明显问题'} | {'↓ 降级' if self.indirectness else '-'} |",
            f"| 不精确性 | {'⚠️ 不精确' if self.imprecision else '✅ 精确'} | {'↓ 降级' if self.imprecision else '-'} |",
            f"| 发表偏倚 | {'⚠️ 可能存在' if self.publication_bias else '✅ 无明显证据'} | {'↓ 降级' if self.publication_bias else '-'} |",
            f"| 剂量-效应 | {'⬆️ 存在' if self.dose_response else '-'} | {'↑ 升级' if self.dose_response else ''} |",
            f"| 效应量大 | {'⬆️ 是' if self.large_magnitude else '-'} | {'↑ 升级' if self.large_magnitude else ''} |",
            "",
            f"### 证据质量",
            "",
            f"**{quality_map.get(self.quality, '❓')}**  {self.quality}",
            "",
        ]
        if self.justification:
            lines.append(f"**判断依据**: {self.justification}")
        return '\n'.join(lines)


class GRADEAssessor:
    """
    GRADE 证据质量分级

    RCT 起始为 High，观察性研究起始为 Low。
    - RCT 可因 5 个因素降级
    - 观察性研究可降级（至 Very Low）或升级（有充分理由时）
    """

    def assess(self, outcome: str, study_design: str = "RCT", **kwargs) -> GRADEResult:
        """
        评估证据质量

        Args:
            outcome: 具体的结局指标描述
            study_design: 'RCT' 或 'Observational'
            **kwargs: 各项影响因素布尔值
        """
        result = GRADEResult(
            outcome=outcome,
            study_design=study_design,
            **kwargs
        )

        # 计算初始质量
        if study_design == "RCT":
            quality_score = 4  # High = 4
        else:
            quality_score = 2   # Low = 2 (观察性研究)

        # 降级因素
        if result.risk_of_bias:
            quality_score -= 1
        if result.inconsistency:
            quality_score -= 1
        if result.indirectness:
            quality_score -= 1
        if result.imprecision:
            quality_score -= 1
        if result.publication_bias:
            quality_score -= 1

        # 观察性研究升级因素
        if study_design != "RCT":
            upgrade_count = sum([result.dose_response, result.large_magnitude, result.confounders])
            quality_score += upgrade_count

        # 映射到 GRADE 等级
        quality_map = {5: "High", 4: "High", 3: "Moderate", 2: "Low", 1: "Very Low", 0: "Very Low"}
        quality_score = max(0, min(5, quality_score))
        result.quality = quality_map.get(quality_score, "Unknown")
        result.certainty = result.quality

        return result

    def assess_query(self, query: str, context: str = "") -> GRADEResult:
        """
        根据研究问题描述，LLM 辅助评估 GRADE 等级
        需要人工审核结果
        """
        # 简单启发式判断，可替换为 LLM 调用
        text = (query + " " + context).lower()

        # 检测研究设计
        design = "RCT"
        design_kw = ['randomized', 'rct', 'randomised', 'placebo', 'double-blind']
        observational_kw = ['cohort', 'case-control', 'cross-sectional', 'registry', 'retrospective']

        if not any(k in text for k in design_kw):
            if any(k in text for k in observational_kw):
                design = "Observational"

        # 降级因素检测
        kwargs = {
            'risk_of_bias': any(k in text for k in ['high risk', 'unclear', 'bias', 'no blinding']),
            'inconsistency': any(k in text for k in ['heterogeneity', 'i2', 'inconsistent', 'different results']),
            'indirectness': any(k in text for k in ['indirect', 'surrogate', 'intermediate']),
            'imprecision': any(k in text for k in ['wide confidence', 'small sample', 'few participants', 'narrow']),
            'publication_bias': any(k in text for k in ['publication bias', 'funnel plot', 'eggers']),
            'dose_response': any(k in text for k in ['dose-response', 'dose dependent', 'graded']),
            'large_magnitude': any(k in text for k in ['large effect', 'rr=', 'or=', 'hr=', 'risk ratio', 'odds ratio']),
            'confounders': any(k in text for k in ['adjusted', 'confounder', 'multivariate', 'propensity']),
        }

        result = self.assess(query, design, **kwargs)
        result.justification = (
            f"基于关键词自动判断。研究设计: {design}。"
            f"降级: {sum([kwargs[k] for k in ['risk_of_bias','inconsistency','indirectness','imprecision','publication_bias']])} 项，"
            f"升级: {sum([kwargs[k] for k in ['dose_response','large_magnitude','confounders']])} 项。"
            f"请人工审核此评估。"
        )
        return result
