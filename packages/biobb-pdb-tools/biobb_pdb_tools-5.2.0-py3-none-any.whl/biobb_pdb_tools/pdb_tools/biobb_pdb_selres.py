#!/usr/bin/env python3

"""Module containing the Pdbselres class and the command line interface."""

from typing import Optional
from biobb_common.generic.biobb_object import BiobbObject
from biobb_common.tools import file_utils as fu
from biobb_common.tools.file_utils import launchlogger


class Pdbselres(BiobbObject):
    """
    | biobb_pdb_tools Pdbselres
    | Selects residues by their index, piecewise or in a range.
    | Works by selecting residues based on their index. Can select individual residues, a range of residues, or residues at regular intervals.

    Args:
        input_file_path (str): Input PDB file. File type: input. `Sample file <https://raw.githubusercontent.com/bioexcel/biobb_pdb_tools/master/biobb_pdb_tools/test/data/pdb_tools/1IGY.pdb>`_. Accepted formats: pdb (edam:format_1476).
        output_file_path (str): PDB file with selected residues. File type: output. `Sample file <https://raw.githubusercontent.com/bioexcel/biobb_pdb_tools/master/biobb_pdb_tools/test/reference/pdb_tools/ref_pdb_selres.pdb>`_. Accepted formats: pdb (edam:format_1476).
        properties (dic):
            * **selection** (*string*) - (None) Residue selection format: individual residues "1,2,4,6", range "1:10", multiple ranges "1:10,20:30", open ranges "1:", ":5", or intervals "::5", "1:10:5".
            * **binary_path** (*str*) - ("pdb_selres") Path to the pdb_selres executable binary.
            * **remove_tmp** (*bool*) - (True) [WF property] Remove temporal files.
            * **restart** (*bool*) - (False) [WF property] Do not execute if output files exist.

    Examples:
        This is a use example of how to use the building block from Python::

            from biobb_pdb_tools.pdb_tools.biobb_pdb_selres import biobb_pdb_selres

            prop = {
                'selection': '1:20:2'
            }
            biobb_pdb_selres(input_file_path='/path/to/input.pdb',
                    output_file_path='/path/to/output.pdb',
                    properties=prop)

    Info:
        * wrapped_software:
            * name: pdb_tools
            * version: >=2.5.0
            * license: Apache-2.0
        * ontology:
            * name: EDAM
            * schema: http://edamontology.org/EDAM.owl

    """

    def __init__(
        self, input_file_path, output_file_path, properties=None, **kwargs
    ) -> None:
        properties = properties or {}

        super().__init__(properties)
        self.locals_var_dict = locals().copy()

        self.io_dict = {
            "in": {"input_file_path": input_file_path},
            "out": {"output_file_path": output_file_path},
        }

        self.binary_path = properties.get("binary_path", "pdb_selres")
        self.selection = properties.get("selection", None)
        self.properties = properties
        self.check_init(properties)

    @launchlogger
    def launch(self) -> int:
        """Execute the :class:`Pdbselres <biobb_pdb_tools.pdb_tools.pdb_selres>` object."""

        if self.check_restart():
            return 0
        self.stage_files()

        instructions = []
        if self.selection:
            instructions.append("-" + str(self.selection))
            fu.log("Selecting residues with pattern: " + self.selection, self.out_log, self.global_log)

        self.cmd = [
            self.binary_path,
            " ".join(instructions),
            self.stage_io_dict["in"]["input_file_path"],
            ">",
            self.io_dict["out"]["output_file_path"],
        ]

        fu.log(" ".join(self.cmd), self.out_log, self.global_log)

        fu.log(
            "Creating command line with instructions and required arguments",
            self.out_log,
            self.global_log,
        )

        self.run_biobb()
        self.copy_to_host()
        self.remove_tmp_files()
        self.check_arguments(output_files_created=True, raise_exception=False)

        return self.return_code


def biobb_pdb_selres(
    input_file_path: str,
    output_file_path: str,
    properties: Optional[dict] = None,
    **kwargs,
) -> int:
    """Create :class:`Pdbselres <biobb_pdb_tools.pdb_tools.pdb_selres>` class and
    execute the :meth:`launch() <biobb_pdb_tools.pdb_tools.pdb_selres.launch>` method."""

    return Pdbselres(**dict(locals())).launch()


biobb_pdb_selres.__doc__ = Pdbselres.__doc__
main = Pdbselres.get_main(biobb_pdb_selres, "Selects residues by their index, piecewise or in a range.")

if __name__ == "__main__":
    main()
