import math
import numpy as np
import time

Sbox = []

n = 5
# # Calculate the size of the input space based on the number of bits
N = 2 ** n


def count_fixed_and_opposite_fixed_points(Sbox, n):
    count_fixed = 0
    count_opposite_fixed = 0

    for x in range(2 ** n):
        if Sbox[x] == x:
            count_fixed += 1
        elif Sbox[x] == (2 ** n - 1 - x):
            count_opposite_fixed += 1

    return count_fixed, count_opposite_fixed


# Function to calculate the Total Overlap (TO)
def calculate_TO(Sbox):
    # Calculate and store the boolean functions for each bit position i
    boolean_functions_sbox = ["".join(str((Sbox[x] >> i) & 1) for x in range(2 ** n)) for i in range(n)]

    # Calculate Af(u) for each f_i(x) with u ranging from 0 to 31
    Af_values = [[] for _ in range(2 ** n)]
    for i, f in enumerate(boolean_functions_sbox):
        for u in range(2 ** n):
            Af_u = sum((-1) ** (int(f[x]) ^ int(f[x ^ u])) for x in range(2 ** n))
            Af_values[u].append(Af_u)

    # Calculate the combined absolute sums
    combined_absolute_sums = [abs(sum(Af_values[u])) for u in range(2 ** n)]

    # Calculate the baseline and the total sum excluding the first value
    baseline = combined_absolute_sums[0]
    total_sum_excluding_first = sum(combined_absolute_sums[1:])

    # Calculate TO
    TO = n - (total_sum_excluding_first / (2 ** n ** 2 - 2 ** n))
    return TO


# Function to calculate the Maximum Total Overlap (MTO)
def calculate_MTO(Sbox):
    # Calculate and store the boolean functions for each bit position i
    boolean_functions_sbox = ["".join(str((Sbox[x] >> i) & 1) for x in range(2 ** n)) for i in range(n)]

    # Calculate Af_u for each value of i, j, and u
    Af_u_values_MTO = np.zeros((n, n, 2 ** n), dtype=int)
    for i in range(n):
        for j in range(n):
            for u in range(2 ** n):
                boolean_i = boolean_functions_sbox[i]
                boolean_j = boolean_functions_sbox[j]
                Af_u_MTO = sum((-1) ** (int(boolean_i[x]) ^ int(boolean_j[x ^ u])) for x in range(2 ** n))
                Af_u_values_MTO[i, j, u] = Af_u_MTO

    # Initialize a list to store the 60 sums
    sums_uj = [0] * (n * (2 ** n - 1))

    # Calculate the sums for each (u, j) pair with i running from 0 to 3
    index = 0
    for u in range(1, 2 ** n):
        for j in range(n):
            total_sum = sum(Af_u_values_MTO[i, j, u] for i in range(n))
            sums_uj[index] = total_sum
            index += 1

    # Take the absolute value of each sum
    abs_sums_uj = [abs(total_sum) for total_sum in sums_uj]

    # Calculate the final sum of absolute values
    final_sum_MTO = sum(abs_sums_uj)

    # Calculate MTO
    MTO = n - (final_sum_MTO / ((2 ** n) ** 2 - 2 ** n))
    return MTO


# Function to calculate the Relative Total Overlap (RTO)
def calculate_RTO(Sbox):
    # Calculate and store the boolean functions for each bit position i
    boolean_functions_sbox = ["".join(str((Sbox[x] >> i) & 1) for x in range(2 ** n)) for i in range(n)]

    # Calculate Af_u for each value of i, j, and u
    Af_u_values_RTO = np.zeros((n, n, 2 ** n), dtype=int)
    for i in range(n):
        for j in range(n):
            for u in range(2 ** n):
                boolean_i = boolean_functions_sbox[i]
                boolean_j = boolean_functions_sbox[j]
                Af_u_RTO = sum((-1) ** (int(boolean_i[x]) ^ int(boolean_j[x ^ u])) for x in range(2 ** n))
                Af_u_values_RTO[i, j, u] = Af_u_RTO

    # Initialize a list to store the 15 sums
    sums_u = [0] * (2 ** n - 1)

    # Calculate the sums for each u from 1 to 15
    for u in range(1, 2 ** n):
        total_sum = sum(Af_u_values_RTO[i, j, u] for i in range(n) for j in range(n))
        sums_u[u - 1] = total_sum

    # Take the absolute value of each sum
    abs_sums_u = [abs(total_sum) for total_sum in sums_u]

    # Calculate the final sum of absolute values
    final_sum = sum(abs_sums_u)

    # Calculate RTO
    RTO = n - (final_sum / (2 ** (2 * n) - 2 ** n))

    return RTO


