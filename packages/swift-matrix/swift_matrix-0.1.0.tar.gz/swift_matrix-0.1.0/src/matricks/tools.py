def normalize_hash(num: int) -> str:
    alphabet = 'abcdefghijklmnopqrstuvwxyz:/-.'
    result = ''
    while num > 0:
        result += alphabet[num % 30]
        num = num // 30
    return result[::-1]