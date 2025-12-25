import base64
import random
import string
import time


def time_uuid() -> str:
    timestamp = int(time.time() * 1.0e6)
    rand = random.getrandbits(10)
    unique_value = (timestamp << 10) | rand  # Combine timestamp + random bits
    text = base64.urlsafe_b64encode(unique_value.to_bytes(8, "big")).decode().rstrip("=")
    return text.replace("-", "_")


def simple_uuid():
    """Generate a simple random UUID of 4 digits."""
    rnd_letter = random.choice(string.ascii_uppercase)  # ascii_letters
    rnd_num = random.randint(100, 999)
    return f"{rnd_letter}{rnd_num}"
