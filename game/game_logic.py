from datetime import datetime
from game.models import Guess

MAX_ATTEMPTS = 6

def get_word(game):
    if game.mode == "day":
        today = datetime.now().date()
        word = "omena" # lisää kun eelin koodi valmis

        if not word:
            raise ValueError("No daily word")
        
        return word
    
    elif game.mode == "inf":
        word = "astia" # lisää kun eelin koodi valmis

        if not word:
            raise ValueError("No daily word")
        
        return word


def evaluate_guess(guess_word, target_word):
    feedback = []
    for i in range(5):
        if guess_word[i] == target_word[i]:
            feedback.append("G")
        elif guess_word[i] in target_word:
            feedback.append("Y")
        else:
            feedback.append("X")
    return "".join(feedback)

def process_guess(game, guessed_word):
    if game.won:
        raise ValueError("Game already won")
    
    if game.attempts >= MAX_ATTEMPTS:
        raise ValueError("No attempts left")
    
    if len(guessed_word) != 5:
        raise ValueError("Word must be 5 letters")
    
    target_word = game.target_word
    feedback = evaluate_guess(guessed_word, target_word)

    guess = Guess(game=game, guessed_word=guessed_word, feedback=feedback)

    game.attempts += 1

    if feedback == "GGGGG":
        game.won = True
    
    return guess
