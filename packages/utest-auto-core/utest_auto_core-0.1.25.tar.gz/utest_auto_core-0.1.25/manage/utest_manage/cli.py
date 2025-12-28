# -*- coding: utf-8 -*-
"""
utest-manage CLI 实现（已与根仓库解耦）

子命令：
- init：初始化脚本目录（从模板复制、创建虚拟环境并安装依赖）
- new-case：在 test_cases 下创建新用例
- list-cases：列出所有测试用例及其步骤信息（静态分析，无需执行）
- update-core：更新核心文件（uv.toml、start_test.py等）
- clean：清理构建产物
"""

import argparse
import os
import sys
import shutil
import subprocess
from pathlib import Path
import importlib.metadata
import tempfile
import urllib.request
import zipfile

# 导入用例收集器（支持包安装和直接运行两种方式）
try:
    from .case_collector import collect_test_cases
except ImportError:
    # 如果相对导入失败（直接运行脚本时），尝试绝对导入
    try:
        from utest_manage.case_collector import collect_test_cases
    except ImportError:
        # 如果绝对导入也失败，尝试从当前目录导入（开发环境）
        import sys
        from pathlib import Path
        manage_dir = Path(__file__).parent
        if str(manage_dir) not in sys.path:
            sys.path.insert(0, str(manage_dir))
        from case_collector import collect_test_cases


