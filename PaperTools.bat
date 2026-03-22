@echo off
chcp 65001 >nul 2>&1

:: PaperTools 一键启动器
:: 自动检测Python / 自动安装依赖 / 自动下载源码
:: 双击即可运行，全程无需配置

:: ── 切换到 bat 所在目录，确保模块路径正确 ──────────────
cd /d "%~dp0"

title PaperTools 论文工具

:: ── 检测 Python ───────────────────────────────────────
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo  [错误] 未检测到 Python
    echo.
    echo  请先安装 Python 3.10+：
    echo  https://www.python.org/downloads/
    echo.
    echo  安装时请勾选: Add Python to PATH
    echo.
    pause
    start https://www.python.org/downloads/
    exit /b
)

:: ── 检测依赖 ──────────────────────────────────────────
python -c "import requests,aiohttp,feedparser" 2>nul
if %errorlevel% neq 0 (
    echo  [提示] 正在安装依赖 requests aiohttp feedparser ...
    python -m pip install requests aiohttp feedparser --quiet
    if %errorlevel% neq 0 (
        echo  [错误] 依赖安装失败，请检查网络后重试
        pause
        exit /b
    )
)

:: ── 检测源码 ─────────────────────────────────────────
if not exist "%~dp0scripts\paper_tools.py" (
    echo  [提示] 正在下载 PaperTools 源码...
    echo  (首次运行需要网络连接)
    echo.

    :: 方法1: git clone
    where git >nul 2>&1
    if %errorlevel% equ 0 (
        git clone --depth 1 https://github.com/xiaguxunlian-dev/PaperTools.git "%~dp0temp_pt" 2>nul
        if exist "%~dp0temp_pt" (
            xcopy /E /I /Y "%~dp0temp_pt\scripts" "%~dp0scripts\" 2>nul
            rmdir /S /Q "%~dp0temp_pt" 2>nul
            goto :ready
        )
    )

    :: 方法2: 用 curl 下载 zip
    where curl >nul 2>&1
    if %errorlevel% equ 0 (
        echo  正在从 GitHub 下载...
        curl -L "https://github.com/xiaguxunlian-dev/PaperTools/archive/refs/heads/main.zip" -o "%~dp0PaperTools.zip" 2>nul
        powershell -Command "Expand-Archive -Force '%~dp0PaperTools.zip' '%~dp0temp_pt'" 2>nul
        if exist "%~dp0temp_pt\PaperTools-main\scripts" (
            xcopy /E /I /Y "%~dp0temp_pt\PaperTools-main\scripts" "%~dp0scripts\" 2>nul
            rmdir /S /Q "%~dp0temp_pt" 2>nul
            del "%~dp0PaperTools.zip" 2>nul
            goto :ready
        )
    )

    :: 方法3: PowerShell WebClient
    echo  正在通过 PowerShell 下载...
    powershell -Command "[Net.ServicePointManager]::SecurityProtocol='Tls12'; Invoke-WebRequest -Uri 'https://github.com/xiaguxunlian-dev/PaperTools/archive/refs/heads/main.zip' -OutFile '%~dp0PaperTools.zip'" 2>nul
    if exist "%~dp0PaperTools.zip" (
        powershell -Command "Expand-Archive -Force '%~dp0PaperTools.zip' '%~dp0temp_pt'" 2>nul
        if exist "%~dp0temp_pt\PaperTools-main\scripts" (
            xcopy /E /I /Y "%~dp0temp_pt\PaperTools-main\scripts" "%~dp0scripts\" 2>nul
        )
        rmdir /S /Q "%~dp0temp_pt" 2>nul
        del "%~dp0PaperTools.zip" 2>nul
        if exist "%~dp0scripts\paper_tools.py" goto :ready
    )

    echo.
    echo  [错误] 自动下载失败
    echo.
    echo  请手动操作：
    echo  1. 打开浏览器访问
    echo  https://github.com/xiaguxunlian-dev/PaperTools
    echo  2. 点击 Code ^> Download ZIP
    echo  3. 解压后将 scripts 文件夹放到本文件同一目录
    echo.
    pause
    exit /b
)

:ready
echo  [就绪] PaperTools 论文工具
echo.

