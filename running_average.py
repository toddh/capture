class RunningAverage:
    def __init__(self):
        self.count = 0
        self.sum = 0

    def update(self, new_value):
        self.count += 1
        self.sum += new_value
        return self.sum / self.count
