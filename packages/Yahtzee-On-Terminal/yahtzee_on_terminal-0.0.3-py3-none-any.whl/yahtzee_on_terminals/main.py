#TAC 116, Fall 2025
#Final Project
#Name: Lily Hirasawa
#Email: lhirasaw@usc.edu
#Filename: gameplay2.py
#Description:
#This file is responsible for playing "Yahtzee". Yahtzee is a famous two-player game where the users
#roll five rolls up to three times each round, trying to score a maximum possible score.

import pandas as pd
import random
from importlib import resources
from pathlib import Path

#A function for setting up a game: game2_scoresheet provides a template for user_scores
#that will be used to print user scores
def set_up_game(filename="scoresheet.csv"):
    # If the caller gives an explicit filesystem path, use it.
    p = Path(filename)
    if p.exists():
        return pd.read_csv(p)

    # Otherwise, treat it as a packaged resource: yahtzee_on_terminals/data/<filename>
    resource = resources.files("yahtzee_on_terminals").joinpath("data", filename)

    # as_file() gives you a real pathlib.Path when pandas needs a filesystem path
    with resources.as_file(resource) as resource_path:
        return pd.read_csv(resource_path)

#Takes in a dataframe to print them nicely formatted
def display_score(data):
    print("Score so far: ")
    print(data.to_string(index=False))

#Rolls dice (using range) five times and stores them in the list.
#Some indices of the list might have some values in it: this means they are reserving it
#for the upcoming rolls as well, so you don't want to overwrite those.
def roll_dice(dice_list):
    for i in range(5):
        if dice_list[i] == 0:
        #Insert only if the element is set to 0
            dice_list[i] = random.randrange(1, 7)
    return dice_list

