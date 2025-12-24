
from pathlib import Path

from logging import Logger
from logging import getLogger

from zlib import decompress
from zlib import ZLIB_VERSION

from umlio.IOTypes import PROJECT_SUFFIX
from umlio.IOTypes import UmlProject
from umlio.IOTypes import XML_SUFFIX
from umlio.deserializer.XmlToUmlShapes import XmlToUmlShapes
from umlio.exceptions.UnsupportedFileTypeException import UnsupportedFileTypeException


class Reader:
    """
    """
    def __init__(self):

        self.logger: Logger = getLogger(__name__)

    def readProjectFile(self, fileName: Path) -> UmlProject:
        """
        Parse the input PROJECT_SUFFIX file

        Args:
            fileName: The fully qualified file name
        """
        suffix: str = fileName.suffix
        if len(suffix) < 0 or suffix != PROJECT_SUFFIX:
            raise UnsupportedFileTypeException(message=f'File does not end with {PROJECT_SUFFIX} suffix')

        rawXmlString: str = self._decompressFile(fileName=fileName)

        xmlToUmlShapes: XmlToUmlShapes = XmlToUmlShapes()

        xmlToUmlShapes.deserializeXml(xmlString=rawXmlString, fileName=fileName)

        return xmlToUmlShapes.umlProject

    def readXmlFile(self, fileName: Path) -> UmlProject:
        """
        Parse the input XML file;

        Args:
            fileName: Fully qualified file name
        """
        suffix: str = fileName.suffix
        if len(suffix) < 0 or suffix != XML_SUFFIX:
            raise UnsupportedFileTypeException(message=f'File does not end with .xml suffix')

        xmlToUmlShapes: XmlToUmlShapes = XmlToUmlShapes()

        xmlToUmlShapes.deserializeXmlFile(fileName=fileName)

        return xmlToUmlShapes.umlProject

    def _decompressFile(self, fileName: Path) -> str:
        """
        Decompresses a previously UML Diagrammer compressed file

        Args:
            fileName: Fully qualified file name with a PROJECT_SUFFIX suffix

        Returns:  A raw XML String
        """
        try:
            with open(fileName, "rb") as compressedFile:
                compressedData: bytes = compressedFile.read()
        except (ValueError, Exception) as e:
            self.logger.error(f'decompress open:  {e}')
            raise e
        else:
            self.logger.info(f'{ZLIB_VERSION=}')
            xmlBytes:  bytes = decompress(compressedData)  # has b`....` around it
            xmlString: str   = xmlBytes.decode()
            self.logger.debug(f'Document read:\n{xmlString}')

        return xmlString
