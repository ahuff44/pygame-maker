import random

def get_input():
    with open("game_atoms.txt", 'r') as file_:
        for line in file_:
            yield line.strip()

qualities = list(get_input())
for i in range(10):
    random.shuffle(qualities)
    print '%25s%25s%25s'%tuple(qualities[:3])
