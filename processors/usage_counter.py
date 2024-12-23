import urllib.request


class UsageCounter:
    def request_hits(api_url: str, headers):
        """使用计数请求

        Args:
            api_url: 请求URL
            headers: 请求头
        """
        request = urllib.request.Request(
            api_url,
            headers=headers,
        )
        urllib.request.urlopen(request)
