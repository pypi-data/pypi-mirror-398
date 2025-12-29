from docstring_parser.common import DocstringExample as BaseDocstringExample


class DocstringExample:
    _example: BaseDocstringExample

    def __init__(self, example: BaseDocstringExample):
        self._example = example

        if example.description:
            lines = example.description.split("\n")
            description = []
            snippet = []

            for line in lines:
                stripped_line = line.strip()
                if stripped_line.startswith(">>>") or stripped_line.startswith("..."):
                    if stripped_line.startswith(">>>"):
                        snippet.append(line.replace(">>> ", "", 1).rstrip())
                    else:
                        snippet.append(line.replace("... ", "", 1).rstrip())
                else:
                    if line:
                        description.append(line)

            self._description = "\n".join(description)
            self._snippet = "\n".join(snippet)

    @property
    def description(self) -> str:
        return self._description

    @property
    def snippet(self) -> str:
        return self._snippet
