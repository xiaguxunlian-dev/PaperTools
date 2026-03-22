#!/usr/bin/env python3
"""
PaperTools CLI — Scientific Literature & Evidence Assistant
Entry point for all research operations.
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import argparse
import json
import dataclasses
from pathlib import Path

# Add project root and scripts dir to path so modules can be found
# regardless of which directory the script is invoked from
_SCRIPT_DIR = Path(__file__).resolve().parent          # .../scripts/
_PROJECT_ROOT = _SCRIPT_DIR.parent                     # .../PaperTools/
sys.path.insert(0, str(_SCRIPT_DIR))
sys.path.insert(0, str(_PROJECT_ROOT))

from config import Config
from search.federated import FederatedSearcher
from assess.rob2 import RoB2Assessor
from assess.robins import RoBINSIAssessor
from assess.grade import GRADEAssessor
from assess.jbi import JBIAssessor
from synthesize.pico import PICOExtractor
from synthesize.evidence_table import EvidenceTableGenerator
from synthesize.prisma import PRISMAGenerator
from write.imrad import IMRADWriter
from write.references import ReferenceFormatter

# Phase 3: Meta Analysis
from meta.analyzer import MetaAnalyzer
from meta.effect_size import EffectSizeExtractor
from meta.forest_plot import ForestPlotGenerator
from meta.heterogeneity import HeterogeneityCalculator

# Phase 3: Knowledge Graph
from kg.builder import KnowledgeGraphBuilder, TrendAnalyzer, GraphVisualizer, KnowledgeGraph
from kg.extractor import EntityExtractor, RelationExtractor, Entity, Relation


def cmd_search(args):
    dbs = (args.database or 'pubmed').split(',')
    limit = args.limit or 3
    query = ' '.join(args.query) if isinstance(args.query, list) else args.query

    searcher = FederatedSearcher(api_keys=Config().get_api_keys())
    results = searcher.search(query, databases=dbs, limit=limit)
    
    print(f"\n{'='*60}")
    print(f"[SEARCH] Found {results['total']} papers")
    print(f"{'='*60}\n")

    for i, paper in enumerate(results['papers'], 1):
        print(f"[{i}] {paper.get('title', 'N/A')}")
        print(f"    Authors: {', '.join(paper.get('authors', [])[:3])}{' et al.' if len(paper.get('authors', [])) > 3 else ''}")
        print(f"    Year: {paper.get('year', 'N/A')} | DB: {paper.get('source', 'N/A')}")
        print(f"    DOI: {paper.get('doi', 'N/A')}")
        print(f"    Abstract: {paper.get('abstract', 'N/A')[:200]}...")
        print(f"    Keywords: {', '.join(paper.get('keywords', []))}")
        print()
    
    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))


def cmd_assess(args):
    tool = args.tool.lower()
    paper_paths = args.papers or []
    
    results = []
    if tool == 'rob2':
        assessor = RoB2Assessor()
        for p in paper_paths:
            r = assessor.assess_file(p)
            results.append(r)
    elif tool == 'robins':
        assessor = RoBINSIAssessor()
        for p in paper_paths:
            r = assessor.assess_file(p)
            results.append(r)
    elif tool == 'grade':
        assessor = GRADEAssessor()
        r = assessor.assess_query(args.query or "", args.context or "")
        results.append(r)
    elif tool == 'jbi':
        assessor = JBIAssessor()
        for p in paper_paths:
            r = assessor.assess_file(p)
            results.append(r)
    else:
        print(f"Unknown tool: {tool}")
        return
    
    for r in results:
        # Dataclass objects are not JSON-serializable by default; convert first
        if dataclasses.is_dataclass(r) and not isinstance(r, type):
            r = dataclasses.asdict(r)
        print(json.dumps(r, ensure_ascii=False, indent=2))


def cmd_pico(args):
    extractor = PICOExtractor()
    result = extractor.extract(args.text or args.query or "")
    # PICO is a dataclass — convert to dict before JSON serialization
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))


def cmd_table(args):
    query = args.query
    format_ = args.format or 'markdown'
    limit = args.limit or 20
    
    searcher = FederatedSearcher(api_keys=Config().get_api_keys())
    results = searcher.search(query, databases=['pubmed', 'arxiv', 'semantic'], limit=limit)
    
    generator = EvidenceTableGenerator()
    table = generator.generate(results['papers'], format_=format_)
    print(table)


def cmd_prisma(args):
    searcher = FederatedSearcher(api_keys=Config().get_api_keys())
    results = searcher.search(args.query, databases=['pubmed', 'arxiv'], limit=200)
    
    generator = PRISMAGenerator()
    flow_data = generator.generate(results, query=args.query)
    
    print(json.dumps(flow_data, ensure_ascii=False, indent=2))
    print("\n📊 PRISMA 流程图数据已生成，可导入 PRISMA Flow Diagram 工具")


def cmd_review(args):
    searcher = FederatedSearcher(api_keys=Config().get_api_keys())
    topic = args.topic or args.query
    results = searcher.search(topic, databases=['pubmed', 'arxiv', 'semantic'], limit=50)
    
    writer = IMRADWriter()
    extractor = PICOExtractor()
    pico = extractor.extract(args.topic)
    
    review = writer.generate(
        topic=args.topic,
        papers=results['papers'],
        pico=pico,
        sections=args.sections.split(',') if args.sections else ['background', 'methods'],
    )
    print(review)
    
    if args.output:
        Path(args.output).write_text(review, encoding='utf-8')
        print(f"\n✅ 已保存到 {args.output}")


def cmd_refs(args):
    formatter = ReferenceFormatter(style=args.style or 'bibtex')
    papers_file = args.papers or 'papers.json'
    
    try:
        papers = json.loads(Path(papers_file).read_text(encoding='utf-8'))
    except:
        papers = []
    
    output = formatter.format(papers)
    print(output)
    
    if args.output:
        Path(args.output).write_text(output, encoding='utf-8')


# ──────────── Phase 3: Meta Analysis ────────────

def cmd_meta(args):
    """执行 Meta 分析"""
    analyzer = MetaAnalyzer()
    
    if args.studies:
        # 从 JSON 文件加载研究数据
        import json
        studies_data = json.loads(Path(args.studies).read_text(encoding='utf-8'))
        for s in studies_data:
            analyzer.add_study_direct(
                name=s['name'],
                effect_type=s.get('type', 'OR'),
                effect=float(s['effect']),
                ci_lower=float(s['ci_lower']),
                ci_upper=float(s['ci_upper']),
                year=s.get('year'),
                n_total=s.get('n_total'),
                n_events=s.get('n_events'),
                group=s.get('group', ''),
            )
    elif args.extract:
        # 从文本文件提取
        text = Path(args.extract).read_text(encoding='utf-8', errors='ignore')
        extractor = EffectSizeExtractor()
        effects = extractor.extract_all(text)
        if not effects:
            print("❌ 未找到效应量，请使用 --studies 直接输入数据")
            return
        effect = effects[0]
        analyzer.add_study_direct(
            name=args.extract,
            effect_type=effect.type,
            effect=float(effect.point_estimate),
            ci_lower=float(effect.ci_lower),
            ci_upper=float(effect.ci_upper),
            p_value=float(effect.p_value) if effect.p_value else None,
        )
    
    results = analyzer.analyze(model=args.model)
    report = analyzer.report(results)
    print(report)
    
    if args.output:
        import json
        Path(args.output).write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f"\n✅ JSON 结果已保存到 {args.output}")


def cmd_forest(args):
    """生成森林图"""
    import json
    
    if args.data:
        data = json.loads(Path(args.data).read_text(encoding='utf-8'))
    else:
        # 生成示例数据
        data = {
            'studies': [
                {'name': 'Smith', 'year': 2020, 'effect': 0.75, 'ci_lower': 0.55, 'ci_upper': 1.02, 'weight': 25.0},
                {'name': 'Johnson', 'year': 2021, 'effect': 0.68, 'ci_lower': 0.50, 'ci_upper': 0.92, 'weight': 30.0},
                {'name': 'Williams', 'year': 2022, 'effect': 0.82, 'ci_lower': 0.60, 'ci_upper': 1.12, 'weight': 20.0},
                {'name': 'Brown', 'year': 2023, 'effect': 0.71, 'ci_lower': 0.52, 'ci_upper': 0.97, 'weight': 25.0},
            ],
            'pooled': {'effect': 0.72, 'ci_lower': 0.60, 'ci_upper': 0.87, 'pvalue': 0.0005},
            'heterogeneity': {'q': 2.5, 'p': 0.47, 'i2': 20},
        }
    
    gen = ForestPlotGenerator()
    forest_data = gen.generate(
        studies=data['studies'],
        pooled=data['pooled'],
        heterogeneity=data['heterogeneity'],
        model=args.model or 'random',
        effect_type=args.type or 'RR',
    )
    
    print(forest_data.to_ascii())
    
    if args.format == 'json':
        print("\n" + forest_data.to_json())
    elif args.format == 'plotly':
        print(json.dumps(forest_data.to_plotly(), ensure_ascii=False, indent=2))
    elif args.format == 'revman':
        print(gen.to_revman(forest_data))
    elif args.format == 'stata':
        print(gen.to_stata(forest_data))


# ──────────── Phase 3: Knowledge Graph ────────────

def cmd_kg_build(args):
    """构建知识图谱"""
    import json
    
    builder = KnowledgeGraphBuilder()
    
    if args.papers:
        # 从 JSON 文件加载论文
        papers = json.loads(Path(args.papers).read_text(encoding='utf-8'))
        for p in papers:
            builder.add_paper(
                pmid=p.get('pmid', ''),
                title=p.get('title', ''),
                abstract=p.get('abstract', ''),
                year=p.get('year'),
                keywords=p.get('keywords', []),
            )
    elif args.texts:
        # 从文本目录读取
        for txt_file in Path(args.texts).glob('*.txt'):
            text = txt_file.read_text(encoding='utf-8', errors='ignore')
            builder.add_text(text, source=txt_file.stem)
    
    kg = builder.build()
    summary = builder.summary()
    
    # 输出摘要
    print("\n" + GraphVisualizer(kg).to_ascii())
    
    # 导出
    if args.format == 'neo4j':
        print(kg.to_neo4j_cypher())
    elif args.format == 'networkx':
        print(json.dumps(kg.to_networkx(), ensure_ascii=False, indent=2))
    else:
        print(kg.to_json())
    
    if args.output:
        if args.format == 'neo4j':
            Path(args.output).write_text(kg.to_neo4j_cypher(), encoding='utf-8')
        elif args.format == 'networkx':
            Path(args.output).write_text(json.dumps(kg.to_networkx(), ensure_ascii=False, indent=2), encoding='utf-8')
        else:
            Path(args.output).write_text(kg.to_json(), encoding='utf-8')
        print(f"\n✅ 图谱已保存到 {args.output}")


def cmd_kg_trends(args):
    """研究趋势分析"""
    import json
    
    if not args.kg:
        print("❌ 需要先构建图谱: paper_tools kg-build --papers <file> --output kg.json")
        return
    
    kg_data = json.loads(Path(args.kg).read_text(encoding='utf-8'))
    
    # 重建 KG
    kg = KnowledgeGraph()
    for e_data in kg_data.get('entities', []):
        kg.entities.append(Entity(**e_data))
    for r_data in kg_data.get('relations', []):
        kg.relations.append(Relation(**r_data))
    
    analyzer = TrendAnalyzer(kg)
    trends = analyzer.analyze_trends()
    
    print("\n📈 研究趋势分析\n")
    
    # 发表时间线
    timeline = trends['publication_timeline']
    if timeline:
        print("发表时间线:")
        for entry in timeline[-10:]:
            bar = '▓' * min(entry['count'], 30)
            print(f"  {entry['year']}: {bar} {entry['count']}")
    
    # 新兴实体
    emerging = trends.get('emerging_entities', [])
    if emerging:
        print("\n🆕 新兴实体 (近3年):")
        for e in emerging[:10]:
            print(f"  [{e['type']}] {e['name']}: 出现 {e['recent_count']} 次 (共 {e['total_count']})")
    
    # 热门通路
    pathways = trends.get('hot_pathways', [])
    if pathways:
        print("\n🔥 热门通路:")
        for p in pathways[:5]:
            print(f"  {p['pathway']}: {p['mention_count']} 次 ({', '.join(p['relation_types'])})")
    
    # Gap 分析
    gap = analyzer.gap_analysis()
    print(f"\n🔍 Gap 分析 ({gap['target_type']}):")
    print(f"  已有连接的实体: {gap['with_connections']}/{gap['total_entities']}")
    if gap['well_connected']:
        print("  研究充分:")
        for item in gap['well_connected'][:5]:
            print(f"    - {item['entity']}: {item['connections']} 个关联")
    
    if args.output:
        Path(args.output).write_text(json.dumps(trends, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f"\n✅ 趋势分析已保存到 {args.output}")


def cmd_config(args):
    cfg = Config()
    if args.set_key:
        key, value = args.set_key.split('=', 1)
        cfg.set_api_key(key.strip(), value.strip())
        print(f"✅ 已设置 {key} = {value}")
    elif args.list_keys:
        keys = cfg.list_api_keys()
        for k, v in keys.items():
            print(f"  {k}: {'✅ 已设置' if v else '❌ 未设置'}")
    else:
        print("用法: paper_tools config set <key>=<value>")


def main():
    parser = argparse.ArgumentParser(
        prog='research',
        description='🔬 Research Suite — AI 加速科研助手'
    )
    sub = parser.add_subparsers(dest='cmd')
    
    # Search
    p_search = sub.add_parser('search', help='多源文献检索')
    p_search.add_argument('query', nargs='+', help='检索词')
    p_search.add_argument('--database', '--db', dest='database', help='数据库列表，逗号分隔')
    p_search.add_argument('--limit', '--max', dest='limit', type=int, default=3, help='每库返回数量')
    p_search.add_argument('--json', action='store_true', help='JSON 输出')
    p_search.set_defaults(func=cmd_search)
    
    # Assess
    p_assess = sub.add_parser('assess', help='研究质量评估')
    p_assess.add_argument('--tool', required=True, choices=['rob2', 'robins', 'grade', 'jbi'], help='评估量表')
    p_assess.add_argument('--papers', nargs='+', help='论文路径列表')
    p_assess.add_argument('--query', help='研究问题（用于 GRADE）')
    p_assess.add_argument('--context', help='额外上下文（用于 GRADE）')
    p_assess.set_defaults(func=cmd_assess)
    
    # PICO
    p_pico = sub.add_parser('pico', help='PICO 框架解析')
    p_pico.add_argument('--text', help='输入文本')
    p_pico.add_argument('--query', dest='query', help='研究问题')
    p_pico.set_defaults(func=cmd_pico)
    
    # Table
    p_table = sub.add_parser('table', help='生成证据表格')
    p_table.add_argument('--query', required=True, help='检索词')
    p_table.add_argument('--format', choices=['markdown', 'csv', 'json'], default='markdown')
    p_table.add_argument('--limit', type=int)
    p_table.set_defaults(func=cmd_table)
    
    # PRISMA
    p_prisma = sub.add_parser('prisma', help='生成 PRISMA 流程图数据')
    p_prisma.add_argument('--query', required=True, help='系统综述检索词')
    p_prisma.set_defaults(func=cmd_prisma)
    
    # Review
    p_review = sub.add_parser('review', help='生成综述草稿')
    p_review.add_argument('--topic', required=True, help='综述主题')
    p_review.add_argument('--sections', help='章节列表，逗号分隔')
    p_review.add_argument('--output', '-o', help='输出文件路径')
    p_review.set_defaults(func=cmd_review)
    
    # Refs
    p_refs = sub.add_parser('refs', help='格式化参考文献')
    p_refs.add_argument('--papers', help='论文 JSON 文件')
    p_refs.add_argument('--style', choices=['bibtex', 'ris', 'endnote', 'vancouver'], default='bibtex')
    p_refs.add_argument('--output', '-o', help='输出文件路径')
    p_refs.set_defaults(func=cmd_refs)
    
    # Config
    p_cfg = sub.add_parser('config', help='配置管理')
    p_cfg.add_argument('--set-key', help='设置 API Key，格式: name=value')
    p_cfg.add_argument('--list-keys', action='store_true', help='列出所有 Key 状态')
    p_cfg.set_defaults(func=cmd_config)
    
    # Meta Analysis (Phase 3)
    p_meta = sub.add_parser('meta', help='Meta 分析')
    p_meta.add_argument('--studies', help='研究数据 JSON 文件')
    p_meta.add_argument('--extract', help='从文本文件提取效应量')
    p_meta.add_argument('--model', choices=['fixed', 'random'], help='效应模型')
    p_meta.add_argument('--output', '-o', help='输出 JSON 文件')
    p_meta.set_defaults(func=cmd_meta)
    
    # Forest Plot (Phase 3)
    p_forest = sub.add_parser('forest', help='生成森林图')
    p_forest.add_argument('--data', help='森林图数据 JSON 文件')
    p_forest.add_argument('--type', dest='type', default='RR', choices=['RR', 'OR', 'HR', 'MD', 'SMD'])
    p_forest.add_argument('--model', choices=['fixed', 'random'], default='random')
    p_forest.add_argument('--format', choices=['ascii', 'json', 'plotly', 'revman', 'stata'], default='ascii')
    p_forest.set_defaults(func=cmd_forest)
    
    # Knowledge Graph Build (Phase 3)
    p_kg = sub.add_parser('kg-build', help='构建知识图谱')
    p_kg.add_argument('--papers', help='论文 JSON 文件（含 pmid/title/abstract）')
    p_kg.add_argument('--texts', help='文本文件目录')
    p_kg.add_argument('--format', choices=['json', 'neo4j', 'networkx'], default='json')
    p_kg.add_argument('--output', '-o', help='输出文件')
    p_kg.set_defaults(func=cmd_kg_build)
    
    # Knowledge Graph Trends (Phase 3)
    p_trends = sub.add_parser('kg-trends', help='研究趋势分析')
    p_trends.add_argument('--kg', required=True, help='知识图谱 JSON 文件')
    p_trends.add_argument('--output', '-o', help='输出文件')
    p_trends.set_defaults(func=cmd_kg_trends)
    
    args = parser.parse_args()
    
    if not args.cmd:
        parser.print_help()
        return
    
    args.func(args)


if __name__ == '__main__':
    main()
