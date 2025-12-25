from heaobject import root


class Record(root.AbstractDesktopObject):
    def __init__(self):
        super().__init__()

    @property
    def type_display_name(self) -> str:
        return "Record"
