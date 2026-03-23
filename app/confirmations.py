import random

CONFIRMATIONS = [
    "Done!",
    "Got it!",
    "Sure!",
    "On it!",
    "Consider it done!",
    "Alright!",
    "No problem!",
    "There you go!",
    "All set!",
    "Of course!",
    "Right away!",
    "Done and done!",
    "Easy!",
    "You got it!",
    "Happy to help!",
    "Done, as requested!",
    "Sorted!",
    "Leave it to me!",
    "Taken care of!",
    "Done in a flash!",
]

def get_confirmation() -> str:
    return random.choice(CONFIRMATIONS)
