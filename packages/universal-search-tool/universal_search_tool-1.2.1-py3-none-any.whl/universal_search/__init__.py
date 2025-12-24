"""
Universal Search Tool - 任何人都能直接使用的搜索工具

特色功能:
- 零配置，内置 API key
- 支持多个搜索引擎 (Google, Bing, DuckDuckGo)
- 专业级搜索结果，绕过搜索限制
- 简单易用的命令行接口

使用方法:
  universal-search "搜索内容"
  universal-search --engine bing "AI工具" --count 5
"""

__version__ = "1.0.0"
__author__ = "Claude Code"
__email__ = "claude@anthropic.com"

from .core import UniversalSearch

__all__ = ['UniversalSearch']