import urllib.request

class UsageCounter:
    def request_hits(api_url: str, headers):
        request = urllib.request.Request(
            api_url,
            headers=headers,
        )
        urllib.request.urlopen(request)