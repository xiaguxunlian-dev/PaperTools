"""
知识图谱构建与趋势分析器
整合实体抽取 + 关系抽取 → 构建图谱 → 趋势分析 → 可视化
"""
import json
import math
from collections import defaultdict
from typing import Optional

from .extractor import EntityExtractor, RelationExtractor, Entity, Relation, KnowledgeGraph


class KnowledgeGraphBuilder:
    """
    知识图谱构建器
    
    流水线:
    1. 实体抽取（基因/疾病/药物/通路/症状）
    2. 关系抽取（上下调/治疗/因果/相互作用）
    3. 图谱构建（去重/合并/质量控制）
    4. 统计摘要
    """
    
    def __init__(self):
        self.kg = KnowledgeGraph()
        self.entity_extractor = EntityExtractor()
        self.relation_extractor = RelationExtractor()
        self._papers = []  # 原始论文数据
    
    def add_paper(
        self,
        pmid: str,
        title: str,
        abstract: str,
        year: Optional[int] = None,
        keywords: list[str] = None,
    ) -> 'KnowledgeGraphBuilder':
        """
        添加一篇论文到图谱
        
        Args:
            pmid: PubMed ID
            title: 论文标题
            abstract: 摘要
            year: 发表年份
            keywords: 关键词列表
        """
        text = f"{title} {abstract}"
        keywords = keywords or []
        
        # 1. 抽取实体
        entities = self.entity_extractor.extract_entities(text, pmid=pmid)
        
        # 2. 抽取关系
        relations = self.relation_extractor.extract_relations(text, entities, pmid=pmid)
        
        # 3. 添加到图谱
        for entity in entities:
            entity.source = title[:100]  # 截断
            entity.properties['year'] = year
            entity.properties['keywords'] = keywords
            self.kg.add_entity(entity)
        
        for rel in relations:
            rel.paper = title[:100]
            self.kg.add_relation(rel)
        
        self._papers.append({
            'pmid': pmid,
            'title': title,
            'year': year,
            'entities': len(entities),
            'relations': len(relations),
        })
        
        return self
    
    def add_text(
        self,
        text: str,
        source: str = "",
        year: Optional[int] = None,
    ) -> 'KnowledgeGraphBuilder':
        """直接添加文本"""
        entities = self.entity_extractor.extract_entities(text, pmid=source)
        relations = self.relation_extractor.extract_relations(text, entities, pmid=source)
        
        for entity in entities:
            entity.source = source
            entity.properties['year'] = year
            self.kg.add_entity(entity)
        
        for rel in relations:
            rel.paper = source
            self.kg.add_relation(rel)
        
        return self
    
    def build(self) -> KnowledgeGraph:
        """返回构建好的图谱"""
        self.kg.metadata = {
            'n_papers': len(self._papers),
            'created_by': 'ResearchSuite KG Builder',
        }
        return self.kg
    
    def summary(self) -> dict:
        """生成图谱统计摘要"""
        entity_counts = defaultdict(int)
        relation_counts = defaultdict(int)
        
        for e in self.kg.entities:
            entity_counts[e.type] += 1
        
        for r in self.kg.relations:
            relation_counts[r.type] += 1
        
        # 计算度数
        degree = defaultdict(lambda: {'in': 0, 'out': 0})
        for r in self.kg.relations:
            degree[r.target_id]['in'] += 1
            degree[r.source_id]['out'] += 1
        
        # 找出 hub 实体（度数最高的节点）
        hub_entities = sorted(
            degree.items(),
            key=lambda x: x[1]['in'] + x[1]['out'],
            reverse=True
        )[:10]
        
        return {
            'n_entities': len(self.kg.entities),
            'n_relations': len(self.kg.relations),
            'n_papers': len(self._papers),
            'entity_types': dict(entity_counts),
            'relation_types': dict(relation_counts),
            'top_entities': [
                {
                    'id': eid,
                    'total_degree': d['in'] + d['out'],
                    'in_degree': d['in'],
                    'out_degree': d['out'],
                }
                for eid, d in hub_entities
            ],
        }