#This function calculates all the possible choices that the user can make and
#how many points they would score if they select the particular options
def calculate_options(dice):
    my_options = {}
    sum = 0
    #Sum of all the dices which goes into chance

    #If these lists are emtpy, it means that there are not three of a kind, four of a kind of yahtzee
    three_of_a_kind = []
    #Insert the number in which they have a three of a kind in
    four_of_a_kind = []
    #Insert the number in which they have a four of a kind in
    yahtzee = []
    #Insert the number in which they have a yahtzee in (if they have 5 of the same number)

    small_straight = [
        [1, 2, 3, 4],
        [2, 3, 4, 5],
        [3, 4, 5, 6],
    ]
    #This is the possible combinations for users to get a small straight

    large_straight = [
        [1, 2, 3, 4, 5],
        [2, 3, 4, 5, 6],
    ]
    #This is the possible combinations for users to get a large straight

    isSmallStraight = False
    isLargeStraight = False
    isFullHouse = False
    #Boolean values to determine whether they have a small straight, large straight or a full house.

    #A list of words that allows us to match numbers to a particular number in word (which is necessary for indexing reasons)
    num_to_letter = ["Ones", "Twos", "Threes", "Fours", "Fives", "Sixes"]

    for i in range(6):
    #Iterate through all the possible number of dice to check if we have a small straight, large straight or yahtzee
    #No elif was used because all these branching can happen concurrently
        if dice.count(i + 1) >= 3:
            three_of_a_kind.append(i + 1)
        if dice.count(i + 1) >= 4:
            four_of_a_kind.append(i + 1)
        if dice.count(i + 1) == 5:
            yahtzee.append(i + 1)
        if i != 5:
        #This basically is an iteration of 0-4, which aligns with the indexing we have for dice: summing up the
        #dice for chance
            sum += dice[i]
        my_options[num_to_letter[i]] = dice.count(i + 1) * (i+1)
        #This calculates how many of each number there are in the dice, and calculates an appropriate sum for each.

    if len(three_of_a_kind) > 0:
    #If there is at least one three of a kind
        score = three_of_a_kind[0]*3
        prev = 0
        for i in range(5):
        #Iterate through the list of dice we've got
            if dice[i] != three_of_a_kind[0]:
            #If the dice is not the same as the element we have in three of a kind, we add to the score.
            #There's a slight bug here: when we get four of a kind, this will disregard the fourth element to its sum:
            #this gets solved as we update the score for "Three of a Kind" when we deal with four of a kind.
                if prev == 0:
                    prev = dice[i]
                elif prev == dice[i]:
                #Prev allows us to check whether we had two numbers that are not the same as the one in three of a kind:
                #checks for a full ouse
                    isFullHouse = True
                score += dice[i]
        my_options["Three of a kind"] = score

    else:
        my_options["Three of a kind"] = 0

    if len(four_of_a_kind) > 0:
    #Checks for four of a kind using the same logic used in three of a kind
        score = four_of_a_kind[0] * 4
        for i in range(5):
            if dice[i] != four_of_a_kind[0]:
                score += dice[i]
        my_options["Four of a kind"] = score
        my_options["Three of a kind"] = score
        #Updates the score in three of a kind to make sure that the scores get summed up appropriately

    else:
        my_options["Four of a kind"] = 0

    if isFullHouse:
    #If full house, set the score to 25
        my_options["Full house"] = 25
    else:
        my_options["Full house"] = 0

    #This section determines whether we have a small or a large straight.
    #We first sort the dice
    sorted_dice = sorted(dice)

    #Define a set: where you can only have 1 element of something
    set_dice = []

    #Loop through the sorted dice list, and inputs them if it doesn't exist in set_dice
    #This allows us to have unique values that was rolled in an increasing order
    for i in range(len(sorted_dice)):
        unique = True
        for j in range(len(set_dice)):
            if set_dice[j] == sorted_dice[i]:
                unique = False
        if unique:
            set_dice.append(sorted_dice[i])

    #If the set dice has more than four elements, then it has small straight
    if len(set_dice) >= 4:
        for i in range(len(small_straight)):
        #Compare with the small_straight list that was primarily declared to see
        #whether the list contains a small straight
            if set_dice[0:4] == small_straight[i]:
                isSmallStraight = True

    #Same logic as small straight but now we need to have all 5 elements in dice list to be different.
    if len(set_dice) >= 5:
        for i in range(len(large_straight)):
            if set_dice[0:i+5] == large_straight[i]:
                isLargeStraight = True

    if isSmallStraight:
    #Small straight gives you 30 points
        my_options["Sm straight"] = 30
    else:
        my_options["Sm straight"] = 0
    if isLargeStraight:
    #Large straight gives you 40 points
        my_options["Lg straight"] = 40
    else:
        my_options["Lg straight"] = 0

    if len(yahtzee) > 0:
    #Yahtzee gives you 50 points
        my_options["Yahtzee"] = 50
    else:
        my_options["Yahtzee"] = 0

    #Chance is the sum of all dice you've rolled
    my_options["Chance"] = sum

    return my_options

def display_options(my_options):
#Based on my_options dataframe calculated, you can print it using this function.
    print("Here's the possible scores you can get: ")
    data = pd.DataFrame(list(my_options.items()), columns=["Category", "Score"])
    print(data.to_string(index=False))

def display_dice(dice_list):
#Prints dice_list to show what the users rolled
    print("You have rolled: ", dice_list)

def user_choice(my_options, user_cnt):
#Provides users with a list of choice

    if user_cnt == 2:
    #If user_cnt == 2, the user has run out of runts: they need to choose which option they want to score for.
        print("You've run out of your turns. Please select the option you would like to add your score to.")
        save_index = []
        user_input = ""

        while user_input not in my_options:
        #Ensures that user input is available in my_options
            user_input = input("Enter your choice: ").capitalize()
            #Capitalises so it matches with the format in the file

        save_index.append(user_input)

        #True identifies that the user's turn is over. save_index in this part of branching does nothing.
        return True, save_index

    else:
    #Users have the freedom to choose whether they want to terminate their turn or roll again
        print("Would you like to...")
        print("1. Roll one more time")
        print("2. Turn over")

        user_input = ""
        save_index = []
        # save_index is for storing the index of list from dice that corresponds to the ones that the user wants to save

        while user_input != "1" and user_input != "2":
            user_input = input("Enter your choice: ")
        if user_input == "1":
        #If users want to roll one more time...
            index_input = ""
            print("Select the index of the dice you'd want to save. Press 'q' when you're done (0 based indexing)")

            while index_input != "q":
                index_input = input("Enter your choice: ")

                if index_input.isdigit() and 6 > int(index_input) >= 0:
                #If valid user input, then add to save_index
                    save_index.append(int(index_input))

            #Return false means the player's turn hasn't ended yet.
            #save_index will be used to identify which number they want to save for the next roll
            return False, save_index
        else:
        #If the user wants to end their turn
            print("Select which option you'd like to add your score to: ")
            user_input = ""

            while user_input not in my_options:
            #select an option they want to score for
                user_input = input("Enter your choice: ").capitalize()
                print(user_input)

            save_index.append(user_input)
            # Here, save_index does nothing again.
            return True, save_index

