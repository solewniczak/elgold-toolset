import json
import os
from collections import defaultdict

import click

from utils.dataset import Dataset
from utils.wikipedia import Wikipedia


@click.group()
def cli():
    """
    Convert the elgold dataset to different formats. Use convert.py [command] --help for detailed information about
    available commands.
    """
    pass


@cli.command()
@click.option('--data', type=click.Path(exists=True, file_okay=False), default='data',
              help="The path to the elgold dataset.")
@click.option('--split/--no-split', default=False,
              help='Generate separate data file for each articles category. 0 '
                    'category contains all data. If activated, "target" must be a'
                    ' directory.')
@click.argument('target', nargs=1, type=click.Path(exists=False, file_okay=True), default='spacy.json')
def spacy(data, split, target):
    """
    Prepare dataset for spaCy NER evaluation. This command converts the dataset to a single json array. Each array
    element is a single text from the dataset. Each text is represented as a json object with keys "text" and
    "entities". The "text" contains a raw text and "entities" is an array of entities from the text. Each entity is
    an array of three elements: [start, end, class], where start and end define the starting and ending character of
    the entity and the class is the entity class.

    This format drops the Wikipedia links.

    This format was intended to be used for evaluating the elgold dataset with spaCy NER.
    """
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
    """
    Prepare dataset for BLINK evaluation. This command converts the dataset to a jsonl format. Each line represents
    a single entity from the dataset. Each entity is represented by json object with the following fields:
    'id': the auto incermented id of the entity.
    'label': the Wikipedia article that was linked to the entity.
    'label_id': the id of the Wikipedia article that was linked to the entity.
    'context_left': The content of the raw text before the mention.
    'mention': The text marked as the mention.
    'context_right': The content of the raw text after the mention.

    This format drops the information about entity type and mentions without links to Wikipedia.

    This format was intended to be used for evaluating the elgold dataset with BLINK.
    """
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
