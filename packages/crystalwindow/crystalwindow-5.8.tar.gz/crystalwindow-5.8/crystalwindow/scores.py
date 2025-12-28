class Score:
    def __init__(self, name: str, value: int = 0, max_value: int | None = None):
        self.name = name
        self.value = value
        self.max_value = max_value

    def __str__(self):
        return f"{self.name}: {self.value}"


    def score_up(self, amount: int = 1):
        self.value += amount
        if self.max_value is not None:
            self.value = min(self.value, self.max_value)

    def reset(self):
        self.value = 0

    def score_down(self, amount: int = 1):
        self.value = max(0, self.value - amount)

    def set_score(self, value: int):
        self.value = value
        if self.max_value is not None:
            self.value = min(self.value, self.max_value)
    def set_maxv(self, value: int):
        self.max_value = value
        if self.value > self.max_value:
            self.value = self.max_value            

def get_score(name: str, scores: list[Score]) -> Score | None:
    for score in scores:
        if score.name == name:
            return score
    return None