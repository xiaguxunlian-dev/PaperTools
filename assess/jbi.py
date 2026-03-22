"""
JBI 批判性评价清单
来源: JBI (Joanna Briggs Institute) Critical Appraisal Checklist
涵盖 9 种研究类型的评价清单
"""
from dataclasses import dataclass


# 各研究类型的 JBI 清单
JBI_CHECKLISTS = {
    'RCT': {
        'name': '随机对照试验 (RCT)',
        'items': [
            (' randomization', '是否真正随机分配？'),
            (' allocation_concealment', '是否隐藏分配序列？'),
            (' blinding_participants', '受试者是否采用盲法？'),
            (' blinding_treatment', '干预实施者是否采用盲法？'),
            (' blinding_outcome', '结果评估者是否采用盲法？'),
            (' equal_treatment', '除干预外，各组处理是否相同？'),
            (' follow_up', '是否完成随访且随访完整？'),
            (' outcomes_measured', '结局指标是否测量正确？'),
            (' appropriate_analysis', '统计分析方法是否恰当？'),
            (' trial_design', '试验设计是否合理？'),
        ],
        'default_max_score': 10,
    },
    'cohort': {
        'name': '队列研究',
        'items': [
            (' groups_similar', '各组是否相似且仅在暴露/干预上不同？'),
            (' exposure_measured', '暴露因素是否用有效方法测量？'),
            (' exposure_valid', '暴露是否测量准确？'),
            (' confounding', '是否识别并控制了混杂因素？'),
            (' outcomes_assessed', '结局指标是否用有效方法测量？'),
            (' follow_up_complete', '随访是否完整？'),
            (' strategies_followup', '随访策略是否一致？'),
            (' outcomes_long_enough', '结局指标是否随访足够长时间？'),
            (' appropriate_analysis', '统计分析方法是否恰当？'),
        ],
        'default_max_score': 9,
    },
    'case_control': {
        'name': '病例对照研究',
        'items': [
            (' groups_comparable', '病例组和对照组是否可比？'),
            (' cases_definite', '病例诊断是否明确？'),
            (' controls_disease_free', '对照组是否确认为无病？'),
            (' exposure_measured', '暴露是否用有效方法测量？'),
            (' exposure_same_method', '病例和对照的暴露测量方法是否相同？'),
            (' exposure_valid', '暴露测量是否准确？'),
            (' confounding', '是否识别并控制了混杂因素？'),
            (' exposure_recollected', '暴露是否通过回顾或记录获得？'),
        ],
        'default_max_score': 8,
    },
    'cross_sectional': {
        'name': '横断面研究',
        'items': [
            (' sample_representative', '样本是否具有代表性？'),
            (' criteria_clear', '纳入排除标准是否明确？'),
            (' exposure_valid', '暴露因素是否测量准确？'),
            (' outcome_valid', '结局指标是否测量准确？'),
            (' confounding_identified', '是否识别了混杂因素？'),
            (' confounding_dealt', '混杂因素是否得到适当处理？'),
            (' outcomes_assessed', '结局指标是否用标准方法评估？'),
            (' appropriate_analysis', '统计分析是否恰当？'),
        ],
        'default_max_score': 8,
    },
    'systematic_review': {
        'name': '系统综述',
        'items': [
            (' question_clear', '综述问题是否清晰明确？'),
            (' inclusion_criteria', '纳入标准是否恰当？'),
            (' strategy_appropriate', '检索策略是否全面？'),
            (' sources_adequate', '数据来源是否充分？'),
            (' appraised', '是否批判性评价了纳入研究？'),
            (' quality_considered', '是否在合成时考虑了质量？'),
            (' methods_reproducible', '方法是否可重复？'),
            (' specific_conflicts', '是否识别并处理了利益冲突？'),
        ],
        'default_max_score': 8,
    },
}