class TrendAnalyzer:
    """
    研究趋势分析器
    
    基于知识图谱和论文集合，分析：
    1. 研究热度趋势（随时间发表数量）
    2. 关键词趋势
    3. 新兴实体（近年新出现的基因/药物）
    4. 热门通路
    5. 竞争格局（多机构/多团队分析）
    """
    
    def __init__(self, kg: KnowledgeGraph, papers: list[dict] = None):
        self.kg = kg
        self.papers = papers or []
    
    def analyze_trends(self) -> dict:
        """综合趋势分析"""
        return {
            'publication_timeline': self.publication_timeline(),
            'entity_trends': self.entity_trends(),
            'emerging_entities': self.emerging_entities(),
            'hot_pathways': self.hot_pathways(),
            'entity_cooccurrence': self.entity_cooccurrence(),
        }
    
    def publication_timeline(self) -> list[dict]:
        """发表时间线"""
        by_year = defaultdict(int)
        for paper in self.papers:
            year = paper.get('year')
            if year:
                by_year[str(year)] += 1
        
        return [
            {'year': year, 'count': count}
            for year, count in sorted(by_year.items())
        ]
    
    def entity_trends(self) -> dict:
        """各类实体随时间的分布"""
        trends = defaultdict(lambda: defaultdict(int))
        
        for entity in self.kg.entities:
            etype = entity.type
            year = str(entity.properties.get('year', 'unknown'))
            trends[etype][year] += 1
        
        return {
            etype: [
                {'year': year, 'count': count}
                for year, count in sorted(by_year.items())
            ]
            for etype, by_year in trends.items()
        }
    
    def emerging_entities(self, recent_years: int = 3) -> list[dict]:
        """新兴实体（最近几年出现且频率上升的）"""
        recent_entities = defaultdict(int)
        all_entities = defaultdict(int)
        
        import datetime
        current_year = datetime.date.today().year
        
        for entity in self.kg.entities:
            etype = entity.type
            year = entity.properties.get('year')
            
            if year and (current_year - int(year)) <= recent_years:
                recent_entities[f"{etype}:{entity.name}"] += 1
            all_entities[f"{etype}:{entity.name}"] += 1
        
        # 计算增长比
        emerging = []
        for key, recent_count in recent_entities.items():
            total_count = all_entities[key]
            if total_count > 0:
                growth_ratio = recent_count / total_count
                if recent_count >= 2:  # 至少出现2次
                    parts = key.split(':', 1)
                    emerging.append({
                        'type': parts[0],
                        'name': parts[1],
                        'recent_count': recent_count,
                        'total_count': total_count,
                        'growth_ratio': round(growth_ratio, 3),
                    })
        
        emerging.sort(key=lambda x: (x['recent_count'], x['growth_ratio']), reverse=True)
        return emerging[:20]
    
    def hot_pathways(self) -> list[dict]:
        """热门通路排名"""
        pathway_counts = defaultdict(int)
        pathway_relations = defaultdict(set)
        
        for rel in self.kg.relations:
            # 找出 pathway 类型的实体
            if ':' in rel.source_id:
                src_type = rel.source_id.split(':')[0]
                tgt_type = rel.target_id.split(':')[0]
                
                if src_type == 'pathway':
                    pathway_counts[rel.source_id] += 1
                    pathway_relations[rel.source_id].add(rel.type)
                elif tgt_type == 'pathway':
                    pathway_counts[rel.target_id] += 1
                    pathway_relations[rel.target_id].add(rel.type)
        
        return [
            {
                'pathway': pid.split(':')[1],
                'mention_count': count,
                'relation_types': list(rel_types),
            }
            for pid, (count, rel_types) in sorted(
                [(k, (c, vr)) for k, c in pathway_counts.items() for vr in [pathway_relations[k]]],
                key=lambda x: x[1][0],
                reverse=True
            )
        ][:10]
    
    def entity_cooccurrence(self) -> list[dict]:
        """实体共现分析（哪些实体经常一起出现）"""
        cooccur = defaultdict(int)
        
        # 从关系中提取共现
        for rel in self.kg.relations:
            key = tuple(sorted([rel.source_id, rel.target_id]))
            cooccur[key] += 1
        
        return [
            {
                'entity1': pair[0].split(':')[1] if ':' in pair[0] else pair[0],
                'entity2': pair[1].split(':')[1] if ':' in pair[1] else pair[1],
                'cooccur_count': count,
                'relation_type': 'related',
            }
            for pair, count in sorted(cooccur.items(), key=lambda x: x[1], reverse=True)
            if count >= 2
        ][:20]
    
    def gap_analysis(self, target_entity_type: str = "disease") -> dict:
        """
        Gap 分析 — 找出某类型实体（如疾病）的研究空白
        
        发现：已有很多基因与某疾病关联，但还有很多基因未被研究
        """
        # 获取该类型的所有实体
        target_entities = {e.id: e for e in self.kg.entities if e.type == target_entity_type}
        
        # 找出与这些实体有关联的基因/药物
        connected_to = defaultdict(set)
        for rel in self.kg.relations:
            if rel.target_id in target_entities:
                connected_to[rel.target_id].add(rel.source_id)
            if rel.source_id in target_entities:
                connected_to[rel.source_id].add(rel.target_id)
        
        return {
            'target_type': target_entity_type,
            'total_entities': len(target_entities),
            'with_connections': sum(1 for v in connected_to.values() if v),
            'without_connections': sum(1 for v in connected_to.values() if not v),
            'well_connected': [
                {
                    'entity': eid.split(':')[1] if ':' in eid else eid,
                    'connections': len(connections),
                }
                for eid, connections in sorted(
                    connected_to.items(),
                    key=lambda x: len(x[1]),
                    reverse=True
                )[:10]
            ],
            'isolated_entities': [
                eid.split(':')[1] if ':' in eid else eid
                for eid, connections in connected_to.items()
                if not connections
            ],
        }


