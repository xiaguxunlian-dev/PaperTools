"""
Meta 分析编排器
整合效应量提取 → 异质性计算 → 森林图生成 → 报告输出
"""
import json
from typing import Optional
from dataclasses import asdict

from .effect_size import EffectSizeExtractor, EffectSizeConverter
from .heterogeneity import HeterogeneityCalculator
from .forest_plot import ForestPlotGenerator, ForestPlotData


class MetaAnalyzer:
    """
    Meta 分析流水线
    
    完整流程:
    1. 提取各研究的效应量 (RR/OR/HR/MD/SMD)
    2. 计算异质性统计量 (I², Q, τ²)
    3. 选择效应模型 (固定 / 随机)
    4. 合并效应量
    5. 生成森林图数据
    6. 输出分析报告
    """
    
    def __init__(self):
        self.extractor = EffectSizeExtractor()
        self.converter = EffectSizeConverter()
        self.het_calc = HeterogeneityCalculator()
        self.forest_gen = ForestPlotGenerator()
        self._studies = []      # 处理后的研究数据
        self._effects = []      # 原始效应量对象
    
    def add_study(
        self,
        name: str,
        text: str,
        year: int = None,
        n_total: int = None,
        n_events: int = None,
        group: str = "",
    ) -> 'MetaAnalyzer':
        """
        添加一项研究
        
        Args:
            name: 研究标识（如 "Smith 2023"）
            text: 论文全文或方法+结果部分文本
            year: 发表年份
            n_total: 总样本量
            n_events: 总事件数
            group: 亚组名称
        """
        effects = self.extractor.extract_all(text)
        
        if not effects:
            print(f"⚠️  {name}: 未找到效应量")
            return self
        
        # 取第一个效应量（可改进为选择特定类型的逻辑）
        effect = effects[0]
        
        study = {
            'name': name,
            'year': year,
            'text': text[:500],
            'n_total': n_total,
            'n_events': n_events,
            'group': group,
            'effect_obj': effect,
            'effect_raw': effect.point_estimate,
            'ci_lower': effect.ci_lower,
            'ci_upper': effect.ci_upper,
            'effect_type': effect.type,
            'p_value': effect.p_value,
            'significant': effect.significant,
        }
        
        # log 转换
        if effect.type in ['RR', 'OR', 'HR']:
            study['ln_effect'] = effect.ln_rr or effect.point_estimate
            study['ln_ci_lower'] = effect.ln_ci_lower
            study['ln_ci_upper'] = effect.ln_ci_upper
        else:
            study['ln_effect'] = effect.point_estimate
            study['ln_ci_lower'] = effect.ci_lower
            study['ln_ci_upper'] = effect.ci_upper
        
        # 计算方差
        if study['ln_ci_lower'] and study['ln_ci_upper']:
            se = (study['ln_ci_upper'] - study['ln_ci_lower']) / (2 * 1.96)
            study['variance'] = se ** 2
            study['weight'] = 1 / study['variance'] if study['variance'] > 0 else 1
        
        self._studies.append(study)
        return self
    
    def add_study_direct(
        self,
        name: str,
        effect_type: str,
        effect: float,
        ci_lower: float,
        ci_upper: float,
        year: int = None,
        n_total: int = None,
        n_events: int = None,
        group: str = "",
        p_value: float = None,
    ) -> 'MetaAnalyzer':
        """
        直接输入效应量数据（当无法从文本提取时）
        """
        study = {
            'name': name,
            'year': year,
            'effect_type': effect_type,
            'effect_raw': effect,
            'ci_lower': ci_lower,
            'ci_upper': ci_upper,
            'n_total': n_total,
            'n_events': n_events,
            'group': group,
            'p_value': p_value,
        }
        
        if effect_type in ['RR', 'OR', 'HR']:
            study['ln_effect'] = effect if effect <= 0 else __import__('math').log(effect)
            if ci_lower > 0 and ci_upper > 0:
                study['ln_ci_lower'] = __import__('math').log(ci_lower)
                study['ln_ci_upper'] = __import__('math').log(ci_upper)
        else:
            study['ln_effect'] = effect
            study['ln_ci_lower'] = ci_lower
            study['ln_ci_upper'] = ci_upper
        
        if study.get('ln_ci_lower') and study.get('ln_ci_upper'):
            se = (study['ln_ci_upper'] - study['ln_ci_lower']) / (2 * 1.96)
            study['variance'] = se ** 2
            study['weight'] = 1 / se ** 2 if se > 0 else 1
        
        self._studies.append(study)
        return self
    
    def analyze(
        self,
        model: str = None,
    ) -> dict:
        """
        执行完整的 Meta 分析
        
        Args:
            model: 'fixed' / 'random' / None (自动选择)
        
        Returns:
            完整分析结果字典
        """
        if len(self._studies) < 2:
            return {'error': '需要至少2项研究'}
        
        effects_for_het = [
            {'ln_rr': s['ln_effect'], 'ci_lower': s.get('ln_ci_lower'), 'ci_upper': s.get('ln_ci_upper')}
            for s in self._studies
        ]
        
        # 1. 异质性分析
        het_result = self.het_calc.calculate(effects_for_het)
        
        # 2. 自动选择模型
        if model is None:
            model = 'random' if het_result.p_value < 0.1 or het_result.i_squared > 50 else 'fixed'
        
        # 3. 合并效应量
        weights = [1 / s.get('variance', 1) for s in self._studies]
        sum_w = sum(weights)
        
        ln_pooled = sum(w * s['ln_effect'] for w, s in zip(weights, self._studies)) / sum_w
        
        # 计算 pooled SE 和 CI
        if model == 'fixed':
            pooled_var = 1 / sum_w
        else:
            # 随机效应：D&L 调整
            tau_sq = het_result.tau_squared
            # 调整权重
            adj_weights = [1 / (s.get('variance', 1) + tau_sq) for s in self._studies]
            sum_w_adj = sum(adj_weights)
            ln_pooled = sum(w * s['ln_effect'] for w, s in zip(adj_weights, self._studies)) / sum_w_adj
            pooled_var = 1 / sum_w_adj
        
        pooled_se = __import__('math').sqrt(pooled_var)
        pooled_ci_lower = ln_pooled - 1.96 * pooled_se
        pooled_ci_upper = ln_pooled + 1.96 * pooled_se
        
        # Pooled p-value
        import math
        z = ln_pooled / pooled_se
        pooled_p = 2 * (1 - _normal_cdf(abs(z)))
        
        # 4. 转换回原始尺度
        effect_type = self._studies[0].get('effect_type', 'RR')
        if effect_type in ['RR', 'OR', 'HR']:
            pooled_effect_raw = math.exp(ln_pooled)
            pooled_ci_lower_raw = math.exp(pooled_ci_lower)
            pooled_ci_upper_raw = math.exp(pooled_ci_upper)
        else:
            pooled_effect_raw = ln_pooled
            pooled_ci_lower_raw = pooled_ci_lower
            pooled_ci_upper_raw = pooled_ci_upper
        
        # 5. 标准化权重
        total_variance = sum(1 / s.get('variance', 1) for s in self._studies)
        norm_weights = [1 / s.get('variance', 1) / total_variance * 100 for s in self._studies]
        for s, w in zip(self._studies, norm_weights):
            s['weight_pct'] = w
        
        # 6. 生成森林图数据
        forest_studies = [
            {
                'name': s['name'],
                'year': s['year'],
                'effect': s.get('ln_effect', 0),
                'ci_lower': s.get('ln_ci_lower', 0),
                'ci_upper': s.get('ln_ci_upper', 0),
                'weight': s.get('weight_pct', 0),
                'n_total': s.get('n_total'),
                'n_events': s.get('n_events'),
                'group': s.get('group', ''),
                'effect_raw': s.get('effect_raw'),
                'ci_raw_lower': s.get('ci_lower'),
                'ci_raw_upper': s.get('ci_upper'),
            }
            for s in self._studies
        ]
        
        forest_data = self.forest_gen.generate(
            studies=forest_studies,
            pooled={
                'effect': pooled_effect_raw,
                'ci_lower': pooled_ci_lower_raw,
                'ci_upper': pooled_ci_upper_raw,
                'pvalue': pooled_p,
            },
            heterogeneity={
                'q': het_result.q_statistic,
                'df': het_result.df,
                'p': het_result.p_value,
                'i2': het_result.i_squared,
                'tau2': het_result.tau_squared,
            },
            model=model,
            effect_type=effect_type,
        )
        
        return {
            'n_studies': len(self._studies),
            'model': model,
            'effect_type': effect_type,
            'pooled': {
                'effect': pooled_effect_raw,
                'ci_lower': pooled_ci_lower_raw,
                'ci_upper': pooled_ci_upper_raw,
                'pvalue': pooled_p,
                'significant': pooled_p < 0.05,
            },
            'heterogeneity': {
                'q': round(het_result.q_statistic, 3),
                'df': het_result.df,
                'p': round(het_result.p_value, 4),
                'i2': round(het_result.i_squared, 1),
                'tau2': round(het_result.tau_squared, 4),
                'label': het_result.i2_label,
            },
            'recommendation': het_result.recommendation,
            'studies': [
                {
                    'name': s['name'],
                    'year': s['year'],
                    'effect': round(s.get('effect_raw', 0), 3),
                    'ci': f"[{round(s.get('ci_lower', 0), 3)}, {round(s.get('ci_upper', 0), 3)}]",
                    'weight': round(s.get('weight_pct', 0), 1),
                    'p': s.get('p_value'),
                }
                for s in self._studies
            ],
            'forest_plot': json.loads(forest_data.to_json()),
        }
    
    def report(self, results: dict = None) -> str:
        """生成文字报告"""
        if results is None:
            results = self.analyze()
        
        if 'error' in results:
            return f"❌ {results['error']}"
        
        pooled = results['pooled']
        het = results['heterogeneity']
        effect_type = results['effect_type']
        sig = "✅ 显著" if pooled['significant'] else "❌ 不显著"
        
        lines = [
            "╔══════════════════════════════════════════════════════════════╗",
            "║              🔬 Meta 分析结果报告                           ║",
            "╚══════════════════════════════════════════════════════════════╝",
            "",
            f"📊 分析概况",
            f"   研究数量: {results['n_studies']} 项",
            f"   效应模型: {'随机效应模型' if results['model'] == 'random' else '固定效应模型'}",
            f"   效应类型: {effect_type}",
            "",
            f"📈 合并效应量",
            f"   {effect_type} = {pooled['effect']:.3f} (95% CI: {pooled['ci_lower']:.3f}–{pooled['ci_upper']:.3f})",
            f"   p = {pooled['pvalue']:.4f} — {sig}",
            "",
            f"📐 异质性分析",
            f"   Q = {het['q']:.3f}, df = {het['df']}, p = {het['p']:.4f}",
            f"   I² = {het['i2']}% — {het['label']}",
            f"   τ² = {het['tau2']}",
            "",
            f"   {het['recommendation']}",
            "",
            "📋 各研究详情",
            f"   {'研究':<25} {'年份':>6} {effect_type:>8} {'95% CI':>20} {'权重':>8} {'p值':>8}",
            "   " + "─" * 75,
        ]
        
        for s in results['studies']:
            p_str = f"{s['p']:.4f}" if s['p'] else 'N/R'
            lines.append(
                f"   {s['name']:<25} {str(s['year'] or 'N/A'):>6} "
                f"{s['effect']:>8.3f} {s['ci']:>20} {s['weight']:>7.1f}% {p_str:>8}"
            )
        
        lines.append("")
        
        # 森林图 ASCII
        forest = self.forest_gen.generate(
            studies=[
                {'name': s['name'], 'year': s['year'], 'effect': s['effect'],
                 'ci_lower': float(s['ci'][1:-1].split(',')[0]),
                 'ci_upper': float(s['ci'][1:-1].split(',')[1]),
                 'weight': s['weight'], 'n_total': None, 'n_events': None, 'group': ''}
                for s in results['studies']
            ],
            pooled={'effect': pooled['effect'], 'ci_lower': pooled['ci_lower'],
                    'ci_upper': pooled['ci_upper'], 'pvalue': pooled['pvalue']},
            heterogeneity={'q': het['q'], 'p': het['p'], 'i2': het['i2']},
            model=results['model'],
            effect_type=effect_type,
        )
        lines.append(forest.to_ascii())
        
        return '\n'.join(lines)


def _normal_cdf(z: float) -> float:
    """标准正态分布 CDF"""
    import math
    return 0.5 * (1 + math.erf(abs(z) / math.sqrt(2)))
