import os
from collections import Counter
from statistics import mean, stdev

import click

from utils.dataset import Dataset
from utils.wikipedia import Wikipedia


class Colors:
    MAGENTA = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


@click.group()
def cli():
    pass


@cli.command()
@click.option('--data', type=click.Path(exists=True, file_okay=False), default='data')
@click.option('--class', 'search_classes', multiple=True, help='entity classes we want to search for')
@click.option('--target', 'search_targets', multiple=True, help='target link we want to search for')
def search(data, search_classes, search_targets):
    dataset = Dataset(data)
    for line in dataset.iterate_lines():
        entities = line['entities']
        if len(search_classes) > 0:  # check if line contains specified classes if defined
            entities = [entity for entity in entities if entity['class'] in search_classes]
        if len(search_targets) > 0:
            entities = [entity for entity in entities if any([t in entity['target'] for t in search_targets])]

        if any(entities):
            file = line['file']
            line_nb = line['nb']
            print(f'{Colors.MAGENTA}{file}{Colors.ENDC}:{Colors.BLUE}{line_nb}{Colors.ENDC}', end=':')
            for token in line['tokens']:
                if token['type'] == 'entity':
                    target = token['target']
                    for t in search_targets:
                        pos = target.find(t)
                        if pos != -1:
                            target = f'{target[:pos]}{Colors.RED}{target[pos:pos+len(t)]}{Colors.ENDC}{target[pos+len(t):]}'
                            break  # highlight only first occurrence for simpler code logic
                    output = '{{' + token['text'] + '|' + token['class'] + '|' + target + '}}'
                    if token['class'] in search_classes:
                        output = f'{Colors.BOLD}{output}{Colors.ENDC}'
                    print(output, end='')
                else:
                    print(token['text'], end='')
            print()


@cli.command()
@click.option('--data', type=click.Path(exists=True, file_okay=False), default='data')
@click.option('--exclude', multiple=True, help='entity classes we want to exclude from the dataset')
@click.argument('target', type=click.Path(exists=False, file_okay=False), default='out')
def filter(data, exclude, target):
    dataset = Dataset(data)
    if not os.path.exists(target):
        os.makedirs(target)
    if os.listdir(target):
        raise click.ClickException('output directory not empty')

    for parsed_file in dataset.iterate_files():
        output = []
        for parsed_line in parsed_file['lines']:
            output_line = ''
            for token in parsed_line['tokens']:
                if token['type'] == 'entity' and token['class'] not in exclude:
                    output_line += token['raw']
                else:
                    output_line += token['text']
            output.append(output_line + '\n')
        with open(os.path.join(target, parsed_file['file']), 'w') as fp:
            fp.writelines(output)


@cli.command()
@click.option('--data', type=click.Path(exists=True, file_okay=False), default='data')
@click.option('--exclude-targets/--include-targets', default=True, help="don't search for non-ascii chars inside entities targets")
@click.argument('chars')  # chars we want to search for
def search_chars(data, exclude_targets, chars):
    dataset = Dataset(data)
    chars = set(chars)
    non_ascii = Counter()
    for parsed_line in dataset.iterate_lines():
        file = parsed_line['file']
        line_nb = parsed_line['nb']
        output = f'{Colors.MAGENTA}{file}{Colors.ENDC}:{Colors.BLUE}{line_nb}{Colors.ENDC}:'
        non_ascii_in_line = set()

        def highlight(text):
            output = ''
            for ch in text:
                if 0 <= ord(ch) <= 127:  # ascii char
                    output += ch
                else:
                    non_ascii[ch] += 1
                    non_ascii_in_line.add(ch)
                    if ch in chars:  # this is a char we are searching for
                        ch = Colors.RED + ch
                    output += f'{Colors.BOLD}{ch}{Colors.ENDC}'
            return output

        for token in parsed_line['tokens']:
            if exclude_targets and token['type'] == 'entity':
                output += '{{' + highlight(token['text']) + '|' + token['class'] + '|' + token['target'] + '}}'
            else:
                output += highlight(token['text'])
        if chars & non_ascii_in_line:  # we have non-ascii chars in line we are looking for
            print(output)
    print('Non-ascii chars in dataset:')
    for ch, count in non_ascii.most_common():
        print(f"'{ch}': {count}")


@cli.command()
@click.option('--data', type=click.Path(exists=True, file_okay=False), default='data')
@click.option('--exclude-targets/--include-targets', default=True, help="don't replace inside entities targets")
@click.option('--delete', help="remove given charters")
@click.option('--unicode-escape/--no-unicode-escape', default=False, help="interpret delete, search and replace as unicode strings")
@click.argument('search')  # chars we want to search for
@click.argument('replace')  # chars we want to replace
@click.argument('target', nargs=1, type=click.Path(exists=False, file_okay=False), default='out')
def replace_chars(data, exclude_targets, delete, unicode_escape, search, replace, target):
    dataset = Dataset(data)
    if not os.path.exists(target):
        os.makedirs(target)
    if os.listdir(target):
        raise click.ClickException('output directory not empty')

    if unicode_escape:
        delete = bytes(delete, 'ascii').decode('unicode-escape')
        search = bytes(search, 'ascii').decode('unicode-escape')
        replace = bytes(replace, 'ascii').decode('unicode-escape')

    if len(search) != len(replace):
        raise click.ClickException('no 1:1 search replace mapping')

    char_map = dict(zip(search, replace))
    replacements = Counter()

    def replace(text):
        output = ''
        for ch in text:
            if ch in delete:
                replacements[ch] += 1
                continue
            elif ch in char_map:
                output += char_map[ch]
                replacements[ch] += 1
            else:
                output += ch
        return output

    for parsed_file in dataset.iterate_files():
        output = []
        for parsed_line in parsed_file['lines']:
            output_line = ''
            for token in parsed_line['tokens']:
                if exclude_targets and token['type'] == 'entity':
                    output_line += '{{' + replace(token['text']) + '|' + token['class'] + '|' + token['target'] + '}}'
                else:
                    output_line += replace(token['text'])
            output.append(output_line + '\n')
        with open(os.path.join(target, parsed_file['file']), 'w') as fp:
            fp.writelines(output)

    print("replaced:")
    for search, replace in char_map.items():
        print(f'"{search}" -> "{replace}": ' + str(replacements[search]))

    print("deleted:")
    for ch in delete:
        print(f'"{ch}": ' + str(replacements[ch]))