class GraphVisualizer:
    """
    图谱可视化数据生成器
    
    支持导出格式:
    - D3.js 兼容 JSON
    - ECharts 兼容
    - Cytoscape 格式
    - 静态 ASCII 图
    """
    
    def __init__(self, kg: KnowledgeGraph):
        self.kg = kg
    
    def to_d3_json(self) -> str:
        """D3.js 力导向图数据"""
        nodes = [
            {
                'id': e.id,
                'name': e.name,
                'group': e.type,
                'degree': self._degree(e.id),
            }
            for e in self.kg.entities
        ]
        
        links = [
            {
                'source': r.source_id,
                'target': r.target_id,
                'type': r.type,
                'value': r.weight,
            }
            for r in self.kg.relations
        ]
        
        return json.dumps({'nodes': nodes, 'links': links}, ensure_ascii=False, indent=2)
    
    def to_echarts(self) -> dict:
        """ECharts 关系图数据"""
        nodes = []
        categories = []
        cat_names = set()
        
        for e in self.kg.entities:
            if e.type not in cat_names:
                cat_names.add(e.type)
                categories.append({'name': e.type})
            
            nodes.append({
                'name': e.name,
                'category': e.type,
                'draggable': True,
                'value': self._degree(e.id),
            })
        
        edges = [
            {'source': r.source_id.split(':')[-1], 'target': r.target_id.split(':')[-1], 'value': r.weight}
            for r in self.kg.relations
        ]
        
        return {
            'title': {'text': '知识图谱', 'subtext': f'{len(nodes)}实体 / {len(edges)}关系'},
            'tooltip': {},
            'legend': [{'data': list(cat_names)}],
            'series': [{
                'type': 'graph',
                'layout': 'force',
                'data': nodes,
                'links': edges,
                'categories': categories,
                'roam': True,
                'label': {'show': True, 'position': 'right'},
                'force': {'repulsion': 100},
            }],
        }
    
    def to_ascii(self, max_nodes: int = 50) -> str:
        """ASCII 艺术可视化（简化版）"""
        lines = [
            "╔═══════════════════════════════════════════════════════╗",
            f"║           🔗 知识图谱概览 (共 {len(self.kg.entities)} 实体 / {len(self.kg.relations)} 关系)    ║",
            "╚═══════════════════════════════════════════════════════╝",
            "",
        ]
        
        # 实体类型统计
        counts = defaultdict(int)
        for e in self.kg.entities:
            counts[e.type] += 1
        
        lines.append("📊 实体分布:")
        for etype, count in sorted(counts.items(), key=lambda x: x[1], reverse=True):
            bar = '█' * min(count, 30)
            lines.append(f"  {etype:<12} {bar} {count}")
        
        lines.append("")
        lines.append("🔗 关系分布:")
        rel_counts = defaultdict(int)
        for r in self.kg.relations:
            rel_counts[r.type] += 1
        
        for rtype, count in sorted(rel_counts.items(), key=lambda x: x[1], reverse=True):
            bar = '●' * min(count, 30)
            lines.append(f"  {rtype:<20} {bar} {count}")
        
        # Top 实体
        lines.append("")
        lines.append("⭐ Top 连接度实体:")
        degree = {}
        for r in self.kg.relations:
            degree[r.source_id] = degree.get(r.source_id, 0) + 1
            degree[r.target_id] = degree.get(r.target_id, 0) + 1
        
        for eid, deg in sorted(degree.items(), key=lambda x: x[1], reverse=True)[:10]:
            ename = eid.split(':')[1] if ':' in eid else eid
            lines.append(f"  {ename:<20} (度数: {deg})")
        
        return '\n'.join(lines)
    
    def _degree(self, eid: str) -> int:
        return sum(
            1 for r in self.kg.relations
            if r.source_id == eid or r.target_id == eid
        )
