import os
from collections import Counter
from statistics import mean, stdev

import click
from matplotlib import pyplot as plt

from utils.dataset import Dataset


@click.group()
def cli():
    pass


@cli.command()
@click.option('--data', type=click.Path(exists=True, file_okay=False), default='data')
@click.argument('categories', nargs=-1, type=click.Path(exists=False, file_okay=False))
def text_stat(data, categories):
    dataset = Dataset(data)
    if len(categories) == 0:
        categories = ['']  # get all categories

    files_lenghts = {category: [] for category in categories}

    for parsed_file in dataset.iterate_files():
        # get first matching category
        current_category = None
        for category in categories:
            if category in parsed_file['category']:
                current_category = category
                break
        if current_category is not None:
            files_lenghts[current_category].append(
                sum([len(line['plain_text_tokens']) for line in parsed_file['lines']]))

    print('id\tcount\tmin\tmax\tavg\tstd')
    for category, tokens_count in files_lenghts.items():
        nb_of_texts = len(tokens_count)
        cat_min = min(tokens_count)
        cat_max = max(tokens_count)
        cat_avg = mean(tokens_count)
        cat_stdev = stdev(tokens_count)
        print(f'{category}\t{nb_of_texts}\t{cat_min}\t{cat_max}\t{cat_avg:.0f}\t{cat_stdev:.0f}')


@cli.command()
@click.option('--data', type=click.Path(exists=True, file_okay=False), default='intermediate/annotated-raw')
def texts_per_author(data):
    texts_to_annotators = Counter()
    for f in os.listdir(data):
        annotator_dir = os.path.join(data, f)
        if os.path.isdir(annotator_dir):
            annotated_texts = len(
                [f for f in os.listdir(annotator_dir) if os.path.isfile(os.path.join(annotator_dir, f))])
            texts_to_annotators[annotated_texts] += 1

    min_texts = min(texts_to_annotators)
    max_texts = max(texts_to_annotators)
    # data_to_plot = {}
    # for n_texts in range(min_texts, max_texts+1):
    #     data_to_plot[n_texts] = texts_to_annotators[n_texts]

    labels, values = zip(*texts_to_annotators.most_common())

    fig, axs = plt.subplots()
    bars = axs.bar(labels, values)
    axs.bar_label(bars)
    axs.set_xticks(range(min_texts, max_texts + 1))
    axs.set_xlabel("Number of annotated texts")
    axs.set_ylabel("Number of annotators")
    fig.set_tight_layout(True)
    plt.show()


@cli.command()
@click.option('--first', type=click.Path(exists=True, file_okay=False), default='verification-team')
@click.option('--second', type=click.Path(exists=True, file_okay=False), default='verification-by-authors')
def links_diff(first, second):
    first_dataset = Dataset(first)
    second_dataset = Dataset(second)

    first_files = {parsed_file['file']: parsed_file for parsed_file in first_dataset.iterate_files()}
    second_files = {parsed_file['file']: parsed_file for parsed_file in second_dataset.iterate_files()}

    def entity2tuple(entity):
        return (entity['class'], entity['target'], entity['text'])

    total = 0
    for file_name, first_file in first_files.items():
        second_file = second_files[file_name]
        first_entites = [entity2tuple(entity) for entity in first_file['entities']]
        second_entites = [entity2tuple(entity) for entity in second_file['entities']]
        diff = [entity for entity in first_entites if not entity in second_entites or second_entites.remove(entity)]
        if len(diff) > 0:
            total += len(diff)
            print(f'{file_name}:', len(diff))

    print('total:', total)