#!/usr/bin/env python3
"""Simple Rock-Paper-Scissors CLI game.
Player plays against computer until quitting. Tracks overall wins.
"""
import random

CHOICES = {
    "r": "rock",
    "p": "paper",
    "s": "scissors",
}
BEATS = {
    "rock": "scissors",
    "scissors": "paper",
    "paper": "rock",
}


def get_player_choice():
    raw = input("Enter [r]ock, [p]aper, [s]cissors or [q]uit: ").strip().lower()
    if raw in ("q", "quit"):
        return None
    if raw in CHOICES:
        return CHOICES[raw]
    if raw in CHOICES.values():
        return raw
    print("Invalid input. Try again.")
    return get_player_choice()


def get_computer_choice():
    return random.choice(list(BEATS.keys()))


def compare(player, computer):
    if player == computer:
        return "tie"
    if BEATS[player] == computer:
        return "player"
    return "computer"


def main():
    print("Rock Paper Scissors — play until you quit (q).")
    player_score = 0
    computer_score = 0
    rounds = 0

    try:
        while True:
            player = get_player_choice()
            if player is None:
                break
            computer = get_computer_choice()
            rounds += 1
            result = compare(player, computer)

            print(f"You played: {player}. Computer played: {computer}.")
            if result == "tie":
                print("Result: Tie!")
            elif result == "player":
                player_score += 1
                print("Result: You win this round!")
            else:
                computer_score += 1
                print("Result: Computer wins this round!")

            print(f"Score — You: {player_score} | Computer: {computer_score} | Rounds: {rounds}\n")
    except (KeyboardInterrupt, EOFError):
        print("\nQuitting...")

    print("Final score:")
    print(f"You: {player_score} | Computer: {computer_score} | Rounds played: {rounds}")
    if player_score > computer_score:
        print("Overall winner: You! Congratulations.")
    elif computer_score > player_score:
        print("Overall winner: Computer. Better luck next time.")
    else:
        print("Overall: It's a tie.")


if __name__ == "__main__":
    main()
