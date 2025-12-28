def factorial(n):
    if n <= 1:
        return 1
    return factorial(n - 1) * n

def test_fact():
    assert factorial(5) == 120
    print("test_fact complete!")
    
if __name__ == '__main__':
    test_fact()