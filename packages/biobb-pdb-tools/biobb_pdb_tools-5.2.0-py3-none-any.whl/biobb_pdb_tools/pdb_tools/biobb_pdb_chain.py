#!/usr/bin/env python3

"""Module containing the Pdbchain class and the command line interface."""

from typing import Optional
from biobb_common.generic.biobb_object import BiobbObject
from biobb_common.tools import file_utils as fu
from biobb_common.tools.file_utils import launchlogger


class Pdbchain(BiobbObject):
    """
    | biobb_pdb_tools Pdbchain
    | Modifies the chain identifier column of a PDB file.
    | This tool modifies the chain identifier column of a PDB file. It can be used to change the chain identifier of a PDB file or to remove the chain identifier from a PDB file.

    Args:
        input_file_path (str): Input PDB file. File type: input. `Sample file <https://raw.githubusercontent.com/bioexcel/biobb_pdb_tools/master/biobb_pdb_tools/test/data/pdb_tools/1AKI.pdb>`_. Accepted formats: pdb (edam:format_1476).
        output_file_path (str): PDB file with selected modified chain. File type: output. `Sample file <https://raw.githubusercontent.com/bioexcel/biobb_pdb_tools/master/biobb_pdb_tools/test/reference/pdb_tools/ref_pdb_chain.pdb>`_. Accepted formats: pdb (edam:format_1476).
        properties (dic):
            * **chain** (*string*) - ('A') Modifies the chain identifier column of a PDB file.
            * **binary_path** (*str*) - ("pdb_chain") Path to the pdb_chain executable binary.
            * **remove_tmp** (*bool*) - (True) [WF property] Remove temporal files.
            * **restart** (*bool*) - (False) [WF property] Do not execute if output files exist.

    Examples:
        This is a use example of how to use the building block from Python::

            from biobb_pdb_tools.pdb_tools.biobb_pdb_chain import biobb_pdb_chain

            prop = {
                'chain': 'A'
            }
            biobb_pdb_chain(input_file_path='/path/to/input.pdb',
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

        self.binary_path = properties.get("binary_path", "pdb_chain")
        self.chain = properties.get("chain", False)
        self.properties = properties
        self.check_init(properties)

    @launchlogger
    def launch(self) -> int:
        """Execute the :class:`Pdbchain <biobb_pdb_tools.pdb_tools.pdb_chain>` object."""

        if self.check_restart():
            return 0
        self.stage_files()

        instructions = []
        if self.chain:
            instructions.append("-" + str(self.chain))
            fu.log("Appending optional boolean property", self.out_log, self.global_log)

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
            self.out_log, self.global_log)

        self.run_biobb()
        self.copy_to_host()
        self.remove_tmp_files()
        self.check_arguments(output_files_created=True, raise_exception=False)

        return self.return_code


def biobb_pdb_chain(
    input_file_path: str,
    output_file_path: str,
    properties: Optional[dict] = None,
    **kwargs,
) -> int:
    """Create :class:`Pdbchain <biobb_pdb_tools.pdb_tools.pdb_chain>` class and
    execute the :meth:`launch() <biobb_pdb_tools.pdb_tools.pdb_chain.launch>` method."""
    return Pdbchain(**dict(locals())).launch()


biobb_pdb_chain.__doc__ = Pdbchain.__doc__
main = Pdbchain.get_main(biobb_pdb_chain, "Modifies the chain identifier column of a PDB file.")

if __name__ == "__main__":
    main()
