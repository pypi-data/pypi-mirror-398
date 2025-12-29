"""
使用示例：请求级别的参数覆盖

这个文件展示了如何在 pp_primp 中使用请求级别的参数来临时覆盖客户端的默认设置。
"""
import pp_primp


def example_1_impersonate_override():
    """示例 1: 为不同的请求使用不同的浏览器指纹"""
    print("示例 1: 动态切换浏览器指纹")
    print("-" * 50)

    # 创建一个默认使用 Chrome 的客户端
    client = pp_primp.Client(impersonate="chrome_143")

    # 第一个请求使用默认的 Chrome
    print(f"默认浏览器: {client.impersonate}")

    # 第二个请求临时使用 Firefox
    # 注意：传入 impersonate 参数后，这个请求会使用 Firefox 的指纹
    response = client.get(
        'https://httpbin.org/headers',
        impersonate="firefox_143"
    )
    print("使用 Firefox 指纹发送请求")

    # 第三个请求临时使用 Safari
    response = client.get(
        'https://httpbin.org/headers',
        impersonate="safari_18",
        impersonate_os="macos"
    )
    print("使用 Safari/macOS 指纹发送请求\n")


def example_2_proxy_rotation():
    """示例 2: 为不同的请求使用不同的代理"""
    print("示例 2: 动态切换代理")
    print("-" * 50)

    # 创建一个客户端
    client = pp_primp.Client()

    # 代理列表（示例，实际使用时需要有效的代理）
    proxies = [
        'http://proxy1.example.com:8080',
        'http://proxy2.example.com:8080',
        'http://proxy3.example.com:8080',
    ]

    # 每个请求使用不同的代理
    for i, proxy in enumerate(proxies, 1):
        print(f"请求 {i} 使用代理: {proxy}")
        # response = client.get('https://httpbin.org/ip', proxy=proxy)
        # 实际使用时取消注释

    print()


def example_3_timeout_per_request():
    """示例 3: 为不同的请求设置不同的超时"""
    print("示例 3: 为不同类型的请求设置不同超时")
    print("-" * 50)

    # 创建一个默认超时 30 秒的客户端
    client = pp_primp.Client(timeout=30)

    # 快速请求使用较短超时
    response = client.get(
        'https://httpbin.org/get',
        timeout=5  # 5 秒超时
    )
    print("快速请求: 5 秒超时")

    # 慢速请求使用较长超时
    response = client.get(
        'https://httpbin.org/delay/10',
        timeout=15  # 15 秒超时
    )
    print("慢速请求: 15 秒超时")

    # 使用 read_timeout 控制响应读取超时
    response = client.get(
        'https://httpbin.org/stream-bytes/10240',
        timeout=10,
        read_timeout=5  # 读取超时 5 秒
    )
    print("流式响应: 10 秒连接超时，5 秒读取超时\n")


def example_4_ssl_verification():
    """示例 4: 为特定请求禁用 SSL 验证"""
    print("示例 4: 灵活控制 SSL 验证")
    print("-" * 50)

    # 创建一个默认验证 SSL 的客户端
    client = pp_primp.Client(verify=True)

    # 大多数请求使用默认的 SSL 验证
    response = client.get('https://httpbin.org/get')
    print("正常请求: 验证 SSL 证书")

    # 某些内部或测试服务器可能需要禁用验证
    try:
        response = client.get(
            'https://internal-server.local',
            verify=False  # 仅此请求禁用验证
        )
        print("内部服务器请求: 禁用 SSL 验证")
    except:
        print("内部服务器请求: 禁用 SSL 验证（模拟）")

    print()


def example_5_redirect_control():
    """示例 5: 控制重定向行为"""
    print("示例 5: 控制重定向行为")
    print("-" * 50)

    # 创建一个默认跟随重定向的客户端
    client = pp_primp.Client(follow_redirects=True, max_redirects=10)

    # 某些请求需要获取重定向前的响应
    response = client.get(
        'https://httpbin.org/redirect/3',
        follow_redirects=False  # 不跟随重定向
    )
    print(f"不跟随重定向: 状态码 {response.status_code}")

    # 某些请求需要限制重定向次数
    response = client.get(
        'https://httpbin.org/redirect/3',
        max_redirects=2  # 最多跟随 2 次重定向
    )
    print(f"限制重定向次数: 状态码 {response.status_code}\n")


def example_6_mixed_parameters():
    """示例 6: 同时覆盖多个参数"""
    print("示例 6: 同时覆盖多个参数")
    print("-" * 50)

    # 创建一个基础客户端
    client = pp_primp.Client(
        impersonate="chrome_143",
        timeout=30,
        verify=True
    )

    # 为特殊请求同时覆盖多个参数
    response = client.post(
        'https://api.example.com/data',
        impersonate="firefox_143",     # 使用 Firefox 指纹
        timeout=10,                     # 10 秒超时
        verify=False,                   # 禁用 SSL 验证
        proxy='http://proxy.example.com:8080',  # 使用代理
        headers={'X-Custom': 'Value'},  # 自定义头
        json={'key': 'value'}           # JSON 数据
    )
    print("特殊请求: 覆盖了 impersonate, timeout, verify, proxy 等参数\n")


def example_7_https_http2_control():
    """示例 7: 控制 HTTPS 和 HTTP/2"""
    print("示例 7: 控制 HTTPS 和 HTTP/2")
    print("-" * 50)

    client = pp_primp.Client()

    # 强制使用 HTTPS
    print("请求 1: 强制使用 HTTPS")
    # response = client.get('http://example.com', https_only=True)

    # 强制使用 HTTP/2
    print("请求 2: 强制使用 HTTP/2")
    # response = client.get('https://api.example.com', http2_only=True)

    # 同时使用
    print("请求 3: 同时强制 HTTPS 和 HTTP/2")
    # response = client.get('https://api.example.com', https_only=True, http2_only=True)

    print()


def example_8_per_api_settings():
    """示例 7: 为不同的 API 使用不同的设置"""
    print("示例 7: 为不同的 API 端点使用不同设置")
    print("-" * 50)

    client = pp_primp.Client(impersonate="chrome_143")

    # API 1: 快速，需要 Chrome 指纹
    response = client.get(
        'https://api1.example.com/data',
        timeout=5
    )
    print("API 1: Chrome 指纹，5 秒超时")

    # API 2: 慢速，需要 Firefox 指纹
    response = client.get(
        'https://api2.example.com/data',
        impersonate="firefox_143",
        timeout=30
    )
    print("API 2: Firefox 指纹，30 秒超时")

    # API 3: 内网，不验证 SSL
    response = client.get(
        'https://internal-api.local/data',
        verify=False,
        timeout=10
    )
    print("API 3: 不验证 SSL，10 秒超时\n")


if __name__ == "__main__":
    print("=" * 70)
    print("pp_primp 请求级别参数覆盖功能示例")
    print("=" * 70 + "\n")

    examples = [
        example_1_impersonate_override,
        example_2_proxy_rotation,
        example_3_timeout_per_request,
        example_4_ssl_verification,
        example_5_redirect_control,
        example_6_mixed_parameters,
        example_7_https_http2_control,
        example_8_per_api_settings,
    ]

    for example in examples:
        try:
            example()
        except Exception as e:
            print(f"示例执行出错: {e}\n")

    print("=" * 70)
    print("所有示例展示完成!")
    print("=" * 70)
