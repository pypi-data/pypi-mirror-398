import random
import secrets
import string
import uuid


def generate_difficult_password(*, difficult: int = 1):
    # динамический диапазон длины
    base = 32 + difficult * 16  # минимальная длина
    variance = 64 + difficult * 32  # насколько может "гулять"
    target_len = random.randint(base, base + variance)

    alphabet = (
            string.ascii_letters +
            string.digits +
            string.punctuation
    )

    password = []

    # добавляем случайный шум из UUID блоков
    for _ in range(difficult * 2):
        noise_block = uuid.uuid4().hex
        password.append(noise_block)

    # основная часть пароля — криптостойкие символы
    for _ in range(target_len):
        password.append(secrets.choice(alphabet))

    # финальная перемешка обеспечивает нерегулярность структуры
    secrets.SystemRandom().shuffle(password)

    return "".join(password)


def __example():
    pass


if __name__ == '__main__':
    __example()
