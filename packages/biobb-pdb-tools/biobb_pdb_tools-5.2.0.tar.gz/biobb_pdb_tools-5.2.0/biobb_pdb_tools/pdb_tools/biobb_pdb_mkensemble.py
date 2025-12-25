#!/usr/bin/env python3

"""Module containing the Mkensemble class and the command line interface."""

import os
import zipfile
from pathlib import Path
from typing import Optional
from biobb_common.generic.biobb_object import BiobbObject
from biobb_common.tools import file_utils as fu
from biobb_common.tools.file_utils import launchlogger


class Mkensemble(BiobbObject):
    """
    | biobb_pdb_tools Mkensemble
    | Merges several PDB files into one multi-model (ensemble) file.
    | This tool merges several PDB files into one multi-model (ensemble) file. It can be used to merge several PDB files into one multi-model (ensemble) file.

    Args:
        input_file_path (str): Input ZIP file of selected proteins. File type: input. `Sample file <https://raw.githubusercontent.com/bioexcel/biobb_pdb_tools/master/biobb_pdb_tools/test/data/pdb_tools/input_pdb_mkensemble.zip>`_. Accepted formats: zip (edam:format_3987).
        output_file_path (str): Multi-model (ensemble) PDB file with input PDBs merged. File type: output. `Sample file <https://raw.githubusercontent.com/bioexcel/biobb_pdb_tools/master/biobb_pdb_tools/test/reference/pdb_tools/ref_pdb_mkensemble.pdb>`_. Accepted formats: pdb (edam:format_3987).
        properties (dic):
            * **binary_path** (*str*) - ("pdb_mkensemble") Path to the pdb_mkensemble executable binary.
            * **remove_tmp** (*bool*) - (True) [WF property] Remove temporal files.
            * **restart** (*bool*) - (False) [WF property] Do not execute if output files exist.

    Examples:
        This is a use example of how to use the building block from Python::

            from biobb_pdb_tools.pdb_tools.biobb_pdb_mkensemble import biobb_pdb_mkensemble

            biobb_pdb_mkensemble(input_file_path='/path/to/input1.zip',
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

        self.binary_path = properties.get("binary_path", "pdb_mkensemble")
        self.properties = properties
        self.check_init(properties)

    @launchlogger
    def launch(self) -> int:
        """Execute the :class:`Mkensemble <biobb_pdb_tools.pdb_tools.pdb_mkensemble>` object."""

        if self.check_restart():
            return 0
        self.stage_files()

        input_file_path = self.stage_io_dict["in"]["input_file_path"]
        folder_path = os.path.dirname(input_file_path)

        if zipfile.is_zipfile(input_file_path):
            with zipfile.ZipFile(input_file_path, "r") as zip_ref:
                zip_ref.extractall(folder_path)

            pdb_files = [
                file
                for file in os.listdir(folder_path)
                if file.lower().endswith(".pdb")
            ]

            input_file_list = [os.path.join(
                folder_path, file) for file in pdb_files]

            input_file_list = [Path(i) for i in input_file_list]
            input_file_list = sorted(
                input_file_list, key=lambda i: i.stem.upper())
            input_file_list = [str(i) for i in input_file_list]

            self.cmd = [
                self.binary_path,
                *input_file_list,
                ">",
                self.io_dict["out"]["output_file_path"],
            ]

        else:
            fu.log(
                f"The archive {input_file_path} is not a ZIP!",
                self.out_log,
                self.global_log,
            )

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


def biobb_pdb_mkensemble(
    input_file_path: str,
    output_file_path: str,
    properties: Optional[dict] = None,
    **kwargs,
) -> int:
    """Create :class:`Mkensemble <biobb_pdb_tools.pdb_tools.pdb_mkensemble>` class and
    execute the :meth:`launch() <biobb_pdb_tools.pdb_tools.pdb_mkensemble.launch>` method."""
    return Mkensemble(**dict(locals())).launch()


biobb_pdb_mkensemble.__doc__ = Mkensemble.__doc__
main = Mkensemble.get_main(biobb_pdb_mkensemble, "Merges several PDB files into one multi-model (ensemble) file.")

if __name__ == "__main__":
    main()
