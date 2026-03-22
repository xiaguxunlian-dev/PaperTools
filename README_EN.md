# PaperTools — Scientific Literature & Evidence Assistant

A comprehensive literature research toolkit: multi-source search, evidence quality assessment, meta-analysis, and knowledge graph construction — **zero API keys required to start**.

**GitHub**: https://github.com/xiaguxunlian-dev/PaperTools

---

## Features

| Module | Command | Description |
|--------|---------|-------------|
| 🔍 **Search** | `search` | Concurrent search across PubMed / arXiv / Semantic Scholar / OpenAlex / CrossRef |
| 📊 **Assessment** | `assess` | RoB 2 / ROBINS-I / GRADE / JBI standardized quality assessment |
| 📋 **PICO Extraction** | `pico` | Auto-extract Population / Intervention / Comparison / Outcome from text |
| 📝 **Evidence Table** | `table` | Generate Markdown / CSV / JSON evidence summary tables |
| 🌲 **PRISMA Flowchart** | `prisma` | Generate PRISMA systematic review flowchart data |
| 📖 **Review Writer** | `review` | IMRAD-format review article draft generation |
| 📚 **References** | `refs` | BibTeX / Vancouver / RIS multi-format citation export |
| 🔬 **Meta-Analysis** | `meta` | Effect size extraction + heterogeneity calculation + forest plot |
| 🌲 **Forest Plot** | `forest` | ASCII / Plotly / RevMan / Stata forest plots |
| 🕸️ **Knowledge Graph** | `kg-build` | Build KG from local files or papers, export to Neo4j / JSON / NetworkX |
| 📈 **Research Trends** | `kg-trends` | Entity timelines + hotspot analysis + gap discovery |
| ⚙️ **Configuration** | `config` | API key storage and management |

---

## Quick Install

### Option 1: One-Click Setup (Recommended)

```powershell
# 1. Install Python 3.12+
winget install Python.Python.3.12
# Or download from https://python.org (check "Add to PATH" during install)

# 2. Clone the repo
git clone https://github.com/xiaguxunlian-dev/PaperTools.git
cd PaperTools

# 3. Install dependencies
pip install -r requirements.txt

# 4. Verify
python scripts/paper_tools.py --help
```

### Option 2: Portable (No Install Required)

```powershell
# Python is all you need — run directly
python scripts/paper_tools.py search "CRISPR cancer" --database pubmed --limit 3
```

---

## Tutorial

### 1. Literature Search

```powershell
# PubMed (no API key needed)
python scripts/paper_tools.py search "CRISPR cancer" --database pubmed --limit 5

# arXiv
python scripts/paper_tools.py search "machine learning healthcare" --database arxiv --limit 5

# Multiple databases at once
python scripts/paper_tools.py search "PD-1 immunotherapy" --database pubmed,semantic --limit 3

# JSON output (for programmatic use)
python scripts/paper_tools.py search "metformin diabetes" --database pubmed --json
```

### 2. Evidence Quality Assessment

```powershell
# GRADE assessment (keyword-based auto-analysis)
python scripts/paper_tools.py assess --tool grade --query "Aspirin cardiovascular prevention"

# RoB 2 for RCT bias risk
python scripts/paper_tools.py assess --tool rob2 --papers paper1.txt paper2.txt

# JBI checklist
python scripts/paper_tools.py assess --tool jbi --papers paper.txt
```

### 3. PICO Framework Extraction

```powershell
python scripts/paper_tools.py pico --text "Aspirin for cardiovascular disease prevention in adults with diabetes mellitus"
```

### 4. Meta-Analysis

```powershell
# Load study data from JSON
python scripts/paper_tools.py meta --studies studies.json --model random --output result.json

# Extract effect sizes from paper text
python scripts/paper_tools.py meta --extract paper_abstract.txt --model random
```

**studies.json format**:
```json
[
  {
    "name": "Smith 2020",
    "type": "OR",
    "effect": 0.65,
    "ci_lower": 0.48,
    "ci_upper": 0.88,
    "year": 2020
  },
  {
    "name": "Johnson 2021",
    "type": "OR",
    "effect": 0.72,
    "ci_lower": 0.55,
    "ci_upper": 0.95,
    "year": 2021
  }
]
```

### 5. Forest Plot

```powershell
# ASCII forest plot (zero dependencies)
python scripts/paper_tools.py forest --format ascii

# JSON format (for programmatic use)
python scripts/paper_tools.py forest --format json --output forest.json

# Interactive HTML with Plotly
python scripts/paper_tools.py forest --format plotly --output forest.html
```

