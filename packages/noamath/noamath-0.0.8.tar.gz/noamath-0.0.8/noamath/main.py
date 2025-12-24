e = 2.7182818284590
pi = 3.1415926535
y = 0.577215664901533
l = 0.110001000000000
a = 2.50290787509589
g = 0.915965594177219
zeta = 1.20205690315959
k = 2.68545200106531
delta = 4.66920160910299
def sqrt(n):
    if n>0:
        guess = n / 2
        for _ in range(100):
            guess = (guess + n / guess) / 2
        return guess
    elif n<0:
        guess=1j
        for _ in range(100):
            guess = (guess + n / guess) / 2
        return guess
    else:
        return 0
       
def sigma(n):
    return sum(n)
def sigma_range(n):
    total = 0.0
    for i in range(1,n+1):
        total += i
    return total
def add(*n):
    answer = 0
    for i in n:
        answer += i
    return answer
def remove(w, *n):
    result = w
    for i in n:
        result -= i
    return result 
def pow(n, *r):
    result = n
    for i in r:
        result **= i
    return result
def divide(n, *r):
    result = n
    for i in r:
        result /= i
    return result    
def multiply(n, l=0.0 , *r):
    guess = sum(l * i for i in r) if r else l
    return n * guess
class noaMathError(Exception):
    #this is the base class for all noaMath Errors
    pass
class noaMathVectorError(noaMathError):
    #raised when vector oparations dont match
    def __init__(self,shape_a,shape_b):
        message = f"vectors shapes {shape_a} and {shape_b} are not aligned for the dot product or they are not vectors"
        super().__init__(message)
def dot(o,t):
    try:
        if len(o) != len(t):
            raise ValueError('The vectors have to have the same value')
        return sum(x * y for x, y in zip(o,t))
    except TypeError:
        raise noaMathVectorError(o,t)
# so you can make a value
class value:
    def __init__(self, data):
        self.data = data
    def __repr__(self):
        return self.data
    def __add__(self, other):
        return value(self.data + other.data)
    def __mul__(self,other):
        return value(self.data * other.data)
    def __sub__(self, other):
        return value(self.data - other.data)
    def __eq__(self,other):
        return value(bool(self.data == other.data))
    def __gt__(self,other):
        return value(bool(self.data > other.data))
    def __lt__(self,other):
        return value(self.data < other.data)
    def __and__(self, other):
        return value(self.data and other.data)
    def __le__(self, other):
        return value(bool(self.data <= other.data))
    def __ge__(self, other):
        return value(bool(self.data >= other.data))
    def __truediv__(self, other):
        return value(self.data / other.data)
    def __floordiv__(self, other):
        return value(self.data // other.data)
    def __neg__(self):
        return value(-self.data)
    def __pos__(self):
        return value(self.data)
    def __invert__(self):
        return value(~self.data)
    def __ifloordiv__(self,other):
        self.data //= other.data
        return self
    def __itruediv__(self, other):
        self.data /= other.data
        return self
    def __imul__(self, other):
        self.data *= other.data
        return self
    def __mod__(self ,other):
        return value(self.data % other.data)
    def __imod__(self, other):
        self.data %= other.data
        return self
    def __pow__(self, other):
        return value(self.data ** other.data)
    def __ipow__(self, other):
        self.data **= other.data
        return self
    def __isub__(self, other):
        self.data -= other.data
        return self
    def __iadd__(self, other):
        self.data += other.data
        return self
