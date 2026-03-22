#!/usr/bin/env python3
"""Research Suite — 模块测试"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from config import Config
from assess.rob2 import RoB2Assessor
from assess.grade import GRADEAssessor
from assess.jbi import JBIAssessor
from synthesize.pico import PICOExtractor
from synthesize.evidence_table import EvidenceTable
from synthesize.prisma import PRISMAGenerator
from write.imrad import IMRADWriter
from write.references import ReferenceFormatter
from meta.analyzer import MetaAnalyzer
from meta.effect_size import EffectSizeExtractor
from meta.heterogeneity import HeterogeneityCalculator
from meta.forest_plot import ForestPlotGenerator
from kg.builder import KnowledgeGraphBuilder
from kg.extractor import EntityExtractor, RelationExtractor


def test_config():
    print("\n" + "="*60)
    print("TEST 1: Config")
    cfg = Config()
    print(f"  API keys loaded: {list(cfg.get_api_keys().keys())}")
    print("  ✅ PASS")


def test_pico():
    print("\n" + "="*60)
    print("TEST 2: PICO Extractor")
    extractor = PICOExtractor()
    
    test_queries = [
        "Aspirin for cardiovascular disease prevention in adults",
        "他汀类药物对心血管疾病二级预防的疗效和安全性",
    ]
    
    for q in test_queries:
        result = extractor.extract(q)
        print(f"\n  Query: {q}")
        print(f"  P: {result.population}")
        print(f"  I: {result.intervention}")
        print(f"  C: {result.comparison}")
        print(f"  O: {result.outcome}")
        print(f"  Type: {result.study_type}")
    
    print("\n  ✅ PASS")


def test_rob2():
    print("\n" + "="*60)
    print("TEST 3: RoB 2 Assessor")
    
    text = """
    This was a randomized, double-blind, placebo-controlled trial.
    Patients were randomly assigned using a computer-generated sequence.
    Allocation was concealed using sealed opaque envelopes.
    Both participants and investigators were blinded to treatment assignment.
    Primary outcome was assessed by an independent committee blinded to allocation.
    Intention-to-treat analysis was performed.
    The trial was registered at ClinicalTrials.gov (NCT12345678).
    """
    
    assessor = RoB2Assessor()
    result = assessor.assess_text(text, "Test RCT Paper")
    print(result.to_markdown())
    print(f"  Overall: {result.overall} ✅ PASS")


def test_jbi():
    print("\n" + "="*60)
    print("TEST 4: JBI Critical Appraisal")
    
    text = """
    This randomized controlled trial enrolled 200 patients.
    Randomization was performed using a random number table.
    Participants and personnel were blinded to allocation.
    Outcomes were measured using validated instruments.
    Complete follow-up was achieved in all participants.
    """
    
    assessor = JBIAssessor()
    result = assessor.assess(text, study_type='RCT', title="Test JBI")
    print(result.to_markdown())
    print("  ✅ PASS")


def test_grade():
    print("\n" + "="*60)
    print("TEST 5: GRADE Assessor")
    
    result = GRADEAssessor().assess(
        outcome="All-cause mortality",
        study_design="RCT",
        risk_of_bias=False,
        inconsistency=True,
        indirectness=False,
        imprecision=False,
        publication_bias=False,
    )
    print(result.to_markdown())
    print("  ✅ PASS")


def test_evidence_table():
    print("\n" + "="*60)
    print("TEST 6: Evidence Table Generator")
    
    papers = [
        {
            'title': 'Statins for cardiovascular prevention',
            'authors': ['Smith', 'Jones'],
            'year': '2022',
            'journal': 'NEJM',
            'doi': '10.1234/nejm.2022',
            'abstract': 'A randomized trial of statins in 5000 patients with cardiovascular disease showed significant reduction in mortality.',
            'source': 'pubmed',
            'citations': 45,
        },
        {
            'title': 'Effect of statins on lipid levels',
            'authors': ['Wang'],
            'year': '2021',
            'journal': 'Lancet',
            'doi': '10.1234/lancet.2021',
            'abstract': 'Cohort study of 3000 patients treated with statins.',
            'source': 'semantic',
            'citations': 23,
        },
    ]
    
    from synthesize.evidence_table import EvidenceTableGenerator
    gen = EvidenceTableGenerator()
    table = gen.generate(papers, format_='markdown')
    print(table[:500])
    print("  ✅ PASS")


def test_prisma():
    print("\n" + "="*60)
    print("TEST 7: PRISMA Generator")
    
    gen = PRISMAGenerator()
    data = gen.generate_manual(
        db_records=1500,
        duplicates=450,
        screened=1050,
        excluded=800,
        assessed=250,
        included_reports=12,
        query="Statins cardiovascular prevention",
        databases=['pubmed', 'arxiv', 'semantic'],
    )
    print(gen.to_ascii_diagram(data))
    print("  ✅ PASS")


def test_imrad():
    print("\n" + "="*60)
    print("TEST 8: IMRAD Writer")
    
    papers = [
        {
            'title': 'Statins and cardiovascular outcomes',
            'authors': ['Smith A', 'Jones B'],
            'year': '2022',
            'journal': 'NEJM',
            'abstract': 'RCT showing statin efficacy.',
            'doi': '10.1234/nejm',
            'citations': 50,
        },
    ]
    
    writer = IMRADWriter()
    review = writer.generate(
        topic="Statins for cardiovascular prevention",
        papers=papers,
        sections=['background', 'methods', 'results'],
    )
    print(review[:600])
    print("\n  ✅ PASS")


def test_references():
    print("\n" + "="*60)
    print("TEST 9: Reference Formatter")
    
    papers = [
        {
            'title': 'A study on statins',
            'authors': ['Smith A', 'Jones B', 'Wang C'],
            'year': '2022',
            'journal': 'NEJM',
            'doi': '10.1234/nejm.2022',
        },
    ]
    
    for style in ['bibtex', 'ris', 'vancouver']:
        fmt = ReferenceFormatter(style=style)
        print(f"\n  [{style.upper()}]")
        print(fmt.format(papers))
    
    print("  ✅ PASS")


def test_meta_analysis():
    print("\n" + "="*60)
    print("TEST 10: Meta Analysis")
    
    analyzer = MetaAnalyzer()
    
    # 添加虚拟研究数据（直接输入）
    studies = [
        {'name': 'Smith 2020', 'type': 'OR', 'effect': 0.65, 'ci_lower': 0.48, 'ci_upper': 0.88, 'year': 2020},
        {'name': 'Johnson 2021', 'type': 'OR', 'effect': 0.72, 'ci_lower': 0.55, 'ci_upper': 0.95, 'year': 2021},
        {'name': 'Williams 2022', 'type': 'OR', 'effect': 0.58, 'ci_lower': 0.40, 'ci_upper': 0.84, 'year': 2022},
        {'name': 'Brown 2023', 'type': 'OR', 'effect': 0.69, 'ci_lower': 0.50, 'ci_upper': 0.95, 'year': 2023},
    ]
    
    for s in studies:
        analyzer.add_study_direct(**s)
    
    results = analyzer.analyze(model='random')
    report = analyzer.report(results)
    print(report)
    print("  ✅ PASS")


def test_effect_size():
    print("\n" + "="*60)
    print("TEST 11: Effect Size Extractor")
    
    extractor = EffectSizeExtractor()
    
    text = """
    The treatment group showed a significantly reduced risk of mortality
    compared to control (RR = 0.75, 95% CI: 0.55-1.02, p = 0.06).
    Odds ratio was 0.68 (95% CI: 0.50-0.92).
    Hazard ratio for overall survival was 0.72 (95% CI: 0.55-0.95).
    """
    
    effects = extractor.extract_all(text)
    print(f"  Found {len(effects)} effect sizes:")
    for e in effects:
        print(f"  - {e.type}: {e.point_estimate} (95% CI: {e.ci_lower}–{e.ci_upper}) p={e.p_value}")
    
    print("  ✅ PASS")


def test_heterogeneity():
    print("\n" + "="*60)
    print("TEST 12: Heterogeneity Calculator")
    
    calc = HeterogeneityCalculator()
    effects = [
        {'ln_rr': -0.43, 'ci_lower': -0.73, 'ci_upper': -0.13},
        {'ln_rr': -0.33, 'ci_lower': -0.60, 'ci_upper': -0.05},
        {'ln_rr': -0.55, 'ci_lower': -0.92, 'ci_upper': -0.17},
        {'ln_rr': -0.37, 'ci_lower': -0.69, 'ci_upper': -0.05},
    ]
    
    result = calc.calculate(effects)
    print(result.to_markdown())
    print("  ✅ PASS")


def test_forest_plot():
    print("\n" + "="*60)
    print("TEST 13: Forest Plot Generator")
    
    gen = ForestPlotGenerator()
    studies = [
        {'name': 'Smith', 'year': 2020, 'effect': 0.75, 'ci_lower': 0.55, 'ci_upper': 1.02, 'weight': 25.0},
        {'name': 'Johnson', 'year': 2021, 'effect': 0.68, 'ci_lower': 0.50, 'ci_upper': 0.92, 'weight': 30.0},
        {'name': 'Williams', 'year': 2022, 'effect': 0.82, 'ci_lower': 0.60, 'ci_upper': 1.12, 'weight': 20.0},
        {'name': 'Brown', 'year': 2023, 'effect': 0.71, 'ci_lower': 0.52, 'ci_upper': 0.97, 'weight': 25.0},
    ]
    
    data = gen.generate(
        studies=studies,
        pooled={'effect': 0.72, 'ci_lower': 0.60, 'ci_upper': 0.87, 'pvalue': 0.0005},
        heterogeneity={'q': 2.5, 'p': 0.47, 'i2': 20},
        model='random',
        effect_type='RR',
    )
    
    print(data.to_ascii())
    print("\n  ✅ PASS")


def test_knowledge_graph():
    print("\n" + "="*60)
    print("TEST 14: Knowledge Graph Builder")
    
    text = """
    TP53 is a tumor suppressor gene that is frequently mutated in many cancers.
    BRCA1 mutations increase the risk of breast cancer.
    EGFR inhibitors are effective in EGFR-mutant non-small cell lung cancer.
    PD-1 checkpoint inhibitors activate T cell immune response against tumor cells.
    CTLA-4 blockade enhances anti-tumor immunity.
    mTOR pathway is activated in many cancers and can be targeted by everolimus.
    """
    
    builder = KnowledgeGraphBuilder()
    builder.add_text(text, source="Test Paper", year=2023)
    
    kg = builder.build()
    summary = builder.summary()
    
    print(f"  Entities: {summary['n_entities']}")
    print(f"  Relations: {summary['n_relations']}")
    print(f"  Entity types: {summary['entity_types']}")
    print(f"  Relation types: {summary['relation_types']}")
    
    from kg.builder import GraphVisualizer
    viz = GraphVisualizer(kg)
    print(viz.to_ascii())
    
    print("  ✅ PASS")


def test_entity_extractor():
    print("\n" + "="*60)
    print("TEST 15: Entity & Relation Extractor")
    
    text = """
    TP53 mutations are associated with poor prognosis in breast cancer.
    EGFR inhibitors treat non-small cell lung cancer by targeting the EGFR pathway.
    IL-6 is upregulated in rheumatoid arthritis and promotes inflammation.
    Aspirin inhibits COX enzymes and reduces inflammatory responses.
    PD-1/PD-L1 checkpoint blockade activates T cells to attack tumor cells.
    """
    
    entity_ext = EntityExtractor()
    rel_ext = RelationExtractor()
    
    entities = entity_ext.extract_entities(text, pmid="TEST123")
    relations = rel_ext.extract_relations(text, entities, pmid="TEST123")
    
    print(f"  Extracted {len(entities)} entities:")
    for e in entities:
        print(f"    - [{e.type}] {e.name}")
    
    print(f"\n  Extracted {len(relations)} relations:")
    for r in relations:
        print(f"    - {r.source_id} --[{r.type}]--> {r.target_id}")
    
    print("  ✅ PASS")


def main():
    print("\n" + "╔" + "═"*58 + "╗")
    print("║       🔬 Research Suite — 模块测试               ║")
    print("╚" + "═"*58 + "╝")
    
    tests = [
        ("Config", test_config),
        ("PICO Extractor", test_pico),
        ("RoB 2 Assessor", test_rob2),
        ("JBI Assessor", test_jbi),
        ("GRADE Assessor", test_grade),
        ("Evidence Table", test_evidence_table),
        ("PRISMA Generator", test_prisma),
        ("IMRAD Writer", test_imrad),
        ("Reference Formatter", test_references),
        ("Meta Analysis", test_meta_analysis),
        ("Effect Size Extractor", test_effect_size),
        ("Heterogeneity Calculator", test_heterogeneity),
        ("Forest Plot Generator", test_forest_plot),
        ("Knowledge Graph Builder", test_knowledge_graph),
        ("Entity & Relation Extractor", test_entity_extractor),
    ]
    
    passed = 0
    failed = 0
    
    for name, func in tests:
        try:
            func()
            passed += 1
        except Exception as e:
            print(f"\n  ❌ FAIL: {name}")
            print(f"     Error: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "="*60)
    print(f"  📊 结果: {passed} 通过, {failed} 失败, 共 {passed+failed} 项测试")
    print("="*60)
    
    if failed == 0:
        print("\n  🎉 全部测试通过！")
    else:
        print(f"\n  ⚠️  {failed} 项测试失败，请检查错误输出")
    
    return failed == 0


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
