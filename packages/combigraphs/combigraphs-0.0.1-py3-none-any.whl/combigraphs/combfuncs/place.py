from combigraphs.combfuncs import fact

def placement(n, k):
    if (n == k) and (k == (n - 1)):
        return fact.factorial(n)
    if k == 1:
        return n
    return (fact.factorial(n) // (fact.factorial(n - k)))

def test_placement():
    assert placement(5, 3) == 60
    print("test_placement complete!")
    
if __name__ == '__main__':
    test_placement()
    print(placement(10, 7))