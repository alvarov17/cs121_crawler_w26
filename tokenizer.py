# Tokenizer from A1

import sys

# Important to keep in mind with this implementation:
# I chose to determine if a sequence is valid by using the individual
# ASCII value of each character
# Due to the vagueness of the instructions, what I did was only use
# the A-Z, a-z, and 0-9 ASCII values for validation.
# Anything else will be considered delimiters
# This tokenizer separates hyphenated words and makes two
# separate tokens from them along with those with an apostrophe.
# Examples: Jinx's -> Jinx's(1), built-in -> built-in(1) if hyphen is the one from the ASCII family
# Helдlo -> Hel(1) lo(2)

class Token:
    """
    Token class
    Each word in the given file will be an alphanumeric sequence of characters
    """
    def __init__(self, data: str):
        self.data = data

    def get_data(self) -> str:
        """
        Accessor method that returns the token's value

        :return: str

        Time Complexity: O(1)
        """
        return self.data


def tokenize(content: list[str]) -> list[Token] | None:
    """
    Method that turns each word in the given file into a token.
    Takes the filename, opens it, and uses list comprehension to create a list of tokens.

    :param file: str
    :return: list or None

    Time Complexity: O(n)
    """
    # try:
    tokens = []
    current = []
    for item in content:
        # print(line)
        if not item:
            break
        for ch in item:
            if 'A' <= ch <= 'Z' or 'a' <= ch <= 'z' or '0' <= ch <= '9' or ch == '\'' or ch == '-':
                current.append(ch.lower())
            else:
                if current:
                    tokens.append(Token(''.join(current)))
                    current = []
        if current:
            tokens.append(Token(''.join(current)))
    return tokens

    # except FileNotFoundError:
    #     print("")
    #     return None

def compute_word_frequencies(tokens: list[Token]) -> dict:
    """
    Method that computes the frequencies of each token's value

    Takes a list of tokens and iterates through them, computing frequencies using a
    dictionary. Key = token's value. Value = integer representing frequency

    :param tokens: list[Token]
    :return: dict

    Time Complexity: O(n)
    """
    freq = {}
    for token in tokens:
        if token.data.lower() in freq:
            freq[token.data.lower()] += 1
        else:
            freq[token.data.lower()] = 1
    return freq

# def print_frequencies(tokens: dict):
#     """
#     Method that prints the frequencies of tokens

#     Takes a dictionary, prints the key, value pairs

#     :param tokens: dict
#     :return: None

#     Time Complexity: O(n)
#     """
#     sorted_tokens = dict(sorted(tokens.items(), key = lambda item: item[1], reverse=True))
#     for key, value in sorted_tokens.items():
#         if value:
#             print(f'{key} -> {value}')

# def main() -> None:
#     """
#     Main method
#     :return: None
#     """
#     if len(sys.argv) < 2:
#         print("No filename provided")
#     else:
#         filename = sys.argv[1]
#         tokens = tokenize(filename)
#         token_freq = compute_word_frequencies(tokens)
#         print_frequencies(token_freq)

# if __name__ == "__main__":
#     main()
