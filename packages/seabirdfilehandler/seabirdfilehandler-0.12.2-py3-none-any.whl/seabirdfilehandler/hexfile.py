from pathlib import Path

from seabirdfilehandler import DataFile, XMLCONFile


class HexFile(DataFile):
    """
    A representation of a .hex file as used by SeaBird.

    Parameters
    ----------
    path_to_file: Path | str:
        the path to the file
    """

    def __init__(
        self,
        path_to_file: Path | str,
        path_to_xmlcon: Path | str = "",
        *args,
        **kwargs,
    ):
        # force loading only metadata
        super().__init__(path_to_file, True)
        self.xmlcon = self.get_corresponding_xmlcon(path_to_xmlcon)

    def get_corresponding_xmlcon(
        self,
        path_to_xmlcon: Path | str = "",
    ) -> XMLCONFile | None:
        """
        Finds the best matching .xmlcon file inside the same directory.

        Parameters
        ----------
        path_to_xmlcon: Path | str:
            A fixed path to a xmlcon file. Will be checked.
        """
        # xmlcon path given, test and use it
        if isinstance(path_to_xmlcon, str):
            if path_to_xmlcon:
                return XMLCONFile(path_to_xmlcon)
        else:
            if path_to_xmlcon.exists():
                return XMLCONFile(path_to_xmlcon)
        # no xmlcon path, lets find one in the same dir
        # get all xmlcons in the dir
        xmlcons = [
            xmlcon
            for xmlcon in self.file_dir.glob("*.XMLCON", case_sensitive=False)
        ]
        if not xmlcons:
            return None
        # find excact match
        for xmlcon in xmlcons:
            if xmlcon.stem.lower() == self.file_name.lower():
                return XMLCONFile(xmlcon)
        # TODO:
        # otherwise, take the last fitting one in a sorted xmlcon list, or,
        # the one sharing the same prefix
        else:
            same_prefix_xmlcons = [
                xmlcon
                for xmlcon in xmlcons
                if self.file_name.lower().startswith(xmlcon.stem.lower()[:5])
            ]
            if not same_prefix_xmlcons:
                return None
            return XMLCONFile(same_prefix_xmlcons[0])
