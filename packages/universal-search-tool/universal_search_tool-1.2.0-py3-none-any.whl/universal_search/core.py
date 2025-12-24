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
            api_key: 必须提供用户自己的 API key，或自动从配置中获取多个key
        """
        self.api_keys = []
        self.current_key_index = 0
        self.key_usage_count = {}  # 记录每个key的使用次数

        # 初始化API keys
        if api_key:
            # 如果传入了单个key，也检查配置文件中的其他key
            all_keys = [api_key]
            config_keys = self._get_user_api_keys()
            if config_keys:
                all_keys.extend([k for k in config_keys if k != api_key])
            self.api_keys = all_keys
        else:
            self.api_keys = self._get_user_api_keys()

        if not self.api_keys:
            self._guide_user_config()
            sys.exit(1)

    def _get_user_api_keys(self) -> List[str]:
        """获取用户配置的多个 API keys"""
        keys = []

        # 方法1: 环境变量 (支持多个key，用逗号分隔)
        env_keys = os.getenv('SERPAPI_API_KEYS', '')
        if env_keys:
            keys.extend([key.strip() for key in env_keys.split(',') if key.strip()])

        # 方法2: 单个环境变量 (向后兼容)
        single_key = os.getenv('SERPAPI_API_KEY')
        if single_key and single_key not in keys:
            keys.append(single_key)

        # 方法3: 配置文件 (支持新格式和旧格式)
        config_file = os.path.expanduser('~/.serpapi_config.json')
        if os.path.exists(config_file):
            try:
                import json
                with open(config_file, 'r') as f:
                    config = json.load(f)

                # 新格式：支持多个key
                if 'api_keys' in config:
                    config_keys = config['api_keys']
                    if isinstance(config_keys, list):
                        keys.extend([key for key in config_keys if key and key not in keys])

                # 旧格式：单个key (向后兼容)
                elif 'api_key' in config:
                    single_config_key = config['api_key']
                    if single_config_key and single_config_key not in keys:
                        keys.append(single_config_key)

            except Exception:
                pass

        return keys

    def _get_current_api_key(self) -> str:
        """获取当前可用的API key"""
        if not self.api_keys:
            raise RuntimeError("没有可用的API keys")

        return self.api_keys[self.current_key_index]

    def _rotate_key(self):
        """轮换到下一个可用的API key"""
        if len(self.api_keys) <= 1:
            return  # 只有一个key，无法轮换

        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        print(f"🔄 切换到API key #{self.current_key_index + 1}")

    def _handle_search_failure(self, error: Exception) -> bool:
        """处理搜索失败，判断是否需要切换key

        Args:
            error: 搜索失败的异常

        Returns:
            bool: True表示已切换key，需要重试；False表示所有key都不可用
        """
        error_str = str(error).lower()

        # 判断是否是额度耗尽或key无效的错误
        key_related_errors = [
            'quota exceeded',
            'rate limit exceeded',
            'api key invalid',
            'unauthorized',
            'forbidden',
            'payment required',
            'credit exhausted'
        ]

        is_key_error = any(err in error_str for err in key_related_errors)

        if not is_key_error:
            # 不是key相关错误，不切换key
            return False

        # 记录当前key使用次数
        current_key = self._get_current_api_key()
        self.key_usage_count[current_key] = self.key_usage_count.get(current_key, 0) + 1

        # 如果还有其他key可用
        if len(self.api_keys) > 1:
            old_index = self.current_key_index
            self._rotate_key()

            # 避免无限循环：如果所有key都试过了，就停止
            if old_index == 0 and self.current_key_index == 1:
                # 第一次轮换，继续
                return True
            elif old_index < self.current_key_index:
                # 正常轮换
                return True
            else:
                # 所有key都试过了
                print("❌ 所有API keys都已耗尽或不可用")
                return False

        return False

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
        print("🔑 单个API Key设置:")
        print("方法1 - 环境变量:")
        print("  export SERPAPI_API_KEY='your_api_key_here'")
        print("")
        print("方法2 - 配置文件:")
        print("  echo '{\"api_key\": \"your_api_key_here\"}' > ~/.serpapi_config.json")
        print("")
        print("🚀 多个API Key设置 (推荐，自动切换):")
        print("方法3 - 环境变量 (多个key，逗号分隔):")
        print("  export SERPAPI_API_KEYS='key1,key2,key3'")
        print("")
        print("方法4 - 配置文件 (新格式):")
        print("  echo '{\"api_keys\": [\"key1\", \"key2\", \"key3\"]}' > ~/.serpapi_config.json")
        print("")
        print("🎯 多Key优势:")
        print("  ✅ 额度耗尽自动切换到下一个key")
        print("  ✅ 高并发搜索请求负载均衡")
        print("  ✅ 一个key失效不影响使用")
        print("  ✅ 实时显示当前使用的key编号")
        print("")
        print("🔒 您的 API Keys 是私密的，只有在您的设备上使用")
        print("🎊 配置完成后即可开始搜索！")
        print("")
        print("💡 现在就打开网站获取您的专属 API Keys:")
        print("   https://serpapi.com/")

    def search(self,
               query: str,
               engine: str = "google",
               count: int = 5,
               time_filter: Optional[str] = None) -> List[Dict[str, str]]:
        """执行搜索"""
        if not query.strip():
            raise ValueError("搜索内容不能为空")

        # 重试机制：最多尝试所有可用的keys
        max_retries = len(self.api_keys)

        for attempt in range(max_retries):
            try:
                current_key = self._get_current_api_key()
                print(f"🔑 使用API key #{self.current_key_index + 1} 搜索...")

                params = {
                    "api_key": current_key,
                    "engine": engine,
                    "q": query,
                    "num": count if engine == "google" else count,
                }

                # 添加时间筛选参数 (仅Google支持)
                if engine == "google" and time_filter:
                    params["tbs"] = f"qdr:{time_filter}"

                # 执行搜索
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
                    # 记录成功使用
                    print(f"✅ API key #{self.current_key_index + 1} 搜索成功")
                    return self._format_results(results["organic_results"])
                else:
                    return []

            except Exception as e:
                if attempt < max_retries - 1:
                    # 还有其他key可以尝试
                    if self._handle_search_failure(e):
                        print(f"⚠️  当前key失败: {str(e)}")
                        continue  # 尝试下一个key
                    else:
                        break  # 所有key都试过了
                else:
                    # 最后一个key也失败了
                    raise RuntimeError(f"搜索失败，所有API keys都不可用: {e}")

        return []

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