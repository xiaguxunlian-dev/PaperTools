"""
证据表格生成器
将检索结果转化为标准化的证据表格（Evidence Table）
支持 Markdown / CSV / JSON 格式输出
"""
import csv
import json
from io import StringIO
from typing import Literal


class EvidenceTableGenerator:
    """
    生成循证医学证据表格
    
    表格字段：
    - Study / Author
    - Year
    - Study Design
    - Population
    - Intervention
    - Comparison
    - Outcome
    - Results (Effect Size)
    - Quality (RoB)
    - GRADE
    """
    
    def __init__(self):
        self.fields = [
            'Study', 'Year', 'Design', 'Population',
            'Intervention', 'Comparison', 'Outcome',
            'Effect Size', 'CI', 'Sample Size',
            'Quality (RoB)', 'Quality (JBI)', 'GRADE',
            'Source', 'DOI',
        ]
    
    def generate(
        self,
        papers: list[dict],
        format_: Literal['markdown', 'csv', 'json'] = 'markdown',
        include_quality: bool = True,
    ) -> str:
        """
        生成证据表格
        
        Args:
            papers: 论文列表（来自 FederatedSearcher 的结果）
            format_: 输出格式
            include_quality: 是否包含质量评估列
        
        Returns:
            格式化后的表格字符串
        """
        rows = []
        for p in papers:
            # 提取第一作者
            authors = p.get('authors', [])
            first_author = authors[0] if authors else 'Unknown'
            year = p.get('year', 'N/A')
            study_name = f"{first_author} et al. ({year})"
            
            # 推断研究设计
            abstract = p.get('abstract', '').lower()
            design = self._infer_design(abstract)
            
            row = {
                'Study': study_name,
                'Year': year,
                'Design': design,
                'Population': self._extract_population(p.get('abstract', '')),
                'Intervention': self._extract_intervention(p.get('abstract', '')),
                'Comparison': self._extract_comparison(p.get('abstract', '')),
                'Outcome': self._extract_outcome(p.get('abstract', '')),
                'Effect Size': p.get('effect_size', 'N/R'),
                'CI': p.get('ci', 'N/R'),
                'Sample Size': p.get('sample_size', 'N/R'),
                'Quality (RoB)': 'N/R',
                'Quality (JBI)': 'N/R',
                'GRADE': 'N/R',
                'Source': p.get('source', 'N/A'),
                'DOI': p.get('doi', 'N/R'),
            }
            rows.append(row)
        
        if format_ == 'markdown':
            return self._to_markdown(rows, include_quality)
        elif format_ == 'csv':
            return self._to_csv(rows, include_quality)
        else:
            return json.dumps(rows, ensure_ascii=False, indent=2)
    
    def _to_markdown(self, rows: list[dict], include_quality: bool) -> str:
        if not rows:
            return "**无相关文献**"
        
        quality_cols = ['Quality (RoB)', 'Quality (JBI)', 'GRADE'] if include_quality else []
        basic_cols = [f for f in self.fields if f not in quality_cols]
        
        lines = [
            "# 证据表格 (Evidence Table)\n",
            f"*共 {len(rows)} 项研究*\n",
            "| " + " | ".join(basic_cols) + " |",
            "| " + " | ".join(['---'] * len(basic_cols)) + " |",
        ]
        
        for r in rows:
            cells = []
            for f in basic_cols:
                val = str(r.get(f, 'N/A'))
                # 截断长文本
                if len(val) > 40:
                    val = val[:37] + '...'
                cells.append(val)
            lines.append("| " + " | ".join(cells) + " |")
        
        lines.append("\n---\n")
        lines.append("**图例**: N/R = 未报告 | RoB = 偏倚风险 | GRADE = 证据质量分级")
        
        return '\n'.join(lines)
    
    def _to_csv(self, rows: list[dict], include_quality: bool) -> str:
        quality_cols = ['Quality (RoB)', 'Quality (JBI)', 'GRADE'] if include_quality else []
        cols = [f for f in self.fields if f not in quality_cols]
        
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=cols, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)
        return output.getvalue()
    
    def _infer_design(self, text: str) -> str:
        if any(k in text for k in ['randomized', 'randomised', 'rct', 'double-blind', 'placebo-controlled']):
            return 'RCT'
        elif any(k in text for k in ['cohort', 'prospective', 'retrospective', 'longitudinal']):
            return 'Cohort'
        elif any(k in text for k in ['case-control', 'case control']):
            return 'Case-Control'
        elif any(k in text for k in ['cross-sectional', 'cross sectional']):
            return 'Cross-sectional'
        elif any(k in text for k in ['systematic review', 'meta-analysis', 'meta analysis']):
            return 'Systematic Review'
        elif any(k in text for k in ['clinical trial', 'phase i', 'phase ii', 'phase iii', 'phase iv']):
            return 'Clinical Trial'
        else:
            return 'Observational'
    
    def _extract_population(self, text: str) -> str:
        import re
        patterns = [
            r'patients? with ([\w\s]+)',
            r'adults? (?:with|aged)?\s*([\w\s]+)',
            r'included ([\d,]+) patients?',
            r'study (?:in|of) ([\w\s]{5,30})',
        ]
        for p in patterns:
            m = re.search(p, text, re.IGNORECASE)
            if m:
                return m.group(1).strip()[:50]
        return 'N/R'
    
    def _extract_intervention(self, text: str) -> str:
        import re
        patterns = [
            r'treated with ([\w\s]+)',
            r'administration of ([\w\s]+)',
            r'(?:drug|therapy|intervention)[:\s]+([\w\s]+)',
            r'received ([\w\s]+)',
        ]
        for p in patterns:
            m = re.search(p, text, re.IGNORECASE)
            if m:
                return m.group(1).strip()[:50]
        return 'N/R'
    
    def _extract_comparison(self, text: str) -> str:
        import re
        patterns = [
            r'compar(?:ed|ison) (?:with|to) ([\w\s]+)',
            r'versus ([\w\s]+)',
            r'vs\.?\s+([\w\s]+)',
            r'control(?:led)? (?:group )?(?:of|with)?\s*([\w\s]+)',
        ]
        for p in patterns:
            m = re.search(p, text, re.IGNORECASE)
            if m:
                return m.group(1).strip()[:50]
        return 'N/R'
    
    def _extract_outcome(self, text: str) -> str:
        import re
        patterns = [
            r'(?:primary |main )?outcome[s]?[:\s]+([^\.]+)',
            r'(?:efficacy|safety|response)[:\s]+([^\.]+)',
            r'result(?:ed|ing) (?:in|with) ([^\.]+)',
        ]
        for p in patterns:
            m = re.search(p, text, re.IGNORECASE)
            if m:
                return m.group(1).strip()[:50]
        return 'N/R'
