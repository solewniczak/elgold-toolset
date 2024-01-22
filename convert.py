import json
import os
from collections import defaultdict

import click

from utils.dataset import Dataset
from utils.wikipedia import Wikipedia


@click.group()
def cli():
    pass


@cli.command()
@click.option('--data', type=click.Path(exists=True, file_okay=False), default='data')
@click.option('--split/--no-split', default=False, help='Generate separate data file for each articles category. 0 '
                                                        'category contains all data. If activated, "target" must be a'
                                                        ' directory.')
@click.argument('target', nargs=1, type=click.Path(exists=False, file_okay=True), default='spacy.json')
def spacy(data, split, target):
    dataset = Dataset(data)
    if not split and os.path.exists(target):
        raise click.ClickException('target file exists')
    if split and not os.path.exists(target):
        os.makedirs(target)
    if split and os.listdir(target):
        raise click.ClickException('target directory not empty')

    target_data = defaultdict(list)
    for parsed_file in dataset.iterate_files():
        output = {'text': '', 'entities': []}
        for parsed_line in parsed_file['lines']:
            for token in parsed_line['tokens']:
                if token['type'] == 'entity':
                    start = len(output['text'])
                    end = start + len(token['text'])
                    output['entities'].append([start, end, token['class']])
                output['text'] += token['text']
            output['text'] += '\n'
        target_data['0'].append(output)
        target_data[parsed_file['category'][0]].append(output)  # ignore subcategories

    if split:
        for category, files in target_data.items():
            filepath = os.path.join(target, f'{category}.json')
            with open(filepath, 'w') as fp:
                json.dump(files, fp)
    else:
        with open(target, 'w') as fp:
            json.dump(target_data['0'], fp)


@cli.command()
@click.option('--data', type=click.Path(exists=True, file_okay=False), default='data')
@click.option('--split/--no-split', default=False, help='Generate separate data file for each articles category. 0 '
                                                        'category contains all data. If activated, "target" must be a'
                                                        ' directory.')
@click.argument('target', nargs=1, type=click.Path(exists=False, file_okay=True), default='blink.jsonl')
def blink(data, split, target):
    dataset = Dataset(data)
    if not split and os.path.exists(target):
        raise click.ClickException('target file exists')
    if split and not os.path.exists(target):
        os.makedirs(target)
    if split and os.listdir(target):
        raise click.ClickException('target directory not empty')

    wikipedia = Wikipedia()
    records = defaultdict(list)
    id = 0
    for parsed_file in dataset.iterate_files():
        print(f'processing ' + parsed_file['file'])
        targets = {entity['target'] for entity in parsed_file['entities'] if
                   entity['target']}  # get only non-empty targes
        page_ids = wikipedia.get_ids(targets)

        left_context = []
        right_context = []
        for parsed_line in parsed_file['lines']:
            right_context.extend(parsed_line['tokens'])
            right_context.append({'type': 'text', 'text': '\n'})

        while len(right_context) > 0:
            token = right_context.pop(0)
            if token['type'] == 'entity' and token['target'] in page_ids:
                record = {
                    'id': id,
                    'label': token['target'],
                    'label_id': page_ids[token['target']],
                    'context_left': ''.join([token['text'] for token in left_context]),
                    'mention': token['text'],
                    'context_right': ''.join([token['text'] for token in right_context])
                }
                records['0'].append(record)
                records[parsed_file['category'][0]].append(record)  # ignore subcategories
                id += 1
            left_context.append(token)

    if split:
        for category, category_records in records.items():
            filepath = os.path.join(target, f'{category}.jsonl')
            with open(filepath, 'w') as fp:
                for record in category_records:
                    json.dump(record, fp)
                    fp.write('\n')
    else:
        with open(target, 'w') as fp:
            for record in records['0']:
                json.dump(record, fp)
                fp.write('\n')


if __name__ == '__main__':
    cli()
