import sys
import random
from textwrap import dedent


def log(*args):
    if __debug__:
        print(*args, file=sys.stderr)


def load_vocabulary():
    with open('/usr/share/dict/words') as f:
        words = f.read().splitlines()

    return [w for w in words if w[0].islower() and "'" not in w]


def main():
    vocabulary = load_vocabulary()

    my_cards = input().split()
    opp_cards = input().split()
    neutral_cards = input().split()
    assassin = input()

    log(dedent(
        f"""\
        {my_cards=}
        {opp_cards=}
        {neutral_cards=}
        {assassin=}""",
    ))

    while True:
        command = input()
        if command == 'produce-clue':
            # random clue
            print(
                random.choice(vocabulary),
                random.randrange(1, len(my_cards) + 1),
            )
        elif command == 'opponent-clue':
            clue, num = input().split()
            log(f'opponent gave clue of {clue=} {num=}')


if __name__ == '__main__':
    main()