# Function to calculate Hamming Weight
def hamming_weight(x):
    # Count the number of 1 bits in the value x
    weight = bin(x).count('1')
    return weight


# Function to calculate Confusion
def confusion(sbox):
    # Create a list to store all average values
    average_results = []
    average_results1 = []

    # Calculate and store the average value as k varies
    for k in range(1,2**n):
        sum_of_results = 0
        sum_of_results1=0
        for x in range(2**n):
            term1 = hamming_weight(sbox[x])
            term2 = hamming_weight(sbox[x ^ k])
            result = ((term1 - term2) ** 2) / 4
            sum_of_results += result
            result1 = ((term1 - term2) ** 2)
            sum_of_results1 += result1
        average_result = sum_of_results / (2**n)
        average_results.append(average_result)

        average_result1 = sum_of_results1 / (2 ** n)
        average_results1.append(average_result1)

    # Calculate the expected value of E_avg
    expected_value = sum(average_results1) / len(average_results1)

    # Calculate the variance of E_avg
    CCV = sum((x - expected_value) ** 2 for x in average_results1) / len(average_results1)


# Sort the list of average values
    sorted_averages = sorted(average_results)

    # Get the second smallest average value (remove case 0)
    MCC = sorted_averages[1]
    return MCC,CCV

# Function to calculate Walsh Spectra
def calculate_walsh_spectra(f):
    walsh_spectra = []

    for i in range(n):
        # Create the corresponding Boolean function for the i-th bit
        f_values = [(Sbox[x] >> i) & 1 for x in range(2 ** n)]

        # Compute the matrix y = f(x) xor (w.x)
        y_matrix = np.zeros((2 ** n, 2 ** n), dtype=int)
        for x in range(2 ** n):
            for w in range(2 ** n):
                wx = sum(int(xi) & int(wi) for xi, wi in zip(bin(x)[2:].zfill(n), bin(w)[2:].zfill(n)))
                y_matrix[x, w] = f_values[x] ^ wx

        # Compute the matrix (-1) to the power of y
        matrix = (-1) ** y_matrix

        # Compute the S matrix
        walsh_spectrum = np.sum(matrix, axis=0)
        walsh_spectra.append(walsh_spectrum)

    return walsh_spectra


# Function to calculate Signal-to-Noise Ratio (SNR)
def calculate_SNR(Sbox):
    # Calculate the Walsh spectra for all 4 Boolean functions of the S-box
    walsh_spectra = calculate_walsh_spectra(Sbox)

    # Calculate the sum of values at corresponding positions in the 4 Walsh spectra
    total_walsh_sums = np.sum(walsh_spectra, axis=0)

    # Calculate the sum of values raised to the power of 4
    total_walsh_sums_power4 = np.sum(total_walsh_sums ** 4)

    # Calculate the Signal-to-Noise Ratio (SNR) value
    SNR = n * (2 ** (2 * n)) / np.sqrt(abs(total_walsh_sums_power4))

    return SNR


# Function to calculate Difference Distribution Table (DDT) for S-box
def ddtsbox(S, n, m):
    D = [[0] * (2 ** m) for _ in range(2 ** n)]
    for alpha in range(2 ** n):
        for x in range(2 ** n):
            beta = S[x] ^ S[x ^ alpha]
            D[alpha][beta] += 1
    return D


# Function to calculate Differential Distribution Table (DDT)
def cal_ddt(S, n, m):
    D = ddtsbox(S, n, m)
    max_values = []

    for alpha in range(2 ** n):
        for beta in range(2 ** m):
            max_values.append(D[alpha][beta])

    max_values = sorted(set(max_values), reverse=True)
    second_max = 0

    for value in max_values:
        if value != 2 ** n:  # Do not use the value at (0,0)
            second_max = value
            ddt = second_max / 2 ** n
            break

    return ddt


