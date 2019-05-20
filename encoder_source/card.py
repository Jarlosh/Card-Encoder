


class Card:
    def __init__(self, name, question, tips):
        self.name = name
        self.question = question
        self.tips = tips

    def __str__(self):
        return self.name

