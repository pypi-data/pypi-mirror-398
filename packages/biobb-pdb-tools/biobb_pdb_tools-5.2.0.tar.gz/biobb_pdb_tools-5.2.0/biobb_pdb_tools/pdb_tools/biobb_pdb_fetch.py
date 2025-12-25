#!/usr/bin/env python3

"""Module containing the Pdbfetch class and the command line interface."""

from typing import Optional
from biobb_common.generic.biobb_object import BiobbObject
from biobb_common.tools import file_utils as fu
from biobb_common.tools.file_utils import launchlogger


class Pdbfetch(BiobbObject):
    """
    | biobb_pdb_tools Pdbfetch
    | Downloads a structure in PDB format from the RCSB website.
    | This tool downloads a structure in PDB format from the RCSB website. It can be used to download a structure in PDB format from the RCSB website.

    Args:
        output_file_path (str): PDB file of the protein selected. File type: output. `Sample file <https://raw.githubusercontent.com/bioexcel/biobb_pdb_tools/master/biobb_pdb_tools/test/reference/pdb_tools/ref_pdb_fetch.pdb>`_. Accepted formats: pdb (edam:format_1476).
        properties (dic):
            * **pdbid** (*string*) - ('1aki') ID of the protein.
            * **biounit** (*string*) - (False) Allows downloading the (first) biological structure if selected.
            * **binary_path** (*str*) - ("pdb_fetch") Path to the pdb_fetch executable binary.
            * **remove_tmp** (*bool*) - (True) [WF property] Remove temporal files.
            * **restart** (*bool*) - (False) [WF property] Do not execute if output files exist.

    Examples:
        This is a use example of how to use the building block from Python::

            from biobb_pdb_tools.pdb_tools.biobb_pdb_fetch import biobb_pdb_fetch

            prop = {
                'biounit': False,
                'pdbid': '1aki'
            }
            biobb_pdb_fetch(output_file_path='/path/to/file.pdb',
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

    def __init__(self, output_file_path, properties=None, **kwargs) -> None:
        properties = properties or {}

        super().__init__(properties)
        self.locals_var_dict = locals().copy()
        self.io_dict = {"out": {"output_file_path": output_file_path}}

        self.pdbid = properties.get("pdbid", "1aki")
        self.binary_path = properties.get("binary_path", "pdb_fetch")
        self.biounit = properties.get("biounit", False)
        self.properties = properties
        self.check_init(properties)

    @launchlogger
    def launch(self) -> int:
        """Execute the :class:`Pdbfetch <biobb_pdb_tools.pdb_tools.pdb_fetch>` object."""

        if self.check_restart():
            return 0
        instructions = []
        if self.biounit:
            instructions.append("-biounit")
            fu.log("Appending optional boolean property",
                   self.out_log, self.global_log)

        self.cmd = [
            self.binary_path,
            " ".join(instructions),
            self.pdbid,
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


def biobb_pdb_fetch(
    output_file_path: str, properties: Optional[dict] = None, **kwargs
) -> int:
    """Create :class:`Pdbfetch <biobb_pdb_tools.pdb_tools.pdb_fetch>` class and
    execute the :meth:`launch() <biobb_pdb_tools.pdb_tools.pdb_fetch.launch>` method."""
    return Pdbfetch(**dict(locals())).launch()


main = Pdbfetch.get_main(biobb_pdb_fetch, "Downloads a structure in PDB format from the RCSB website.")
biobb_pdb_fetch.__doc__ = Pdbfetch.__doc__

if __name__ == "__main__":
    main()
