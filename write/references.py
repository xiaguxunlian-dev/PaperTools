"""
参考文献格式化工具
支持 BibTeX / RIS / Vancouver / EndNote 格式
"""
import re


class ReferenceFormatter:
    """
    参考文献格式化工具
    
    支持格式:
    - BibTeX: .bib 文件，LaTeX 引用
    - RIS: 医学/生命科学常用
    - Vancouver: 医学期刊编号式
    - EndNote: XML/Tag 格式
    """
    
    def __init__(self, style: str = 'bibtex'):
        self.style = style
    
    def format(self, papers: list[dict]) -> str:
        """将论文列表格式化为指定参考文献格式"""
        formatter = getattr(self, f'_to_{self.style}', self._to_bibtex)
        return '\n'.join(formatter(p) for p in papers)
    
    def _to_bibtex(self, p: dict) -> str:
        """转换为 BibTeX 格式"""
        authors = ' and '.join(p.get('authors', [])[:10])
        if len(p.get('authors', [])) > 10:
            authors += ' et al.'
        
        # 生成 citation key
        first_author = p.get('authors', ['Unknown'])
        if isinstance(first_author, list) and first_author:
            last_name = first_author[0].split()[-1] if ' ' in first_author[0] else first_author[0]
        else:
            last_name = 'Unknown'
        year = p.get('year', 'n.d.')
        key = f"{last_name}{year}".replace(' ', '').replace(',', '')
        
        title = p.get('title', 'Untitled')
        journal = p.get('journal', '')
        doi = p.get('doi', '')
        
        lines = [
            f"@article{{{key},",
            f"  title = {{{title}}},",
            f"  author = {{{authors}}},",
            f"  journal = {{{journal}}},",
            f"  year = {{{year}}},",
        ]
        if doi:
            lines.append(f"  doi = {{{doi}}},")
        
        lines.append("}")
        return '\n'.join(lines)
    
    def _to_ris(self, p: dict) -> str:
        """转换为 RIS 格式"""
        lines = ["TY  - JOUR"]
        
        for author in p.get('authors', []):
            lines.append(f"AU  - {author}")
        
        title = p.get('title', 'Untitled')
        lines.append(f"TI  - {title}")
        
        journal = p.get('journal', '')
        if journal:
            lines.append(f"JO  - {journal}")
        
        year = p.get('year', '')
        if year:
            lines.append(f"PY  - {year}")
        
        doi = p.get('doi', '')
        if doi:
            lines.append(f"DO  - {doi}")
        
        lines.append("ER  -")
        return '\n'.join(lines)
    
    def _to_vancouver(self, p: dict) -> str:
        """转换为 Vancouver 格式（编号式）"""
        authors = p.get('authors', [])
        if len(authors) <= 6:
            author_str = ', '.join(a.split()[-1] if ' ' in a else a for a in authors)
        else:
            first_three = ', '.join(a.split()[-1] if ' ' in a else a for a in authors[:3])
            author_str = f"{first_three}, et al."
        
        year = p.get('year', 'n.d.')
        title = p.get('title', 'Untitled')
        journal = p.get('journal', '')
        volume = p.get('volume', '')
        pages = p.get('pages', '')
        doi = p.get('doi', '')
        
        ref = f"{author_str}. {title}. {journal}"
        if year:
            ref += f" {year}"
        if volume:
            ref += f";{volume}"
        if pages:
            ref += f":{pages}"
        if doi:
            ref += f". doi:{doi}"
        
        return ref + '.'
    
    def _to_endnote(self, p: dict) -> str:
        """转换为 EndNote Tagged format"""
        lines = [
            "%0 Journal Article",
        ]
        for author in p.get('authors', []):
            lines.append(f"%A {author}")
        
        lines.append(f"%T {p.get('title', 'Untitled')}")
        lines.append(f"%J {p.get('journal', '')}")
        
        year = p.get('year', '')
        if year:
            lines.append(f"%D {year}")
        
        doi = p.get('doi', '')
        if doi:
            lines.append(f"%M {doi}")
        
        lines.append("ER  -")
        return '\n'.join(lines)
    
    def format_batch(self, papers: list[dict], style: str = None) -> dict:
        """批量格式化为多种格式"""
        style = style or self.style
        styles = ['bibtex', 'ris', 'vancouver', 'endnote']
        
        result = {}
        for s in styles:
            self.style = s
            result[s] = self.format(papers)
        
        return result