### 6. Knowledge Graph Construction

```powershell
# Build KG from local text files
python scripts/paper_tools.py kg-build --texts ./test_corpus --format json

# Build from PubMed search results
python scripts/paper_tools.py search "TP53 cancer" --database pubmed --limit 20 --json > papers.json
python scripts/paper_tools.py kg-build --papers papers.json --format neo4j --output kg.cypher

# Research trend analysis
python scripts/paper_tools.py kg-trends --kg kg.json --output trends.json
```

### 7. Review Article Writing

```powershell
# Generate IMRAD-format review draft
python scripts/paper_tools.py review --topic "CRISPR gene editing cancer therapy" --output review.md

# Specify sections
python scripts/paper_tools.py review --topic "Immunotherapy melanoma" \
  --sections background,methods,results,discussion
```

---

## API Key Configuration (Optional)

| Database | Sign Up | Use Case |
|----------|---------|----------|
| PubMed (NCBI) | https://ncbi.nlm.nih.gov/account | Higher search limits |
| Semantic Scholar | https://api.semanticscholar.org | Citation data |
| OpenAlex | https://dev.openalex.org | Knowledge graph data |
| CrossRef | https://crossref.org | Metadata |

```powershell
# Set API keys
python scripts/paper_tools.py config --set-key pubmed=YOUR_KEY
python scripts/paper_tools.py config --set-key semantic=YOUR_KEY

# List configured keys
python scripts/paper_tools.py config --list-keys
```

---

## Project Structure

```
PaperTools/
├── scripts/
│   ├── paper_tools.py       # Main CLI entry point
│   ├── config.py            # Configuration management
│   ├── search/              # Multi-source search adapters
│   │   ├── federated.py    # Federated search engine
│   │   ├── pubmed.py      # PubMed / Europe PMC
│   │   ├── arxiv.py       # arXiv
│   │   ├── semantic.py     # Semantic Scholar
│   │   ├── openalex.py   # OpenAlex
│   │   ├── crossref.py   # CrossRef
│   │   └── bgpt.py       # BGPT medical database
│   ├── assess/             # Quality assessment tools
│   │   ├── rob2.py       # RoB 2 (Cochrane)
│   │   ├── robins.py      # ROBINS-I
│   │   ├── grade.py       # GRADE
│   │   └── jbi.py        # JBI checklist
│   ├── synthesize/           # Evidence synthesis
│   │   ├── pico.py       # PICO framework
│   │   ├── evidence_table.py # Evidence table
│   │   └── prisma.py    # PRISMA flowchart
│   ├── write/              # Writing assistance
│   │   ├── imrad.py     # IMRAD review
│   │   └── references.py # Citation formatter
│   ├── meta/              # Meta-analysis
│   │   ├── effect_size.py # Effect size extraction
│   │   ├── heterogeneity.py # Heterogeneity statistics
│   │   ├── forest_plot.py # Forest plot
│   │   └── analyzer.py   # Meta-analysis pipeline
│   └── kg/               # Knowledge graph
│       ├── extractor.py     # Entity/relation extraction
│       └── builder.py      # KG builder + trend analysis
├── SKILL.md              # OpenClaw Skill definition
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

---

## Dependencies

| Package | Purpose |
|---------|---------|
| `requests` | HTTP requests |
| `aiohttp` | Async concurrent search |
| `feedparser` | PubMed XML parsing |
| `matplotlib` | Forest plot visualization (optional) |
| `networkx` | Graph network analysis (optional) |

> **Zero-dependency mode**: All core modules are fully standalone. Search and assessment work with Python 3.10+ alone — no pip install needed.

---

## Troubleshooting

**Q: PubMed returns 0 results?**
A: Check internet access to `https://eutils.ncbi.nlm.nih.gov`. The API is free and no VPN is needed.

**Q: SSL errors on corporate network?**
A: Try:
```powershell
set SSL_CERT_FILE=C:\Python312\Lib\site-packages\certifi\cacert.pem
python scripts/paper_tools.py search "query" --database pubmed
```

**Q: arXiv times out?**
A: arXiv now requires HTTPS. Ensure network can access `https://export.arxiv.org`.

**Q: How to batch-process multiple papers?**
A: Save papers as `.txt` files in a directory:
```powershell
python scripts/paper_tools.py kg-build --texts ./papers/ --format json
```

---

## License

MIT License

Star the repo if this tool helps your research!