:: ── 主菜单 ───────────────────────────────────────────
:menu
cls
echo.
echo  ██████╗   ████████╗  ████████╗  ███████╗   ███████╗   PaperTools
echo  ╚════██╗  ╚════██╔╝  ╚════██╔╝  ╚════██║   ╚════██║   论文工具
echo   █████╔╝    █████╔╝     █████╔╝    █████╔╝     █████╔╝   v1.0
echo   ╚════╝     ╚════╝      ╚════╝     ╚════╝      ╚════╝
echo.
echo  https://github.com/xiaguxunlian-dev/PaperTools
echo.
echo  功能菜单（直接输入数字回车）:
echo.
echo  [1] 文献检索     PubMed / arXiv / Semantic Scholar 多数据库
echo  [2] 质量评估     GRADE / RoB2 / JBI 标准化评估
echo  [3] PICO 提取    自动识别研究四要素
echo  [4] 证据表格     Markdown / CSV 格式
echo  [5] Meta 分析     森林图 + 异质性检验
echo  [6] 知识图谱     实体关系网络构建
echo  [7] 综述写作     IMRAD 格式草稿
echo  [8] 完整工作流   检索^>评估^>Meta^>综述一键完成
echo  [9] 安装/更新依赖
echo  [0] 使用说明
echo  [Q] 退出
echo.
set /p c="请选择 [1-9, 0, Q]: "

if "%c%"=="1" goto :do_search
if "%c%"=="2" goto :do_assess
if "%c%"=="3" goto :do_pico
if "%c%"=="4" goto :do_table
if "%c%"=="5" goto :do_forest
if "%c%"=="6" goto :do_kg
if "%c%"=="7" goto :do_review
if "%c%"=="8" goto :do_workflow
if "%c%"=="9" goto :do_install
if "%c%"=="0" goto :do_help
if /i "%c%"=="Q" goto :end
goto :menu

:: ── 文献检索 ────────────────────────────────────────
:do_search
cls
echo.
echo  [文献检索] PubMed / arXiv / Semantic Scholar / OpenAlex / CrossRef
echo  ───────────────────────────────────────────────────────────────
echo.
set /p q="检索词（必填）: "
if "%q%"=="" (echo  [错误] 检索词不能为空 & timeout /t 2 >nul & goto :menu)
set /p dbs="数据库 [留空=全库, pubmed=仅PubMed, arxiv=仅arXiv]: "
if "%dbs%"=="" set dbs=pubmed,arxiv,semantic
set /p n="返回数量 [留空=10]: "
if "%n%"=="" set n=10
echo.
python "%~dp0scripts\paper_tools.py" search %q% --database %dbs% --limit %n%
echo.
pause
goto :menu

:: ── 质量评估 ─────────────────────────────────────────
:do_assess
cls
echo.
echo  [证据质量评估] GRADE / RoB2 / ROBINS-I / JBI
echo  ───────────────────────────────────────────────────────────────
echo.
echo  [1] GRADE   — 证据质量分级（推荐）
echo  [2] RoB2    — RCT 偏倚风险
echo  [3] ROBINS  — 非随机化研究
echo  [4] JBI     — 批判性评价
echo.
set /p t="选择工具 [1-4]: "
if "%t%"=="" goto :do_assess
if "%t%"=="1" set tool=grade
if "%t%"=="2" set tool=rob2
if "%t%"=="3" set tool=robins
if "%t%"=="4" set tool=jbi
echo.
set /p txt="粘贴研究描述或摘要: "
if "%txt%"=="" (echo  [错误] 文本不能为空 & timeout /t 2 >nul & goto :menu)
echo.
if "%t%"=="1" (
    python "%~dp0scripts\paper_tools.py" assess --tool %tool% --query %txt%
) else (
    python "%~dp0scripts\paper_tools.py" assess --tool %tool% --papers %txt%
)
echo.
pause
goto :menu

:: ── PICO ─────────────────────────────────────────────
:do_pico
cls
echo.
echo  [PICO 框架提取] 自动识别研究四要素
echo  ───────────────────────────────────────────────────────────────
echo.
set /p pt="输入研究标题或摘要: "
if "%pt%"=="" (echo  [错误] 文本不能为空 & timeout /t 2 >nul & goto :menu)
echo.
python "%~dp0scripts\paper_tools.py" pico --text %pt%
echo.
pause
goto :menu

:: ── 证据表格 ─────────────────────────────────────────
:do_table
cls
echo.
echo  [证据表格生成]
echo  ───────────────────────────────────────────────────────────────
echo.
set /p qt="检索词: "
if "%qt%"=="" (echo  [错误] 检索词不能为空 & timeout /t 2 >nul & goto :menu)
echo.
python "%~dp0scripts\paper_tools.py" table --query %qt% --format markdown
echo.
pause
goto :menu

