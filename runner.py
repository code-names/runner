# pick team that goes first
# that team has an extra word
# get the word list, each team's word list, and assassin from runner 

# GUESSER
# initial input:
# give guesser word list (one line space delimited)
# input: 
# clue word, number
# output: 
# one guessed word per line
# wait for clue giver to give yay or nay -- clue giver will write ours, neutral, opponent
# continue while ours or until hit number+1

# give clue giver 4 lines
#   word list
#   that team word list
#   opponent word list
#   assassin
# runner runs a shared timer
#   if timer runs out the turn is forfeited. we go to the next team
# runner needs to keep score

NUM_CARDS = 5 * 5

class GameState:
    def __init__(self, first_cards, second_cards, gray_cards, assassin):
        self.first_cards = first_cards
        self.second_cards = second_cards
        self.gray_cards = gray_cards
        self.assassin = assassin
    
    @classmethod 
    def new_game(cls, dictionary, rand):
        all_cards = set(rand.sample(dictionary, NUM_CARDS))