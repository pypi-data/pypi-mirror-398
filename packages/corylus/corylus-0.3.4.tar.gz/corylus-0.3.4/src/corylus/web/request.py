__all__ = ['request']

import httpx
import json

def request(a, timeout=300):
    if isinstance(a, str): a = {'url': a}
    data = json.dumps(a['body']) if 'body' in a else None
    response = httpx.request(
        a.get('method', 'GET'),
        a['url'],
        headers=a.get('headers'),
        data=data,
        timeout=timeout
    )
    return {
        'status': response.status_code,
        'headers': dict(response.headers),
        'body': response.json(),
    }
