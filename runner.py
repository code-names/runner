import enum
import random
import subprocess
import sys

TOTAL_CARDS = 5 * 5
TEAM_CARDS = 8


def log(*args):
    print(*args, file=sys.stderr)


def load_vocabulary():
    with open('/usr/share/dict/words') as f:
        words = f.read().splitlines()

    return {w for w in words if w[0].islower() and "'" not in w}


class Team(enum.Enum):
    first = 0
    second = 1


class GameState:
    def __init__(self,
                 first_team_cards,
                 second_team_cards,
                 neutral_cards,
                 assassin,
                 active_team):
        self.first_team_cards = first_team_cards
        self.second_team_cards = second_team_cards
        self.neutral_cards = neutral_cards
        self.assassin = assassin
        self.active_team = active_team

    @property
    def inactive_team(self):
        return (
            Team.first
            if self.active_team == Team.second else
            Team.second
        )

    @classmethod
    def new_game(cls, vocabulary, rand):
        all_cards = set(rand.sample(list(vocabulary), TOTAL_CARDS))
        first_team_cards = set(rand.sample(list(all_cards), TEAM_CARDS + 1))
        all_cards -= first_team_cards
        second_team_cards = set(rand.sample(list(all_cards), TEAM_CARDS))
        all_cards -= second_team_cards
        assassin = rand.choice(list(all_cards))
        all_cards -= {assassin}
        return cls(
            first_team_cards,
            second_team_cards,
            all_cards,
            assassin,
            active_team=Team.first,
        )

    @property
    def active_cards(self):
        return (
            self.first_team_cards,
            self.second_team_cards,
        )[self.active_team.value]

    @property
    def inactive_cards(self):
        return (
            self.first_team_cards,
            self.second_team_cards,
        )[(self.active_team.value + 1) % 2]

    @property
    def remaining_cards(self):
        return (
            self.first_team_cards |
            self.second_team_cards |
            self.neutral_cards |
            {self.assassin}
        )


class BotRunner:
    def __init__(self, cmd):
        self._proc = subprocess.Popen(
            cmd,
            encoding='utf-8',
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
        )

    def send(self, line):
        self._proc.stdin.write(line + '\n')
        self._proc.stdin.flush()

    def readline(self):
        return self._proc.stdout.readline().strip()


class ClueGiverRunner(BotRunner):
    def start_game(self,
                   my_cards,
                   opp_cards,
                   neutral_cards,
                   assassin):
        self.send(' '.join(sorted(my_cards)))
        self.send(' '.join(sorted(opp_cards)))
        self.send(' '.join(sorted(neutral_cards)))
        self.send(assassin)

    def produce_clue(self):
        self.send('produce-clue')
        word, count = self.readline().split()
        return word, int(count)


class GuessResult(enum.Enum):
    correct = 'correct'
    opponent = 'opponent'
    neutral = 'neutral'
    invalid = 'invalid'


class GuesserRunner(BotRunner):
    def start_game(self, all_cards):
        self.send(' '.join(sorted(all_cards)))

    def guess(self, clue, count):
        self.send('produce-guess')
        self.send(' '.join((clue, str(count))))
        while True:
            guess = self.readline()
            if guess == '*done*':
                return
            result = (yield guess)
            self.send(result.value)
            if result != GuessResult.correct:
                break

    def opponent_clue(self, clue, count):
        self.send('opponent-clue')
        self.send(' '.join((clue, str(count))))

    def opponent_guess(self, guess, result):
        self.send('opponent-guess')
        self.send(' '.join((guess, result.value)))


class BotTeam:
    def __init__(self, name, clue_giver, guesser):
        self.name = name
        self.clue_giver = clue_giver
        self.guesser = guesser

    @classmethod
    def from_cmds(cls, name, clue_giver, guesser):
        return cls(name, ClueGiverRunner(clue_giver), GuesserRunner(guesser))

    def __repr__(self):
        return f'<{type(self).__name__}: {self.name}>'


class Game:
    def __init__(self, starting_state, first_team, second_team):
        self.state = starting_state
        self.first_team = first_team
        self.second_team = second_team
        self.vocabulary = load_vocabulary()

    @property
    def active_team(self):
        return (
            self.first_team,
            self.second_team,
        )[self.state.active_team.value]

    @property
    def inactive_team(self):
        return (
            self.first_team,
            self.second_team,
        )[self.state.inactive_team.value]

    @classmethod
    def from_seed_and_commands(cls, seed, team_a_cmds, team_b_cmds):
        rand = random.Random(seed)
        team_a = BotTeam.from_cmds(*team_a_cmds)
        team_b = BotTeam.from_cmds(*team_b_cmds)
        first_team = team_a
        second_team = team_b
        if rand.random() > 0.5:
            first_team, second_team = second_team, first_team
        return cls(
            GameState.new_game(
                load_vocabulary(),
                rand,
            ),
            first_team,
            second_team,
        )

    def _start(self):
        self.first_team.clue_giver.start_game(
            self.state.first_team_cards,
            self.state.second_team_cards,
            self.state.neutral_cards,
            self.state.assassin,
        )
        self.second_team.clue_giver.start_game(
            self.state.second_team_cards,
            self.state.first_team_cards,
            self.state.neutral_cards,
            self.state.assassin,
        )

        self.first_team.guesser.start_game(self.state.remaining_cards)
        self.second_team.guesser.start_game(self.state.remaining_cards)

    def _step(self):
        active_team = self.active_team
        clue, count = active_team.clue_giver.produce_clue()
        if clue not in self.vocabulary:
            log(
                f'team {self.state.active_team} gave clue {clue} which was not'
                ' in the vocabulary, skipping their turn',
            )
            return
        elif clue in self.state.remaining_cards:
            log(
                f'team {self.state.active_team} gave clue {clue!r} which was'
                ' one of the remaining cards, skipping their turn',
            )
            return

        guess_coro = active_team.guesser.guess(clue, count)
        guess = next(guess_coro)
        while True:
            if guess not in self.state.remaining_cards:
                log(
                    f'team {self.active_team} guessed {guess!r}'
                    ' which is not one of the remaining cards, skipping',
                )
                try:
                    guess_coro.send(GuessResult.invalid)
                except StopIteration:
                    break
            elif guess in self.state.active_cards:
                log(
                    f'team {self.active_team} guessed {guess!r}'
                    ' which is was one of their cards',
                )
                self.state.active_cards.remove(guess)
                if not self.state.active_cards:
                    return self.active_team
                try:
                    guess = guess_coro.send(GuessResult.correct)
                except StopIteration:
                    break
            elif guess in self.state.inactive_cards:
                log(
                    f'team {self.active_team} guessed {guess!r}'
                    ' which is was one of their opponents cards',
                )
                self.state.inactive_cards.remove(guess)
                if not self.state.inactive_cards:
                    return self.inactive_team
                try:
                    guess = guess_coro.send(GuessResult.opponent)
                except StopIteration:
                    break
            elif guess in self.state.neutral_cards:
                log(
                    f'team {self.active_team} guessed {guess!r}'
                    ' which is was one of the neutral cards',
                )
                self.state.neutral_cards.remove(guess)
                try:
                    guess = guess_coro.send(GuessResult.neutral)
                except StopIteration:
                    break
            else:
                assert(guess == self.state.assassin)
                log(
                    f'team {self.active_team} guessed {guess!r} which is'
                    f' the assassin.'
                )
                return self.inactive_team
        list(guess_coro)
        self.state.active_team = self.state.inactive_team
        return None

    def run(self):
        self._start()
        while (winner := self._step()) is None:
            pass
        return winner
