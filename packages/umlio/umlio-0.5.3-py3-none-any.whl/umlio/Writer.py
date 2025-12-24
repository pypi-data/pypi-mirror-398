
from logging import Logger
from logging import getLogger
from pathlib import Path

from zlib import compress
from zlib import ZLIB_VERSION

from umlio.IOTypes import PROJECT_SUFFIX
from umlio.IOTypes import UmlProject
from umlio.IOTypes import XML_SUFFIX
from umlio.serializer.UmlShapesToXml import UmlShapesToXml


class Writer:
    """
    A shim on top of the UML serialization layer;
    The write only writes the latest XML version
    """

    def __init__(self):

        self.logger: Logger = getLogger(__name__)

    def writeFile(self, umlProject: UmlProject, fileName: Path):
        """
        Writes to a compressed project file file

        Args:
            umlProject: The project we have to serialize
            fileName:   Where to write the XML;  Should be a full qualified file name
        """
        if fileName.suffix != PROJECT_SUFFIX:
            fileName = fileName / PROJECT_SUFFIX

        umlShapesToXml: UmlShapesToXml = UmlShapesToXml(projectFileName=fileName, projectCodePath=umlProject.codePath)

        for umlDiagram in umlProject.umlDocuments.values():
            umlShapesToXml.serialize(umlDiagram=umlDiagram)

        rawXml: str = umlShapesToXml.xml

        self.logger.debug(f'{ZLIB_VERSION=}')
        byteText:        bytes  = rawXml.encode()
        compressedBytes: bytes = compress(byteText)

        fileName.write_bytes(compressedBytes)

    def writeXmlFile(self, umlProject: UmlProject, fileName: Path):
        """
        Writes to an XML file
        Args:
            umlProject:   The project we have to serialize
            fileName:     Where to write the XML;  Should be a full qualified file name
        """
        if fileName.suffix != XML_SUFFIX:
            fileName = fileName / XML_SUFFIX

        umlToXml: UmlShapesToXml = UmlShapesToXml(projectFileName=umlProject.fileName, projectCodePath=umlProject.codePath)

        for umlDiagram in umlProject.umlDocuments.values():
            umlToXml.serialize(umlDiagram=umlDiagram)

        umlToXml.writeXml(fileName=fileName)
