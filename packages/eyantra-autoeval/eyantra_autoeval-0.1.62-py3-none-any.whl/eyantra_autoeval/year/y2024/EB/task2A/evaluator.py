"""
evaluator.py

This file is used to evaluate task 2A of FPGA theme.
It generates the dump_txt.txt file which is used in the simulation.

"""
import os
import random

def toBinary(a):
    l,m=[],[]
    for i in a:
        l.append(ord(i))
    for i in l:
        m.append(bin(i)[2:].zfill(8))
    return m

def write_to_file(filepath, data, module,changed_indices):
    with open(filepath, 'w') as f:
        for parity,i in enumerate(data):
            f.write('0\n')
            for j in i:
                f.write(j)
                f.write('\n') 
            if module == "rx":
                if parity in changed_indices:
                    parity_bit = int(i.count('1')%2 == 0)
                else:
                    parity_bit = int(i.count('1')%2 != 0)
                f.write(str(parity_bit))
                f.write('\n')
            f.write('1\n')

def evaluate():
    directory_path = "/simulation/modelsim/"
    result = {}

    try:
        full_path = os.getcwd() + directory_path
        if os.path.isdir(full_path):
            module = input("Enter the module (tx/rx): ")
            if module == "tx" or module == "rx":
                text = input("Enter the text: ")
                length = len(text)

                if length <= 10:
                    changed_indices = []
                    num_letters = random.choice([1,1+length%4])
                    if module == "rx":
                        random_indices = random.sample(range(length), num_letters)
                        string_list = list(text)
                        for i in random_indices:
                            string_list[i] = chr(ord(string_list[i]) - 2)
                        modified_text = ''.join(string_list)
                        changed_indices = random_indices

                    data = toBinary(text)
                
                    write_to_file(full_path + 'data.txt', data, module,changed_indices)

                    print("File data.txt has been created.")

                else:
                    print("Entered text size is greater than 10!")
            else:
                print("Entered module name is not listed!")
        else:
            print(f"The directory '{directory_path}' does not exist.")

    except Exception as e:
        print(f"An error occurred: {e}")

    result["generate"] = False
    return result

if __name__ == "__main__":
    evaluate()
