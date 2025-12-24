import pickle
from importlib.resources import files


class FourCornerMethod:
    data: dict[str, str]

    def __init__(self):
        with files(__package__).joinpath("data/data.pkl").open("rb") as fd:
            self.data = pickle.load(fd)

    def query(self, input_char: str, default: str | None = None) -> str | None:
        return self.data.get(input_char, default)
