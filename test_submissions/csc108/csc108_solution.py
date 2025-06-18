def fizzbuzz(n: int) -> list:
    """
    Generates the FizzBuzz sequence from 1 to n.

    For each number in the range 1 to n (inclusive):
    - If divisible by 3, returns 'Fizz'
    - If divisible by 5, returns 'Buzz'
    - If divisible by both 3 and 5, returns 'FizzBuzz'
    - Otherwise, returns the number itself

    Args:
        n (int): The upper limit of the range (inclusive).

    Returns:
        list: A list containing the FizzBuzz results from 1 to n.

    >>> fizzbuzz(5)
    [1, 2, 'Fizz', 4, 'Buzz']

    >>> fizzbuzz(15)
    [1, 2, 'Fizz', 4, 'Buzz', 'Fizz', 7, 8, 'Fizz', 'Buzz', 
    11, 'Fizz', 13, 14, 'FizzBuzz']
    """
    result = []
    for i in range(1, n + 1):
        output = ''
        if i % 3 == 0:
            output += 'Fizz'
        if i % 5 == 0:
            output += 'Buzz'
        result.append(output or i)
    return result
