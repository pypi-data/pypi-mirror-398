import json
from pathlib import Path
from platformdirs import user_data_dir

data_dir = Path(user_data_dir("ospm"))
config_filename = "config.json"


class Config:
    def __init__(self, from_file: bool = True):
        if not from_file:
            self.default_password_length = 16
        else:
            if not self.exists():
                self.init()
            with open(data_dir / config_filename, "r") as f:
                obj = json.loads(f.read())
                self.default_password_length = obj["default_password_length"]

    @classmethod
    def exists(cls) -> bool:
        return Path.exists(data_dir / config_filename)

    @classmethod
    def init(cls) -> None:
        if not Path.exists(data_dir):
            Path.mkdir(data_dir, parents=True)

        cls(from_file=False).save()

    def to_json(self) -> str:
        return json.dumps(self.__dict__())

    def save(self):
        with open(data_dir / config_filename, "w") as f:
            f.write(self.to_json())

    def __dict__(self) -> dict:
        return {
            "default_password_length": self.default_password_length
        }