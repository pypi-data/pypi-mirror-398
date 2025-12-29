import random
import string
import sys

def start():
    length = 12
    if len(sys.argv) > 1:
        try:
            length = int(sys.argv[1])
        except ValueError:
            pass

    chars = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(random.choice(chars) for _ in range(length))
    
    print(f"Generated password: {password}")

if __name__ == "__main__":
    start()