:: ── 森林图 ────────────────────────────────────────────
:do_forest
cls
echo.
echo  [Meta 分析森林图]
echo  ───────────────────────────────────────────────────────────────
echo.
echo  [1] ASCII 预览   （终端直接显示）
echo  [2] Plotly HTML  （浏览器打开交互图，推荐）
echo  [3] JSON 格式    （程序处理）
echo.
set /p ft="选择格式 [1-3]: "
if "%ft%"=="" goto :do_forest
if "%ft%"=="1" (
    python "%~dp0scripts\paper_tools.py" forest --format ascii
)
if "%ft%"=="2" (
    python "%~dp0scripts\paper_tools.py" forest --format plotly --output forest.html
    if exist forest.html start forest.html
)
if "%ft%"=="3" (
    python "%~dp0scripts\paper_tools.py" forest --format json --output forest.json
)
echo.
pause
goto :menu

:: ── 知识图谱 ──────────────────────────────────────────
:do_kg
cls
echo.
echo  [知识图谱构建] 从论文构建实体关系网络
echo  ───────────────────────────────────────────────────────────────
echo.
set /p kq="输入研究主题（将自动检索论文）: "
if "%kq%"=="" (echo  [错误] 主题不能为空 & timeout /t 2 >nul & goto :menu)
echo.
echo  正在检索论文并构建图谱，请稍候...
python "%~dp0scripts\paper_tools.py" search %kq% --database pubmed --limit 15 --json > _p.json 2>nul
python "%~dp0scripts\paper_tools.py" kg-build --papers _p.json --format json > kg_result.json 2>nul
del _p.json 2>nul
echo.
if exist kg_result.json (
    echo  [成功] 图谱已保存到 kg_result.json
) else (
    echo  [失败] 请检查网络连接
)
echo.
pause
goto :menu

:: ── 综述写作 ──────────────────────────────────────────
:do_review
cls
echo.
echo  [综述写作辅助] IMRAD 格式草稿生成
echo  ───────────────────────────────────────────────────────────────
echo.
set /p rt="研究主题: "
if "%rt%"=="" (echo  [错误] 主题不能为空 & timeout /t 2 >nul & goto :menu)
set /p ro="输出文件名（留空=屏幕输出）: "
echo.
if "%ro%"=="" (
    python "%~dp0scripts\paper_tools.py" review --topic %rt%
) else (
    python "%~dp0scripts\paper_tools.py" review --topic %rt% --output "%ro%"
    echo  [成功] 已保存到 %ro%
)
echo.
pause
goto :menu

:: ── 完整工作流 ─────────────────────────────────────────
:do_workflow
cls
echo.
echo  [完整工作流] 检索 ^> 评估 ^> Meta ^> 综述
echo  ───────────────────────────────────────────────────────────────
echo.
set /p wt="输入研究主题: "
if "%wt%"=="" (echo  [错误] 主题不能为空 & timeout /t 2 >nul & goto :menu)
echo.
echo  Step 1/4: 文献检索...
python "%~dp0scripts\paper_tools.py" search %wt% --database pubmed,arxiv --limit 10
echo.
echo  Step 2/4: 森林图...
python "%~dp0scripts\paper_tools.py" forest --format ascii
echo.
echo  Step 3/4: GRADE 评估...
python "%~dp0scripts\paper_tools.py" assess --tool grade --query %wt%
echo.
echo  Step 4/4: 生成综述草稿...
python "%~dp0scripts\paper_tools.py" review --topic %wt% --output "综述_%wt%.md"
echo.
echo  [完成] 综述已保存到 综述_%wt%.md
pause
goto :menu

:: ── 安装依赖 ─────────────────────────────────────────
:do_install
cls
echo.
echo  [安装/更新依赖]
echo  ───────────────────────────────────────────────────────────────
echo.
python -m pip install requests aiohttp feedparser matplotlib networkx --upgrade
echo.
pause
goto :menu

:: ── 使用说明 ─────────────────────────────────────────
:do_help
cls
echo.
echo  PaperTools 论文工具 - 使用说明
echo  ==================================================================
echo.
echo  首次使用:
echo  1. 双击本程序（PaperTools.bat）
echo  2. 若提示安装 Python，请从 python.org 下载
echo  3. 安装时勾选 Add Python to PATH
echo  4. 重新双击本程序即可
echo.
echo  功能说明:
echo  1 - 输入关键词，多数据库并发搜索文献
echo  2 - 粘贴研究描述，自动评估证据质量
echo  3 - 输入论文标题，自动提取 PICO 四要素
echo  4 - 生成规范的文献汇总表格
echo  5 - Meta 分析森林图可视化
echo  6 - 从论文构建知识图谱
echo  7 - 生成 IMRAD 综述草稿
echo  8 - 一键完成全套研究流程
echo.
echo  GitHub: https://github.com/xiaguxunlian-dev/PaperTools
echo.
pause
goto :menu

:end
cls
echo.
echo  感谢使用 PaperTools!
echo  https://github.com/xiaguxunlian-dev/PaperTools
echo.
timeout /t 3 >nul 2>&1
exit /b
