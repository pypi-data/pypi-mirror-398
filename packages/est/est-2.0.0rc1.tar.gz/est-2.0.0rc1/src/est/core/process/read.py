from ..io.information import InputInformation
from ..io.read_xas import read_from_input_information
from .base import Process


class ReadXasObject(
    Process,
    input_names=["input_information"],
    output_names=["xas_obj"],
):
    @staticmethod
    def definition() -> str:
        return "read XAS data from file"

    def run(self):
        self.setConfiguration(self.inputs.input_information)
        input_information = InputInformation.from_dict(self.inputs.input_information)
        xas_obj = read_from_input_information(input_information)
        self.outputs.xas_obj = xas_obj
