"""
Semantic Scholar 检索 — via Semantic Scholar API
文档: https://api.semanticscholar.org/api-docs/
免费层: 100 req/5min，无需 API Key
"""
import urllib.request
import urllib.parse
import json
from typing import Optional


class SemanticScholarSearcher:
    BASE_URL = "https://api.semanticscholar.org/graph/v1"
    
    # 免费字段
    FIELDS = ','.join([
        'title', 'abstract', 'authors', 'year', 'venue',
        'publicationDate', 'citationCount', 'openAccessPdf',
        'externalIds', 'keywords', 'fieldsOfStudy',
    ])
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
    
    def search(self, query: str, limit: int = 20) -> list[dict]:
        params = {
            'query': query,
            'limit': min(limit * 2, 100),
            'fields': self.FIELDS,
        }
        
        url = f"{self.BASE_URL}/paper/search?" + urllib.parse.urlencode(params)
        headers = {
            'User-Agent': 'ResearchSuite/1.0',
            'Accept': 'application/json',
        }
        if self.api_key:
            headers['x-api-key'] = self.api_key
        
        req = urllib.request.Request(url, headers=headers)
        
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode('utf-8'))
        except Exception as e:
            print(f"Semantic Scholar search error: {e}")
            return []
        
        papers = []
        for item in data.get('data', []):
            authors = []
            for a in item.get('authors', []):
                if isinstance(a, dict):
                    authors.append(a.get('name', ''))
                else:
                    authors.append(str(a))
            
            external = item.get('externalIds', {}) or {}
            keywords = item.get('keywords', []) or []
            
            papers.append({
                'id': item.get('paperId', ''),
                'title': item.get('title', 'N/A'),
                'abstract': item.get('abstract') or '',
                'authors': authors,
                'year': item.get('year'),
                'journal': item.get('venue', 'N/A'),
                'doi': external.get('DOI'),
                'url': f"https://www.semanticscholar.org/paper/{item.get('paperId', '')}",
                'keywords': keywords if isinstance(keywords, list) else [],
                'citations': item.get('citationCount', 0) or 0,
            })
        
        return papers
