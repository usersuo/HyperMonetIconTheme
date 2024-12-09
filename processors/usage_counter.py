import urllib.request

# 使用计数请求
class UsageCounter:
    def request_hits(api_url: str, headers):
        request = urllib.request.Request(
            api_url,
            headers=headers,
        )
        urllib.request.urlopen(request)