class CommandLineTool:
    """命令行管理工具主类"""

    def __init__(self):
        self.parser = argparse.ArgumentParser(
            description="UTest 自动化测试框架管理工具",
            epilog="""
使用示例：
  # 查看版本信息
  utest-manage --version

  # 初始化（从远程模板直接解压到目标目录；失败回退本地模板）
  utest-manage init my_test_project
  utest-manage init ./my_test_project --force

  # 在框架目录中创建测试用例
  cd my_test_project
  utest-manage new-case MyTestCase

  # 列出所有测试用例及其步骤信息
  utest-manage list-cases              # 显示详细信息
  utest-manage list-cases --summary    # 仅显示汇总信息
  utest-manage list-cases --json cases.json  # 输出JSON格式

  # 更新核心文件（默认更新全部核心项）
  utest-manage update-core
  # 仅更新部分核心项（多次 --files 或逗号分隔）
  utest-manage update-core --files uv.toml --files start_test
  utest-manage update-core --files "uv.toml,run.sh,internal"
  # 指定目标目录并强制覆盖
  utest-manage update-core /path/to/project --force

  # 清理构建产物
  utest-manage clean
            """,
            formatter_class=argparse.RawDescriptionHelpFormatter
        )

        # 动态获取版本号
        try:
            # 尝试从已安装的包中获取版本号
            version = importlib.metadata.version('utest-auto-manage')
        except importlib.metadata.PackageNotFoundError:
            # 如果包未安装，尝试从 pyproject.toml 读取
            try:
                import tomllib
                pyproject_path = Path(__file__).parent.parent / 'pyproject.toml'
                with open(pyproject_path, 'rb') as f:
                    data = tomllib.load(f)
                version = data['project']['version']
            except (FileNotFoundError, KeyError, ImportError):
                # 如果都失败了，使用默认版本号
                version = '0.1.16'

        # 添加版本参数
        self.parser.add_argument(
            '--version', '-V',
            action='version',
            version=f'%(prog)s {version}',
            help='显示版本信息并退出'
        )
        subparsers = self.parser.add_subparsers(dest="command", help="可用子命令")

        case_parser = subparsers.add_parser(
            "new-case",
            help="创建新的测试用例文件（需在框架目录中执行）",
            description="""在 test_cases 目录下创建完整的测试用例模板文件，包含：
• setup/teardown 前置后置操作示例
• 性能监控、录制、logcat 收集功能
• 多种断言方法使用示例
• 日志记录和截图功能
• 异常处理策略
• 性能数据记录

注意：必须在已初始化的框架目录中执行此命令。""",
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        case_parser.add_argument("name", help="测试用例文件名（不含 .py 扩展名，会自动转换为类名）")
        case_parser.set_defaults(func=self.new_case)


        clean_parser = subparsers.add_parser(
            "clean",
            help="清理构建产物和临时文件（需在框架目录中执行）",
            description="""清理项目中的临时文件和构建产物，包括：
• 构建目录（dist/、build/）
• 测试结果目录（test_result/）
• Python 缓存文件（__pycache__/、*.pyc、*.pyo）
• 日志文件（*.log）
• 压缩包文件（*.zip、*.whl）
• 包信息目录（*.egg-info/）

注意：必须在已初始化的框架目录中执行此命令。""",
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        clean_parser.set_defaults(func=self.clean)

        # list-cases 命令
        list_parser = subparsers.add_parser(
            "list-cases",
            help="列出所有测试用例及其步骤信息（需在框架目录中执行）",
            description="""静态分析test_cases目录下的所有测试用例，提取用例信息和步骤信息，包括：
• 用例名称和描述
• 用例所属文件和类名
• 用例下的所有步骤信息（步骤名称和描述）

支持输出格式：
• 控制台输出（默认）：显示汇总和详细信息
• JSON文件输出：使用 --json 参数指定输出文件路径

注意：必须在已初始化的框架目录中执行此命令。""",
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        list_parser.add_argument(
            "--json",
            help="输出JSON格式到指定文件（例如：--json cases.json）"
        )
        list_parser.add_argument(
            "--summary",
            action="store_true",
            help="仅显示汇总信息，不显示详细步骤"
        )
        list_parser.set_defaults(func=self.list_cases)

        # init 命令
        init_parser = subparsers.add_parser(
            "init",
            help="初始化新的测试框架项目（可在任何目录执行）",
            description="""从模板创建完整的测试框架项目，包括：
• 从远程模板ZIP下载并直接解压到目标目录（仅远程，失败则不生成）
• 复制所有模板文件（配置文件、测试用例、脚本等）
• 自动安装 uv 工具（如果未安装）
• 创建 Python 3.10.12 虚拟环境
• 安装项目依赖
• 提供虚拟环境激活命令

参数说明：
• 目标可以是【路径】或【项目名】
  - 若为相对/绝对路径：将在该路径创建/覆盖项目
  - 若为纯项目名：将在当前目录下创建同名子目录

注意：仅从远程下载模板，如果下载失败则不生成项目。

此命令可在任何目录执行，会在指定目录创建新的框架项目。""",
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        init_parser.add_argument("target", nargs="?", default=".", help="目标路径或项目名（默认：当前目录）。支持相对/绝对路径；若仅为名称，将在当前目录下创建同名项目目录。")
        init_parser.add_argument("--force", action="store_true", help="强制覆盖已存在的文件（默认：检查冲突后退出）")
        init_parser.set_defaults(func=self.init_only_scripts)

        # update-core 命令：更新核心文件
        update_parser = subparsers.add_parser(
            "update-core",
            help="更新当前目录或指定目录的核心文件（支持指定文件或全部）",
            description=(
                "从远程模板更新以下核心文件：\n"
                "- uv.toml\n- update_config.py\n- start_test.py\n- run.sh\n- requirements.txt\n- build.py\n- test_cases/internal/ 目录包\n\n"
                "支持：\n"
                "- 默认更新全部核心项\n"
                "- 使用 --files 选择部分项（可多次传入或用逗号分隔）\n"
                "- 使用 --force 强制覆盖\n\n"
                "注意：仅从远程下载，如果下载失败则不更新。\n\n"
                "示例：\n"
                "  utest-manage update-core\n"
                "  utest-manage update-core --files uv.toml --files start_test\n"
                "  utest-manage update-core --files 'uv.toml,run.sh,internal'\n"
                "  utest-manage update-core /path/to/project --force\n"
            ),
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        update_parser.add_argument("target", nargs="?", default=".", help="目标路径（默认：当前目录）")
        update_parser.add_argument(
            "--files",
            action="append",
            help=(
                "指定需要更新的文件/目录，支持多次传入或逗号分隔。"
                "可用别名：uv.toml|uvtoml, update_config, start_test, run.sh|run_sh, requirements|requirements.txt, build|build.py, internal"
            )
        )
        update_parser.add_argument("--force", action="store_true", help="强制覆盖目标文件/目录")
        update_parser.set_defaults(func=self.update_core)

    # ----------------- 子命令实现 -----------------

    def _check_framework_directory(self) -> bool:
        """检查当前目录是否为有效的框架目录"""
        required_files = ["config.yml", "start_test.py", "requirements.txt", "run.sh", "update_config.py", "uv.toml"]
        required_dirs = ["test_cases"]

        for file in required_files:
            if not Path(file).exists():
                print(f"❌ 当前目录不是有效的框架目录，缺少文件：{file}")
                print("请先使用 'init' 命令初始化框架，或切换到正确的框架目录")
                return False

        for dir_name in required_dirs:
            if not Path(dir_name).exists() or not Path(dir_name).is_dir():
                print(f"❌ 当前目录不是有效的框架目录，缺少目录：{dir_name}")
                print("请先使用 'init' 命令初始化框架，或切换到正确的框架目录")
                return False

        return True

    def init_only_scripts(self, args) -> None:
        """初始化脚本工程：
        1) 从远程模板包下载并解压到目标目录（仅从远程下载，失败则不生成）；
        2) 在目标目录创建虚拟环境：uv venv --python 3.10.12；
        3) 打印平台对应的激活命令；
        4) 使用虚拟环境安装 requirements.txt 依赖。
        """
        target_dir = Path(args.target).resolve()

        # 远程模板ZIP下载地址
        TEMPLATE_ZIP_URL = (
            "https://lab-paas-apk-1254257443.cos.ap-nanjing.myqcloud.com/utestAutoScriptTemp/ubox-script-temp-master.zip"
        )

        def download_and_extract_template(url: str, extract_to: Path) -> bool:
            """下载远程模板并解压到指定目录。

            Args:
                url: 模板ZIP下载链接
                extract_to: 解压目标路径
            Returns:
                bool: 是否成功下载并解压
            """
            try:
                extract_to.mkdir(parents=True, exist_ok=True)
                # 使用临时文件保存ZIP
                with tempfile.TemporaryDirectory() as tmpdir:
                    zip_path = Path(tmpdir) / "template.zip"
                    print(f"正在从远程下载模板: {url}")
                    # 下载ZIP（内置urllib，避免新增依赖）
                    urllib.request.urlretrieve(url, zip_path.as_posix())
                    print("模板下载完成，开始解压...")
                    # 解压ZIP
                    with zipfile.ZipFile(zip_path, 'r') as zf:
                        zf.extractall(extract_to)
                    print(f"模板解压完成: {extract_to}")
                return True
            except Exception as e:
                print(f"❌ 远程模板下载或解压失败：{e}")
                return False

        # 防护：存在关键文件且未 --force 时不覆盖
        if target_dir.exists() and not args.force:
            key_files = [target_dir / "config.yml", target_dir / "start_test.py"]
            if any(p.exists() for p in key_files):
                print(f"目标目录 {target_dir} 已存在，并包含关键文件。使用 --force 覆盖。")
                return

        target_dir.mkdir(parents=True, exist_ok=True)

        # 先清空（在 --force 时）
        if any(target_dir.iterdir()) and args.force:
            for child in list(target_dir.iterdir()):
                try:
                    if child.is_dir():
                        shutil.rmtree(child, ignore_errors=True)
                    else:
                        child.unlink(missing_ok=True)
                except Exception as e:
                    print(f"⚠️ 清理目标目录项失败 {child}: {e}")

        # 从远程下载模板（仅远程，失败则不生成）
        tmp_extract_dir = target_dir / "._tpl_tmp_extract"
        if not download_and_extract_template(TEMPLATE_ZIP_URL, tmp_extract_dir):
            print("❌ 初始化失败：无法从远程下载模板")
            # 清理可能已创建的目标目录
            if target_dir.exists() and not any(target_dir.iterdir()):
                try:
                    target_dir.rmdir()
                except Exception:
                    pass
            return

        # 远程包通常会带一个根目录，尝试探测并将其内容搬运到目标目录
        try:
            # 找到唯一根目录，否则就用当前解压目录
            subdirs = [p for p in tmp_extract_dir.iterdir() if p.is_dir() and p.name != "__MACOSX"]
            copy_root = subdirs[0] if len(subdirs) == 1 else tmp_extract_dir
            for item in copy_root.iterdir():
                if item.name == "__MACOSX":
                    continue
                dst = target_dir / item.name
                if item.is_dir():
                    shutil.copytree(item, dst, dirs_exist_ok=True)
                else:
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(item, dst)
            print("✅ 模板文件已复制到目标目录")
        except Exception as e:
            print(f"❌ 远程模板拷贝失败：{e}")
            return
        finally:
            # 清理临时解压目录
            shutil.rmtree(tmp_extract_dir, ignore_errors=True)

        # 检查并安装 uv
        def check_uv_installed() -> bool:
            """检查 uv 是否已安装"""
            try:
                subprocess.check_call(["uv", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return True
            except (subprocess.CalledProcessError, FileNotFoundError):
                return False

        def install_uv() -> bool:
            """根据操作系统安装 uv"""
            print("检测到未安装 uv，正在自动安装...")

            if os.name == "nt":  # Windows
                print("在 Windows 上安装 uv...")
                try:
                    cmd = [
                        "powershell", "-ExecutionPolicy", "ByPass", "-c",
                        "irm https://astral.sh/uv/install.ps1 | iex"
                    ]
                    subprocess.check_call(cmd)
                    print("✅ uv 安装完成")
                    return True
                except Exception as e:
                    print(f"❌ Windows 上安装 uv 失败：{e}")
                    print(
                        "请手动安装：powershell -ExecutionPolicy ByPass -c \"irm https://astral.sh/uv/install.ps1 | iex\"")
                    return False
            else:  # Linux/macOS
                print("在 Linux/macOS 上安装 uv...")
                try:
                    # 尝试 curl
                    try:
                        cmd = ["curl", "-LsSf", "https://astral.sh/uv/install.sh", "|", "sh"]
                        subprocess.check_call("curl -LsSf https://astral.sh/uv/install.sh | sh", shell=True)
                        print("✅ uv 安装完成（使用 curl）")
                        return True
                    except:
                        # 如果 curl 失败，尝试 wget
                        cmd = ["wget", "-qO-", "https://astral.sh/uv/install.sh", "|", "sh"]
                        subprocess.check_call("wget -qO- https://astral.sh/uv/install.sh | sh", shell=True)
                        print("✅ uv 安装完成（使用 wget）")
                        return True
                except Exception as e:
                    print(f"❌ Linux/macOS 上安装 uv 失败：{e}")
                    print("请手动安装：")
                    print("  curl -LsSf https://astral.sh/uv/install.sh | sh")
                    print("  或")
                    print("  wget -qO- https://astral.sh/uv/install.sh | sh")
                    return False

        # 检查 uv 是否已安装
        if not check_uv_installed():
            if not install_uv():
                print("❌ 无法安装 uv，请手动安装后重试")
                return
        else:
            print("✅ 检测到 uv 已安装")

        # 创建虚拟环境：uv venv --python 3.10.12
        def run(cmd, cwd=None, capture_output=False, shell=False) -> bool:
            """运行外部命令，失败时返回 False。"""
            try:
                if isinstance(cmd, str):
                    print("执行：" + cmd)
                else:
                    print("执行：" + " ".join(cmd))

                if capture_output:
                    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, shell=shell)
                    if result.returncode != 0:
                        print(f"命令失败，返回码：{result.returncode}")
                        if result.stdout:
                            print(f"标准输出：{result.stdout}")
                        if result.stderr:
                            print(f"错误输出：{result.stderr}")
                        return False
                    return True
                else:
                    subprocess.check_call(cmd, cwd=cwd, shell=shell)
                    return True
            except Exception as e:
                print(f"命令失败：{e}")
                return False

        created = run(["uv", "venv", "--python", "3.10.12"], cwd=str(target_dir))
        if not created:
            print("❌ 未能创建虚拟环境，请检查 Python 3.10.12 是否可用")

        # 计算 venv 内 Python 路径（不要求已激活）
        if os.name == "nt":
            venv_python = target_dir / ".venv" / "Scripts" / "python.exe"
            activate_hint = ".\\.venv\\Scripts\\Activate.ps1"
        else:
            venv_python = target_dir / ".venv" / "bin" / "python"
            activate_hint = "source .venv/bin/activate"

        # 安装依赖：激活虚拟环境后使用 uv pip 安装
        req_file = target_dir / "requirements.txt"
        if req_file.exists():
            # 根据操作系统选择激活脚本
            if os.name == "nt":  # Windows
                # 优先尝试使用批处理文件激活（更稳定）
                activate_bat = target_dir / ".venv" / "Scripts" / "activate.bat"
                if activate_bat.exists():
                    # 使用正确的引号转义
                    install_cmd = f"call \"{activate_bat}\" && uv pip install -r requirements.txt"
                    print(f"尝试使用 CMD 激活虚拟环境并安装依赖...")
                    # 直接使用字符串而不是列表，避免引号问题
                    installed = run(f'cmd /c "{install_cmd}"', cwd=str(target_dir), capture_output=True, shell=True)
                else:
                    # 如果批处理文件不存在，尝试 PowerShell（需要设置执行策略）
                    activate_script = target_dir / ".venv" / "Scripts" / "Activate.ps1"
                    if activate_script.exists():
                        # 使用 -ExecutionPolicy Bypass 绕过执行策略限制
                        install_cmd = f"& '{activate_script}'; uv pip install -r requirements.txt"
                        print(f"尝试使用 PowerShell 激活虚拟环境并安装依赖...")
                        installed = run(f'powershell -ExecutionPolicy Bypass -Command "{install_cmd}"',
                                        cwd=str(target_dir), capture_output=True, shell=True)
                    else:
                        print("未找到虚拟环境激活脚本，跳过依赖安装。")
                        installed = False
            else:  # Linux/macOS
                activate_script = target_dir / ".venv" / "bin" / "activate"
                if activate_script.exists():
                    # 在 bash 中激活虚拟环境并安装依赖
                    install_cmd = f"source {activate_script} && uv pip install -r requirements.txt"
                    print(f"尝试使用 bash 激活虚拟环境并安装依赖...")
                    installed = run(f'bash -c "{install_cmd}"', cwd=str(target_dir), capture_output=True, shell=True)
                else:
                    print("未找到虚拟环境激活脚本，跳过依赖安装。")
                    installed = False

            if not installed:
                print("依赖安装失败，可手动在激活环境后执行：")
                if os.name == "nt":
                    print(
                        "  Windows CMD: .venv\\Scripts\\activate.bat && uv pip install -r requirements.txt --index-strategy unsafe-best-match")
                    print(
                        "  Windows PowerShell: .venv\\Scripts\\Activate.ps1 && uv pip install -r requirements.txt --index-strategy unsafe-best-match")
                else:
                    print(
                        "  Linux/macOS: source .venv/bin/activate && uv pip install -r requirements.txt --index-strategy unsafe-best-match")
        else:
            print("未找到 requirements.txt，跳过依赖安装。")

        # 打印激活提示（区分平台）
        print("虚拟环境已创建在目标目录下的 .venv")
        if os.name == "nt":
            print(f"PowerShell 激活命令：{activate_hint}")
            print("若使用 CMD：.\\.venv\\Scripts\\activate.bat")
        else:
            print(f"bash/zsh 激活命令：{activate_hint}")

        print(f"已初始化脚本工程：{target_dir}")

    def update_core(self, args) -> None:
        """更新核心文件/目录到目标路径。

        行为：
        1) 从远程模板ZIP获取最新文件（仅远程，失败则不更新）。
        2) 默认更新全部核心项；若提供 --files 则仅更新所选项。
        3) --force 时无条件覆盖；否则仅在不存在时写入，存在则提示跳过。
        """
        target_dir = Path(args.target).resolve()
        target_dir.mkdir(parents=True, exist_ok=True)

        # 远程模板ZIP下载地址
        TEMPLATE_ZIP_URL = (
            "https://lab-paas-apk-1254257443.cos.ap-nanjing.myqcloud.com/utestAutoScriptTemp/ubox-script-temp-master.zip"
        )

        # 定义核心文件映射（模板内的相对路径 -> 目标内的相对路径）
        # 这里源与目标相同命名，若模板结构不同可在此调整映射
        core_map = {
            "uv.toml": "uv.toml",
            "update_config.py": "update_config.py",
            "start_test.py": "start_test.py",
            "run.sh": "run.sh",
            "requirements.txt": "requirements.txt",
            "build.py": "build.py",
            "test_cases/internal": "test_cases/internal",
            "FRAMEWORK_USAGE.md": "FRAMEWORK_USAGE.md",
            "README.md": "README.md",
        }

        # 别名支持，便于 --files 传入
        alias_map = {
            "uv.toml": "uv.toml",
            "update_config": "update_config.py",
            "start_test": "start_test.py",
            "run.sh": "run.sh",
            "run_sh": "run.sh",
            "requirements": "requirements.txt",
            "requirements.txt": "requirements.txt",
            "build": "build.py",
            "build.py": "build.py",
            "internal": "test_cases/internal",
        }

        # 解析 --files 选择；为空则表示全部
        selected_relpaths = set()
        if args.files:
            for entry in args.files:
                for token in str(entry).split(','):
                    name = token.strip()
                    if not name:
                        continue
                    # 映射到真实相对路径
                    if name in alias_map:
                        selected_relpaths.add(alias_map[name])
                    elif name in core_map:
                        selected_relpaths.add(name)
                    else:
                        print(f"⚠️ 未识别的文件别名/路径：{name}，已忽略")
        else:
            # 默认全部
            selected_relpaths = set(core_map.keys())

        # 下载远程模板到临时目录，并确定源根目录
        def fetch_source_root() -> Path:
            """获取模板源根目录：仅从远程下载，失败则抛出异常。"""
            with tempfile.TemporaryDirectory() as tmpdir:
                tmp_extract = Path(tmpdir) / "extract"
                tmp_extract.mkdir(parents=True, exist_ok=True)
                try:
                    print(f"正在下载远程模板：{TEMPLATE_ZIP_URL}")
                    zip_path = Path(tmpdir) / "tpl.zip"
                    urllib.request.urlretrieve(TEMPLATE_ZIP_URL, zip_path.as_posix())
                    with zipfile.ZipFile(zip_path, 'r') as zf:
                        zf.extractall(tmp_extract)
                    # 检测是否单根目录
                    entries = [p for p in tmp_extract.iterdir() if p.name != "__MACOSX"]
                    if len(entries) == 1 and entries[0].is_dir():
                        # 只有一个根目录，进入它
                        src_root = entries[0]
                    else:
                        src_root = tmp_extract
                    # 将远程源复制到一个持久目录再返回（避免with结束被删除）
                    persist_dir = Path(tempfile.mkdtemp(prefix="utest_tpl_src_"))
                    # 仅复制，不过滤，以便后续匹配路径
                    for item in src_root.iterdir():
                        if item.name == "__MACOSX":
                            continue
                        dst = persist_dir / item.name
                        if item.is_dir():
                            shutil.copytree(item, dst, dirs_exist_ok=True)
                        else:
                            shutil.copy2(item, dst)
                    print("✅ 已获取远程模板")
                    return persist_dir
                except Exception as e:
                    raise RuntimeError(f"无法从远程下载模板：{e}")

        try:
            source_root = fetch_source_root()
        except Exception as e:
            print(f"❌ 无法获取模板源：{e}")
            return

        def parse_requirements(requirements_path: Path) -> dict:
            """解析 requirements.txt 文件，返回包名到完整行的映射。
            
            Args:
                requirements_path: requirements.txt 文件路径
                
            Returns:
                dict: {package_name: full_line} 映射，例如 {'ubox-py-sdk': 'ubox-py-sdk>=0.1.38'}
            """
            result = {}
            if not requirements_path.exists():
                return result
            
            try:
                with open(requirements_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        original_line = line.rstrip('\n')
                        line = original_line.strip()
                        
                        # 跳过空行和注释
                        if not line or line.startswith('#'):
                            continue
                        
                        # 跳过特殊指令（-r, -e, --index-url 等）
                        if line.startswith('-') or line.startswith('--'):
                            continue
                        
                        # 提取包名（去除版本约束、注释、extras等）
                        # 支持格式：
                        # - package==1.0.0
                        # - package>=1.0.0
                        # - package~=1.0.0
                        # - package[extra]>=1.0.0
                        # - package>=1.0.0,<2.0.0
                        # - package  # 注释
                        
                        # 先去除行内注释
                        if '#' in line:
                            line = line.split('#')[0].strip()
                        
                        # 提取包名：先处理 extras [extra]，再处理版本约束
                        if '[' in line:
                            # 处理 extras: package[extra]>=1.0.0
                            package_part = line.split('[')[0].strip()
                        else:
                            package_part = line
                        
                        # 处理版本约束：>=, ==, ~=, !=, <=, <
                        version_operators = ['>=', '==', '~=', '!=', '<=', '<']
                        package_name = package_part
                        for op in version_operators:
                            if op in package_name:
                                package_name = package_name.split(op)[0].strip()
                                break
                        
                        # 处理逗号分隔的多个版本约束：package>=1.0.0,<2.0.0
                        if ',' in package_name:
                            package_name = package_name.split(',')[0].strip()
                        
                        if package_name:
                            result[package_name.lower()] = original_line
            except Exception as e:
                print(f"⚠️ 解析 requirements.txt 失败：{e}")
            
            return result
        
        def merge_requirements(template_req: Path, user_req: Path, output_req: Path) -> None:
            """合并模板和用户的 requirements.txt。
            
            策略：
            1. 模板中存在的包：使用模板的版本（更新）
            2. 用户自定义的包：保留用户的版本（不删除）
            3. 保持原有顺序：先模板包，后用户自定义包
            """
            template_packages = parse_requirements(template_req)
            user_packages = parse_requirements(user_req)
            
            # 找出模板中的包和用户自定义的包
            template_package_names = set(template_packages.keys())
            user_package_names = set(user_packages.keys())
            user_custom_packages = user_package_names - template_package_names
            
            # 构建合并后的内容
            merged_lines = []
            
            # 1. 先写入模板中的包（使用模板的版本，保留注释和空行）
            if template_req.exists():
                try:
                    with open(template_req, 'r', encoding='utf-8') as f:
                        for line in f:
                            original_line = line.rstrip('\n')
                            line_stripped = original_line.strip()
                            
                            # 保留空行和注释
                            if not line_stripped or line_stripped.startswith('#'):
                                merged_lines.append(original_line)
                                continue
                            
                            # 跳过特殊指令（-r, -e, --index-url 等）
                            if line_stripped.startswith('-') or line_stripped.startswith('--'):
                                merged_lines.append(original_line)
                                continue
                            
                            # 提取包名（使用与 parse_requirements 相同的逻辑）
                            # 先去除行内注释
                            line_for_parse = line_stripped
                            if '#' in line_for_parse:
                                line_for_parse = line_for_parse.split('#')[0].strip()
                            
                            # 提取包名
                            if '[' in line_for_parse:
                                package_part = line_for_parse.split('[')[0].strip()
                            else:
                                package_part = line_for_parse
                            
                            version_operators = ['>=', '==', '~=', '!=', '<=', '<']
                            package_name = package_part
                            for op in version_operators:
                                if op in package_name:
                                    package_name = package_name.split(op)[0].strip()
                                    break
                            
                            if ',' in package_name:
                                package_name = package_name.split(',')[0].strip()
                            
                            if package_name and package_name.lower() in template_packages:
                                # 使用模板的版本（从解析结果中获取）
                                merged_lines.append(template_packages[package_name.lower()])
                            else:
                                # 如果无法解析包名，保留原行（可能是特殊格式）
                                merged_lines.append(original_line)
                except Exception as e:
                    print(f"⚠️ 读取模板 requirements.txt 失败：{e}")
                    # 如果读取失败，直接使用模板内容
                    if template_req.exists():
                        with open(template_req, 'r', encoding='utf-8') as f:
                            merged_lines = [line.rstrip('\n') for line in f]
            
            # 2. 添加用户自定义的包（保留用户的版本）
            if user_custom_packages:
                if merged_lines and not merged_lines[-1].startswith('#'):
                    merged_lines.append('')  # 添加空行分隔
                merged_lines.append('# 用户自定义依赖（以下包不会被模板更新覆盖）')
                for package_name in sorted(user_custom_packages):
                    merged_lines.append(user_packages[package_name])
            
            # 3. 写入合并后的内容
            try:
                with open(output_req, 'w', encoding='utf-8') as f:
                    for line in merged_lines:
                        f.write(line + '\n')
                print(f"✓ 已合并 requirements.txt（模板包已更新，用户自定义包已保留）")
            except Exception as e:
                print(f"⚠️ 写入合并后的 requirements.txt 失败：{e}")
                raise
        
        def copy_entry(relpath: str) -> None:
            """复制单个映射项（文件或目录）。"""
            src = source_root / relpath
            dst = target_dir / core_map.get(relpath, relpath)
            if not src.exists():
                print(f"⚠️ 模板中缺少项：{relpath}，已跳过")
                return
            
            # 特殊处理 requirements.txt：智能合并而不是直接覆盖
            if relpath == "requirements.txt" and dst.exists():
                try:
                    print(f"🔄 智能合并 requirements.txt（保留用户自定义依赖）...")
                    merge_requirements(src, dst, dst)
                    print(f"✓ 已更新：{relpath} -> {dst}")
                    return
                except Exception as e:
                    print(f"⚠️ 合并 requirements.txt 失败：{e}，将使用直接覆盖方式")
                    # 如果合并失败，回退到直接覆盖（如果用户使用了 --force）
                    if not args.force:
                        print(f"⏭ 已存在且未使用 --force，跳过：{dst}")
                        return
            
            try:
                dst.parent.mkdir(parents=True, exist_ok=True)
                if src.is_dir():
                    # 目录复制：force 则先删再拷；否则增量覆盖
                    if dst.exists() and args.force:
                        shutil.rmtree(dst, ignore_errors=True)
                    shutil.copytree(src, dst, dirs_exist_ok=True)
                else:
                    if dst.exists() and not args.force:
                        print(f"⏭ 已存在且未使用 --force，跳过：{dst}")
                        return
                    shutil.copy2(src, dst)
                print(f"✓ 已更新：{relpath} -> {dst}")
            except Exception as e:
                print(f"⚠️ 更新失败：{relpath} -> {dst}，原因：{e}")

        # 执行复制
        for rel in sorted(selected_relpaths):
            copy_entry(rel)

        print(f"✅ 核心文件更新完成，目标目录：{target_dir}")

    def new_case(self, args) -> None:
        """在 test_cases 目录下创建一个完整的示例用例文件"""
        # 检查是否在框架目录中
        if not self._check_framework_directory():
            return

        name = args.name
        tc_dir = Path("test_cases")
        tc_dir.mkdir(parents=True, exist_ok=True)
        file_path = tc_dir / f"{name}.py"
        if file_path.exists():
            print(f"文件已存在：{file_path}")
            return

        content = (
            "#!/usr/bin/env python3\n"
            "\n"
            "import time\n"
            "from core.test_case import TestCase, StepStatus, FailureStrategy\n"
            "from ubox_py_sdk import DriverType, OSType, DeviceButton, EventHandler, Device, LogcatTask\n"
            "\n"
            "\n"
            "class {cls}(TestCase):\n"
            "    \"\"\"{cls} 测试用例类\n"
            "\n"
            "    演示内容：\n"
            "    1) 用例名称/描述设置（见 __init__）\n"
            "    2) 步骤管理（start_step/end_step）end_step不是必须调用的，在断言中会自动设置结果\n"
            "    3) 断言（assert_true/assert_equal 等）\n"
            "    4) 录制（start_record/stop_record）\n"
            "    5) logcat 采集（start_logcat）\n"
            "    6) 性能采集（start_perf/stop_perf，停时自动解析 perf.json 并写入报告）\n"
            "    \"\"\"\n"
            "\n"
            "    def __init__(self, device: Device):\n"
            "        # 设置用例名称与描述（会显示在报告中）\n"
            "        super().__init__(\n"
            "            name=\"{cls}\",\n"
            "            description=\"演示步骤/断言/性能采集/logcat/录制等能力\",\n"
            "            device=device\n"
            "        )\n"
            "        # 初始化事件处理器（如需使用，可在用例内添加 watcher 等逻辑）\n"
            "        self.event_handler = self.device.handler\n"
            "        # 失败策略：失败是否继续执行。这里采用\"遇错即停\"，更贴近日常回归诉求\n"
            "        # 如需收集全部失败可切换为 FailureStrategy.CONTINUE_ON_FAILURE\n"
            "        self.failure_strategy = FailureStrategy.STOP_ON_FAILURE\n"
            "        self.logcat_task = None\n"
            "\n"
            "    def setup(self) -> None:\n"
            "        \"\"\"测试前置操作\n"
            "        - 仅做通用初始化类工作\n"
            "        - 如需启动被测应用，可通过 get_package_name() 获取配置中的包名并启动\n"
            "        \"\"\"\n"
            "        self.log_info(\"开始准备测试环境...\")\n"
            "\n"
            "        # 示例：如果配置了包名，则启动APP\n"
            "        package_name = self.get_package_name()\n"
            "        if package_name:\n"
            "            self.start_step(\"启动应用\", f\"启动应用: {{package_name}}\")\n"
            "            success = self.device.start_app(package_name)\n"
            "            self.assert_true(\"应用应成功启动\", success)\n"
            "            self.end_step(StepStatus.PASSED if success else StepStatus.FAILED)\n"
            "        else:\n"
            "            self.log_info(\"未配置应用包名，跳过应用启动\")\n"
            "\n"
            "        # 开始录制，录制文件路径会自动记录到测试结果中\n"
            "        self.start_record()\n"
            "\n"
            "        # 启动 logcat 采集（返回 LogcatTask）\n"
            "        self.logcat_task = self.start_logcat()\n"
            "\n"
            "    def teardown(self) -> None:\n"
            "        \"\"\"测试后置操作\n"
            "        - 手动停止录制\n"
            "        - 可选择性地关闭应用、回到桌面\n"
            "        \"\"\"\n"
            "        self.log_info(\"开始清理测试环境...\")\n"
            "\n"
            "        # 停止录制（录制停止后会在报告中展示录屏文件路径）\n"
            "        self.stop_record()\n"
            "\n"
            "        # 如果需要，可在此处停止被测应用并回到主界面\n"
            "        package_name = self.get_package_name()\n"
            "        if package_name:\n"
            "            self.device.stop_app(package_name)\n"
            "            self.log_info(f\"应用已停止: {{package_name}}\")\n"
            "        self.device.press(DeviceButton.HOME)\n"
            "        self.log_info(\"已返回主界面\")\n"
            "        if self.logcat_task:\n"
            "            self.logcat_task.stop()\n"
            "\n"
            "    def run_test(self) -> None:\n"
            "        \"\"\"执行示例测试\n"
            "        - 演示步骤编排与断言\n"
            "        - 演示关键阶段开启性能监控\n"
            "        \"\"\"\n"
            "        # 步骤1：进入页面/准备场景（示例）\n"
            "        self.start_step(\"准备场景\", \"示例：准备业务前置条件\")\n"
            "        time.sleep(1)\n"
            "        # 示例断言：总是为真（真实项目中请替换为业务校验）\n"
            "        self.assert_true(\"示例断言：环境已就绪\", True)\n"
            "        self.end_step(StepStatus.PASSED)\n"
            "\n"
            "        # 步骤2：关键路径 - 开启性能监控\n"
            "        self.start_step(\"开启性能监控\", \"在关键路径前启动性能采集\")\n"
            "        perf_started = self.start_perf()\n"
            "        self.assert_true(\"性能采集应成功启动\", perf_started)\n"
            "        self.end_step(StepStatus.PASSED if perf_started else StepStatus.FAILED)\n"
            "\n"
            "        try:\n"
            "            # 步骤3：执行核心业务操作（示例）\n"
            "            self.start_step(\"核心操作\", \"执行示例性业务流程\")\n"
            "            time.sleep(2)  # 这里模拟业务耗时\n"
            "            # 示例的等值断言（真实项目中替换为实际校验）\n"
            "            self.assert_equal(\"示例断言：结果应相等\", actual=1 + 1, expected=2)\n"
            "            self.end_step(StepStatus.PASSED)\n"
            "\n"
            "            # 步骤4：收尾校验\n"
            "            self.start_step(\"收尾校验\", \"示例：检查数据/页面状态\")\n"
            "            time.sleep(1)\n"
            "            self.assert_true(\"示例断言：收尾检查通过\", True)\n"
            "            self.end_step(StepStatus.PASSED)\n"
            "        finally:\n"
            "            # 性能监控需要显式停止，停止后会自动解析 get_log_dir()/perf.json 并入报告\n"
            "            self.stop_perf()\n"
        ).format(cls=name[:1].upper() + name[1:])

        file_path.write_text(content, encoding="utf-8")
        print(f"✅ 已创建测试用例文件：{file_path}")
        print("该示例包含：")
        print("- setup/teardown 前置后置操作")
        print("- 应用启动/停止和事件处理器")
        print("- 性能监控、录制、logcat收集")
        print("- 步骤管理和断言方法")
        print("- 日志记录功能")

    def clean(self, args) -> None:
        """清理构建产物和临时文件"""
        # 检查是否在框架目录中
        if not self._check_framework_directory():
            return

        print("开始清理构建产物和临时文件...")

        # 需要清理的目录和文件
        cleanup_items = [
            "dist/",
            "build/",
            "test_result/",
            "*.egg-info/",
            "__pycache__/",
            "*.pyc",
            "*.pyo",
            "*.log",
            "*.zip",
        ]

        cleaned_count = 0

        # 清理目录
        for pattern in cleanup_items:
            if pattern.endswith('/'):
                # 目录模式
                dir_name = pattern[:-1]
                if Path(dir_name).exists() and Path(dir_name).is_dir():
                    try:
                        shutil.rmtree(dir_name, ignore_errors=True)
                        print(f"  ✓ 已删除目录：{dir_name}")
                        cleaned_count += 1
                    except Exception as e:
                        print(f"  ⚠ 删除目录失败：{dir_name} - {e}")
            else:
                # 文件模式
                for item in Path('.').glob(pattern):
                    if item.is_file():
                        try:
                            item.unlink()
                            print(f"  ✓ 已删除文件：{item}")
                            cleaned_count += 1
                        except Exception as e:
                            print(f"  ⚠ 删除文件失败：{item} - {e}")
                    elif item.is_dir():
                        try:
                            shutil.rmtree(item, ignore_errors=True)
                            print(f"  ✓ 已删除目录：{item}")
                            cleaned_count += 1
                        except Exception as e:
                            print(f"  ⚠ 删除目录失败：{item} - {e}")

        # 清理 test_cases 下的 __pycache__
        test_cases_dir = Path("test_cases")
        if test_cases_dir.exists():
            for pycache_dir in test_cases_dir.rglob("__pycache__"):
                try:
                    shutil.rmtree(pycache_dir, ignore_errors=True)
                    print(f"  ✓ 已删除：{pycache_dir}")
                    cleaned_count += 1
                except Exception as e:
                    print(f"  ⚠ 删除失败：{pycache_dir} - {e}")

        if cleaned_count > 0:
            print(f"✅ 清理完成，共清理了 {cleaned_count} 个项目")
        else:
            print("ℹ️ 没有找到需要清理的文件或目录")

    def list_cases(self, args) -> None:
        """列出所有测试用例及其步骤信息"""
        # 检查test_cases目录是否存在
        test_cases_dir = Path("test_cases")
        if not test_cases_dir.exists():
            print("❌ 当前目录不是有效的框架目录，缺少目录：test_cases")
            print("请先使用 'init' 命令初始化框架，或切换到正确的框架目录")
            return

        try:
            # 收集用例信息
            print("正在分析测试用例文件...")
            collector = collect_test_cases("test_cases")
            
            if not collector.test_cases:
                print("⚠️ 未找到任何测试用例")
                return
            
            # 根据参数决定输出格式
            if args.json:
                # 输出JSON格式
                output_path = args.json
                collector.to_json(output_path)
                print(f"✅ 用例信息已保存到: {output_path}")
            else:
                # 控制台输出
                if args.summary:
                    collector.print_summary()
                else:
                    collector.print_detailed()
        except Exception as e:
            print(f"❌ 收集用例信息失败: {e}")
            import traceback
            print(traceback.format_exc())



def main() -> None:
    tool = CommandLineTool()
    args = tool.parser.parse_args()
    if hasattr(args, 'func'):
        args.func(args)
    else:
        tool.parser.print_help()


if __name__ == "__main__":
    main()
