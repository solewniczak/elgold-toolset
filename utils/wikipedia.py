import requests


class Wikipedia:
    def __init__(self, language: str = 'en') -> None:
        self.uri = f'https://{language}.wikipedia.org/w/api.php'

    def check_targets(self, titles: set) -> dict:
        if not titles:  # no titles = empty result
            return {}
        params = {'format': 'json', 'action': 'query', 'prop': 'info', 'redirects': '1', 'titles': '|'.join(titles)}
        r = requests.get(self.uri, params=params)
        response = r.json()
        query_pages = response['query']['pages'] if 'query' in response else {}
        pages = {value['title']: int(key) > 0 for key, value in query_pages.items()}
        query_normalized = response['query']['normalized'] if 'normalized' in response['query'] else {}
        normalized = {value['from']: value['to'] for value in query_normalized}
        query_redirects = response['query']['redirects'] if 'redirects' in response['query'] else {}
        redirects = {value['from']: value['to'] for value in query_redirects}
        targets = {}
        for title in titles:
            normalized_title = normalized[title] if title in normalized else title
            final_destination = redirects[normalized_title] if normalized_title in redirects else normalized_title
            targets[title] = {
                'normalized': normalized_title,
                'redirect': final_destination,
                'exists': pages[final_destination]
            }
        return targets

    def get_ids(self, titles: set) -> dict:
        if not titles:  # no titles = empty result
            return {}
        params = {'format': 'json', 'action': 'query', 'titles': '|'.join(titles)}
        r = requests.get(self.uri, params=params)
        response = r.json()
        query_pages = response['query']['pages'] if 'query' in response else {}
        title2id = {page['title']: page_id for page_id, page in query_pages.items()}
        return title2id