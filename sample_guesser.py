import random
import sys


def log(*args):
    if __debug__:
        print(*args, file=sys.stderr)


def main():
    cards = input().split()

    log(f'{cards=}')

    while True:
        command = input()
        if command == 'produce-guess':
            clue, count = input().split()
            count = int(count)
            for _ in range(count):
                guess = random.choice(cards)
                cards.remove(guess)
                print(guess)
                result = input()
                if result != 'correct':
                    break
            else:
                print('*done*')
        elif command == 'opponent-clue':
            clue, count = input().split()
            count = int(count)
            log('opponent gave {clue} {count} as a clue')
        elif command == 'opponent-guess':
            guess, result = input().split()
            log('opponent guessed {clue} which was {result}')
            cards.remove(guess)


if __name__ == '__main__':
    main()
