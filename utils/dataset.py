import os
import re
from collections.abc import Iterator


def atoi(text):
    return int(text) if text.isdigit() else text


def natural_keys(text):
    '''
    alist.sort(key=natural_keys) sorts in human order
    http://nedbatchelder.com/blog/200712/human_sorting.html
    (See Toothy's implementation in the comments)
    '''
    return [atoi(c) for c in re.split(r'(\d+)', text)]


class Dataset:
    def __init__(self, data_dir: str = 'data') -> None:
        self.data_dir = data_dir
        self.files = sorted([f for f in os.listdir(data_dir) if os.path.isfile(os.path.join(data_dir, f))],
                            key=natural_keys)

    @staticmethod
    def parse_line(line: str) -> dict:
        split = re.split(r'({{[^{}]*}})', line)
        tokens = []
        entities = []
        plain_text = ''
        for i, raw_token in enumerate(split):
            if i % 2 == 0:  # text
                tokens.append({'type': 'text', 'text': raw_token})
                plain_text += raw_token
            else:  # entity
                text, cls, target = raw_token.lstrip('{').rstrip('}').split('|')
                entity = {'type': 'entity', 'raw': raw_token, 'text': text, 'class': cls, 'target': target}
                tokens.append(entity)
                entities.append(entity)
                plain_text += text

        return {'tokens': tokens, 'entities': entities, 'plain_text': plain_text}

    def iterate_lines(self) -> Iterator[dict]:
        for parsed_file in self.iterate_files():
            for line in parsed_file['lines']:
                line['file'] = parsed_file['file']
                yield line

    def iterate_files(self) -> Iterator[dict]:
        for f in self.files:
            category, serial = f.removesuffix('.txt').split('_')
            parsed_file = {'file': f, 'category': category, 'serial': serial, 'lines': [], 'entities': []}
            with open(os.path.join(self.data_dir, f)) as fp:
                for nb, line in enumerate(fp, start=1):
                    line = line.rstrip('\n')
                    parsed_line = self.parse_line(line)
                    parsed_file['lines'].append({
                        'file': f,
                        'nb': nb,
                        'raw': line,
                        'plain_text': parsed_line['plain_text'],
                        'plain_text_tokens': parsed_line['plain_text'].split(),
                        'tokens': parsed_line['tokens'],
                        'entities': parsed_line['entities'],
                    })
                    parsed_file['entities'].extend(parsed_line['entities'])
            yield parsed_file
