"""
PICO 框架提取器
PICO: Population, Intervention, Comparison, Outcome
系统综述的标准化问题框架
"""
import re
import json
from dataclasses import dataclass, field, asdict


@dataclass
class PICO:
    """PICO 框架结构"""
    population: list[str] = field(default_factory=list)    # 研究人群
    intervention: list[str] = field(default_factory=list)  # 干预措施
    comparison: list[str] = field(default_factory=list)    # 对照措施
    outcome: list[str] = field(default_factory=list)        # 结局指标
    study_type: list[str] = field(default_factory=list)    # 研究类型
    context: str = ""                                        # 附加背景
    
    def to_markdown(self) -> str:
        lines = [
            "## PICO 框架",
            "",
            f"**P (人群)**: {', '.join(self.population) or '待定义'}",
            f"**I (干预)**: {', '.join(self.intervention) or '待定义'}",
            f"**C (对照)**: {', '.join(self.comparison) or '待定义'}",
            f"**O (结局)**: {', '.join(self.outcome) or '待定义'}",
            f"**研究类型**: {', '.join(self.study_type) or '未指定'}",
        ]
        if self.context:
            lines.append(f"\n**背景**: {self.context}")
        return '\n'.join(lines)
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    def to_search_query(self) -> str:
        """生成检索用查询字符串"""
        parts = (
            self.population[:2] +
            self.intervention[:2] +
            self.outcome[:1]
        )
        return ' '.join(parts)


# PICO 关键词模式
PICO_PATTERNS = {
    'population': [
        r'population[s]?[:\s]+([^\.]+)',
        r'patient[s]?[:\s]+([^\.]+)',
        r'study population[:\s]+([^\.]+)',
        r'in adult[s]?|in children|in elderly|in patients',
        r'with ([\w\s]+)', r'suffering from ([\w\s]+)',
        r'diagnosed with ([\w\s]+)',
    ],
    'intervention': [
        r'intervention[:\s]+([^\.]+)',
        r'treated with ([\w\s]+)',
        r'administration of ([\w\s]+)',
        r'received ([\w\s]+)',
        r'using ([\w\s]+)',
        r'therapy with ([\w\s]+)',
    ],
    'comparison': [
        r'compar(?:ed?|ison|ator)[:\s]+([^\.]+)',
        r'control(?:led)?[:\s]+([^\.]+)',
        r'versus ([\w\s]+)',
        r'vs\.?\s+([\w\s]+)',
        r'compared to ([\w\s]+)',
        r'placebo|standard care|usual care|no treatment',
    ],
    'outcome': [
        r'outcome[s]?[:\s]+([^\.]+)',
        r'primary outcome[:\s]+([^\.]+)',
        r'measure[d]?[:\s]+([^\.]+)',
        r'result[s]?[:\s]+([^\.]+)',
        r'efficacy|safety|tolerance|response rate|survival|mortality|adverse',
    ],
}


class PICOExtractor:
    """
    PICO 框架提取器
    
    支持：
    - 基于关键词规则提取（无需 LLM）
    - 结构化输出为 Markdown / JSON
    - 生成检索查询字符串
    """
    
    def extract(self, text: str) -> PICO:
        """
        从文本中提取 PICO 框架
        
        Args:
            text: 研究问题或摘要文本
        
        Returns:
            PICO 对象
        """
        text_lower = text.lower()
        
        pico = PICO()
        
        # 提取 Population
        for pattern in PICO_PATTERNS['population']:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            pico.population.extend([m.strip() if isinstance(m, str) else str(m).strip() for m in matches])
        
        # 提取 Intervention
        for pattern in PICO_PATTERNS['intervention']:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            pico.intervention.extend([m.strip() if isinstance(m, str) else str(m).strip() for m in matches])
        
        # 提取 Comparison
        for pattern in PICO_PATTERNS['comparison']:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            pico.comparison.extend([m.strip() if isinstance(m, str) else str(m).strip() for m in matches])
        
        # 提取 Outcome
        for pattern in PICO_PATTERNS['outcome']:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            pico.outcome.extend([m.strip() if isinstance(m, str) else str(m).strip() for m in matches])
        
        # 去重清理
        for field in ['population', 'intervention', 'comparison', 'outcome']:
            items = getattr(pico, field)
            cleaned = []
            seen = set()
            for item in items:
                item = item.strip()
                if item and len(item) > 3 and item not in seen:
                    seen.add(item)
                    cleaned.append(item)
            setattr(pico, field, cleaned[:5])  # 每类最多保留5项
        
        # 推断研究类型
        if any(k in text_lower for k in ['randomized', 'rct', 'randomised']):
            pico.study_type = ['RCT', '随机对照试验']
        if any(k in text_lower for k in ['cohort', 'prospective']):
            pico.study_type.extend(['队列研究'])
        if any(k in text_lower for k in ['case-control', 'case control']):
            pico.study_type.extend(['病例对照'])
        
        pico.study_type = list(set(pico.study_type))[:3]
        
        # 如果提取失败，提供默认模板
        if not any([pico.population, pico.intervention, pico.outcome]):
            pico.context = self._generate_context_hint(text)
        
        return pico
    
    def _generate_context_hint(self, text: str) -> str:
        return (
            "未能自动提取 PICO 框架。请人工定义：\n"
            "- P (人群): \n"
            "- I (干预): \n"
            "- C (对照): \n"
            "- O (结局): "
        )
    
    def extract_from_query(self, query: str) -> PICO:
        """
        从自然语言检索问题中提取 PICO
        例如: "他汀类药物对心血管疾病二级预防的疗效"
        """
        return self.extract(query)
    
    def generate_search_query(self, pico: PICO, strategy: str = 'detailed') -> list[str]:
        """
        根据 PICO 生成多个检索查询组合
        
        Returns:
            list of search query strings
        """
        queries = []
        
        if strategy in ['detailed', 'all']:
            # 策略1: P + I + O
            if pico.population and pico.intervention:
                queries.append(' AND '.join(pico.population[:2] + pico.intervention[:2]))
            # 策略2: I + O
            if pico.intervention and pico.outcome:
                queries.append(' AND '.join(pico.intervention[:2] + pico.outcome[:1]))
            # 策略3: 宽松检索（仅 I）
            if pico.intervention:
                queries.append(pico.intervention[0])
        
        if strategy in ['broad', 'all']:
            # 策略4: 广泛检索（关键词组合）
            all_terms = pico.population + pico.intervention + pico.outcome
            if all_terms:
                queries.append(' '.join(all_terms[:5]))
        
        # 去重
        return list(dict.fromkeys(queries))[:5]
