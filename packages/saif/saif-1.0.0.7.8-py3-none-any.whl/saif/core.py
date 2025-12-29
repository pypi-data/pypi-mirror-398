__version__ = "1.0.0.7.8"

class Love:
    def __init__(self):
        self.person = "Saif"
        self.love_for = "Myheer"
    
    def __str__(self):
        return f"{self.person} is in love with {self.love_for} ❤️"

def inLove():
    return True

def loveWithWhom():
    return "Myheer"

def get_version():
    return __version__