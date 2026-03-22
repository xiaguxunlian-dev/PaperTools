"""
CrossRef 检索 — via CrossRef API
文档: https://www.crossref.org/documentation/retrieve-links/rest-api/
免费，速率: 50 req/sec
"""
import urllib.request
import urllib.parse
import json
from typing import Optional


class CrossRefSearcher:
    BASE_URL = "https://api.crossref.org/works"
    AGENT = "ResearchSuite/1.0 (mailto:research@example.com)"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
    
    def search(self, query: str, limit: int = 20) -> list[dict]:
        params = {
            'query': query,
            'rows': min(limit * 2, 100),
            'select': 'DOI,title,author,abstract,published-print,published-online,journal-'
                      'title,container-title,subject,volume,issue,page,URL',
            'mailto': 'research@example.com',
        }
        
        url = self.BASE_URL + '?' + urllib.parse.urlencode(params)
        headers = {
            'User-Agent': self.AGENT,
            'Accept': 'application/json',
        }
        if self.api_key:
            headers['X-USER-TOKEN'] = self.api_key
        
        req = urllib.request.Request(url, headers=headers)
        
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode('utf-8'))
        except Exception as e:
            print(f"CrossRef search error: {e}")
            return []
        
        papers = []
        for item in data.get('message', {}).get('items', []):
            authors_raw = item.get('author', []) or []
            authors = [
                f"{a.get('given', '')} {a.get('family', '')}".strip()
                for a in authors_raw
            ]
            
            date = item.get('published-print') or item.get('published-online') or {}
            date_parts = date.get('date-parts', [[]])
            year = str(date_parts[0][0]) if date_parts and date_parts[0] else 'N/A'
            
            journal = (
                item.get('journal-title') or
                item.get('container-title', ['N/A'])[0]
            )
            
            papers.append({
                'id': item.get('DOI', ''),
                'title': (item.get('title', ['N/A'])[0] if item.get('title') else 'N/A'),
                'abstract': item.get('abstract') or '',
                'authors': authors,
                'year': year,
                'journal': journal,
                'doi': item.get('DOI'),
                'url': item.get('URL', ''),
                'keywords': [s.lower() for s in item.get('subject', [])[:5]],
                'citations': 0,
            })
        
        return papers
