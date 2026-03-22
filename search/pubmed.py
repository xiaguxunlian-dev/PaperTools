"""
PubMed / PMC 检索 — via NCBI E-utilities API
文档: https://www.ncbi.nlm.nih.gov/home/develop/api/
"""
import urllib.request
import urllib.parse
import json
import time
import xml.etree.ElementTree as ET
from typing import Optional


class PubMedSearcher:
    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
    
    def _request(self, url: str, params: dict = None) -> dict:
        if params:
            params['api_key'] = self.api_key
            params['retmode'] = 'json'
            url += '?' + urllib.parse.urlencode(params)
        
        req = urllib.request.Request(url, headers={'User-Agent': 'ResearchSuite/1.0'})
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode('utf-8'))
    
    def _fetch_details(self, ids: list[str], fields: str = 'all') -> list[dict]:
        if not ids:
            return []
        id_list = ','.join(ids[:100])  # Efetch 限制每次最多100条
        url = f"{self.BASE_URL}/efetch.fcgi?db=pubmed&id={id_list}&rettype=xml&retmode=xml"
        req = urllib.request.Request(url, headers={'User-Agent': 'ResearchSuite/1.0'})
        
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                xml_content = resp.read().decode('utf-8')
        except Exception:
            return []
        
        return self._parse_pubmed_xml(xml_content)
    
    def _parse_pubmed_xml(self, xml_str: str) -> list[dict]:
        papers = []
        try:
            root = ET.fromstring(xml_str)
            for article in root.findall('.//PubmedArticle'):
                pubmed_data = article.find('MedlineCitation')
                article_data = pubmed_data.find('Article') if pubmed_data else None
                
                if article_data is None:
                    continue
                
                # 标题
                title_el = article_data.find('ArticleTitle')
                title = title_el.text if title_el is not None else 'N/A'
                
                # 摘要
                abstract_els = article_data.findall('AbstractText')
                abstract = ' '.join(el.text or '' for el in abstract_els)
                
                # 作者
                authors = []
                author_list = article_data.find('AuthorList')
                if author_list:
                    for author in author_list.findall('Author'):
                        last = author.find('LastName')
                        fore = author.find('ForeName')
                        if last is not None:
                            name = f"{fore.text} {last.text}" if fore is not None else last.text
                            authors.append(name.strip())
                
                # 年份
                pub_date = article_data.find('Journal') or article_data
                date_el = pub_date.find('JournalPublishedDate') or pub_date.find('PubDate')
                year = None
                if date_el is not None:
                    year_el = date_el.find('Year')
                    if year_el is not None and year_el.text:
                        year = year_el.text
                
                # DOI
                doi = None
                pubmed_id = None
                pmid_el = pubmed_data.find('PMID')
                if pmid_el is not None:
                    pubmed_id = pmid_el.text
                for idt in article_data.findall('.//ArticleId'):
                    if idt.get('IdType') == 'doi':
                        doi = idt.text
                        break
                
                # 期刊
                journal_el = article_data.find('Journal')
                journal = journal_el.find('Title').text if journal_el is not None else 'N/A'
                
                # 关键词
                keywords = []
                kw_list = article.find('.//KeywordList')
                if kw_list:
                    for kw in kw_list.findall('Keyword'):
                        if kw.text:
                            keywords.append(kw.text.strip().lower())
                
                papers.append({
                    'id': pubmed_id,
                    'title': title,
                    'abstract': abstract,
                    'authors': authors,
                    'year': year,
                    'journal': journal,
                    'doi': doi,
                    'keywords': keywords,
                })
        except ET.ParseError:
            pass
        
        return papers
    
    def search(self, query: str, limit: int = 20) -> list[dict]:
        """
        检索 PubMed
        
        Returns:
            list of paper dicts with fields: title, abstract, authors, year, journal, doi, keywords
        """
        # Step 1: esearch — 获取 ID 列表
        params = {
            'db': 'pubmed',
            'term': query,
            'retmax': min(limit * 3, 500),  # 多取一些以便去重
            'sort': 'relevance',
            'usehistory': 'n',
        }
        
        try:
            result = self._request(f"{self.BASE_URL}/esearch.fcgi", params)
            ids = result.get('esearchresult', {}).get('idlist', [])
        except Exception as e:
            print(f"PubMed search error: {e}")
            return []
        
        if not ids:
            return []
        
        time.sleep(0.4)  # 遵守 NCBI 速率限制（无 API Key 时）
        
        # Step 2: efetch — 获取详细信息
        papers = self._fetch_details(ids, fields='all')
        
        return papers[:limit]
