#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试框架打包脚本

将整个测试框架项目打包为 zip 文件，包含：
• 所有框架代码文件
• 测试用例目录
• 配置文件（config.yml、requirements.txt 等）
• 脚本文件（run.sh、update_config.py 等）

自动排除临时文件和构建产物（__pycache__、.venv、test_result 等）。

新增功能：
• 进度条显示打包进度
• 详细的文件统计信息
• 配置文件验证
• 更好的错误处理和日志记录
• 支持自定义排除规则

使用方法：
    python build.py [--output OUTPUT_FILE] [--exclude PATTERN] [--verbose]

参数：
    --output, -o        输出 zip 文件名（默认：{框架名}_{时间戳}.zip）
    --exclude, -e       自定义排除模式（可多次使用）
    --verbose, -v       显示详细输出
    --dry-run, -d       预览模式，不实际创建文件
    --config, -c        指定配置文件路径
"""

import argparse
import fnmatch
import logging
import os
import sys
import time
import zipfile
from datetime import datetime
from pathlib import Path
from typing import List, Set, Tuple, Optional
import json


class FrameworkBuilder:
    """测试框架打包器类"""
    
    def __init__(self, verbose: bool = False, dry_run: bool = False):
        """
        初始化打包器
        
        Args:
            verbose: 是否显示详细输出
            dry_run: 是否为预览模式
        """
        self.verbose = verbose
        self.dry_run = dry_run
        self.logger = self._setup_logger()
        
        # 默认排除模式
        self.default_exclude_patterns = [
            "__pycache__",
            ".venv",
            ".idea",
            "venv",
            "env",
            "*.pyc",
            "*.pyo",
            ".git",
            ".gitignore",
            "test_result/",
            "*.zip",
            "dist/",
            "build/",
            "*.egg-info/",
            "*.log",
            "*.tmp",
            ".DS_Store",
            "Thumbs.db",
            ".pytest_cache/",
            ".coverage",
            "htmlcov/",
            ".tox/",
            ".mypy_cache/",
            ".ruff_cache/",
            "*.md"
        ]
        
        # 统计信息
        self.stats = {
            'total_files': 0,
            'included_files': 0,
            'excluded_files': 0,
            'total_size': 0,
            'included_size': 0,
            'start_time': None,
            'end_time': None
        }
    
    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger('FrameworkBuilder')
        logger.setLevel(logging.DEBUG if self.verbose else logging.INFO)
        
        # 创建控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG if self.verbose else logging.INFO)
        
        # 创建格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(formatter)
        
        logger.addHandler(console_handler)
        return logger
    
    def _should_exclude(self, file_path: Path, exclude_patterns: List[str]) -> bool:
        """
        判断文件是否应该被排除
        
        Args:
            file_path: 文件路径
            exclude_patterns: 排除模式列表
            
        Returns:
            bool: 是否应该排除
        """
        # 安全地获取相对于当前目录的路径
        try:
            rel_path = file_path.relative_to(Path.cwd().resolve())
            rel_path_str = str(rel_path)
        except ValueError:
            # 如果文件不在当前目录下，使用绝对路径
            rel_path_str = str(file_path)
        
        file_name = file_path.name
        
        for pattern in exclude_patterns:
            # 支持通配符匹配（相对路径）
            if fnmatch.fnmatch(rel_path_str, pattern) or fnmatch.fnmatch(file_name, pattern):
                return True
            # 支持目录匹配
            if pattern.endswith('/') and rel_path_str.startswith(pattern.rstrip('/')):
                return True
                
        return False
    
    def _get_file_stats(self, file_path: Path) -> Tuple[int, bool]:
        """
        获取文件统计信息
        
        Args:
            file_path: 文件路径
            
        Returns:
            Tuple[int, bool]: (文件大小, 是否可读)
        """
        try:
            if file_path.is_file():
                return file_path.stat().st_size, True
        except (OSError, PermissionError):
            pass
        return 0, False
    
    def _validate_config(self, config_path: Optional[Path] = None) -> bool:
        """
        验证配置文件是否存在且有效
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            bool: 配置文件是否有效
        """
        if config_path is None:
            config_path = Path('config.yml')
        
        # 检查配置文件是否存在
        if not config_path.exists():
            self.logger.warning(f"配置文件不存在：{config_path}")
            return False
        
        try:
            # 简单的文件内容检查
            with open(config_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if not content.strip():
                    self.logger.warning(f"配置文件为空：{config_path}")
                    return False
        except Exception as e:
            self.logger.error(f"读取配置文件失败：{e}")
            return False
        
        self.logger.info(f"✅ 配置文件验证通过：{config_path}")
        return True
    
    def _collect_files(self, exclude_patterns: List[str]) -> Tuple[List[Path], Set[Path]]:
        """
        收集需要打包的文件
        
        Args:
            exclude_patterns: 排除模式列表
            
        Returns:
            Tuple[List[Path], Set[Path]]: (包含的文件列表, 排除的文件集合)
        """
        included_files = []
        excluded_files = set()
        
        self.logger.info("开始扫描文件...")
        
        for root, dirs, files in os.walk('.'):
            # 过滤排除的目录
            dirs[:] = [d for d in dirs if not self._should_exclude(Path(d), exclude_patterns)]
            
            for file in files:
                file_path = Path(root) / file
                self.stats['total_files'] += 1
                
                # 获取文件大小
                file_size, readable = self._get_file_stats(file_path)
                self.stats['total_size'] += file_size
                
                if not readable:
                    self.logger.warning(f"无法读取文件：{file_path}")
                    excluded_files.add(file_path)
                    self.stats['excluded_files'] += 1
                    continue
                
                if self._should_exclude(file_path, exclude_patterns):
                    excluded_files.add(file_path)
                    self.stats['excluded_files'] += 1
                    if self.verbose:
                        self.logger.debug(f"排除文件：{file_path}")
                else:
                    included_files.append(file_path)
                    self.stats['included_files'] += 1
                    self.stats['included_size'] += file_size
                    if self.verbose:
                        self.logger.debug(f"包含文件：{file_path}")
        
        return included_files, excluded_files
    
    def _normalize_shell_script(self, file_path: Path) -> Optional[bytes]:
        """
        规范化 shell 脚本文件，确保使用 Unix 格式（LF）和 UTF-8 编码
        
        Args:
            file_path: 文件路径
            
        Returns:
            Optional[bytes]: 规范化后的文件内容（字节），如果处理失败返回 None
        """
        try:
            # 尝试以二进制模式读取文件
            with open(file_path, 'rb') as f:
                content = f.read()
            
            # 将 CRLF (Windows) 转换为 LF (Unix)
            # 先替换 CRLF，再替换单独的 CR（Mac 旧格式）
            content = content.replace(b'\r\n', b'\n').replace(b'\r', b'\n')
            
            # 尝试解码为 UTF-8，如果失败则尝试其他编码
            try:
                text = content.decode('utf-8')
            except UnicodeDecodeError:
                # 尝试使用 latin-1 或其他编码
                try:
                    text = content.decode('latin-1')
                except UnicodeDecodeError:
                    # 如果都失败，尝试使用系统默认编码
                    text = content.decode(sys.getdefaultencoding(), errors='replace')
                    self.logger.warning(f"文件 {file_path} 使用非 UTF-8 编码，已转换")
            
            # 重新编码为 UTF-8，确保使用 LF 行结束符
            return text.encode('utf-8')
            
        except Exception as e:
            self.logger.error(f"处理 shell 脚本文件失败 {file_path}: {e}")
            return None
    
    def _create_zip(self, output_file: Path, included_files: List[Path]) -> bool:
        """
        创建ZIP文件
        
        对于 shell 脚本文件（.sh），会进行编码和行结束符规范化处理，
        确保在 Linux 上可以正常执行。
        
        Args:
            output_file: 输出文件路径
            included_files: 要包含的文件列表
            
        Returns:
            bool: 是否创建成功
        """
        if self.dry_run:
            self.logger.info(f"[预览模式] 将创建文件：{output_file}")
            self.logger.info(f"[预览模式] 将包含 {len(included_files)} 个文件")
            return True
        
        try:
            with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zipf:
                for i, file_path in enumerate(included_files, 1):
                    try:
                        # 使用os.path.relpath来获取相对路径，这样更简单可靠
                        # 确保所有文件都相对于当前工作目录
                        arcname = os.path.relpath(file_path, Path.cwd())
                        
                        # 对于 shell 脚本文件，进行规范化处理
                        if file_path.suffix == '.sh':
                            normalized_content = self._normalize_shell_script(file_path)
                            if normalized_content is None:
                                self.logger.warning(f"跳过无法处理的 shell 脚本：{file_path}")
                                continue
                            
                            # 将规范化后的内容写入 ZIP
                            zipf.writestr(arcname, normalized_content)
                            if self.verbose:
                                self.logger.debug(f"已规范化 shell 脚本：{arcname}")
                        else:
                            # 其他文件直接写入
                            zipf.write(file_path, arcname)
                        
                        # 显示进度
                        progress = (i / len(included_files)) * 100
                        self.logger.info(f"进度: {progress:.1f}% - 添加文件: {arcname}")
                        
                    except Exception as e:
                        self.logger.error(f"添加文件失败 {file_path}: {e}")
                        return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"创建ZIP文件失败: {e}")
            return False
    
    def build(self, output_file: Optional[str] = None, 
              custom_excludes: List[str] = None,
              config_path: Optional[str] = None) -> bool:
        """
        执行打包操作
        
        Args:
            output_file: 输出文件名
            custom_excludes: 自定义排除模式
            config_path: 配置文件路径
            
        Returns:
            bool: 是否成功
        """
        self.stats['start_time'] = time.time()
        
        # 生成输出文件名
        if not output_file:
            framework_name = Path.cwd().name
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"{framework_name}_{timestamp}.zip"
        elif not output_file.endswith('.zip'):
            output_file += '.zip'
        
        output_path = Path(output_file)
        
        # 验证配置文件
        self._validate_config(Path(config_path) if config_path else None)
        
        # 合并排除模式
        exclude_patterns = self.default_exclude_patterns.copy()
        if custom_excludes:
            exclude_patterns.extend(custom_excludes)
        
        self.logger.info(f"开始打包框架为：{output_file}")
        self.logger.info(f"排除模式：{exclude_patterns}")
        
        # 收集文件
        included_files, excluded_files = self._collect_files(exclude_patterns)
        
        if not included_files:
            self.logger.error("没有找到需要打包的文件")
            return False
        
        # 创建ZIP文件
        if not self._create_zip(output_path, included_files):
            return False
        
        # 计算统计信息
        self.stats['end_time'] = time.time()
        duration = self.stats['end_time'] - self.stats['start_time']
        
        # 显示结果
        self._print_summary(output_path, duration)
        
        return True
    
    def _print_summary(self, output_path: Path, duration: float) -> None:
        """打印打包摘要"""
        if self.dry_run:
            self.logger.info("=== 预览模式摘要 ===")
        else:
            self.logger.info("=== 打包完成摘要 ===")
        
        self.logger.info(f"输出文件：{output_path}")
        
        if not self.dry_run and output_path.exists():
            file_size = output_path.stat().st_size
            size_mb = file_size / (1024 * 1024)
            self.logger.info(f"文件大小：{size_mb:.2f} MB")
        
        self.logger.info(f"总文件数：{self.stats['total_files']}")
        self.logger.info(f"包含文件：{self.stats['included_files']}")
        self.logger.info(f"排除文件：{self.stats['excluded_files']}")
        self.logger.info(f"包含大小：{self.stats['included_size'] / 1024:.1f} KB")
        self.logger.info(f"耗时：{duration:.2f} 秒")
        
        if self.verbose and self.stats['excluded_files'] > 0:
            self.logger.info("排除的文件类型统计：")
            excluded_extensions = {}
            for pattern in self.default_exclude_patterns:
                if pattern.startswith('*.'):
                    ext = pattern[1:]
                    excluded_extensions[ext] = 0
            
            # 这里可以添加更详细的统计逻辑


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="测试框架打包脚本 - 增强版",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例：
  # 使用默认文件名打包
  python build.py
  
  # 指定输出文件名
  python build.py --output my_framework.zip
  python build.py -o my_framework.zip
  
  # 添加自定义排除模式
  python build.py --exclude "*.bak" --exclude "temp/"
  
  # 预览模式（不实际创建文件）
  python build.py --dry-run
  
  # 详细输出
  python build.py --verbose
  
  # 指定配置文件
  python build.py --config custom_config.yml
        """
    )

    parser.add_argument(
        "--output", "-o",
        help="输出 zip 文件名（默认：{框架名}_{时间戳}.zip）"
    )
    
    parser.add_argument(
        "--exclude", "-e",
        action="append",
        help="自定义排除模式（可多次使用）"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="显示详细输出"
    )
    
    parser.add_argument(
        "--dry-run", "-d",
        action="store_true",
        help="预览模式，不实际创建文件"
    )
    
    parser.add_argument(
        "--config", "-c",
        help="指定配置文件路径"
    )

    args = parser.parse_args()
    
    # 创建打包器实例
    builder = FrameworkBuilder(verbose=args.verbose, dry_run=args.dry_run)
    
    # 执行打包
    success = builder.build(
        output_file=args.output,
        custom_excludes=args.exclude,
        config_path=args.config
    )
    
    # 根据结果设置退出码
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
