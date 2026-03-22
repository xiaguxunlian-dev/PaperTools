#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PaperTools — Modern GUI Launcher v2.0
现代化界面设计，支持结果可视化与一键流转
"""
import sys
import io
import os
import json
import threading
import queue
import subprocess
from pathlib import Path
from datetime import datetime

# ── 路径修正 ─────────────────────────────────────────────────────
if getattr(sys, 'frozen', False):
    _BASE = sys._MEIPASS
else:
    _BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _BASE)

# ── 强制 UTF-8 ────────────────────────────────────────────────────
if sys.stdout and hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr and hasattr(sys.stderr, 'buffer'):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# ── 现代配色方案 (Dark Glassmorphism) ─────────────────────────────
COLORS = {
    'bg': '#0a0e17',
    'bg_secondary': '#111827',
    'bg_card': '#1f2937',
    'bg_hover': '#374151',
    'accent': '#6366f1',
    'accent_hover': '#818cf8',
    'accent_secondary': '#06b6d4',
    'text': '#f9fafb',
    'text_secondary': '#9ca3af',
    'success': '#10b981',
    'warning': '#f59e0b',
    'error': '#ef4444',
    'border': '#374151',
}

# ── 字体配置 ──────────────────────────────────────────────────────
FONTS = {
    'title': ('Segoe UI', 20, 'bold'),
    'subtitle': ('Segoe UI', 12),
    'body': ('Segoe UI', 10),
    'mono': ('Consolas', 9),
    'small': ('Segoe UI', 9),
}

# ── 功能定义 ──────────────────────────────────────────────────────
FEATURES = {
    'search': {
        'label': '🔍 文献检索',
        'desc': '从多个学术数据库检索文献',
        'icon': '🔍',
    },
    'table': {
        'label': '📊 证据表格',
        'desc': '生成标准化的证据汇总表',
        'icon': '📊',
    },
    'review': {
        'label': '✍️ 综述写作',
        'desc': '自动生成 IMRAD 格式综述',
        'icon': '✍️',
    },
    'pico': {
        'label': '🧩 PICO 解析',
        'desc': '提取临床问题的 PICO 要素',
        'icon': '🧩',
    },
    'assess': {
        'label': '🔬 质量评估',
        'desc': 'RoB2 / GRADE 等质量评价',
        'icon': '🔬',
    },
    'meta': {
        'label': '📈 Meta 分析',
        'desc': '效应量合并与异质性检验',
        'icon': '📈',
    },
    'forest': {
        'label': '🌲 森林图',
        'desc': '可视化展示 Meta 分析结果',
        'icon': '🌲',
    },
    'prisma': {
        'label': '🌊 PRISMA',
        'desc': '生成系统综述流程图',
        'icon': '🌊',
    },
    'kg': {
        'label': '🕸️ 知识图谱',
        'desc': '构建文献知识图谱',
        'icon': '🕸️',
    },
    'config': {
        'label': '⚙️ 设置',
        'desc': 'API Key 等配置管理',
        'icon': '⚙️',
    },
}


class ModernButton(tk.Canvas):
    """圆角按钮组件"""
    def __init__(self, parent, text, command=None, width=120, height=36, 
                 bg=None, fg=None, hover_bg=None, font=None, **kwargs):
        self.bg = bg or COLORS['accent']
        self.fg = fg or COLORS['text']
        self.hover_bg = hover_bg or COLORS['accent_hover']
        self.command = command
        
        super().__init__(parent, width=width, height=height, 
                        bg=parent['bg'], highlightthickness=0, **kwargs)
        
        self.font = font or FONTS['body']
        self.text = text
        self.radius = 8
        
        self.bind('<Enter>', self._on_enter)
        self.bind('<Leave>', self._on_leave)
        self.bind('<Button-1>', self._on_click)
        self.bind('<ButtonRelease-1>', self._on_release)
        
        self._draw(self.bg)
        
    def _draw(self, color):
        self.delete('all')
        # 绘制圆角矩形
        self.create_rounded_rect(0, 0, self.winfo_reqwidth(), self.winfo_reqheight(), 
                                self.radius, fill=color, outline='')
        # 文字
        self.create_text(self.winfo_reqwidth()/2, self.winfo_reqheight()/2,
                        text=self.text, fill=self.fg, font=self.font)
        
    def create_rounded_rect(self, x1, y1, x2, y2, radius, **kwargs):
        points = [
            x1+radius, y1, x2-radius, y1, x2, y1, x2, y1+radius,
            x2, y2-radius, x2, y2, x2-radius, y2, x1+radius, y2,
            x1, y2, x1, y2-radius, x1, y1+radius, x1, y1
        ]
        return self.create_polygon(points, smooth=True, **kwargs)
        
    def _on_enter(self, e):
        self._draw(self.hover_bg)
        self.config(cursor='hand2')
        
    def _on_leave(self, e):
        self._draw(self.bg)
        
    def _on_click(self, e):
        self._draw(self.bg)
        
    def _on_release(self, e):
        self._draw(self.hover_bg)
        if self.command:
            self.command()


class PaperToolsApp:
    def __init__(self, root):
        self.root = root
        self.root.title('PaperTools — 科研助手')
        self.root.geometry('1400x900')
        self.root.minsize(1200, 700)
        self.root.configure(bg=COLORS['bg'])
        
        # 状态管理
        self.current_results = None  # 当前检索结果
        self.selected_papers = []    # 选中的文献
        self.q = queue.Queue()
        
        self._build_ui()
        self._poll_queue()
        
    def _build_ui(self):
        # ── 主布局 ─────────────────────────────────────────────────
        # 左侧导航 | 中间内容 | 右侧结果面板
        
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # 左侧导航栏
        self._build_sidebar()
        
        # 中间主内容区
        self._build_main_content()
        
        # 右侧结果面板
        self._build_result_panel()
        
    def _build_sidebar(self):
        sidebar = tk.Frame(self.root, bg=COLORS['bg_secondary'], width=220)
        sidebar.grid(row=0, column=0, sticky='nsew')
        sidebar.grid_propagate(False)
        
        # Logo
        tk.Label(sidebar, text='🔬 PaperTools', font=FONTS['title'],
                bg=COLORS['bg_secondary'], fg=COLORS['text']).pack(pady=(20, 10), padx=20, anchor='w')
        
        tk.Label(sidebar, text='v2.0', font=FONTS['small'],
                bg=COLORS['bg_secondary'], fg=COLORS['text_secondary']).pack(padx=20, anchor='w')
        
        # 分隔线
        tk.Frame(sidebar, height=1, bg=COLORS['border']).pack(fill='x', padx=15, pady=15)
        
        # 功能按钮
        self.nav_buttons = {}
        for key, info in FEATURES.items():
            btn = self._create_nav_button(sidebar, info['icon'], info['label'], 
                                         lambda k=key: self._switch_view(k))
            btn.pack(fill='x', padx=10, pady=2)
            self.nav_buttons[key] = btn
            
        # 底部状态
        tk.Frame(sidebar, height=1, bg=COLORS['border']).pack(fill='x', padx=15, pady=15)
        self.status_label = tk.Label(sidebar, text='就绪', font=FONTS['small'],
                                    bg=COLORS['bg_secondary'], fg=COLORS['text_secondary'])
        self.status_label.pack(side='bottom', pady=15, padx=20, anchor='w')
        
    def _create_nav_button(self, parent, icon, text, command):
        frame = tk.Frame(parent, bg=COLORS['bg_secondary'], height=40)
        frame.pack_propagate(False)
        
        # 悬停效果
        def on_enter(e):
            frame.config(bg=COLORS['bg_card'])
            for w in frame.winfo_children():
                w.config(bg=COLORS['bg_card'])
                
        def on_leave(e):
            frame.config(bg=COLORS['bg_secondary'])
            for w in frame.winfo_children():
                w.config(bg=COLORS['bg_secondary'])
                
        frame.bind('<Enter>', on_enter)
        frame.bind('<Leave>', on_leave)
        frame.bind('<Button-1>', lambda e: command())
        
        tk.Label(frame, text=f'{icon}  {text}', font=FONTS['body'],
                bg=COLORS['bg_secondary'], fg=COLORS['text']).pack(side='left', padx=15)
        
        # 让所有子元素也触发点击
        for child in frame.winfo_children():
            child.bind('<Button-1>', lambda e: command())
            child.bind('<Enter>', on_enter)
            child.bind('<Leave>', on_leave)
            
        return frame
        
    def _build_main_content(self):
        self.main_frame = tk.Frame(self.root, bg=COLORS['bg'])
        self.main_frame.grid(row=0, column=1, sticky='nsew', padx=20, pady=20)
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.rowconfigure(1, weight=1)
        
        # 标题区
        self.header_frame = tk.Frame(self.main_frame, bg=COLORS['bg'])
        self.header_frame.grid(row=0, column=0, sticky='ew', pady=(0, 20))
        
        self.title_label = tk.Label(self.header_frame, text='🔍 文献检索', 
                                   font=FONTS['title'], bg=COLORS['bg'], fg=COLORS['text'])
        self.title_label.pack(anchor='w')
        
        self.desc_label = tk.Label(self.header_frame, text='从多个学术数据库检索文献',
                                  font=FONTS['subtitle'], bg=COLORS['bg'], fg=COLORS['text_secondary'])
        self.desc_label.pack(anchor='w', pady=(5, 0))
        
        # 内容卡片
        self.content_card = tk.Frame(self.main_frame, bg=COLORS['bg_card'], 
                                    highlightbackground=COLORS['border'], highlightthickness=1)
        self.content_card.grid(row=1, column=0, sticky='nsew')
        self.content_card.columnconfigure(0, weight=1)
        self.content_card.rowconfigure(0, weight=1)
        
        # 动态内容容器
        self.content_container = tk.Frame(self.content_card, bg=COLORS['bg_card'])
        self.content_container.place(relx=0.5, rely=0.5, anchor='center')
        
        # 默认显示检索界面
        self._show_search_view()
        
    def _build_result_panel(self):
        """右侧结果面板 - 显示检索结果表格"""
        self.result_frame = tk.Frame(self.root, bg=COLORS['bg_secondary'], width=450)
        self.result_frame.grid(row=0, column=2, sticky='nsew', padx=(0, 0))
        self.result_frame.grid_propagate(False)
        
        # 结果面板标题
        header = tk.Frame(self.result_frame, bg=COLORS['bg_card'], height=50)
        header.pack(fill='x', padx=0, pady=0)
        header.pack_propagate(False)
        
        tk.Label(header, text='📚 检索结果', font=FONTS['body'],
                bg=COLORS['bg_card'], fg=COLORS['text']).pack(side='left', padx=15, pady=10)
        
        self.result_count_label = tk.Label(header, text='(0)', font=FONTS['small'],
                                          bg=COLORS['bg_card'], fg=COLORS['text_secondary'])
        self.result_count_label.pack(side='left')
        
        # 操作按钮区
        self.action_frame = tk.Frame(self.result_frame, bg=COLORS['bg_secondary'])
        self.action_frame.pack(fill='x', padx=10, pady=10)
        
        # 下游功能按钮（初始禁用）
        self.action_buttons = {}
        actions = [
            ('📊 生成表格', self._gen_table),
            ('✍️ 写综述', self._gen_review),
            ('💾 保存', self._save_results),
        ]
        for text, cmd in actions:
            btn = tk.Button(self.action_frame, text=text, font=FONTS['small'],
                          bg=COLORS['accent'], fg=COLORS['text'], relief='flat',
                          padx=12, pady=5, command=cmd, state='disabled')
            btn.pack(side='left', padx=3)
            self.action_buttons[text] = btn
            
        # 结果表格
        self._build_result_table()
        
        # 日志输出区
        self._build_log_area()
        
    def _build_result_table(self):
        """构建文献结果表格"""
        table_frame = tk.Frame(self.result_frame, bg=COLORS['bg_secondary'])
        table_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # 表头
        headers = ['☑', '标题', '年份', '来源']
        col_widths = [3, 35, 8, 10]
        
        header_frame = tk.Frame(table_frame, bg=COLORS['bg_card'])
        header_frame.pack(fill='x')
        
        for i, (h, w) in enumerate(zip(headers, col_widths)):
            tk.Label(header_frame, text=h, font=FONTS['small'],
                    bg=COLORS['bg_card'], fg=COLORS['text_secondary'], 
                    width=w).pack(side='left', padx=2)
                    
        # 表格内容区（带滚动条）
        scroll_frame = tk.Frame(table_frame, bg=COLORS['bg_secondary'])
        scroll_frame.pack(fill='both', expand=True, pady=5)
        
        self.result_canvas = tk.Canvas(scroll_frame, bg=COLORS['bg_secondary'], 
                                      highlightthickness=0)
        scrollbar = ttk.Scrollbar(scroll_frame, orient='vertical', 
                                 command=self.result_canvas.yview)
        
        self.result_table_inner = tk.Frame(self.result_canvas, bg=COLORS['bg_secondary'])
        
        self.result_canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side='right', fill='y')
        self.result_canvas.pack(side='left', fill='both', expand=True)
        
        self.result_canvas_window = self.result_canvas.create_window(
            (0, 0), window=self.result_table_inner, anchor='nw', width=420)
            
        self.result_table_inner.bind('<Configure>', 
            lambda e: self.result_canvas.configure(scrollregion=self.result_canvas.bbox('all')))
            
        self.result_rows = []  # 保存行引用
        
    def _build_log_area(self):
        """底部日志输出区"""
        log_frame = tk.Frame(self.result_frame, bg=COLORS['bg_secondary'], height=200)
        log_frame.pack(fill='x', side='bottom', padx=10, pady=10)
        log_frame.pack_propagate(False)
        
        tk.Label(log_frame, text='📋 执行日志', font=FONTS['small'],
                bg=COLORS['bg_secondary'], fg=COLORS['text_secondary']).pack(anchor='w', pady=(0, 5))
        
        self.log_text = tk.Text(log_frame, font=FONTS['mono'], bg=COLORS['bg'],
                               fg=COLORS['text'], relief='flat', height=10,
                               wrap='word', state='disabled')
        self.log_text.pack(fill='both', expand=True)
        
        # 颜色标签
        self.log_text.tag_config('success', foreground=COLORS['success'])
        self.log_text.tag_config('error', foreground=COLORS['error'])
        self.log_text.tag_config('warning', foreground=COLORS['warning'])
        self.log_text.tag_config('info', foreground=COLORS['accent_secondary'])
        
    # ── 视图切换 ────────────────────────────────────────────────────
    def _switch_view(self, view_name):
        info = FEATURES[view_name]
        self.title_label.config(text=f"{info['icon']} {info['label']}")
        self.desc_label.config(text=info['desc'])
        
        # 清空内容区
        for w in self.content_container.winfo_children():
            w.destroy()
            
        # 加载对应视图
        if view_name == 'search':
            self._show_search_view()
        elif view_name == 'table':
            self._show_table_view()
        elif view_name == 'review':
            self._show_review_view()
        elif view_name == 'pico':
            self._show_pico_view()
        elif view_name == 'assess':
            self._show_assess_view()
        elif view_name == 'meta':
            self._show_meta_view()
        elif view_name == 'forest':
            self._show_forest_view()
        elif view_name == 'prisma':
            self._show_prisma_view()
        elif view_name == 'kg':
            self._show_kg_view()
        elif view_name == 'config':
            self._show_config_view()
            
    # ── 检索视图 ─────────────────────────────────────────────────────
    def _show_search_view(self):
        frame = tk.Frame(self.content_container, bg=COLORS['bg_card'])
        frame.pack(padx=40, pady=40)
        
        tk.Label(frame, text='检索词', font=FONTS['body'],
                bg=COLORS['bg_card'], fg=COLORS['text']).pack(anchor='w')
        
        self.search_entry = tk.Entry(frame, font=FONTS['body'], width=50,
                                    bg=COLORS['bg'], fg=COLORS['text'],
                                    relief='flat', insertbackground=COLORS['text'])
        self.search_entry.pack(pady=10, ipady=8)
        self.search_entry.insert(0, 'COVID-19 vaccine efficacy')
        
        # 选项行
        opts_frame = tk.Frame(frame, bg=COLORS['bg_card'])
        opts_frame.pack(fill='x', pady=10)
        
        tk.Label(opts_frame, text='数据库', font=FONTS['small'],
                bg=COLORS['bg_card'], fg=COLORS['text_secondary']).pack(side='left')
        
        self.db_var = tk.StringVar(value='pubmed,arxiv,semantic')
        db_combo = ttk.Combobox(opts_frame, textvariable=self.db_var, width=25,
                               values=['pubmed', 'arxiv', 'semantic', 
                                      'pubmed,arxiv', 'pubmed,semantic,arxiv'])
        db_combo.pack(side='left', padx=10)
        
        tk.Label(opts_frame, text='数量', font=FONTS['small'],
                bg=COLORS['bg_card'], fg=COLORS['text_secondary']).pack(side='left', padx=(20, 0))
        
        self.limit_var = tk.IntVar(value=10)
        tk.Spinbox(opts_frame, from_=1, to=50, textvariable=self.limit_var, 
                  width=8).pack(side='left', padx=10)
        
        # 执行按钮
        btn_frame = tk.Frame(frame, bg=COLORS['bg_card'])
        btn_frame.pack(pady=20)
        
        tk.Button(btn_frame, text='🔍 开始检索', font=FONTS['body'],
                 bg=COLORS['accent'], fg=COLORS['text'], relief='flat',
                 padx=30, pady=10, cursor='hand2',
                 command=self._do_search).pack()
        
    def _do_search(self):
        query = self.search_entry.get().strip()
        if not query:
            messagebox.showwarning('提示', '请输入检索词')
            return
            
        self._log(f'🔍 开始检索: {query}', 'info')
        self._set_status('检索中...')
        
        # 禁用按钮防止重复点击
        # 在线程中执行
        threading.Thread(target=self._search_thread, args=(query,), daemon=True).start()
        
    def _search_thread(self, query):
        try:
            script = os.path.join(_BASE, 'scripts', 'paper_tools.py')
            output_file = os.path.join(_BASE, 'temp_results.json')
            
            # 检测是否在 PyInstaller 打包环境中运行
            if getattr(sys, 'frozen', False):
                # 打包环境：使用 python 命令直接运行脚本
                cmd = [
                    'python', script,
                    'search', query,
                    '--database', self.db_var.get(),
                    '--limit', str(self.limit_var.get()),
                    '--output', output_file
                ]
            else:
                # 开发环境：使用当前 Python 解释器
                cmd = [
                    sys.executable, script,
                    'search', query,
                    '--database', self.db_var.get(),
                    '--limit', str(self.limit_var.get()),
                    '--output', output_file
                ]
            
            proc = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding='utf-8', errors='replace',
                env={**os.environ, 'PYTHONPATH': _BASE}
            )
            
            output = []
            for line in proc.stdout:
                output.append(line)
                self.q.put(('log', line))
                
            proc.wait()
            
            if proc.returncode == 0:
                # 加载结果
                self.q.put(('search_done', os.path.join(_BASE, 'temp_results.json')))
            else:
                self.q.put(('error', '检索失败'))
                
        except Exception as e:
            self.q.put(('error', str(e)))
            
    def _load_results_to_table(self, filepath):
        """加载检索结果到表格"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                self.current_results = json.load(f)
                
            papers = self.current_results.get('papers', [])
            self._update_result_table(papers)
            self._set_status(f'检索完成，共 {len(papers)} 篇文献')
            self._log(f'✅ 检索完成，共 {len(papers)} 篇文献', 'success')
            
            # 启用下游功能按钮
            for btn in self.action_buttons.values():
                btn.config(state='normal')
                
        except Exception as e:
            self._log(f'❌ 加载结果失败: {e}', 'error')
            
    def _update_result_table(self, papers):
        """更新结果表格"""
        # 清空现有行
        for row in self.result_rows:
            row.destroy()
        self.result_rows = []
        
        self.result_count_label.config(text=f'({len(papers)})')
        
        for i, paper in enumerate(papers[:50]):  # 最多显示50条
            row_frame = tk.Frame(self.result_table_inner, bg=COLORS['bg_secondary'])
            row_frame.pack(fill='x', pady=1)
            
            # 复选框
            var = tk.BooleanVar(value=True)
            cb = tk.Checkbutton(row_frame, variable=var, bg=COLORS['bg_secondary'],
                               selectcolor=COLORS['accent'])
            cb.pack(side='left', padx=5)
            
            # 标题（截断）
            title = paper.get('title', 'N/A')[:30] + '...' if len(paper.get('title', '')) > 30 else paper.get('title', 'N/A')
            tk.Label(row_frame, text=title, font=FONTS['small'],
                    bg=COLORS['bg_secondary'], fg=COLORS['text'], width=30,
                    anchor='w').pack(side='left', padx=5)
            
            # 年份
            year = str(paper.get('year', 'N/A'))
            tk.Label(row_frame, text=year, font=FONTS['small'],
                    bg=COLORS['bg_secondary'], fg=COLORS['text_secondary'], width=6).pack(side='left')
            
            # 来源
            source = paper.get('source', 'N/A')[:8]
            tk.Label(row_frame, text=source, font=FONTS['small'],
                    bg=COLORS['bg_secondary'], fg=COLORS['accent_secondary'], width=8).pack(side='left')
            
            self.result_rows.append(row_frame)
            
        self.result_canvas.update_idletasks()
        self.result_canvas.configure(scrollregion=self.result_canvas.bbox('all'))
        
    # ── 一键流转功能 ────────────────────────────────────────────────
    def _gen_table(self):
        """基于当前结果生成证据表格"""
        if not self.current_results:
            return
        temp_path = os.path.join(_BASE, 'temp_results.json')
        threading.Thread(target=self._downstream_thread, 
                        args=(['table', '--from', temp_path],), 
                        daemon=True).start()
        
    def _gen_review(self):
        """基于当前结果生成综述"""
        if not self.current_results:
            return
        temp_path = os.path.join(_BASE, 'temp_results.json')
        topic = self.current_results.get('query', 'Research Topic')
        threading.Thread(target=self._downstream_thread,
                        args=(['review', '--from', temp_path, '--topic', topic],),
                        daemon=True).start()
        
    def _save_results(self):
        """保存结果到用户选择的位置"""
        if not self.current_results:
            return
        filepath = filedialog.asksaveasfilename(
            defaultextension='.json',
            filetypes=[('JSON files', '*.json'), ('All files', '*.*')]
        )
        if filepath:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.current_results, f, ensure_ascii=False, indent=2)
            self._log(f'💾 结果已保存到: {filepath}', 'success')
            
    def _downstream_thread(self, args):
        """执行下游功能"""
        try:
            script = os.path.join(_BASE, 'scripts', 'paper_tools.py')
            
            # 检测是否在 PyInstaller 打包环境中运行
            if getattr(sys, 'frozen', False):
                cmd = ['python', script] + args
            else:
                cmd = [sys.executable, script] + args
            
            proc = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding='utf-8'
            )
            
            for line in proc.stdout:
                self.q.put(('log', line))
                
            proc.wait()
            
            if proc.returncode == 0:
                self.q.put(('success', f'{args[0]} 完成'))
            else:
                self.q.put(('error', f'{args[0]} 失败'))
                
        except Exception as e:
            self.q.put(('error', str(e)))
            
    # ── 其他视图（简化实现）─────────────────────────────────────────
    def _show_table_view(self):
        self._show_placeholder('📊 证据表格', '从检索结果生成标准化的证据汇总表\n\n请先在"文献检索"中执行检索')
        
    def _show_review_view(self):
        self._show_placeholder('✍️ 综述写作', '自动生成 IMRAD 格式综述草稿\n\n请先在"文献检索"中执行检索')
        
    def _show_pico_view(self):
        frame = tk.Frame(self.content_container, bg=COLORS['bg_card'])
        frame.pack(padx=40, pady=40)
        
        tk.Label(frame, text='输入文本', font=FONTS['body'],
                bg=COLORS['bg_card'], fg=COLORS['text']).pack(anchor='w')
        
        text = tk.Text(frame, font=FONTS['body'], width=60, height=10,
                      bg=COLORS['bg'], fg=COLORS['text'], relief='flat')
        text.pack(pady=10)
        
        tk.Button(frame, text='🧩 解析 PICO', font=FONTS['body'],
                 bg=COLORS['accent'], fg=COLORS['text'], relief='flat',
                 padx=30, pady=10).pack(pady=10)
        
    def _show_assess_view(self):
        self._show_placeholder('🔬 质量评估', '使用 RoB2、GRADE 等工具评估研究质量')
        
    def _show_meta_view(self):
        self._show_placeholder('📈 Meta 分析', '效应量合并与异质性检验')
        
    def _show_forest_view(self):
        self._show_placeholder('🌲 森林图', '可视化展示 Meta 分析结果')
        
    def _show_prisma_view(self):
        self._show_placeholder('🌊 PRISMA', '生成系统综述流程图数据')
        
    def _show_kg_view(self):
        self._show_placeholder('🕸️ 知识图谱', '构建文献知识图谱')
        
    def _show_config_view(self):
        frame = tk.Frame(self.content_container, bg=COLORS['bg_card'])
        frame.pack(padx=40, pady=40, fill='both', expand=True)
        
        tk.Label(frame, text='API Key 配置', font=FONTS['title'],
                bg=COLORS['bg_card'], fg=COLORS['text']).pack(anchor='w', pady=(0, 20))
        
        services = ['PubMed', 'Semantic Scholar', 'OpenAlex', 'CrossRef']
        for svc in services:
            row = tk.Frame(frame, bg=COLORS['bg_card'])
            row.pack(fill='x', pady=5)
            tk.Label(row, text=svc, font=FONTS['body'], width=20,
                    bg=COLORS['bg_card'], fg=COLORS['text']).pack(side='left')
            tk.Entry(row, font=FONTS['body'], width=40, show='•',
                    bg=COLORS['bg'], fg=COLORS['text'], relief='flat').pack(side='left', padx=10)
            
    def _show_placeholder(self, title, message):
        frame = tk.Frame(self.content_container, bg=COLORS['bg_card'])
        frame.pack(padx=40, pady=40)
        tk.Label(frame, text=title, font=FONTS['title'],
                bg=COLORS['bg_card'], fg=COLORS['text']).pack()
        tk.Label(frame, text=message, font=FONTS['body'],
                bg=COLORS['bg_card'], fg=COLORS['text_secondary']).pack(pady=20)
        
    # ── 辅助方法 ────────────────────────────────────────────────────
    def _log(self, message, tag=''):
        """添加日志"""
        self.log_text.config(state='normal')
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.log_text.insert('end', f'[{timestamp}] {message}\n', tag)
        self.log_text.see('end')
        self.log_text.config(state='disabled')
        
    def _set_status(self, text):
        self.status_label.config(text=text)
        
    def _poll_queue(self):
        """轮询消息队列更新 UI"""
        try:
            while True:
                msg_type, data = self.q.get_nowait()
                
                if msg_type == 'log':
                    self._log(data.strip())
                elif msg_type == 'search_done':
                    self._load_results_to_table(data)
                elif msg_type == 'success':
                    self._log(f'✅ {data}', 'success')
                    self._set_status('就绪')
                elif msg_type == 'error':
                    self._log(f'❌ {data}', 'error')
                    self._set_status('出错')
                    
        except queue.Empty:
            pass
        self.root.after(100, self._poll_queue)


def main():
    root = tk.Tk()
    # 设置 DPI 感知
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass
    app = PaperToolsApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()
