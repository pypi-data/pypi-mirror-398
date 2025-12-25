from typing import Optional

from .base import Process


class WriteXasObject(
    Process,
    input_names=["xas_obj", "output_file"],
    output_names=["result"],
):
    @staticmethod
    def definition() -> str:
        return "write XAS object to a file"

    def run(self):
        xas_obj = self.getXasObject(xas_obj=self.inputs.xas_obj)
        xas_obj.to_file(self.output_file)
        self.outputs.result = self.output_file

    @property
    def output_file(self) -> Optional[str]:
        if self.missing_inputs.output_file:
            return None
        return self.inputs.output_file