@dataclass
class JBIScore:
    study_type: str
    paper_title: str
    scores: dict[str, bool | None]  # True=Yes, False=No, None=Unclear
    score: int
    max_score: int
    
    def quality_label(self) -> str:
        pct = self.score / self.max_score if self.max_score > 0 else 0
        if pct >= 0.8:
            return "✅ 高质量"
        elif pct >= 0.5:
            return "⚠️ 中等质量"
        else:
            return "❌ 低质量"
    
    def to_markdown(self) -> str:
        score_emoji = {True: '✅', False: '❌', None: '❓'}
        meta = JBI_CHECKLISTS.get(self.study_type, {})
        name = meta.get('name', self.study_type)
        
        lines = [
            f"## JBI 批判性评价 — {name}",
            f"**论文**: {self.paper_title[:60]}",
            f"**评分**: {self.score}/{self.max_score} — {self.quality_label()}",
            "",
            "| # | 评价项目 | 结果 |",
            "|---|----------|------|",
        ]
        
        for i, (key, desc) in enumerate(meta.get('items', []), 1):
            val = self.scores.get(key)
            lines.append(f"| {i} | {desc} | {score_emoji.get(val, '❓')} |")
        
        return '\n'.join(lines)


class JBIAssessor:
    """
    JBI 批判性评价清单评估器
    支持 RCT、队列研究、病例对照、横断面研究、系统综述等类型
    """
    
    def assess(
        self,
        text: str,
        study_type: str = 'RCT',
        title: str = "Unknown",
    ) -> JBIScore:
        """
        基于文本自动评估
        
        Args:
            text: 研究论文文本
            study_type: 研究类型 ('RCT', 'cohort', 'case_control', 'cross_sectional', 'systematic_review')
            title: 论文标题
        """
        text_lower = text.lower()
        checklist = JBI_CHECKLISTS.get(study_type, JBI_CHECKLISTS['RCT'])
        scores = {}
        yes_count = 0
        
        for key, desc in checklist['items']:
            # 简单关键词匹配判断
            if key == 'randomization':
                val = any(k in text_lower for k in ['randomized', 'randomised', 'random number'])
            elif key == 'allocation_concealment':
                val = any(k in text_lower for k in ['allocation concealment', 'sealed envelope', 'central randomization'])
            elif key == 'blinding_participants':
                val = any(k in text_lower for k in ['double-blind', 'single-blind', 'blinded'])
            elif key == 'follow_up':
                val = None  # 无法自动判断
            elif key == 'confounding':
                val = any(k in text_lower for k in ['adjusted', 'multivariate', 'propensity', 'covariate'])
            elif key == 'outcomes_measured':
                val = True  # 假设正确
            elif key == 'equal_treatment':
                val = any(k in text_lower for k in ['placebo', 'control group', 'usual care'])
            else:
                val = None  # 默认不确定
            
            scores[key] = val
            if val is True:
                yes_count += 1
        
        return JBIScore(
            study_type=study_type,
            paper_title=title,
            scores=scores,
            score=yes_count,
            max_score=len(checklist['items']),
        )
    
    def assess_interactive(self, study_type: str = 'RCT', title: str = "Unknown") -> JBIScore:
        """交互式评估"""
        checklist = JBI_CHECKLISTS.get(study_type, JBI_CHECKLISTS['RCT'])
        print(f"\n{'='*50}\nJBI 评价 — {checklist['name']}: {title}\n{'='*50}")
        
        scores = {}
        for key, desc in checklist['items']:
            print(f"\n{desc}")
            print("  [y] 是  [n] 否  [u] 不确定")
            val = input("  你的选择: ").strip().lower()
            scores[key] = {'y': True, 'n': False, 'u': None}.get(val)
        
        yes_count = sum(1 for v in scores.values() if v is True)
        result = JBIScore(
            study_type=study_type,
            paper_title=title,
            scores=scores,
            score=yes_count,
            max_score=len(checklist['items']),
        )
        
        print(result.to_markdown())
        return result
