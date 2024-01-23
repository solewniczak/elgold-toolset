import json
from collections import Counter, defaultdict

import click
import matplotlib.pyplot as plt

from utils.dataset import Dataset


@click.group()
def cli():
    """
    Plot various dataset statistics. Use plot.py [command] --help for detailed information about
    available commands.
    """
    pass


@cli.command()
@click.option('--data', type=click.Path(exists=True, file_okay=False), default='data',
              help='Path to the elgold dataset.')
@click.option('--percentage/--absolute', default=False,
              help='Should we display the absolute number of entities in each class (default) or percentage?')
@click.option('--labels', type=click.Path(), default='conf/plot_labels.json',
              help='JSON dictionary with mappings between text categories numbers and their labels.')
@click.option('--ner-classes', type=click.Path(), default='conf/ner_classes.json',
              help='JSON array of NER classes that are used in the dataset.')
@click.argument('categories', nargs=-1)
def histogram(data, percentage, labels, ner_classes, categories):
    """
    Summarize the number of entities in each class in the dataset. The histogram can be plotted separately for
    each texts category (categories argument) or for the entire dataset at once (when we provide no categories).
    Histogram shows the number of entities with and without links.
    """
    dataset = Dataset(data)
    with open(labels) as fp:
        labels = json.load(fp)
    with open(ner_classes) as fp:
        ner_classes = json.load(fp)

    if len(categories) == 0:
        categories = ['']  # get all categories in one plot
    classes = {category: defaultdict(Counter) for category in categories}
    nrows = len(categories) // 2 + len(categories) % 2
    ncols = min(len(categories), 2)
    fig, axs = plt.subplots(nrows, ncols, squeeze=False)
    if len(categories) > 1 and len(categories) % 2 != 0:
        fig.delaxes(axs[nrows-1, ncols-1])  # The indexing is zero-based here
    # if len(categories) > 1:
    fig.set_figwidth(ncols * 5)
    fig.set_figheight(nrows * 4)

    for parsed_file in dataset.iterate_files():
        # get first matching category
        counter_category = None
        for category in categories:
            if category in parsed_file['category']:
                counter_category = category
                break
        if counter_category is not None:
            for entity in parsed_file['entities']:
                classes[counter_category][entity['class']]['total'] += 1
                if entity['target'] == '':
                    classes[counter_category][entity['class']]['no-target'] += 1
                else:
                    classes[counter_category][entity['class']]['target'] += 1

    if percentage:
        classes_percentage = {}
        for counter_category in categories:
            target_links = sum([x['target'] for x in classes[counter_category].values()])
            no_target_links = sum([x['no-target'] for x in classes[counter_category].values()])
            total_links = sum([x['total'] for x in classes[counter_category].values()])
            classes_percentage[counter_category] = defaultdict(Counter)
            for ner_class, class_count in classes[counter_category].items():
                classes_percentage[counter_category][ner_class]['target'] = class_count['target'] / total_links * 100
                classes_percentage[counter_category][ner_class]['no-target'] = class_count['no-target'] / total_links * 100
                classes_percentage[counter_category][ner_class]['total'] = class_count['total']/total_links * 100
        classes = classes_percentage

    for i, counter_category in enumerate(categories):
        row = i // 2
        col = i % 2
        target = [classes[counter_category][class_]['target'] for class_ in ner_classes]
        no_target = [classes[counter_category][class_]['no-target'] for class_ in ner_classes]
        bars = axs[row,col].barh(ner_classes, target)
        bars = axs[row, col].barh(ner_classes, no_target, left=target)
        if percentage:
            axs[row,col].bar_label(bars, fmt='{:,.0f}%')
        else:
            axs[row, col].bar_label(bars, labels=[f'{trg}/{trg+ntrg}' for trg, ntrg in zip(target, no_target)])
        if counter_category in labels:
            axs[row, col].set_title(labels[counter_category])

    max_x = max([x['total'] for category_coutner in classes.values() for x in category_coutner.values()])
    if percentage:
        plt.setp(axs, xlim=(0, max_x + 5))  # + 3 for single histogram
    else:
        plt.setp(axs, xlim=(0, max_x + 60))  # + 150 for single histogram
    # plt.xlabel('Nb of entities')
    fig.set_tight_layout(True)
    plt.show()

    print(classes)
    target = sum([x['target'] for category_coutner in classes.values() for x in category_coutner.values()])
    no_target = sum([x['no-target'] for category_coutner in classes.values() for x in category_coutner.values()])
    total = sum([x['total'] for category_coutner in classes.values() for x in category_coutner.values()])
    print('target:', target)
    print('no target:', no_target)
    print('total links:', total)


if __name__ == '__main__':
    cli()