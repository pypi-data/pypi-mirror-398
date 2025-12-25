#!/usr/bin/env python3

"""Module containing the Pdbtofasta class and the command line interface."""

from typing import Optional
from biobb_common.generic.biobb_object import BiobbObject
from biobb_common.tools import file_utils as fu
from biobb_common.tools.file_utils import launchlogger


class Pdbtofasta(BiobbObject):
    """
    | biobb_pdb_tofasta Pdbtofasta
    | Extracts the residue sequence in a PDB file to FASTA format.
    | This tool extracts the residue sequence in a PDB file to FASTA format. It can be used to extract the sequence of a PDB file to FASTA format.

    Args:
        input_file_path (str): Input PDB file. File type: input. `Sample file <https://raw.githubusercontent.com/bioexcel/biobb_pdb_tools/master/biobb_pdb_tools/test/data/pdb_tools/1AKI.pdb>`_. Accepted formats: pdb (edam:format_1476).
        output_file_path (str): FASTA file containing the aminoacids sequence. File type: output. `Sample file <https://raw.githubusercontent.com/bioexcel/biobb_pdb_tools/master/biobb_pdb_tools/test/reference/pdb_tools/ref_pdb_tofasta.fasta>`_. Accepted formats: fasta (edam:format_1929), fa (edam:format_1929).
        properties (dic):
            * **multi** (*bool*) - (True) Splits the different chains into different records in the FASTA file.
            * **binary_path** (*str*) - ("pdb_tofasta") Path to the pdb_tofasta executable binary.
            * **remove_tmp** (*bool*) - (True) [WF property] Remove temporal files.
            * **restart** (*bool*) - (False) [WF property] Do not execute if output files exist.

    Examples:
        This is a use example of how to use the building block from Python::

            from biobb_pdb_tools.pdb_tools.biobb_pdb_tofasta import biobb_pdb_tofasta

            prop = {
                'multi': True
            }
            biobb_pdb_tofasta(input_file_path='/path/to/input.pdb',
                    output_file_path='/path/to/output.fasta',
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

        self.binary_path = properties.get("binary_path", "pdb_tofasta")
        self.multi = properties.get("multi", True)
        self.properties = properties
        self.check_init(properties)

    @launchlogger
    def launch(self) -> int:
        """Execute the :class:`Pdbtofasta <biobb_pdb_tools.pdb_tools.pdb_tofasta>` object."""

        if self.check_restart():
            return 0
        self.stage_files()

        instructions = []
        if self.multi:
            instructions.append("-multi")
            fu.log("Appending optional boolean property",
                   self.out_log, self.global_log)

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


def biobb_pdb_tofasta(
    input_file_path: str,
    output_file_path: str,
    properties: Optional[dict] = None,
    **kwargs,
) -> int:
    """Create :class:`Pdbtofasta <biobb_pdb_tools.pdb_tools.pdb_tofasta>` class and
    execute the :meth:`launch() <biobb_pdb_tools.pdb_tools.pdb_tofasta.launch>` method."""

    return Pdbtofasta(**dict(locals())).launch()


biobb_pdb_tofasta.__doc__ = Pdbtofasta.__doc__
main = Pdbtofasta.get_main(biobb_pdb_tofasta, "Extracts the residue sequence in a PDB file to FASTA format.")

if __name__ == "__main__":
    main()
