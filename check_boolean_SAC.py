#!/usr/bin/env python3
"""
Precisely analyze an n-variable Boolean function from a truth table of length 2^n bits.

The program computes:
- Weight and balancedness
- Maximum absolute Walsh coefficient and nonlinearity
- All SAC values for individual input variables
- Algebraic degree deg(f) and the number of monomials in the ANF
- Algebraic Immunity AI(f), computed exactly over GF(2)
- Autocorrelation spectrum and the absolute indicator Delta_f
- Sum-of-squares indicator sigma_f
- Nonzero linear structures a satisfying D_a f = 0 or D_a f = 1

Truth-table convention:
    f(0), f(1), ..., f(2^n - 1)
In the index representation, x1 is the least significant bit (LSB).

Notes:
- Walsh, SAC, ANF, and autocorrelation computations are fast for moderate n.
- AI is computed exactly using linear algebra over GF(2), so it may become slow
  and memory-intensive for large n. The case n=8 is very lightweight.
"""

from __future__ import annotations

import math
import re
from itertools import combinations


EPSILON = 1e-15


def parse_number_of_variables(text: str) -> int:
    """Parse and validate the number of variables n."""
    try:
        n = int(text.strip())
    except ValueError as exc:
        raise ValueError("n phải là một số nguyên.") from exc

    if n < 1:
        raise ValueError("n phải lớn hơn hoặc bằng 1.")
    if n > 20:
        raise ValueError(
            "n quá lớn cho chương trình phân tích chính xác này. "
            "Hãy dùng n <= 20; riêng AI có thể chậm từ n khoảng 12 trở lên."
        )
    return n


def parse_truth_table(text: str, n: int) -> list[int]:
    """
    Parse a 2^n-bit truth table.

    A contiguous bit string is accepted, as well as input separated by whitespace,
    line breaks, commas, or semicolons.
    """
    expected_size = 1 << n
    cleaned = text.strip().strip("'\"")
    cleaned = re.sub(r"[\s,;]+", "", cleaned)

    if not re.fullmatch(rf"[01]{{{expected_size}}}", cleaned):
        raise ValueError(
            f"Bảng chân trị phải chứa đúng {expected_size} bit 0/1 "
            f"cho hàm {n} biến; hiện nhận được {len(cleaned)} ký tự sau khi làm sạch."
        )

    return [int(bit) for bit in cleaned]


def fwht(values: list[int]) -> list[int]:
    """Compute the unnormalized Fast Walsh-Hadamard Transform."""
    result = values.copy()
    size = len(result)
    step = 1

    while step < size:
        block_size = step << 1
        for start in range(0, size, block_size):
            for offset in range(step):
                left = result[start + offset]
                right = result[start + step + offset]
                result[start + offset] = left + right
                result[start + step + offset] = left - right
        step <<= 1

    return result


def walsh_spectrum(table: list[int]) -> list[int]:
    """Compute the Walsh spectrum W_f(w)."""
    signs = [1 if bit == 0 else -1 for bit in table]
    return fwht(signs)


def nonlinearity_from_walsh(walsh: list[int], n: int) -> int:
    """NL(f) = 2^(n-1) - max|W_f|/2."""
    max_abs_walsh = max(abs(value) for value in walsh)
    return (1 << (n - 1)) - max_abs_walsh // 2


def sac_values(table: list[int], n: int) -> tuple[list[int], list[float]]:
    """
    Compute SAC along the coordinate directions e_i.

    Returns:
    - the number of output changes over all 2^n inputs;
    - the corresponding change probabilities.
    """
    size = len(table)
    change_counts: list[int] = []
    probabilities: list[float] = []

    for bit in range(n):
        direction = 1 << bit
        changed = sum(table[x] ^ table[x ^ direction] for x in range(size))
        change_counts.append(changed)
        probabilities.append(changed / size)

    return change_counts, probabilities


def anf_coefficients(table: list[int], n: int) -> list[int]:
    """Apply the Möbius transform over GF(2) to obtain the ANF coefficients."""
    coefficients = table.copy()
    size = len(coefficients)

    for bit in range(n):
        mask = 1 << bit
        for index in range(size):
            if index & mask:
                coefficients[index] ^= coefficients[index ^ mask]

    return coefficients


def algebraic_degree_from_anf(coefficients: list[int]) -> int:
    """Return the maximum algebraic degree among monomials with coefficient 1."""
    return max(
        (mask.bit_count() for mask, coefficient in enumerate(coefficients) if coefficient),
        default=0,
    )


