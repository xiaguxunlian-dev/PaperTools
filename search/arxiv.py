"""
ArXiv 检索 — via arXiv API
文档: https://info.arxiv.org/help/api/basics.html
"""
import urllib.request
import urllib.parse
import feedparser
import html
import re
from typing import Optional


class ArXivSearcher:
    BASE_URL = "http://export.arxiv.org/api/query"
    
    def search(self, query: str, limit: int = 20) -> list[dict]:
        params = {
            'search_query': f'all:{self._escape_query(query)}',
            'start': 0,
            'max_results': min(limit * 2, 100),
            'sortBy': 'relevance',
            'sortOrder': 'descending',
        }
        
        url = self.BASE_URL + '?' + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers={'User-Agent': 'ResearchSuite/1.0'})
        
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                raw = resp.read().decode('utf-8')
        except Exception as e:
            print(f"ArXiv search error: {e}")
            return []
        
        return self._parse_atom(raw)
    
    def _escape_query(self, query: str) -> str:
        # 去除特殊字符，保留基本搜索语法
        return re.sub(r'[^\w\s\-\:\.\+\"\'\(\)]', '', query).strip()
    
    def _parse_atom(self, xml_str: str) -> list[dict]:
        feed = feedparser.parse(xml_str)
        papers = []
        
        for entry in feed.entries:
            # 作者
            authors = [a.get('name', '') for a in entry.get('authors', [])]
            
            # 摘要（arXiv 有 summary 字段）
            abstract = html.unescape(entry.get('summary', ''))
            abstract = re.sub(r'\s+', ' ', abstract).strip()
            
            # 关键词（arXiv 的 category 作为领域标签）
            tags = [t.get('term', '').lower() for t in entry.get('tags', [])]
            
            # 链接
            links = {l.get('rel', ''): l.get('href', '') for l in entry.get('links', [])}
            
            # 年份
            published = entry.get('published', '')
            year = published[:4] if published else 'N/A'
            
            # DOI
            doi = None
            for l in entry.get('arxiv_identifier', '').split('/'):
                if 'doi' in l:
                    doi = l.replace('doi:', '')
                    break
            
            papers.append({
                'id': entry.get('id', '').split('/')[-1],
                'title': html.unescape(entry.get('title', 'N/A').replace('\n', ' ')),
                'abstract': abstract,
                'authors': authors,
                'year': year,
                'journal': 'arXiv:' + entry.get('arxiv_primary_category', {}).get('term', ''),
                'doi': doi,
                'url': links.get('alternate', links.get('self', '')),
                'keywords': tags,
                'citations': 0,  # arXiv 不提供引用数
            })
        
        return papers
