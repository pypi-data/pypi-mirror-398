"""
Universal Search Tool - 安全版本核心搜索功能

安全原则：
- 不暴露私密 API key
- 用户必须自己配置
- 提供清晰的配置指导
"""

import os
import sys
from typing import List, Dict, Optional

try:
    from serpapi import GoogleSearch, BingSearch, DuckDuckGoSearch
except ImportError:
    print("❌ 请先安装依赖:")
    print("pip install google-search-results")
    sys.exit(1)


class UniversalSearch:
    """通用搜索类 - 安全版本，用户必须配置自己的 API key"""

    def __init__(self, api_key: Optional[str] = None):
        """初始化搜索器

        Args:
            api_key: 必须提供用户自己的 API key
        """
        self.api_key = api_key or self._get_user_api_key()

    def _get_user_api_key(self) -> str:
        """获取用户配置的 API key"""

        # 方法1: 环境变量
        api_key = os.getenv('SERPAPI_API_KEY')
        if api_key:
            return api_key

        # 方法2: 配置文件
        config_file = os.path.expanduser('~/.serpapi_config.json')
        if os.path.exists(config_file):
            try:
                import json
                with open(config_file, 'r') as f:
                    config = json.load(f)
                api_key = config.get('api_key')
                if api_key:
                    return api_key
            except Exception:
                pass

        # 方法3: 引导用户配置
        self._guide_user_config()
        sys.exit(1)

    def _guide_user_config(self):
        """引导用户获取和配置 API key"""
        print("🔐 为了保护隐私和安全，需要配置您自己的搜索 API Key")
        print("=" * 60)
        print("")
        print("📋 获取步骤:")
        print("1️⃣ 访问: https://serpapi.com/")
        print("2️⃣ 注册免费账户 (100次免费搜索)")
        print("3️⃣ 在 Dashboard 复制您的 Private API Key")
        print("")
        print("⚙️ 设置方法:")
        print("")
        print("方法1 - 环境变量 (推荐):")
        print("  export SERPAPI_API_KEY='your_api_key_here'")
        print("")
        print("方法2 - 配置文件:")
        print("  echo '{\"api_key\": \"your_api_key_here\"}' > ~/.serpapi_config.json")
        print("")
        print("🔒 您的 API Key 是私密的，只有在您的设备上使用")
        print("🎊 配置完成后即可开始搜索！")
        print("")
        print("💡 现在就打开网站获取您的专属 API Key:")
        print("   https://serpapi.com/")

    def search(self,
               query: str,
               engine: str = "google",
               count: int = 5,
               time_filter: Optional[str] = None) -> List[Dict[str, str]]:
        """执行搜索"""
        if not query.strip():
            raise ValueError("搜索内容不能为空")

        params = {
            "api_key": self.api_key,
            "engine": engine,
            "q": query,
            "num": count if engine == "google" else count,
        }

        # 添加时间筛选参数 (仅Google支持)
        if engine == "google" and time_filter:
            params["tbs"] = f"qdr:{time_filter}"

        try:
            if engine == "google":
                search = GoogleSearch(params)
            elif engine == "bing":
                search = BingSearch(params)
            elif engine == "duckduckgo":
                search = DuckDuckGoSearch(params)
            else:
                raise ValueError(f"不支持的搜索引擎: {engine}")

            results = search.get_dict()

            if "organic_results" in results:
                return self._format_results(results["organic_results"])
            else:
                return []

        except Exception as e:
            raise RuntimeError(f"搜索失败: {e}")

    def _format_results(self, raw_results: List[Dict]) -> List[Dict[str, str]]:
        """格式化搜索结果"""
        formatted = []
        for result in raw_results:
            formatted.append({
                "title": result.get('title', '无标题'),
                "url": result.get('link', ''),
                "snippet": result.get('snippet', '').replace('\n', '')[:200] + "...",
                "position": len(formatted) + 1
            })
        return formatted

    def print_results(self, query: str, engine: str = "google", count: int = 5, time_filter: Optional[str] = None):
        """打印搜索结果到控制台"""
        time_map = {'h': '小时', 'd': '天', 'w': '周', 'm': '月', 'y': '年'}
        time_desc = f" (最近{time_map.get(time_filter, time_filter)})" if time_filter else ""
        print(f"🔍 {engine.upper()} 搜索{time_desc}: {query}")
        print("=" * 60)

        try:
            results = self.search(query, engine, count, time_filter)

            if results:
                print(f"📋 找到 {len(results)} 个结果:\n")

                for result in results:
                    print(f"{result['position']}. 📄 {result['title']}")
                    print(f"   🔗 {result['url']}")
                    print(f"   💡 {result['snippet']}\n")
            else:
                print("❌ 没有找到结果")

        except Exception as e:
            print(f"❌ 搜索失败: {e}")

    def get_engines(self) -> List[str]:
        """获取支持的搜索引擎列表"""
        return ["google", "bing", "duckduckgo"]