# Function to calculate Dot Product of two vectors
def dot(U, V):
    W = U & V
    dot_result = 0
    while W != 0:
        dot_result ^= W & 1
        W >>= 1
    return dot_result


# Function to calculate Bias of an integer
def bias_integer(S, alpha, beta, n):
    e = 0
    for x in range(2 ** n):
        if dot(alpha, x) ^ dot(beta, S[x]) == 0:
            e += 1
    return e - 2 ** (n - 1)


# Function to calculate Linear Approximation Table (LAT)
def lat(S, n, m):
    L = [[0] * (2 ** m) for _ in range(2 ** n)]
    for alpha in range(2 ** n):
        for beta in range(2 ** m):
            L[alpha][beta] = bias_integer(S, alpha, beta, n)
    return L


# Function to calculate the second largest absolute value in LAT
def lap(S, n, m):
    L = lat(S, n, m)
    all_values = [abs(L[alpha][beta]) for alpha in range(2 ** n) for beta in range(2 ** m)]
    all_values.sort(reverse=True)
    second_largest_abs_value = all_values[1]  # Do not use the value at (0,0)
    lap = second_largest_abs_value / (2 ** n)
    return lap


# Function to calculate Hamming Distance
def hamming_distance(x, y):
    # XOR the input values and count the number of 1 bits in the result
    xor_result = x ^ y
    distance = bin(xor_result).count('1')
    return distance


# Function to calculate Average Hamming Distance
def average_hamming_distance(Sbox):
    total_distance = 0
    num_inputs = 2 ** n

    # Iterate over all input-output pairs
    for input_value in range(2 ** n):
        output_value = Sbox[input_value]
        distance = hamming_distance(input_value, output_value)
        total_distance += distance

    # Calculate the average Hamming distance
    average_distance = total_distance / num_inputs
    return average_distance


def calculate_walsh_spectrum(f):
    # Create a list of values for the function f from the bit string
    f_values = [int(bit) for bit in f]

    # Compute the matrix y = f(x) xor (w.x)
    y_matrix = np.zeros((2 ** n, 2 ** n), dtype=int)
    for x in range(2 ** n):
        for w in range(2 ** n):
            wx = sum(int(xi) & int(wi) for xi, wi in zip(bin(x)[2:].zfill(n), bin(w)[2:].zfill(n)))
            y_matrix[x, w] = f_values[x] ^ wx

    # Compute the matrix (-1) to the power of y
    matrix = (-1) ** y_matrix
    walsh_spectrum = np.sum(matrix, axis=0)

    return walsh_spectrum


def calculate_nonlinearity(walsh_spectrum):
    # Calculate the nonlinearity of a Boolean function based on its Walsh spectrum
    # The nonlinearity is defined as N/2 - max_abs_walsh / 2, where max_abs_walsh is the maximum absolute value in the Walsh spectrum
    max_abs_walsh = max(abs(val) for val in walsh_spectrum)
    nonlinearity = 2 ** n / 2 - max_abs_walsh / 2
    return nonlinearity


def calculate_sac(f):
    # Create a list of values for the function f from the bit string
    f_values = [int(bit) for bit in f]

    # Calculate the number of bits needed to represent the input space
    num_bits = int(np.log2(2 ** n))

    # Initialize the SAC matrix with zeros
    sac_matrix = np.zeros((2 ** n, num_bits), dtype=int)

    # Iterate over all possible inputs
    for x in range(2 ** n):
        # Iterate over each bit position
        for i in range(num_bits):
            t = 1 << i
            # Calculate XOR differences for pairs of inputs differing in a single bit
            xor_x_xort = f_values[x] ^ f_values[x ^ t]
            xor_x_x = f_values[x] ^ f_values[x]
            sac_matrix[x, i] = xor_x_xort - xor_x_x

    return sac_matrix


def calculate_sac_sum(sac_matrix):
    # Calculate the sum of 1s for each bit position in the SAC matrix
    # This represents the number of input pairs that differ in that specific bit position
    bit_sums = np.sum(sac_matrix == 1, axis=0)
    return bit_sums


