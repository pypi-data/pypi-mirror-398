"""
evaluator.py

This file is used to evaluate task 2A of AstroTinker Bot theme.
It generates the dump_txt.txt file which is used in the simulation.

"""
import os

def toBinary(a):
    l,m=[],[]
    for i in a:
        l.append(ord(i))
    for i in l:
        m.append(bin(i)[2:].zfill(8))
    return m


def evaluate():

    directory_path = "/simulation/modelsim/"
    result = {}

    try:
        if os.path.isdir(os.getcwd() + directory_path):
            text = input("Enter the text: ")

            if len(text) <= 10:
                data = toBinary(text)
                with open('simulation/modelsim/dump_txt.txt', 'w') as f:
                    for i in data:
                        f.write(str(0))
                        f.write('\n')
                        for j in i:
                            f.write(j)
                            f.write('\n')
                        f.write(str(1))
                        f.write('\n')

                print("File dump_txt.txt has been created.")

            else:
                print("Entered text size is greater than 10!")
        else:
            print(f"The directory '{directory_path}' does not exist.")

    except Exception as e:
        print(f"An error occurred: {e}")

    result["generate"] = False
    return result