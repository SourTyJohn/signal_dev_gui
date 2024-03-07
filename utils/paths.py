from os.path import join, dirname

ROOT_DIR = dirname(dirname(__file__))
TEMPLATE_DIR = join(
    ROOT_DIR, join("application", "templates")
)
IMAGES_DIR = join(
    ROOT_DIR, join("application", "images")
)
DATA_DIR = join(
    ROOT_DIR, "data"
)

__all__ = (
    "Path",
)


class Path:
    @classmethod
    def to_template(cls, file):
        return join(TEMPLATE_DIR, file)

    @classmethod
    def to_images(cls, file):
        return join(IMAGES_DIR, file)

    @classmethod
    def to_saved_data(cls, file='saved_data.json'):
        return join(DATA_DIR, file)
