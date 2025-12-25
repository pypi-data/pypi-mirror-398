from ewokscore.task import Task


class IgnoreOutput(Task, input_names=["xas_obj"]):
    """Simple Ignore task when an input is provided but no output. Used
    in the case of pure display widget.

    .. note::

        Each OW should define it own task to ensure a safe conversion to ewoks.
    """


class BlankTask(Task, input_names=["xas_obj"], output_names=["xas_obj"]):
    """Simple black task which will copy received xas_obj from inputs to
    outputs.

    .. note::

        Each OW should define it own task to ensure a safe conversion to ewoks.
    """

    def run(self):
        self.outputs.xas_obj = self.inputs.xas_obj


class IgnoreSavingPoint(BlankTask):
    pass


class IgnoreE0Calculation(BlankTask):
    pass
