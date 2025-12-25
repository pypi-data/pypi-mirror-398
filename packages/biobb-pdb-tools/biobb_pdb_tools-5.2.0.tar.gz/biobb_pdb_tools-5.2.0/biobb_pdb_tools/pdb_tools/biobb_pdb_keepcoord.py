#!/usr/bin/env python3

"""Module containing the Pdbkeepcoord class and the command line interface."""

from typing import Optional
from biobb_common.generic.biobb_object import BiobbObject
from biobb_common.tools import file_utils as fu
from biobb_common.tools.file_utils import launchlogger


class Pdbkeepcoord(BiobbObject):
    """
    | biobb_pdb_tools Pdbkeepcoord
    | Removes all non-coordinate records from the file.
    | Keeps only MODEL, ENDMDL, END, ATOM, HETATM, CONECT records from a PDB file.

    Args:
        input_file_path (str): Input PDB file. File type: input. `Sample file <https://raw.githubusercontent.com/bioexcel/biobb_pdb_tools/master/biobb_pdb_tools/test/data/pdb_tools/1AKI.pdb>`_. Accepted formats: pdb (edam:format_1476).
        output_file_path (str): PDB file with only coordinate records. File type: output. `Sample file <https://raw.githubusercontent.com/bioexcel/biobb_pdb_tools/master/biobb_pdb_tools/test/reference/pdb_tools/ref_pdb_keepcoord.pdb>`_. Accepted formats: pdb (edam:format_1476).
        properties (dic):
            * **binary_path** (*str*) - ("pdb_keepcoord") Path to the pdb_keepcoord executable binary.
            * **remove_tmp** (*bool*) - (True) [WF property] Remove temporal files.
            * **restart** (*bool*) - (False) [WF property] Do not execute if output files exist.

    Examples:
        This is a use example of how to use the building block from Python::

            from biobb_pdb_tools.pdb_tools.biobb_pdb_keepcoord import biobb_pdb_keepcoord

            # Keep only coordinate records
            biobb_pdb_keepcoord(input_file_path='/path/to/input.pdb',
                    output_file_path='/path/to/output.pdb')

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

        self.binary_path = properties.get("binary_path", "pdb_keepcoord")
        self.properties = properties
        self.check_init(properties)

    @launchlogger
    def launch(self) -> int:
        """Execute the :class:`Pdbkeepcoord <biobb_pdb_tools.pdb_tools.pdb_keepcoord>` object."""

        if self.check_restart():
            return 0
        self.stage_files()

        self.cmd = [
            self.binary_path,
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


def biobb_pdb_keepcoord(
    input_file_path: str,
    output_file_path: str,
    properties: Optional[dict] = None,
    **kwargs,
) -> int:
    """Create :class:`Pdbkeepcoord <biobb_pdb_tools.pdb_tools.pdb_keepcoord>` class and
    execute the :meth:`launch() <biobb_pdb_tools.pdb_tools.pdb_keepcoord.launch>` method."""

    return Pdbkeepcoord(**dict(locals())).launch()


biobb_pdb_keepcoord.__doc__ = Pdbkeepcoord.__doc__
main = Pdbkeepcoord.get_main(biobb_pdb_keepcoord, "Removes all non-coordinate records from the file. Keeps only MODEL, ENDMDL, END, ATOM, HETATM, CONECT records.")

if __name__ == "__main__":
    main()
