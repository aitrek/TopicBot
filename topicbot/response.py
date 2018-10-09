"""Class to handle the output"""

from typing import Tuple, List, Union


class Response:

    def _export(self) -> Union[dict, List[dict], Tuple[dict]]:
        raise NotImplementedError

    def export(self) -> List[dict]:
        output = self._export()
        if isinstance(output, dict):
            return [output]
        elif isinstance(output, (list, tuple)):
            return output
        else:
            return []   # todo