def calculate_boolean_functions(Sbox, n):
    # Generate boolean functions from an S-box by extracting individual bits
    boolean_functions_sbox = [
        "".join(str((Sbox[x] >> i) & 1) for x in range(2 ** n)) for i in range(n)
    ]

    # Generate XOR combinations of boolean functions
    boolean_functions_combinations = []
    for i in range(n):
        for j in range(i + 1, n):
            xor_result = [str(int(boolean_functions_sbox[i][k]) ^ int(boolean_functions_sbox[j][k])) for k in
                          range(2 ** n)]
            boolean_functions_combinations.append(xor_result)

    # Combine individual boolean functions and XOR combinations
    boolean_functions = boolean_functions_sbox + boolean_functions_combinations

    return boolean_functions


def calnonlinearity(Sbox, n):
    # Calculate nonlinearity, SAC values, and print boolean functions for each function and BIC
    boolean_functions = calculate_boolean_functions(Sbox, n)
    for i in range(len(boolean_functions)):
        f = boolean_functions[i]

        # calculate_nonlinearity
        NL = calculate_nonlinearity(calculate_walsh_spectrum(f))
        ##        if i < n:
        ##            print(f"NL for function {i + 1}: {NL}")
        ##        else:
        ##            print(f"NL for BIC function {i + 1 - n}: {NL}")
        ##
        # SAC Matrix
        sac_matrix = calculate_sac(f)
        sac_bit_sums = calculate_sac_sum(sac_matrix)
        ##        if i < n:
        ##            print(f"Bit Sums for function {i + 1}: {sac_bit_sums/2**n}")
        ##        else:
        ##            print(f"Bit Sums for BIC function {i + 1 - n}: {sac_bit_sums/2**n}")
        ##
        # Boolean Function
        f_str = "".join(f)
    ##        if i < n:
    ##            print(f"Boolean Function for function {i + 1}: {f_str}")
    ##        else:
    ##            print(f"Boolean Function for BIC function {i + 1 - n}: {f_str}")
    ##
    ##        print("\n")

    # calculate Sbox_NL, BIC_NL
    # nonlinearities_1_to_n = [calculate_nonlinearity(calculate_walsh_spectrum(f)) for f in boolean_functions[:n]]
    # nonlinearities_n_to_end = [calculate_nonlinearity(calculate_walsh_spectrum(f)) for f in boolean_functions[n:]]
    #
    # total_nonlinearity_1_to_n = sum(nonlinearities_1_to_n)
    # Sbox_NL = total_nonlinearity_1_to_n / n
    #
    # total_nonlinearity_n_to_end = sum(nonlinearities_n_to_end)
    # BIC_NL = total_nonlinearity_n_to_end / (len(boolean_functions) - n)
    #
    # # calculate SAC_Value
    # sac_bit_sums_1_to_n = [calculate_sac_sum(calculate_sac(f)) for f in boolean_functions[:n]]
    # total_average_sac_bit_sums_1_to_n = sum(np.mean(sac_bit_sum) for sac_bit_sum in sac_bit_sums_1_to_n)
    # SAC_Value = total_average_sac_bit_sums_1_to_n / (n * 2 ** n)

    # calculate BIC_SAC_Value
    sac_bit_sums_n_to_end = [calculate_sac_sum(calculate_sac(f)) for f in boolean_functions[n:]]
    total_average_sac_bit_sums_n_to_end = sum(np.mean(sac_bit_sum) for sac_bit_sum in sac_bit_sums_n_to_end)
    BIC_SAC_Value = total_average_sac_bit_sums_n_to_end / ((len(boolean_functions) - n) * 2 ** n)

    return BIC_SAC_Value


# Function to calculate parameters for a given S-box
def calculate_parameters(Sbox, n):
    # FP, OFP = count_fixed_and_opposite_fixed_points(Sbox, n)
    BIC_SAC_Value = calnonlinearity(Sbox, n)
    # LP = lap(Sbox, n, n)
    # DP = cal_ddt(Sbox, n, n)
    # TO = calculate_TO(Sbox)
    ##    MTO = calculate_MTO(Sbox)
    RTO = calculate_RTO(Sbox)
    # MCC,CCV = confusion(Sbox)
    # SNR = calculate_SNR(Sbox)

    return  BIC_SAC_Value,RTO


