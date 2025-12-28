"""
Rules 文件管理模块

负责：
- IDE 类型检测
- 项目目录检测
- Rules 文件写入
- 备份管理
"""

import os
import shutil
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class RulesManager:
    """Rules 文件管理器"""
    
    # 规则文件映射
    RULES_FILE_MAP = {
        'cursor': '.cursor/rules/project-rules.mdc',
        'windsurf': '.windsurf/rules/project-rules.md',
        'vscode': '.github/copilot-instructions.md',
        'trae': '.trae/rules/project_rules.md'
    }
    
    @staticmethod
    def detect_ide_type() -> str:
        """
        检测当前 IDE 类型
        
        检测方法：
        1. 环境变量（优先级最高）
        2. 进程名称（需要 psutil）
        3. 默认值
        
        Returns:
            IDE 类型: cursor, windsurf, vscode, trae
        """
        # 方法 1: 环境变量
        ide_type = os.environ.get('DEVGENIUS_IDE_TYPE')
        if ide_type:
            ide_type = ide_type.lower()
            logger.info(f"🔍 从环境变量检测到 IDE 类型: {ide_type}")
            return ide_type
        
        # 方法 2: 尝试通过进程名称检测（需要 psutil）
        try:
            import psutil
            parent_process = psutil.Process(os.getppid()).name().lower()
            logger.debug(f"父进程名称: {parent_process}")
            
            if 'cursor' in parent_process:
                logger.info("🔍 通过进程名称检测到 IDE: Cursor")
                return 'cursor'
            elif 'windsurf' in parent_process:
                logger.info("🔍 通过进程名称检测到 IDE: Windsurf")
                return 'windsurf'
            elif 'code' in parent_process:
                logger.info("🔍 通过进程名称检测到 IDE: VS Code")
                return 'vscode'
            elif 'trae' in parent_process:
                logger.info("🔍 通过进程名称检测到 IDE: Trae")
                return 'trae'
        except (ImportError, Exception) as e:
            logger.debug(f"无法通过进程检测 IDE 类型: {e}")
        
        # 方法 3: 默认值
        default_ide = 'cursor'
        logger.info(f"🔍 使用默认 IDE 类型: {default_ide}")
        return default_ide
    
    @staticmethod
    def get_project_root() -> Optional[str]:
        """
        获取项目根目录
        
        检测方法：
        1. 环境变量 DEVGENIUS_PROJECT_PATH（最高优先级）
        2. 环境变量 PWD（IDE 设置的工作目录）
        3. 从当前工作目录向上查找 Git 根目录
        4. 当前工作目录（最后的备选）
        
        Returns:
            项目根目录路径，如果无法确定则返回 None
        """
        # 方法 1: 环境变量 DEVGENIUS_PROJECT_PATH（显式指定）
        project_path = os.environ.get('DEVGENIUS_PROJECT_PATH')
        if project_path and os.path.exists(project_path):
            logger.info(f"📂 从环境变量 DEVGENIUS_PROJECT_PATH 获取项目目录: {project_path}")
            return project_path
        
        # 方法 2: 环境变量 PWD（IDE 通常会设置这个）
        pwd = os.environ.get('PWD')
        if pwd and os.path.exists(pwd):
            # 检查是否是项目目录（包含 .git 或其他项目标识）
            if RulesManager._is_project_directory(pwd):
                logger.info(f"📂 从环境变量 PWD 获取项目目录: {pwd}")
                return pwd
        
        # 方法 3: 当前工作目录
        cwd = os.getcwd()
        logger.debug(f"当前工作目录: {cwd}")
        
        # 方法 4: 从当前工作目录向上查找 Git 根目录
        git_root = RulesManager._find_git_root(cwd)
        if git_root:
            logger.info(f"📂 找到 Git 根目录: {git_root}")
            return git_root
        
        # 方法 5: 检查当前工作目录是否是项目目录
        if RulesManager._is_project_directory(cwd):
            logger.info(f"📂 使用当前工作目录（检测到项目标识）: {cwd}")
            return cwd
        
        # 最后的备选：使用当前工作目录（可能不准确）
        logger.warning(f"⚠️ 无法确定项目目录，使用当前工作目录: {cwd}")
        logger.warning(f"⚠️ 建议在 MCP 配置中设置环境变量 DEVGENIUS_PROJECT_PATH")
        return cwd
    
    @staticmethod
    def _is_project_directory(path: str) -> bool:
        """
        检查目录是否是项目目录
        
        检测标识：.git, package.json, pom.xml, requirements.txt, go.mod 等
        
        Args:
            path: 目录路径
            
        Returns:
            是否是项目目录
        """
        path_obj = Path(path)
        
        # 常见的项目标识文件
        project_markers = [
            '.git',
            'package.json',
            'pom.xml',
            'build.gradle',
            'requirements.txt',
            'pyproject.toml',
            'go.mod',
            'Cargo.toml',
            'composer.json',
            '.project',
            'tsconfig.json',
        ]
        
        for marker in project_markers:
            if (path_obj / marker).exists():
                logger.debug(f"检测到项目标识: {marker}")
                return True
        
        return False
    
    @staticmethod
    def _find_git_root(start_path: str) -> Optional[str]:
        """
        从指定路径向上查找 Git 根目录
        
        Args:
            start_path: 起始路径
            
        Returns:
            Git 根目录路径，如果未找到则返回 None
        """
        current = Path(start_path).resolve()
        
        # 向上查找，最多查找 10 层
        for _ in range(10):
            git_dir = current / '.git'
            if git_dir.exists():
                return str(current)
            
            parent = current.parent
            if parent == current:  # 已到达根目录
                break
            current = parent
        
        return None
    
    @staticmethod
    def get_rules_file_path(ide_type: str, project_root: str) -> str:
        """
        获取规则文件的完整路径
        
        Args:
            ide_type: IDE 类型
            project_root: 项目根目录
            
        Returns:
            规则文件的完整路径
        """
        filename = RulesManager.RULES_FILE_MAP.get(ide_type, '.cursorrules')
        return os.path.join(project_root, filename)
    
    @staticmethod
    def write_rules_file(
        rules_file: str,
        rules_content: str,
        backup: bool = True
    ) -> bool:
        """
        写入规则文件到项目目录（备份后覆盖策略）
        
        Args:
            rules_file: 规则文件路径
            rules_content: 规则内容
            backup: 是否备份现有文件
            
        Returns:
            是否成功写入
        """
        try:
            # 1. 创建目录（如果需要）
            rules_dir = os.path.dirname(rules_file)
            if rules_dir and not os.path.exists(rules_dir):
                os.makedirs(rules_dir, exist_ok=True)
                logger.info(f"📁 创建目录: {rules_dir}")
            
            # 2. 备份现有文件（策略 C）
            if backup and os.path.exists(rules_file):
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_file = f"{rules_file}.backup_{timestamp}"
                shutil.copy2(rules_file, backup_file)
                logger.info(f"💾 已备份现有文件: {backup_file}")
            
            # 3. 写入新内容
            with open(rules_file, 'w', encoding='utf-8') as f:
                f.write(rules_content)
            
            logger.info(f"✅ Rules 已成功写入: {rules_file}")
            return True
            
        except PermissionError:
            logger.error(f"❌ 没有写入权限: {rules_file}")
            return False
        except Exception as e:
            logger.error(f"❌ 写入 Rules 文件失败: {e}", exc_info=True)
            return False
