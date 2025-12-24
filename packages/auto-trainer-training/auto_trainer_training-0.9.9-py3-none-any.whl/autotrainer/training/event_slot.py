class EventSlot:
    def __init__(self):
        self.targets = []

    def __iadd__(self, f):
        self.targets.append(f)
        return self

    def __isub__(self, f):
        while f in self.targets:
            self.targets.remove(f)
        return self

    def __len__(self):
        return len(self.targets)

    def __iter__(self):
        def gen():
            for target in self.targets:
                yield target
        return gen()

    def __getitem__(self, key):
        return self.targets[key]
