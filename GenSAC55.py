# from itertools import combinations
#
import numpy as np
import random
from itertools import combinations

def check_SAC(f):
    n = 5  # Number of variables
    length = 2 ** n  # Output length: 32 for 5 variables
    balanced = True  # Assume the function is balanced for all a with Hamming weight 1

    # Convert the output string into a list of integer values (0 or 1)
    f = list(map(int, f))

    # Check each vector a with Hamming weight 1
    for i in range(n):
        a = 1 << i  # Create vector a by shifting bit 1 left by i positions
        count = 0  # Count the number of occurrences of value 1

        for x in range(length):
            # XOR the two values and count the number of 1s
            if f[x] != f[x ^ a]:
                count += 1

        # Check whether the function is balanced
        if count != 2 ** (n-1):
            balanced = False
            break

    return balanced

def calculate_sac_sum(sac_matrix):
    # Calculate the sum of 1s for each bit position in the SAC matrix
    # This represents the number of input pairs that differ in that specific bit position
    bit_sums = np.sum(sac_matrix == 1, axis=0)
    return bit_sums

def calculate_walsh_spectrum(f):
    n=5
    # Create a list of values for the function f from the bit string
    f_values = [int(bit) for bit in f]

    # Compute the matrix y = f(x) xor (w.x)
    y_matrix = np.zeros((2**n, 2**n), dtype=int)
    for x in range(2**n):
        for w in range(2**n):
            wx = sum(int(xi) & int(wi) for xi, wi in zip(bin(x)[2:].zfill(n), bin(w)[2:].zfill(n)))
            y_matrix[x, w] = f_values[x] ^ wx

    # Compute the matrix (-1) to the power of y
    matrix = (-1) ** y_matrix
    walsh_spectrum = np.sum(matrix, axis=0)

    return walsh_spectrum


def calculate_nonlinearity(walsh_spectrum):
    n=5
    # Calculate the nonlinearity of a Boolean function based on its Walsh spectrum
    # The nonlinearity is defined as N/2 - max_abs_walsh / 2, where max_abs_walsh is the maximum absolute value in the Walsh spectrum
    max_abs_walsh = max(abs(val) for val in walsh_spectrum)
    nonlinearity = 2**n/2 - max_abs_walsh / 2
    return nonlinearity


def generate_balanced_functions():
    n = 5  # Number of variables
    length = 2 ** n  # Output length: 32 for 5 variables

    # Create a list of positions that can contain bit 1
    positions = [i for i in range(length)]

    # Stop after generating 1000 functions
    count = 0

    # Repeatedly generate random functions until 1000 are obtained
    while count < 1000:
        # Randomly sample positions from the list
        combo = random.sample(positions, 16)
        f = ['0'] * length  # Initialize the string with all bits set to 0
        for pos in combo:
            f[pos] = '1'  # Set bit 1 at the selected positions
        if check_SAC(''.join(f)):
            a1 = calculate_walsh_spectrum(f)
            NL = calculate_nonlinearity(a1)
            if NL==12:
                yield ''.join(f)
                count += 1

# Open the output file for writing
with open('1000SAC55.txt', 'w') as file:
    # Check all functions and write the valid ones to the output file
    for f in generate_balanced_functions():
        file.write(f + '\n')  # Write the valid function to the output file

print("Xong! Đã lưu các hàm thỏa mãn vào tệp tin SAC55.txt")
