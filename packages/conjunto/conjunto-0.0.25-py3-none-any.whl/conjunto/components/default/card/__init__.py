from tetra import BasicComponent


class Card(BasicComponent):
    tag = "div"
    _extra_context = "__all__"

    def _pre_load(self, form=None, *args, **kwargs) -> None:
        if form:
            self.tag = "form"
