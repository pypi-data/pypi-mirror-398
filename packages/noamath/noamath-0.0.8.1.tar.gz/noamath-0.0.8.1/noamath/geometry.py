from .main import pi
def sqrt(n):
    guess = n/2
    for i in range(100):
        guess=(guess + guess/n)/2
    return guess
def circleArea(r):
    return pi * r ** 2
def squareArea(s):
    return s**2
def rectArea(s1,s2):
    return s1 * s2
def triangleArea(a,b,c):
    s=(a+b+c)/2
    return sqrt(s*(s-a)*(s-b)*(s-c))
