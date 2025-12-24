import random


QUOTES = [
    "Be kind, for everyone you meet is fighting a hard battle.",
    "Empathy is seeing with the eyes of another, listening with the ears of another, and feeling with the heart of another.",
    "In a world where you can be anything, be kind.",
    "We rise by lifting others.",
    "Kindness is a language which the deaf can hear and the blind can see.",
]


ASCII_HEART = """
         ♥♥♥    ♥♥♥
       ♥♥   ♥♥♥♥   ♥♥
      ♥♥     ♥♥♥     ♥♥
      ♥♥             ♥♥
       ♥♥           ♥♥
         ♥♥       ♥♥
           ♥♥   ♥♥
             ♥♥♥
              ♥
"""


def main():
    quote = random.choice(QUOTES)
    print("\n" + "=" * 60)
    print(ASCII_HEART)
    print("\n💙 " + quote + "\n")
    print("=" * 60 + "\n")