@cli.command()
@click.option('--data', type=click.Path(exists=True, file_okay=False), default='data')
@click.option('--remove-non-existent/--keep-non-existent', default=False, help="normalize targets")
@click.option('--normalize/--no-normalize', default=False, help="normalize targets")
@click.option('--redirect/--no-redirect', default=False, help="replace redirects with destinations")
@click.option('--interactive/--no-interactive', default=False, help="ask before performing replacements")
@click.argument('out', nargs=1, type=click.Path(exists=False, file_okay=False), default='out')
def fix_targets(data, remove_non_existent, normalize, redirect, interactive, out):
    dataset = Dataset(data)
    if not os.path.exists(out):
        os.makedirs(out)
    if os.listdir(out):
        raise click.ClickException('output directory not empty')

    wikipedia = Wikipedia()
    for parsed_file in dataset.iterate_files():
        print(f'processing ' + parsed_file['file'])
        targets = {entity['target'] for entity in parsed_file['entities'] if entity['target']}  # get only non-empty targes
        targets = wikipedia.check_targets(targets)
        output = []
        for parsed_line in parsed_file['lines']:
            output_line = ''
            for token in parsed_line['tokens']:
                if token['type'] == 'entity':
                    target = token['target']
                    if target:  # target not empty
                        if remove_non_existent and not targets[target]['exists']:
                            if interactive:
                                while True:
                                    user_input = input(f'remove non-existing "{target}" [Ynr]: ')
                                    if user_input.lower() == 'y' or user_input.lower() == '':
                                        print(f'removing "{target}"')
                                        target = ''
                                        break
                                    elif user_input.lower() == 'n':
                                        print(f'keeping "{target}"')
                                        break
                                    elif user_input.lower() == 'r':
                                        replacement = input('replace with: ')
                                        print(f'replacing with "{replacement}"')
                                        target = replacement
                                        break
                            else:
                                print(f'removing "{target}')
                                target = ''

                        # If the redirect exists we perform redirect replacement and not normalize.
                        # In interactive mode this may lead to creating non-normalized targets, but we ignore it here
                        # for simplicity. You can always run the command again to normalize remaining targets.
                        elif redirect and targets[target]['normalized'] != targets[target]['redirect']:
                            if interactive:
                                while True:
                                    user_input = input(f'replace "{target}" with redirect "'
                                                       + targets[target]['redirect'] + '" [Ynr]: ')
                                    if user_input.lower() == 'y' or user_input.lower() == '':
                                        print(f'replacing "{target}" with redirect "' + targets[target]['redirect']
                                              + '"')
                                        target = targets[target]['redirect']
                                        break
                                    elif user_input.lower() == 'n':
                                        print(f'keeping "{target}"')
                                        break
                                    elif user_input.lower() == 'r':
                                        replacement = input('replace with: ')
                                        print(f'replacing with "{replacement}"')
                                        target = replacement
                                        break
                            else:
                                print(f'replacing "{target}" with redirect "' + targets[target]['redirect']
                                      + '"')
                                target = targets[target]['redirect']
                        elif normalize and target != targets[target]['normalized']:
                            if interactive:
                                while True:
                                    user_input = input(f'replace "{target}" with "' + targets[target]['normalized'] +
                                                       '" [Yn]: ')
                                    if user_input.lower() == 'y' or user_input.lower() == '':
                                        print(f'replacing "{target} with ' + targets[target]['normalized'])
                                        target = targets[target]['normalized']
                                        break
                                    elif user_input.lower() == 'n':
                                        print(f'keeping "{target}"')
                                        break
                            else:
                                print(f'replacing "{target}" with ' + targets[target]['normalized'])
                                target = targets[target]['normalized']
                    output_line += '{{' + token['text'] + '|' + token['class'] + '|' + target + '}}'
                else:
                    output_line += token['text']
            output.append(output_line + '\n')
        with open(os.path.join(out, parsed_file['file']), 'w') as fp:
            fp.writelines(output)


@cli.command()
@click.option('--data', type=click.Path(exists=True, file_okay=False), default='data')
@click.option('--class', 'search_classes', multiple=True, help='entity classes we want to search for')
def list_entities(data, search_classes):
    dataset = Dataset(data)
    for parsed_file in dataset.iterate_files():
        for parsed_line in parsed_file['lines']:
            for entity in parsed_line['entities']:
                if len(search_classes) > 0 and entity['class'] in search_classes:
                    file = parsed_line['file']
                    line_nb = parsed_line['nb']
                    entity_raw = entity['raw']
                    print(f'{Colors.MAGENTA}{file}{Colors.ENDC}:{Colors.BLUE}{line_nb}{Colors.ENDC}:{entity_raw}')


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


if __name__ == '__main__':
    cli()
