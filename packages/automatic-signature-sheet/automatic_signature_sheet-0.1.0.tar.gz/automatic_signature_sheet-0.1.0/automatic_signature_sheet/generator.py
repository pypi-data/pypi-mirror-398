# Copyright (c) 2025 Yoann Piétri
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT
"""
Module for the generator, generating a pdf from a list of persons.
"""

import os
import shutil
import tempfile
import subprocess
from typing import List
from pathlib import Path

import jinja2

from automatic_signature_sheet.reader import Person

DEFAULT_TITLE = "Signature sheet"  #: Default title of the signature sheet.
DEFAULT_SIZE = "50pt"  #: Default vertical size of each cell for the signature.

LATEX_TEMPLATE_LOCATION = (
    Path(__file__).parent / "latex_templates"
).absolute()  #: Location of the templates.

LATEX_JINJA_ENV = jinja2.Environment(
    block_start_string="\\BLOCK{",
    block_end_string="}",
    variable_start_string="\\VAR{",
    variable_end_string="}",
    comment_start_string="\\#{",
    comment_end_string="}",
    line_statement_prefix="%-",
    line_comment_prefix="%#",
    trim_blocks=True,
    autoescape=False,
    loader=jinja2.FileSystemLoader(LATEX_TEMPLATE_LOCATION),
)  #: Jinja environement for LaTeX.


def get_templates() -> List[str]:
    """Get the list of available templates.

    Returns:
        List[str]: list of available templates.
    """
    return LATEX_JINJA_ENV.list_templates()


def generate(
    persons: List[Person],
    title: str | None = None,
    output: os.PathLike | str = "signature-sheet.pdf",
    template_name: str = "default.tex",
    signature_size: str | None = None,
):
    """Generate the pdf signature sheet file from the list of persons.

    Args:
        persons (List[Person]): list of persons in the signature file.
        title (str | None, optional): title of the signature sheet. If None a default value will be used. Defaults to None.
        output (os.PathLike, optional): filename of the output pdf. Defaults to "signature-sheet.pdf".
        template_name (str, optional): template name, with extension. Defaults to "default.tex".
        signature_size (str | None, optional): size of the signature cell block. The unit may not be omitted. If None, a default value will be used. Defaults to None.

    Raises:
        RuntimeError: if the LaTeX compilation is unsuccessful.
    """
    output_file = Path(output)

    template = LATEX_JINJA_ENV.get_template(template_name)

    with tempfile.TemporaryDirectory() as tmpdirname:
        tmpdir = Path(tmpdirname)
        with open(tmpdir / "temp.tex", "w", encoding="utf8") as f:
            if title is None:
                title = DEFAULT_TITLE
            if signature_size is None:
                signature_size = DEFAULT_SIZE
            f.write(
                template.render(
                    persons=persons,
                    signature_size=signature_size,
                    title=title,
                )
            )

        result = subprocess.run(
            [
                "latexmk",
                "-synctex=1",
                "-interaction=nonstopmode",
                "-file-line-error",
                "-pdf",
                "-cd",
                f"-outdir={tmpdir}",
                tmpdir / "temp.tex",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            raise RuntimeError(
                f"LaTeX failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
            )

        shutil.move(tmpdir / "temp.pdf", output_file.absolute())
