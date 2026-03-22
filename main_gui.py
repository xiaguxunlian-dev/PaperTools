#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PaperTools — 一键运行 GUI 启动器
双击 exe 弹出菜单，选择功能，填写参数，即刻执行。
"""
import sys
import io
import os

# ── 路径修正：exe 内嵌资源解压后路径 ──────────────────────────────
if getattr(sys, 'frozen', False):
    # 打包后，_MEIPASS 为临时解压目录
    _BASE = sys._MEIPASS
else:
    _BASE = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, _BASE)

# ── 强制 UTF-8 输出（Windows 终端兼容）────────────────────────────
if sys.stdout and hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr and hasattr(sys.stderr, 'buffer'):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import subprocess
import json
from pathlib import Path
import queue


# ─────────────────────────────────────────────
#   颜色 & 字体配置
# ─────────────────────────────────────────────
BG = "#0f111a"
FG = "#e8eaf6"
ACCENT = "#7c4dff"
ACCENT2 = "#00bcd4"
SUCCESS = "#69f0ae"
WARN = "#ffeb3b"
ERR = "#ff5252"
CARD = "#1a1d2e"
BTN_BG = "#311b92"

FONT_MONO = ("Consolas", 10)
FONT_BOLD = ("Segoe UI", 11, "bold")
FONT_NORMAL = ("Segoe UI", 10)
FONT_TITLE = ("Segoe UI", 16, "bold")


# ─────────────────────────────────────────────
#   功能菜单定义
# ─────────────────────────────────────────────
FEATURES = [
    {
        "label": "📚  文献检索",
        "desc": "从 arXiv / PubMed / Semantic Scholar 等多数据源检索论文",
        "cmd": "search",
        "params": [
            {"key": "query",    "label": "检索词 *",        "type": "entry",  "required": True,  "flag": ""},
            {"key": "database", "label": "数据库",          "type": "combo",  "required": False, "flag": "--database",
             "values": ["arxiv", "pubmed", "semantic", "crossref", "openalex", "arxiv,pubmed", "pubmed,semantic,arxiv"]},
            {"key": "limit",    "label": "每库结果数",      "type": "spin",   "required": False, "flag": "--limit",
             "from_": 1, "to": 50, "default": 5},
            {"key": "json_out", "label": "同时输出 JSON",   "type": "check",  "required": False, "flag": "--json"},
        ]
    },
    {
        "label": "🔬  质量评估",
        "desc": "用 GRADE / RoB2 / ROBINS-I / JBI 量表评估研究质量",
        "cmd": "assess",
        "params": [
            {"key": "tool",    "label": "量表 *",    "type": "combo",  "required": True,  "flag": "--tool",
             "values": ["grade", "rob2", "robins", "jbi"]},
            {"key": "query",   "label": "研究问题",  "type": "entry",  "required": False, "flag": "--query"},
            {"key": "context", "label": "背景描述",  "type": "entry",  "required": False, "flag": "--context"},
        ]
    },
    {
        "label": "🧩  PICO 解析",
        "desc": "从文本中自动提取 P/I/C/O 四要素",
        "cmd": "pico",
        "params": [
            {"key": "text", "label": "文本 *", "type": "text", "required": True, "flag": "--text"},
        ]
    },
    {
        "label": "📊  证据表格",
        "desc": "自动生成文献证据汇总表（Markdown / CSV / JSON）",
        "cmd": "table",
        "params": [
            {"key": "query",  "label": "检索词 *",  "type": "entry", "required": True,  "flag": "--query"},
            {"key": "format", "label": "格式",      "type": "combo", "required": False, "flag": "--format",
             "values": ["markdown", "csv", "json"]},
            {"key": "limit",  "label": "文献数",    "type": "spin",  "required": False, "flag": "--limit",
             "from_": 1, "to": 100, "default": 20},
        ]
    },
    {
        "label": "🌊  PRISMA 流程图",
        "desc": "生成系统综述 PRISMA 流程图数据",
        "cmd": "prisma",
        "params": [
            {"key": "query", "label": "综述检索词 *", "type": "entry", "required": True, "flag": "--query"},
        ]
    },
    {
        "label": "✍️  综述草稿",
        "desc": "基于检索结果自动生成 IMRAD 结构综述草稿",
        "cmd": "review",
        "params": [
            {"key": "topic",    "label": "综述主题 *", "type": "entry", "required": True,  "flag": "--topic"},
            {"key": "sections", "label": "章节（逗号分隔）", "type": "entry", "required": False, "flag": "--sections"},
            {"key": "output",   "label": "保存到文件（可选）", "type": "entry", "required": False, "flag": "--output"},
        ]
    },
    {
        "label": "📈  Meta 分析",
        "desc": "对多项研究进行效应量合并、异质性检验",
        "cmd": "meta",
        "params": [
            {"key": "studies", "label": "研究数据 JSON 文件", "type": "entry", "required": False, "flag": "--studies"},
            {"key": "extract", "label": "从文本提取（txt 路径）", "type": "entry", "required": False, "flag": "--extract"},
            {"key": "model",   "label": "效应模型",  "type": "combo", "required": False, "flag": "--model",
             "values": ["random", "fixed"]},
            {"key": "output",  "label": "保存 JSON（可选）", "type": "entry", "required": False, "flag": "--output"},
        ]
    },
    {
        "label": "🌲  森林图",
        "desc": "生成 ASCII / JSON / Plotly 格式森林图",
        "cmd": "forest",
        "params": [
            {"key": "data",   "label": "数据 JSON 文件（空=示例）", "type": "entry", "required": False, "flag": "--data"},
            {"key": "type",   "label": "效应量类型", "type": "combo", "required": False, "flag": "--type",
             "values": ["RR", "OR", "HR", "MD", "SMD"]},
            {"key": "format", "label": "输出格式",   "type": "combo", "required": False, "flag": "--format",
             "values": ["ascii", "json", "plotly", "revman", "stata"]},
        ]
    },
    {
        "label": "🕸️  知识图谱",
        "desc": "从论文集合中构建实体关系知识图谱",
        "cmd": "kg-build",
        "params": [
            {"key": "papers", "label": "论文 JSON 文件",  "type": "entry", "required": False, "flag": "--papers"},
            {"key": "texts",  "label": "文本目录（.txt）","type": "entry", "required": False, "flag": "--texts"},
            {"key": "format", "label": "输出格式",        "type": "combo", "required": False, "flag": "--format",
             "values": ["json", "neo4j", "networkx"]},
            {"key": "output", "label": "保存文件（可选）","type": "entry", "required": False, "flag": "--output"},
        ]
    },
    {
        "label": "🔑  API Key 管理",
        "desc": "设置 / 查看各数据库的 API Key",
        "cmd": "config",
        "params": [
            {"key": "set_key",   "label": "设置 Key（name=value）", "type": "entry", "required": False, "flag": "--set-key"},
            {"key": "list_keys", "label": "列出所有 Key",          "type": "check", "required": False, "flag": "--list-keys"},
        ]
    },
]


def build_cmd(feature, values):
    """根据用户输入构建命令参数列表"""
    args = ["research", feature["cmd"]]
    for p in feature["params"]:
        v = values.get(p["key"])
        if not v:
            continue
        flag = p["flag"]
        ptype = p["type"]
        if ptype == "check":
            if v.get():
                args.append(flag)
        elif ptype == "spin":
            val = str(v.get())
            if val and val != "0":
                args += [flag, val]
        elif ptype == "text":
            val = v.get("1.0", "end").strip()
            if val:
                if flag:
                    args += [flag, val]
                else:
                    args.append(val)
        else:
            val = v.get().strip()
            if val:
                if flag:
                    args += [flag, val]
                else:
                    args.append(val)
    return args


# ─────────────────────────────────────────────
#   主窗口
# ─────────────────────────────────────────────
class PaperToolsApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PaperTools — 科研助手")
        self.root.geometry("1100x720")
        self.root.minsize(900, 600)
        self.root.configure(bg=BG)
        self.q = queue.Queue()
        self._build_ui()
        self._poll_queue()

    def _build_ui(self):
        # ── 顶部标题栏 ─────────────────────────────
        header = tk.Frame(self.root, bg=CARD, pady=12)
        header.pack(fill="x")
        tk.Label(header, text="🔬 PaperTools", font=FONT_TITLE,
                 bg=CARD, fg=ACCENT).pack(side="left", padx=20)
        tk.Label(header, text="科学文献 & 循证医学研究套件",
                 font=FONT_NORMAL, bg=CARD, fg=FG).pack(side="left", padx=4)

        # ── 主体布局 ──────────────────────────────
        body = tk.PanedWindow(self.root, orient="horizontal",
                              bg=BG, sashrelief="flat", sashwidth=2)
        body.pack(fill="both", expand=True, padx=0, pady=0)

        # 左侧：功能列表
        left = tk.Frame(body, bg=CARD, width=220)
        body.add(left, minsize=180)
        tk.Label(left, text="功能选择", font=FONT_BOLD,
                 bg=CARD, fg=ACCENT2, pady=8).pack(fill="x", padx=12)
        ttk.Separator(left, orient="horizontal").pack(fill="x", padx=8)

        self.selected_feature = tk.IntVar(value=0)
        for i, feat in enumerate(FEATURES):
            btn = tk.Radiobutton(
                left, text=feat["label"], variable=self.selected_feature,
                value=i, command=self._on_feature_select,
                bg=CARD, fg=FG, selectcolor=BTN_BG,
                activebackground=BTN_BG, activeforeground=FG,
                font=FONT_NORMAL, anchor="w", padx=10, pady=4,
                indicatoron=False, relief="flat", bd=0,
                overrelief="flat", cursor="hand2"
            )
            btn.pack(fill="x", pady=1, padx=4)

        # 右侧：参数 + 输出
        right = tk.Frame(body, bg=BG)
        body.add(right, minsize=500)

        # 参数区域
        self.param_frame = tk.LabelFrame(right, text=" 参数配置 ",
            font=FONT_BOLD, bg=BG, fg=ACCENT2,
            relief="groove", bd=1)
        self.param_frame.pack(fill="x", padx=16, pady=(12, 6))

        self.desc_var = tk.StringVar()
        tk.Label(right, textvariable=self.desc_var,
                 font=FONT_NORMAL, bg=BG, fg=FG, wraplength=700,
                 anchor="w").pack(fill="x", padx=18, pady=(0, 4))

        # 执行按钮
        btn_row = tk.Frame(right, bg=BG)
        btn_row.pack(fill="x", padx=16, pady=4)
        self.run_btn = tk.Button(
            btn_row, text="▶  执行", font=FONT_BOLD,
            bg=ACCENT, fg="white", activebackground="#9c6bff",
            relief="flat", bd=0, padx=20, pady=6,
            cursor="hand2", command=self._run
        )
        self.run_btn.pack(side="left")
        tk.Button(
            btn_row, text="🗑  清空输出", font=FONT_NORMAL,
            bg=CARD, fg=FG, activebackground=BTN_BG,
            relief="flat", bd=0, padx=14, pady=6,
            cursor="hand2", command=self._clear_output
        ).pack(side="left", padx=8)

        self.status_var = tk.StringVar(value="就绪")
        tk.Label(btn_row, textvariable=self.status_var,
                 font=FONT_NORMAL, bg=BG, fg=SUCCESS).pack(side="right", padx=8)

        # 输出区域
        out_frame = tk.LabelFrame(right, text=" 输出 ",
            font=FONT_BOLD, bg=BG, fg=ACCENT2, relief="groove", bd=1)
        out_frame.pack(fill="both", expand=True, padx=16, pady=(0, 12))

        self.output = scrolledtext.ScrolledText(
            out_frame, font=FONT_MONO, bg="#0a0c16", fg=FG,
            insertbackground=FG, relief="flat", bd=0,
            wrap="word", state="disabled"
        )
        self.output.pack(fill="both", expand=True, padx=4, pady=4)
        self.output.tag_config("ok",  foreground=SUCCESS)
        self.output.tag_config("err", foreground=ERR)
        self.output.tag_config("hdr", foreground=ACCENT2)

        # 渲染第一个功能
        self._on_feature_select()

    # ─── 渲染参数面板 ─────────────────────────────
    def _on_feature_select(self):
        idx = self.selected_feature.get()
        feat = FEATURES[idx]
        self.desc_var.set(feat["desc"])

        for w in self.param_frame.winfo_children():
            w.destroy()
        self._param_vars = {}

        for row, p in enumerate(feat["params"]):
            tk.Label(self.param_frame, text=p["label"],
                     font=FONT_NORMAL, bg=BG, fg=FG,
                     anchor="e", width=22).grid(
                row=row, column=0, sticky="e", padx=8, pady=5)

            if p["type"] == "entry":
                var = tk.StringVar()
                tk.Entry(self.param_frame, textvariable=var,
                         font=FONT_MONO, bg=CARD, fg=FG,
                         insertbackground=FG, relief="flat",
                         width=50).grid(row=row, column=1, sticky="w", padx=4)
                self._param_vars[p["key"]] = var

            elif p["type"] == "combo":
                var = tk.StringVar(value=p["values"][0])
                cb = ttk.Combobox(self.param_frame, textvariable=var,
                                  values=p["values"], width=30,
                                  font=FONT_NORMAL, state="readonly")
                cb.grid(row=row, column=1, sticky="w", padx=4)
                self._param_vars[p["key"]] = var

            elif p["type"] == "spin":
                var = tk.IntVar(value=p.get("default", p.get("from_", 1)))
                tk.Spinbox(self.param_frame, from_=p.get("from_", 1),
                           to=p.get("to", 100), textvariable=var,
                           width=8, font=FONT_NORMAL,
                           bg=CARD, fg=FG, relief="flat").grid(
                    row=row, column=1, sticky="w", padx=4)
                self._param_vars[p["key"]] = var

            elif p["type"] == "check":
                var = tk.BooleanVar(value=False)
                tk.Checkbutton(self.param_frame, variable=var,
                               bg=BG, fg=FG, activebackground=BG,
                               selectcolor=BTN_BG).grid(
                    row=row, column=1, sticky="w", padx=4)
                self._param_vars[p["key"]] = var

            elif p["type"] == "text":
                frame = tk.Frame(self.param_frame, bg=BG)
                frame.grid(row=row, column=1, sticky="w", padx=4)
                t = tk.Text(frame, font=FONT_MONO, bg=CARD, fg=FG,
                            insertbackground=FG, relief="flat",
                            width=50, height=4)
                t.pack()
                self._param_vars[p["key"]] = t

        self.param_frame.columnconfigure(1, weight=1)

    # ─── 执行 ──────────────────────────────────
    def _run(self):
        idx = self.selected_feature.get()
        feat = FEATURES[idx]
        cmd_args = build_cmd(feat, self._param_vars)

        # 检查必填项
        for p in feat["params"]:
            if p.get("required"):
                v = self._param_vars.get(p["key"])
                if v is None:
                    continue
                if p["type"] == "text":
                    val = v.get("1.0", "end").strip()
                else:
                    val = str(v.get()).strip()
                if not val:
                    messagebox.showwarning("缺少参数", f"请填写「{p['label']}」")
                    return

        self.run_btn.config(state="disabled")
        self.status_var.set("⏳ 运行中…")
        self._append_output(f"\n{'─'*60}\n▶  {' '.join(cmd_args)}\n{'─'*60}\n", tag="hdr")

        # 在子线程中执行，避免 UI 卡死
        threading.Thread(target=self._exec_thread, args=(cmd_args,), daemon=True).start()

    def _exec_thread(self, cmd_args):
        """子线程中运行命令，通过 queue 传回结果"""
        try:
            if getattr(sys, 'frozen', False):
                # 打包后：找到内嵌的 paper_tools.py 并用 Python 解释器执行
                script = os.path.join(_BASE, "scripts", "paper_tools.py")
                full_cmd = [sys.executable, script] + cmd_args[1:]
            else:
                script = os.path.join(_BASE, "scripts", "paper_tools.py")
                full_cmd = [sys.executable, script] + cmd_args[1:]

            proc = subprocess.Popen(
                full_cmd,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding="utf-8", errors="replace",
                env={**os.environ, "PYTHONPATH": _BASE,
                     "PYTHONIOENCODING": "utf-8"}
            )
            for line in proc.stdout:
                self.q.put(("line", line))
            proc.wait()
            self.q.put(("done", proc.returncode))
        except Exception as e:
            self.q.put(("err", str(e)))

    def _poll_queue(self):
        try:
            while True:
                msg = self.q.get_nowait()
                if msg[0] == "line":
                    self._append_output(msg[1])
                elif msg[0] == "done":
                    rc = msg[1]
                    if rc == 0:
                        self._append_output("\n✅ 完成\n", tag="ok")
                        self.status_var.set("✅ 完成")
                    else:
                        self._append_output(f"\n⚠️ 退出码 {rc}\n", tag="err")
                        self.status_var.set(f"⚠️ 退出码 {rc}")
                    self.run_btn.config(state="normal")
                elif msg[0] == "err":
                    self._append_output(f"\n❌ 错误：{msg[1]}\n", tag="err")
                    self.status_var.set("❌ 出错")
                    self.run_btn.config(state="normal")
        except queue.Empty:
            pass
        self.root.after(80, self._poll_queue)

    # ─── 输出辅助 ─────────────────────────────
    def _append_output(self, text, tag=None):
        self.output.config(state="normal")
        if tag:
            self.output.insert("end", text, tag)
        else:
            self.output.insert("end", text)
        self.output.see("end")
        self.output.config(state="disabled")

    def _clear_output(self):
        self.output.config(state="normal")
        self.output.delete("1.0", "end")
        self.output.config(state="disabled")
        self.status_var.set("就绪")


# ─────────────────────────────────────────────
def main():
    root = tk.Tk()
    app = PaperToolsApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
