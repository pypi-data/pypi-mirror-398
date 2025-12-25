import math
import random

class Console:
    def log(self, *args):
        print(*args)

class Prompt:
    def __call__(self, message):
        return input(message)

class Const:
    def __setattr__(self, name, value):
        if name in self.__dict__:
            raise TypeError(f"Assignment to constant variable '{name}'")
        self.__dict__[name] = value

class Var:
    def __setattr__(self, name, value):
        self.__dict__[name] = value

class Let:
    def __setattr__(self, name, value):
        self.__dict__[name] = value

class JSMath:
    def __init__(self):
        self.PI = math.pi
        self.E = math.e

    def floor(self, x):
        return math.floor(x)
    
    def ceil(self, x):
        return math.ceil(x)
    
    def abs(self, x):
        return abs(x)
    
    def random(self):
        return random.random()
    
    def round(self, x):
        return int(x + 0.5) if x >= 0 else int(x - 0.5)
    
console = Console()
prompt = Prompt()
const = Const()
var = Var()
let = Let()
Math = JSMath()