from silx.io.url import DataUrl


def get_url(my_str):
    if my_str in (None, ""):
        return None

    assert isinstance(my_str, str)
    if "@" in my_str:
        try:
            entry, file_path = my_str.split("@")
        except Exception:
            pass
        else:
            return DataUrl(file_path=file_path, data_path=entry, scheme="silx")
    else:
        try:
            url = DataUrl(path=my_str)
        except Exception:
            pass
        else:
            return url
    raise ValueError(f"unrecognized url {my_str}")
