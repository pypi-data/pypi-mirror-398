"""
MCP服务器日志配置模块
提供完整的日志文件存储和管理功能
"""

import os
import sys
import logging
import logging.handlers
from pathlib import Path
from datetime import datetime
from typing import Optional


class ColoredFormatter(logging.Formatter):
    """带颜色的控制台日志格式化器"""
    
    # ANSI颜色代码
    COLORS = {
        'DEBUG': '\033[36m',    # 青色
        'INFO': '\033[32m',     # 绿色
        'WARNING': '\033[33m',  # 黄色
        'ERROR': '\033[31m',    # 红色
        'CRITICAL': '\033[35m', # 紫色
        'RESET': '\033[0m'      # 重置
    }
    
    def format(self, record):
        # 添加颜色
        if record.levelname in self.COLORS:
            record.levelname = (
                f"{self.COLORS[record.levelname]}"
                f"{record.levelname}"
                f"{self.COLORS['RESET']}"
            )
        return super().format(record)


class LogConfig:
    """日志配置管理器"""
    
    def __init__(self):
        self.log_dir = Path("./logs")
        self.console_log = True
        self.file_log = True
        self.log_level = logging.INFO
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        self.backup_count = 5
        self.loggers_configured = set()
    
    def setup_logging(
        self,
        name: str = "da_mcp_server",
        debug_mode: bool = False,
        log_dir: Optional[str] = None,
        console_log: Optional[bool] = None,
        file_log: Optional[bool] = None,
        log_level: Optional[str] = None
    ) -> logging.Logger:
        """
        设置完整的日志系统
        
        参数:
        - name: 日志记录器名称
        - debug_mode: 调试模式
        - log_dir: 日志目录
        - console_log: 是否启用控制台日志
        - file_log: 是否启用文件日志
        - log_level: 日志级别
        
        返回:
        - 配置好的logger实例
        """
        # 避免重复配置同一个logger
        if name in self.loggers_configured:
            return logging.getLogger(name)
        
        # 更新配置
        if log_dir:
            self.log_dir = Path(log_dir)
        if console_log is not None:
            self.console_log = console_log
        if file_log is not None:
            self.file_log = file_log
        
        # 设置日志级别
        if debug_mode:
            self.log_level = logging.DEBUG
        elif log_level:
            level_map = {
                'DEBUG': logging.DEBUG,
                'INFO': logging.INFO,
                'WARNING': logging.WARNING,
                'ERROR': logging.ERROR,
                'CRITICAL': logging.CRITICAL
            }
            self.log_level = level_map.get(log_level.upper(), logging.INFO)
        
        # 创建logger
        logger = logging.getLogger(name)
        logger.setLevel(self.log_level)
        
        # 清除现有handlers
        logger.handlers.clear()
        
        # 创建日志目录
        if self.file_log:
            self._ensure_log_directory()
        
        # 添加handlers
        if self.console_log:
            self._add_console_handler(logger)
        
        if self.file_log:
            self._add_file_handlers(logger)
        
        # 记录系统信息
        logger.info("=" * 60)
        logger.info(f"{name} 日志系统初始化完成")
        logger.info(f"日志目录: {self.log_dir.absolute()}")
        logger.info(f"日志级别: {logging.getLevelName(self.log_level)}")
        logger.info(f"控制台日志: {'启用' if self.console_log else '禁用'}")
        logger.info(f"文件日志: {'启用' if self.file_log else '禁用'}")
        logger.info(f"调试模式: {'启用' if debug_mode else '禁用'}")
        logger.info("=" * 60)
        
        # 记录Python和系统信息
        logger.debug(f"Python版本: {sys.version}")
        logger.debug(f"当前工作目录: {os.getcwd()}")
        logger.debug(f"脚本路径: {sys.argv[0] if sys.argv else 'Unknown'}")
        
        self.loggers_configured.add(name)
        return logger
    
    def _ensure_log_directory(self):
        """确保日志目录存在"""
        try:
            self.log_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"创建日志目录失败: {e}")
            # 如果无法创建日志目录，禁用文件日志
            self.file_log = False
    
    def _add_console_handler(self, logger):
        """添加控制台处理器"""
        try:
                  
            console_handler = logging.StreamHandler(sys.stderr)
            console_handler.setLevel(self.log_level)
            
            # 使用带颜色的格式化器
            console_formatter = ColoredFormatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%H:%M:%S'
            )
            console_handler.setFormatter(console_formatter)
            
            logger.addHandler(console_handler)
            logger.debug("控制台日志处理器添加成功")
            
        except Exception as e:
            print(f"添加控制台日志处理器失败: {e}")
    
    def _add_file_handlers(self, logger):
        """添加文件处理器"""
        try:
            # 主日志文件 (INFO及以上)
            main_log_file = self.log_dir / "da_mcp_server.log"
            main_handler = logging.handlers.RotatingFileHandler(
                main_log_file,
                maxBytes=self.max_file_size,
                backupCount=self.backup_count,
                encoding='utf-8'
            )
            main_handler.setLevel(logging.INFO)
            main_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s'
            )
            main_handler.setFormatter(main_formatter)
            logger.addHandler(main_handler)
            logger.debug(f"主日志文件处理器添加成功: {main_log_file}")
            
            # 错误日志文件 (ERROR及以上)
            error_log_file = self.log_dir / "da_mcp_server_error.log"
            error_handler = logging.handlers.RotatingFileHandler(
                error_log_file,
                maxBytes=self.max_file_size,
                backupCount=self.backup_count,
                encoding='utf-8'
            )
            error_handler.setLevel(logging.ERROR)
            error_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s\n'
                'Exception: %(exc_info)s\n' + '-' * 80
            )
            error_handler.setFormatter(error_formatter)
            logger.addHandler(error_handler)
            logger.debug(f"错误日志文件处理器添加成功: {error_log_file}")
            
            # 调试日志文件 (仅在DEBUG模式启用)
            if logger.isEnabledFor(logging.DEBUG):
                debug_log_file = self.log_dir / "da_mcp_server_debug.log"
                debug_handler = logging.handlers.RotatingFileHandler(
                    debug_log_file,
                    maxBytes=self.max_file_size,
                    backupCount=self.backup_count,
                    encoding='utf-8'
                )
                debug_handler.setLevel(logging.DEBUG)
                debug_formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s\n'
                    'Thread: %(thread)d - Process: %(process)d\n' + '-' * 80
                )
                debug_handler.setFormatter(debug_formatter)
                logger.addHandler(debug_handler)
                logger.debug(f"调试日志文件处理器添加成功: {debug_log_file}")
            
        except Exception as e:
            print(f"添加文件日志处理器失败: {e}")
            logger.error(f"添加文件日志处理器失败: {e}")
    
    def get_log_files_info(self) -> dict:
        """获取日志文件信息"""
        info = {
            'log_directory': str(self.log_dir.absolute()),
            'directory_exists': self.log_dir.exists(),
            'files': []
        }
        
        if self.log_dir.exists():
            for log_file in self.log_dir.glob("*.log*"):
                try:
                    stat = log_file.stat()
                    info['files'].append({
                        'name': log_file.name,
                        'path': str(log_file.absolute()),
                        'size': stat.st_size,
                        'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                    })
                except Exception as e:
                    info['files'].append({
                        'name': log_file.name,
                        'path': str(log_file.absolute()),
                        'error': str(e)
                    })
        
        return info


# 创建全局日志配置实例
log_config = LogConfig()


def setup_logger(
    name: str = "da_mcp_server",
    debug_mode: bool = False,
    log_dir: Optional[str] = None,
    console_log: Optional[bool] = None,
    file_log: Optional[bool] = None,
    log_level: Optional[str] = None
) -> logging.Logger:
    """
    便捷函数：设置logger
    
    参数:
    - name: 日志记录器名称
    - debug_mode: 调试模式
    - log_dir: 日志目录
    - console_log: 是否启用控制台日志
    - file_log: 是否启用文件日志
    - log_level: 日志级别
    
    返回:
    - 配置好的logger实例
    """
    return log_config.setup_logging(
        name=name,
        debug_mode=debug_mode,
        log_dir=log_dir,
        console_log=console_log,
        file_log=file_log,
        log_level=log_level
    )


def get_log_info() -> dict:
    """获取当前日志配置信息"""
    return log_config.get_log_files_info()