from collections import namedtuple

ImageFileObject = namedtuple("ImageFileObject", ["filename", "content", "content_type"])


__all__ = ["ImageFileObject"]
