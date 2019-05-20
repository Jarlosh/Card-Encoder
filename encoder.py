import os
import sys

from encoder_source.card import Card
from os.path import basename, join, splitext

in_dir = 'unencoded'
out_dir = 'encoded'
enc = 'utf-8'

packet_ext = '.pkt'
card_ext = '.txt'
encoder_version = 1


def to_bytes(integer: int, out_bytes_count: int) -> bytes:
    bits_to_encode = 8 * out_bytes_count
    if integer >= 2**bits_to_encode:
        raise IndexError(f'{integer} must be less than 2**{bits_to_encode}={2**bits_to_encode}')
    return integer.to_bytes(out_bytes_count, 'big')

# region Path stuff
def start_path(packet_name):
    return join(in_dir, packet_name)

def get_output_path(packet_name):
    return join(out_dir, packet_name + packet_ext)

def extend_path(path, *extension_tokens):
    return join(path, *extension_tokens)
# endregion


def read_card(path):
    card_name, _ = splitext(basename(path))
    with open(path, 'r', encoding='Utf-8') as f:
        lines = list(map(lambda line: line.strip(), f.readlines()))
        if len(lines) > 0:
            question = lines[0]
            tips = lines[1:]
            return Card(card_name, question, tips)
        else:
            raise EOFError(f'{path} file is empty!')


def extract_cards(packet_name):
    path = start_path(packet_name)
    stack = [path]
    result = []
    while len(stack):
        path = stack.pop()
        for child_name in os.listdir(path):
            child_path = extend_path(path, child_name)
            if os.path.isdir(child_path):
                stack.append(child_path)
            else:
                _, extension = os.path.splitext(child_path)
                if extension == card_ext:
                    card = read_card(child_path)
                    result.append(card)
    return result


def encode_card(card):
    version = to_bytes(encoder_version, 2)
    name = bytes(card.name, enc)
    question = bytes(card.question, enc)
    tips = [bytes(tip, enc) for tip in card.tips]

    name_len = to_bytes(len(name), 2)
    question_len = to_bytes(len(question), 2)
    t_lens = [to_bytes(len(tip), 3) for tip in tips]

    t_count = to_bytes(len(card.tips), 2)
    # byte format:
    # 2, 2, 2, 2, 3*, n, q, t*
    return bytes.join(b'', [version, name_len, question_len, t_count, *t_lens, name, question, *tips])


def make_packet(cards):
    c_count = to_bytes(len(cards), 3)
    enc_cards = [encode_card(card) for card in cards]

    c_enc_lens = [to_bytes(len(enc_c), 5) for enc_c in enc_cards]
    result = bytes.join(b'', [c_count, *c_enc_lens, *enc_cards])
    return result


def encode_packet(packet_name):
    in_path = start_path(packet_name)
    if not os.path.exists(in_path):
        raise EOFError(f"{start_path(packet_name)} doesn't exist")
    pkt = make_packet(extract_cards(packet_name))
    with open(get_output_path(packet_name), 'bw') as f:
        f.write(pkt)
        print('Encoded!')


def print_help():
    print(f'Encoder version: {encoder_version}.0')
    print(f'  Unencoded packet directories should lie in this_directory/{in_dir}/')
    print(f'  Card extension is {card_ext}')
    print('Usage:')
    script_name = 'encoder_source.py'
    commands = [
        ('PACKET_NAME', 'ENCODE'),
        ('-h', 'THIS DIALOGUE')
    ]
    hashtag_offset = max(map(lambda t: len(t[0]), commands)) + 3
    for com in commands:
        spaces = ' ' * (hashtag_offset - len(com[0]))
        print(f'  {script_name} {com[0]}{spaces}#{com[1]}')


if __name__ == '__main__':
    args = sys.argv
    args_len = len(args)
    if args_len > 1:
        if args[1] == '-h':
            print_help()
        elif args_len == 2:
            encode_packet(args[1])