def generate_ANF_properties(Sbox):
    M16 = np.array([
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        [0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1],
        [0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1],
        [0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1],
        [0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1],
        [0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 1, 0, 1],
        [0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1],
        [0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1],
        [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 1, 0, 1],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 1, 1],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1]
    ], dtype=int)

    def generate_next_M(M):
        # Generate a matrix with twice the size of the input matrix following the M(n) construction rule
        n = M.shape[0] * 2
        next_M = np.zeros((n, n), dtype=int)
        next_M[:n // 2, :n // 2] = M
        next_M[:n // 2, n // 2:] = M
        next_M[n // 2:, n // 2:] = M
        return next_M

    M32 = generate_next_M(M16)

    matrix_5x32 = np.zeros((5, 32), dtype=int)

    for col in range(32):
        sbox_value = Sbox[col]
        binary_value = bin(sbox_value)[2:].zfill(5)
        for row in range(5):
            matrix_5x32[row][col] = int(binary_value[row])

    matrix_5x32 = matrix_5x32[::-1]

    result_matrix = np.dot(matrix_5x32, M32)
    result_matrix[result_matrix % 2 == 0] = 0
    result_matrix[result_matrix % 2 != 0] = 1

    variables = ['x0', 'x1', 'x2', 'x3','x4' ]

    coefficients_matrix = result_matrix

    def index_to_term_with_parentheses(index, variables):
        term = []
        for i, var in enumerate(variables):
            if index & (1 << i):
                term.append(var)
        return '(' + ' & '.join(term) + ')' if term else '1'

    def generate_all_anf_expressions(coefficients_matrix, variables):
        expressions = []
        total_and = 0
        total_xor = 0
        for coefficients in coefficients_matrix:
            expression = ' ^ '.join(index_to_term_with_parentheses(i, variables) for i, coef in enumerate(coefficients) if coef)
            expressions.append(expression)
            total_and += expression.count('&')
            total_xor += expression.count('^')
        return total_and, total_xor

    return generate_all_anf_expressions(coefficients_matrix, variables)






from itertools import combinations


def boolean_to_decimal(boolean_function):
    return int(boolean_function, 2)

# Read the Boolean functions from the input file
with open("IdeaSAC55boolean.txt", "r") as file:
    functions = [line.strip() for line in file.readlines()]


# Output file name
output_file_name = "55Sbox.txt"

# Choose 5 Boolean functions to construct a 5x5 S-box
num_functions_to_choose = 5

# Generate all combinations of 5 Boolean functions
combinations_of_functions = combinations(functions, num_functions_to_choose)

# Open the output file
with open(output_file_name, 'w') as output_file:

    # Iterate through all combinations of 5 Boolean functions
    for index, selected_functions in enumerate(combinations_of_functions):

        # Construct the 5x5 S-box from the 5 selected coordinate functions
        result_array = []

        for i in range(32):
            # Collect the output bits of the 5 Boolean functions
            bits_at_position_i = [
                function[i] for function in selected_functions
            ]

            # Convert the 5-bit output vector to a decimal S-box value
            decimal_value = boolean_to_decimal(
                "".join(map(str, bits_at_position_i))
            )

            result_array.append(decimal_value)

        # Check whether the resulting 5x5 S-box is bijective
        is_unique = len(set(result_array)) == 32

        if not is_unique:
            continue

        # Calculate BIC-SAC
        BIC_SAC_Value = calnonlinearity(result_array, 5)

        print("S-box:", result_array)
        print("BIC-SAC:", BIC_SAC_Value)

        # Keep only S-boxes satisfying BIC-SAC = 0.5
        if BIC_SAC_Value==0.5:

            # Calculate ANF implementation cost
            andgate, xorgate = generate_ANF_properties(result_array)

            print("AND gates:", andgate)
            print("XOR gates:", xorgate)
            print("S-box:", result_array)

            # Save the valid S-box
            output_file.write(f"Sbox{index + 1}:\n")
            output_file.write(f"{result_array}\n")
            output_file.write(f"AND gates: {andgate}\n")
            output_file.write(f"XOR gates: {xorgate}\n\n")
