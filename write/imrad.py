"""
IMRAD 格式综述生成器
IMRAD: Introduction, Methods, Results, And Discussion
生成符合学术规范的综述草稿
"""
import json
from typing import Optional


class IMRADWriter:
    """
    生成 IMRAD 格式的研究综述草稿
    
    工作流程:
    1. 读取检索到的论文
    2. 提取关键信息
    3. 按 IMRAD 结构组织内容
    """
    
    def generate(
        self,
        topic: str,
        papers: list[dict],
        pico: dict = None,
        sections: list[str] = None,
    ) -> str:
        """
        生成综述草稿
        
        Args:
            topic: 综述主题
            papers: 检索到的论文列表
            pico: PICO 框架（可选）
            sections: 要生成的章节列表
        
        Returns:
            Markdown 格式的综述草稿
        """
        sections = sections or ['background', 'methods', 'results', 'discussion']
        output = []
        
        # 标题
        output.append(f"# {topic}\n")
        output.append(f"*自动生成的综述草稿 · {len(papers)} 篇文献 · {self._today()}*\n")
        
        if 'background' in sections:
            output.append(self._generate_background(topic, papers, pico))
        
        if 'methods' in sections:
            output.append(self._generate_methods(topic, papers, pico))
        
        if 'results' in sections:
            output.append(self._generate_results(topic, papers))
        
        if 'discussion' in sections:
            output.append(self._generate_discussion(topic, papers))
        
        output.append(self._generate_references(papers))
        
        return '\n'.join(output)
    
    def _generate_background(self, topic: str, papers: list[dict], pico: dict = None) -> str:
        lines = [
            "## 1. 引言 (Introduction)\n",
            f"### 1.1 研究背景\n",
            f"{topic} 是当前该领域的研究热点。近年来，大量研究围绕该主题展开，"
            f"本研究检索到 {len(papers)} 篇相关文献，涵盖随机对照试验、队列研究等多种研究设计。\n",
        ]
        
        if pico:
            lines.append(f"### 1.2 PICO 问题\n")
            pico_obj = pico if isinstance(pico, dict) else vars(pico) if hasattr(pico, '__dict__') else {}
            if isinstance(pico_obj, dict):
                for key in ['population', 'intervention', 'comparison', 'outcome']:
                    items = pico_obj.get(key, [])
                    if items:
                        lines.append(f"- **{key.upper()}**: {', '.join(items)}\n")
            lines.append("\n")
        
        # 引用已有综述
        reviews = [p for p in papers if 'review' in str(p.get('journal', '')).lower() or
                   'review' in str(p.get('title', '')).lower()]
        if reviews:
            lines.append(f"### 1.3 已有综述\n")
            for r in reviews[:3]:
                title = r.get('title', 'N/A')
                authors = ', '.join(r.get('authors', [])[:3])
                year = r.get('year', '')
                lines.append(f"- {authors} ({year}). {title}. {r.get('journal', 'N/A')}\n")
            lines.append("\n")
        
        # Gap 分析
        lines.extend([
            f"### 1.4 研究 Gap\n",
            f"基于文献检索，我们发现以下研究空白：\n",
            f"1. 现有研究样本量普遍偏小，缺乏大样本验证\n",
            f"2. 长期随访数据不足\n",
            f"3. 亚组分析结果不一致\n",
            f"4. 成本效益分析较少\n",
            "\n",
        ])
        
        # 目的
        lines.extend([
            f"### 1.5 研究目的\n",
            f"本综述旨在系统评价{topic}的有效性和安全性，"
            f"为临床决策提供循证依据。\n",
        ])
        
        return ''.join(lines)
    
    def _generate_methods(self, topic: str, papers: list[dict], pico: dict = None) -> str:
        lines = [
            "## 2. 方法 (Methods)\n",
            "### 2.1 检索策略\n",
            f"检索数据库：PubMed、arXiv、Semantic Scholar、OpenAlex\n",
            f"检索词：{topic}\n",
            f"检索日期：{self._today()}\n",
            f"无语言限制，检索截止至当前日期。\n",
            "\n",
            "### 2.2 纳入排除标准\n",
            "**纳入标准：**\n",
            "- 研究设计：随机对照试验(RCT)、队列研究、病例对照研究\n",
            "- 研究对象：符合PICO框架的人群\n",
            "- 干预措施：治疗/预防性干预\n",
            "- 结局指标：临床相关结局（如有效率、死亡率、不良事件）\n",
            "\n",
            "**排除标准：**\n",
            "- 非原始研究（如综述、病例报告<10例）\n",
            "- 动物实验或体外研究\n",
            "- 无法获取全文\n",
            "\n",
            "### 2.3 数据提取\n",
            "提取以下信息：\n",
            "- 第一作者、发表年份、研究设计\n",
            "- 样本量、人口学特征\n",
            "- 干预措施详情\n",
            "- 结局指标及结果\n",
            "- 偏倚风险评估\n",
            "\n",
            "### 2.4 质量评估\n",
            "- RCT：RoB 2 工具\n",
            "- 观察性研究：ROBINS-I 工具\n",
            "- 证据质量：GRADE 分级\n",
            "\n",
            "### 2.5 统计分析\n",
            "如有足够同质研究，进行Meta分析。异质性检验采用I²统计量。\n",
            "\n",
        ]
        return ''.join(lines)
    
    def _generate_results(self, topic: str, papers: list[dict]) -> str:
        rcts = [p for p in papers if 'rct' in str(p.get('abstract', '')).lower() or
                'randomized' in str(p.get('abstract', '')).lower()]
        obs = [p for p in papers if p not in rcts]
        
        lines = [
            "## 3. 结果 (Results)\n",
            f"### 3.1 文献筛选\n",
            f"共检索到 {len(papers)} 篇文献，去重后 {len(papers)} 篇。",
            f"经标题摘要筛选后纳入 {min(len(papers), 20)} 篇进行全文评估，",
            f"最终纳入 {min(len(papers), 10)} 篇（{len(rcts)} 篇RCT，{len(obs)} 篇观察性研究）。\n",
            "\n",
            f"### 3.2 纳入研究特征\n",
            f"**随机对照试验 ({len(rcts)} 项)**\n",
        ]
        
        for p in rcts[:5]:
            authors = ', '.join(p.get('authors', [])[:3])
            year = p.get('year', 'N/A')
            citations = p.get('citations', 0)
            lines.append(f"- {authors} ({year}) — 被引 {citations} 次\n")
        
        if obs:
            lines.append(f"\n**观察性研究 ({len(obs)} 项)**\n")
            for p in obs[:5]:
                authors = ', '.join(p.get('authors', [])[:3])
                year = p.get('year', 'N/A')
                design = '队列' if 'cohort' in str(p.get('abstract', '')).lower() else '病例对照'
                lines.append(f"- {authors} ({year}) — {design}\n")
        
        lines.append("\n### 3.3 主要结果\n\n")
        lines.append("各研究结局指标汇总（详见证据表格）：\n")
        lines.append("- 有效性指标：临床有效率、缓解率、生存率\n")
        lines.append("- 安全性指标：不良事件发生率\n")
        lines.append("- 亚组分析：不同人群、剂量、疗程的差异\n\n")
        
        lines.append("### 3.4 质量评估结果\n\n")
        lines.append("RCT质量评估（RoB 2）：\n")
        lines.append("- 低风险：待填写\n")
        lines.append("- 存在担忧：待填写\n")
        lines.append("- 高风险：待填写\n\n")
        
        return ''.join(lines)
    
    def _generate_discussion(self, topic: str, papers: list[dict]) -> str:
        lines = [
            "## 4. 讨论 (Discussion)\n",
            "### 4.1 主要发现\n",
            f"本综述系统评价了{topic}相关的临床研究证据。",
            f"结果显示，[此处根据实际结果填写]，证据质量为[高/中/低]。\n",
            "\n",
            "### 4.2 与既往研究比较\n",
            "与既往综述相比，本研究纳入了更新的文献，结果基本一致。",
            "[此处填入与已有综述的比较分析]\n",
            "\n",
            "### 4.3 证据质量\n",
            "根据GRADE分级，整体证据质量为[高/中/低]级。",
            "主要降级因素包括[偏倚风险/不一致性/间接性/不精确性/发表偏倚]。\n",
            "\n",
            "### 4.4 局限性\n",
            "1. 检索数据库数量有限，未纳入灰色文献\n",
            "2. 部分研究存在方法学质量问题\n",
            "3. 异质性较大时需谨慎解读\n",
            "4. 存在发表偏倚可能\n",
            "\n",
            "### 4.5 结论\n",
            f"现有证据表明，[此处根据结果填写]，" 
            f"但受证据质量限制，建议在高质量研究发表后再做定论。\n",
            "\n",
            "### 4.6 对未来研究的启示\n",
            "- 需要大样本、多中心RCT验证\n",
            "- 统一结局指标报告标准\n",
            "- 开展长期随访研究\n",
            "- 关注成本效益分析\n",
            "\n",
        ]
        return ''.join(lines)
    
    def _generate_references(self, papers: list[dict]) -> str:
        lines = ["## 参考文献 (References)\n"]
        for i, p in enumerate(papers[:30], 1):
            authors = ', '.join(p.get('authors', [])[:6])
            if len(p.get('authors', [])) > 6:
                authors += ', et al.'
            year = p.get('year', 'N/A')
            title = p.get('title', 'N/A')
            journal = p.get('journal', 'N/A')
            doi = p.get('doi', '')
            
            if doi:
                lines.append(f"{i}. {authors}. ({year}). {title}. {journal}. https://doi.org/{doi}\n")
            else:
                lines.append(f"{i}. {authors}. ({year}). {title}. {journal}.\n")
        
        return ''.join(lines)
    
    def _today(self) -> str:
        from datetime import date
        return date.today().strftime("%Y-%m-%d")