#Calculate score gets run at the end, where it iterates through the score_sheet to calculate the total value
def calculate_score(score_sheet):
    player1_list = score_sheet.iloc[0:14, 1:2].values.tolist()
    player2_list = score_sheet.iloc[0:14, 2:3].values.tolist()
    player1_score = 0
    player2_score = 0
    player1_bonus = 0
    player2_bonus = 0
    #Bonus gets rewarded if the players score over 63 points in the category Ones - Sixes.

    for i in range(14):
        player1_score += player1_list[i][0]
        player2_score += player2_list[i][0]
        if 0 <= i <= 6:
            player1_bonus += player1_list[i][0]
            player2_bonus += player2_list[i][0]

    if player1_bonus >= 63:
        player1_score += 35
        score_sheet.loc[score_sheet["Category"]=="Bonus", "Player 1"] = 35

    if player2_bonus >= 63:
        player2_score += 35
        score_sheet.loc[score_sheet["Category"]=="Bonus", "Player 2"] = 35

    #Saves the score on row 14 of pandas dataframe
    score_sheet.iloc[14, 1] = player1_score
    score_sheet.iloc[14, 2] = player2_score

#Main function that controls the game flow
def main():
    print("Welcome to Yahtzee")
    print("==========Rule==========")
    print("The purpose of this game is to score more points than your opponent",
          "At each round, you will be provided with a choice to roll 5 dice up to 3 times",
          "For every roll you make, you can choose to preserve some and roll the rest.",
          "There are different category in which you can score your point",
          "eg. Full house, large straight etc..."
          "If you score more than 63 points by just ones-sixes, you will be given bonus points",sep="\n")

    score_sheet = set_up_game()

    #Dice list: one row for player 1 and the other for player 2
    dice = [
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0]
    ]

    #14 turns in total
    for i in range(14):
        #One loop for each player
        for j in range(2):
            print("=========TURN: PLAYER", j+1, "=========")
            user_cnt = 0
            over = False

            while user_cnt < 3 and not over:
            #Over determines if the player's turn is over, if not after three rolls
                user_input = ""
                while user_input != "roll":
                    user_input = input("Enter 'roll' to roll: ").lower()

                dice[j] = roll_dice(dice[j])
                display_dice(dice[j])
                my_options = calculate_options(dice[j])
                display_options(my_options)

                over, save_index = user_choice(my_options, user_cnt)

                if over:
                    print(save_index)
                    print("Player", str(j+1))
                    print(my_options[save_index[0]])
                    score_sheet.loc[score_sheet["Category"] == save_index[0], "Player " + str(j+1)] = my_options[save_index[0]]

                else:
                    new_dice = []
                    for i in range(len(save_index)):
                        new_dice.append(dice[j][save_index[i]])

                    for i in range(5-len(save_index)):
                        new_dice.append(0)

                    print("Current dice: ", new_dice)
                    dice[j] = new_dice

                user_cnt += 1
                print()

            #Display scores once they're all complete
            display_score(score_sheet)
            dice[j] = [0, 0, 0, 0, 0]

    print("=========GAME OVER=========")
    calculate_score(score_sheet)
    display_score(score_sheet)

    #Retrieving the row that stores the final score: to calculate who scored higher
    total_row = score_sheet.loc[
        score_sheet["Category"] == "Total", ["Player 1", "Player 2"]
    ].iloc[0].to_list()

    if total_row[0] > total_row[1]:
        print("Player 1 wins!")
    else:
        print("Player 2 wins!")

if __name__ == "__main__":
    main()

