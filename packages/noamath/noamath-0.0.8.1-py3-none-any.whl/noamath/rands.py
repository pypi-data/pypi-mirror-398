import random
import numpy as np
class rand:
    @staticmethod
    def randint(start, end):
        return random.randint(start, end)
    @staticmethod
    def randfloat(start, end, flrange=None):
        if flrange==None:
            flrange=rand.randfloat.flrange
        a=str(rand.randint(start, end))+"."
        for i in range(flrange):
            a += str(rand.randint(0,9))
        return float(a)
    @staticmethod
    def randnp(*shape):
        return np.random.randn(*shape)
rand.randfloat.flrange=1

    
