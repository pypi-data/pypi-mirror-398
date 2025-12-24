"""
Universal Search Tool - 安全版本命令行接口

保护用户隐私，每个用户使用自己的 API key
"""

import argparse
import os
import json
from .core import UniversalSearch


def main():
    """安全版本的命令行主函数"""
    parser = argparse.ArgumentParser(
        prog='universal-search',
        description='🔍 安全通用搜索工具 - 保护您的 API Key 隐私',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
🔐 安全特色:
   ✅ 每个用户使用自己的 API Key
   ✅ 保护隐私，不泄露敏感信息
   ✅ 免费配额完全归自己所有
   ✅ 安全的配置方式

📝 配置步骤:
   1. 访问 https://serpapi.com/ 注册获取 API Key
   2. export SERPAPI_API_KEY='your_key_here'
   3. universal-search "搜索内容"

📝 使用示例:
   universal-search "编程教程"
   universal-search "AI tools" --engine bing --count 5
   universal-search --setup-guide
        '''
    )

    parser.add_argument('query', nargs='?', help='搜索内容')
    parser.add_argument('--engine', '-e', default='google',
                       choices=['google', 'bing', 'duckduckgo'],
                       help='搜索引擎 (默认: google)')
    parser.add_argument('--count', '-c', type=int, default=5, help='结果数量 (默认: 5)')
    parser.add_argument('--version', action='version', version='Universal Search Secure 1.0.0')
    parser.add_argument('--setup-guide', action='store_true', help='显示设置指南')
    parser.add_argument('--check-config', action='store_true', help='检查配置状态')

    args = parser.parse_args()

    if args.setup_guide:
        show_setup_guide()
        return

    if args.check_config:
        check_config()
        return

    if not args.query:
        print("🔍 安全通用搜索工具 v1.0 - 保护您的隐私")
        print("=" * 50)
        parser.print_help()
        show_setup_guide()
        return

    # 执行搜索
    try:
        search = UniversalSearch()
        search.print_results(args.query, args.engine, args.count)
    except SystemExit:
        print("\n🔑 配置您的 API Key 后即可搜索")
        print("📖 运行: universal-search --setup-guide")
    except Exception as e:
        print(f"❌ 搜索失败: {e}")


def show_setup_guide():
    """显示设置指南"""
    print("""
🔐 安全配置指南 - 保护您的 API Key 隐私
" .__ " *===*   .--.  .--.  .--. .--.
   __/  |\\      /    \\/    \\/    \\/    \\
  /_) '  | \\    |  _  ||  _  ||  _  ||  _  |
  |()| () |  \\   \\/ \\/\\  \\/\\  \\/\\  \\/\\  \\/\\
   \\__/\\__/|\\__\\  /  \\  /  \\  /  \\  /  \\  \\
             || \\/    \\/    \\/    \\/    \\/
         _  /|\\_______________________________________
        (o) /|\\_/

📋 步骤1: 获取您的专属 API Key
   • 访问: https://serpapi.com/
   • 注册免费账户 (100次免费搜索/月)
   • 在 Dashboard 找到 "Private API Key"
   • 复制您的专属 key (以: a1cea4a0... 开头)

⚙️ 步骤2: 配置您的 API Key (选择一种方法)

方法 A - 环境变量 (推荐，临时有效):
   export SERPAPI_API_KEY="your_api_key_here"

方法 B - 配置文件 (永久有效):
   echo '{"api_key": "your_api_key_here"}' > ~/.serpapi_config.json

✅ 步骤3: 验证配置
   universal-search --check-config

🚀 步骤4: 开始搜索
   universal-search "您想搜索的内容"

🔒 隐私保护:
   ✅ 您的 API Key 不会离开您的设备
   ✅ 搜索配额完全属于您自己
   ✅ 不会与其他用户共享
   ✅ 可随时更换自己的 key

🎊 配置完成后，您就是安全的搜索王者！
""")


def check_config():
    """检查配置状态"""
    print("🔍 检查 SerpApi 配置状态...")
    print("=" * 40)

    # 检查环境变量
    env_key = os.getenv('SERPAPI_API_KEY')
    if env_key:
        print("✅ 环境变量: 已配置")
        print(f"   Key: {env_key[:8]}...{env_key[-8:]}")
    else:
        print("❌ 环境变量: 未配置")

    # 检查配置文件
    config_file = os.path.expanduser('~/.serpapi_config.json')
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            file_key = config.get('api_key')
            if file_key:
                print("✅ 配置文件: 已配置")
                print(f"   Key: {file_key[:8]}...{file_key[-8:]}")
            else:
                print("❌ 配置文件: 无 api_key")
        except Exception:
            print("❌ 配置文件: 格式错误")
    else:
        print("❌ 配置文件: 不存在")

    # 测试搜索
    print("\n🧪 测试搜索连接...")
    try:
        search = UniversalSearch()
        results = search.search("Python", "google", 1)
        if results:
            print("✅ 搜索连接: 正常")
            print("🎊 您可以开始搜索了！")
        else:
            print("⚠️  搜索连接: 无结果")
    except SystemExit:
        print("❌ 搜索连接: 配置缺失")
    except Exception as e:
        print(f"❌ 搜索连接: {e}")

    print()
    if not env_key and not os.path.exists(config_file):
        print("💡 开始配置请运行: universal-search --setup-guide")


if __name__ == '__main__':
    main()