def autocorrelation_from_walsh(walsh: list[int]) -> list[int]:
    """
    Compute AC_f(a) using the Wiener-Khinchin relation:
        AC_f = FWHT(W_f^2) / 2^n.
    """
    size = len(walsh)
    transformed = fwht([value * value for value in walsh])

    autocorrelation: list[int] = []
    for value in transformed:
        if value % size != 0:
            raise ArithmeticError("Phổ tự tương quan không nguyên; có lỗi tính toán.")
        autocorrelation.append(value // size)

    return autocorrelation


def find_linear_structures_from_autocorrelation(
    autocorrelation: list[int],
) -> tuple[list[int], list[int]]:
    """
    For a != 0:
    - AC_f(a) = +2^n when D_a f = 0;
    - AC_f(a) = -2^n when D_a f = 1.
    """
    size = len(autocorrelation)
    zero_structures = [
        direction
        for direction in range(1, size)
        if autocorrelation[direction] == size
    ]
    one_structures = [
        direction
        for direction in range(1, size)
        if autocorrelation[direction] == -size
    ]
    return zero_structures, one_structures


def monomial_masks_up_to_degree(n: int, degree: int) -> list[int]:
    """List all monomials whose degree does not exceed degree."""
    masks = [0]  # constant monomial 1

    for current_degree in range(1, degree + 1):
        for variables in combinations(range(n), current_degree):
            mask = 0
            for variable in variables:
                mask |= 1 << variable
            masks.append(mask)

    return masks


def gf2_rank_bitrows(rows: list[int]) -> int:
    """
    Compute the rank of a binary matrix.

    Each row is stored as a Python integer, with each bit representing one GF(2) element.
    """
    basis: dict[int, int] = {}

    for row in rows:
        value = row
        while value:
            pivot = value.bit_length() - 1
            existing = basis.get(pivot)

            if existing is None:
                basis[pivot] = value
                break
            value ^= existing

    return len(basis)


def evaluation_row(x: int, monomial_masks: list[int]) -> int:
    """Construct the evaluation row for all monomials at point x."""
    row = 0

    for column, monomial_mask in enumerate(monomial_masks):
        if (x & monomial_mask) == monomial_mask:
            row |= 1 << column

    return row


def annihilator_nullity(
    constrained_points: list[int],
    monomial_masks: list[int],
) -> int:
    """Return the dimension of the polynomial space annihilating constrained_points."""
    rows = [evaluation_row(x, monomial_masks) for x in constrained_points]
    rank = gf2_rank_bitrows(rows)
    return len(monomial_masks) - rank


def algebraic_immunity(table: list[int], n: int) -> tuple[int, str, int, int]:
    """
    Compute AI(f) exactly.

    AI(f) is the minimum degree of a nonzero g such that f*g = 0 or (f xor 1)*g = 0.
    """
    support_f = [x for x, value in enumerate(table) if value == 1]
    support_complement = [x for x, value in enumerate(table) if value == 0]

    # General upper bound: AI(f) <= ceil(n/2).
    maximum_degree_to_test = math.ceil(n / 2)

    for degree in range(maximum_degree_to_test + 1):
        monomial_masks = monomial_masks_up_to_degree(n, degree)
        nullity_f = annihilator_nullity(support_f, monomial_masks)
        nullity_complement = annihilator_nullity(
            support_complement,
            monomial_masks,
        )

        if nullity_f > 0 or nullity_complement > 0:
            if nullity_f > 0 and nullity_complement > 0:
                side = "Ann(f) và Ann(f⊕1)"
            elif nullity_f > 0:
                side = "Ann(f)"
            else:
                side = "Ann(f⊕1)"

            return degree, side, nullity_f, nullity_complement

    raise RuntimeError("Không tìm thấy annihilator trong cận AI lý thuyết.")


def format_direction(direction: int, n: int) -> str:
    """Format direction a in hexadecimal and as the binary vector xn...x1."""
    hexadecimal_digits = max(1, (n + 3) // 4)
    return (
        f"0x{direction:0{hexadecimal_digits}X} "
        f"({direction:0{n}b})"
    )


def print_report(table: list[int], n: int) -> None:
    """Compute and print the complete analysis report."""
    size = 1 << n
    weight = sum(table)
    balanced = weight * 2 == size

    walsh = walsh_spectrum(table)
    max_abs_walsh = max(abs(value) for value in walsh)
    nonlinearity = nonlinearity_from_walsh(walsh, n)

    change_counts, sac = sac_values(table, n)
    exact_sac = all(count * 2 == size for count in change_counts)
    sac_average = sum(sac) / n
    sac_mean_absolute_error = sum(abs(value - 0.5) for value in sac) / n
    sac_max_error = max(abs(value - 0.5) for value in sac)

    anf = anf_coefficients(table, n)
    degree = algebraic_degree_from_anf(anf)
    number_of_anf_terms = sum(anf)

    if n >= 12:
        print(
            "\nĐang tính AI chính xác. Với n lớn, bước này có thể cần nhiều "
            "thời gian và bộ nhớ...",
            flush=True,
        )
    ai, ai_side, nullity_f, nullity_complement = algebraic_immunity(table, n)

    autocorrelation = autocorrelation_from_walsh(walsh)
    delta_f = max((abs(value) for value in autocorrelation[1:]), default=0)
    sigma_f = sum(value * value for value in autocorrelation)
    zero_structures, one_structures = find_linear_structures_from_autocorrelation(
        autocorrelation
    )
    has_nonzero_linear_structure = bool(zero_structures or one_structures)

    print("\n" + "=" * 78)
    print(f"KẾT QUẢ PHÂN TÍCH HÀM BOOLEAN {n} BIẾN")
    print("=" * 78)
    print(f"Số biến n                       : {n}")
    print(f"Độ dài bảng chân trị           : {size}")
    print(f"Weight                          : {weight}")
    print(f"Balanced                        : {'Có' if balanced else 'Không'}")

    print("\nNONLINEARITY VÀ PHỔ WALSH")
    print("-" * 78)
    print(f"max |W_f(w)|                    : {max_abs_walsh}")
    print(f"Nonlinearity NL(f)              : {nonlinearity}")

    print("\nSTRICT AVALANCHE CRITERION")
    print("-" * 78)
    print("Biến     Số lần đổi/2^n       SAC_i        |SAC_i - 0.5|")
    for index, (count, value) in enumerate(zip(change_counts, sac), start=1):
        print(
            f"x{index:<3}     {count:>7}/{size:<7}   "
            f"{value:>12.10f}   {abs(value - 0.5):>14.10f}"
        )

    print(f"SAC trung bình                  : {sac_average:.10f}")
    print(f"mean_i |SAC_i - 0.5|            : {sac_mean_absolute_error:.10f}")
    print(f"max_i  |SAC_i - 0.5|            : {sac_max_error:.10f}")
    print(f"Exact SAC cho mọi biến          : {'Có' if exact_sac else 'Không'}")

    print("\nCÁC CHỈ TIÊU ĐẠI SỐ VÀ TỰ TƯƠNG QUAN")
    print("-" * 78)
    print(f"Algebraic degree deg(f)         : {degree}")
    print(f"Số monomial trong ANF           : {number_of_anf_terms}")
    print(f"Algebraic Immunity AI(f)        : {ai}")
    print(f"AI tối đa lý thuyết ceil(n/2)   : {math.ceil(n / 2)}")
    print(f"Annihilator xuất hiện ở         : {ai_side}")
    print(f"Nullity Ann(f), tại bậc AI      : {nullity_f}")
    print(f"Nullity Ann(f⊕1), tại bậc AI    : {nullity_complement}")
    print(f"Absolute indicator Delta_f      : {delta_f}")
    print(f"Delta_f / 2^n                   : {delta_f / size:.10f}")
    print(f"Sum-of-squares sigma_f          : {sigma_f}")

    print("\nLINEAR STRUCTURES")
    print("-" * 78)
    print(
        "Có nonzero linear structure     : "
        + ("Có" if has_nonzero_linear_structure else "Không")
    )

    if zero_structures:
        print("Các a != 0 với D_a f = 0:")
        for start in range(0, len(zero_structures), 8):
            block = zero_structures[start:start + 8]
            print("  " + ", ".join(format_direction(a, n) for a in block))

    if one_structures:
        print("Các a != 0 với D_a f = 1:")
        for start in range(0, len(one_structures), 8):
            block = one_structures[start:start + 8]
            print("  " + ", ".join(format_direction(a, n) for a in block))

    if not has_nonzero_linear_structure:
        print("Kết luận                       : Không có nonzero linear structure.")

    print("=" * 78)


def main() -> None:
    print("PHÂN TÍCH HÀM BOOLEAN n BIẾN")
    print("Quy ước: bảng chân trị theo thứ tự f(0), f(1), ..., f(2^n - 1).")
    print("x1 là bit thấp nhất (LSB).\n")

    try:
        n = parse_number_of_variables(input("Nhập số biến n: "))
        expected_size = 1 << n
        print(f"Nhập bảng chân trị gồm đúng {expected_size} bit 0/1.")
        print("Có thể dùng chuỗi liền hoặc phân cách bằng dấu cách/dấu phẩy.")
        truth_table_text = input("Truth table: ")
        table = parse_truth_table(truth_table_text, n)
        print_report(table, n)
    except (ValueError, RuntimeError, ArithmeticError) as error:
        raise SystemExit(f"\nLỗi: {error}") from error


if __name__ == "__main__":
    main()
