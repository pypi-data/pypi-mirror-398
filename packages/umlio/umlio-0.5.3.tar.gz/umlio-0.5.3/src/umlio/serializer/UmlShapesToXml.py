
from logging import Logger
from logging import getLogger

from pathlib import Path

from xml.etree.ElementTree import Element
from xml.etree.ElementTree import ElementTree
from xml.etree.ElementTree import SubElement

from xml.etree.ElementTree import indent as xmlIndent
from xml.etree.ElementTree import tostring as xmlToString
from xml.etree.ElementTree import fromstring as xmlFromString

from umlio.IOTypes import XML_VERSION
from umlio.IOTypes import UmlDocument

from umlio.serializer.UmlLinksToXml import UmlLinksToXml
from umlio.serializer.UmlNotesToXml import UmlNotesToXml
from umlio.serializer.UmlTextsToXml import UmlTextsToXml
from umlio.serializer.UmlClassToXml import UmlClassToXml
from umlio.serializer.UmlUseCasesToXml import UmlUseCasesToXml
from umlio.serializer.UmlLollipopsToXml import UmlLollipopsToXml

from umlio.XMLConstants import XmlConstants

INDENT_SPACES: str = '    '     # TODO: Make this configurable


class UmlShapesToXml:
    """
    The driver class to turn UML Shapes to XML
    """
    def __init__(self, projectFileName: Path, projectCodePath: Path):
        """
        Set up the XML Tree and the top level element

        Args:
            projectFileName:
            projectCodePath:
        """

        self.logger:           Logger = getLogger(__name__)
        self._projectCodePath: Path   = projectCodePath

        xmlProjectElement: Element = Element(XmlConstants.ELEMENT_UML_PROJECT)

        xmlProjectElement.set(XmlConstants.ATTRIBUTE_FILENAME, str(projectFileName))
        xmlProjectElement.set(XmlConstants.ATTRIBUTE_VERSION, XML_VERSION)
        xmlProjectElement.set(XmlConstants.ATTRIBUTE_CODE_PATH, str(projectCodePath))

        diagramTree: ElementTree = ElementTree(xmlProjectElement)

        xmlIndent(diagramTree, space='    ')

        self._diagramTree:       ElementTree = diagramTree
        self._xmlProjectElement: Element     = xmlProjectElement
        self._prettyPrint:       bool        = True

    @property
    def prettyPrint(self) -> bool:
        return self._prettyPrint

    @prettyPrint.setter
    def prettyPrint(self, prettyPrint: bool):
        self._prettyPrint = prettyPrint

    @property
    def xml(self) -> str:
        """

        Returns:  The serialized XML
        """
        if self.prettyPrint:
            return self._toPrettyString(self._xmlProjectElement)
        else:
            return self._toString(self._xmlProjectElement)

    def serialize(self, umlDiagram: UmlDocument):
        """
        Repeatedly call this method for each diagram in a UML project

        Args:
            umlDiagram:  The UML diagram to serialize

        """
        umlClassToXml:   UmlClassToXml    = UmlClassToXml()
        umlUseCaseToXml: UmlUseCasesToXml = UmlUseCasesToXml()
        umlNotesToXml:   UmlNotesToXml    = UmlNotesToXml()
        umlTextsToXml:   UmlTextsToXml    = UmlTextsToXml()
        umlLinksToXml:   UmlLinksToXml    = UmlLinksToXml()
        umlLollipopsToXml: UmlLollipopsToXml = UmlLollipopsToXml()

        documentElement: Element       = self._umlDocumentAttributesToXml(umlDiagram=umlDiagram)

        umlClassToXml.serialize(documentTop=documentElement, umlClasses=umlDiagram.umlClasses)
        umlUseCaseToXml.serialize(documentTop=documentElement, umlUseCases=umlDiagram.umlUseCases, umlActors=umlDiagram.umlActors)

        umlNotesToXml.serialize(documentTop=documentElement, umlNotes=umlDiagram.umlNotes)
        umlTextsToXml.serialize(documentTop=documentElement, umlTexts=umlDiagram.umlTexts)
        umlLinksToXml.serialize(documentTop=documentElement, umlLinks=umlDiagram.umlLinks)

        umlLollipopsToXml.serialize(documentTop=documentElement, umlLollipops=umlDiagram.umlLollipopInterfaces)

    def writeXml(self, fileName: Path):
        """
        Persist the XML

        Args:
            fileName:  The path object to the file
        """
        fileName.write_text(self.xml)

    def _umlDocumentAttributesToXml(self, umlDiagram: UmlDocument) -> Element:
        """
        Create a document sub element under the project element

        Args:
            umlDiagram:

        Returns:  The newly created document top sub element

        """

        attributes = {
            XmlConstants.ATTRIBUTE_DOCUMENT_TYPE:              umlDiagram.documentType.value,
            XmlConstants.ATTRIBUTE_TITLE:             umlDiagram.documentTitle,
            XmlConstants.ATTRIBUTE_SCROLL_POSITION_X: str(umlDiagram.scrollPositionX),
            XmlConstants.ATTRIBUTE_SCROLL_POSITION_Y: str(umlDiagram.scrollPositionY),
            XmlConstants.ATTRIBUTE_PIXELS_PER_UNIT_X: str(umlDiagram.pixelsPerUnitX),
            XmlConstants.ATTRIBUTE_PIXELS_PER_UNIT_Y: str(umlDiagram.pixelsPerUnitY),
        }
        documentTop: Element = SubElement(self._xmlProjectElement, XmlConstants.ELEMENT_UML_DIAGRAM, attrib=attributes)

        return documentTop

    def _toPrettyString(self, originalProjectElement: Element) -> str:
        """
        Create a copy of the input originalElement

        Convert to string, then parse again
        xmlToString() returns a binary, so we need to decode it to get a string

        Args:
            originalProjectElement:

        Returns:  An XML string
        """
        elementCopy: Element = xmlFromString(xmlToString(originalProjectElement))
        xmlIndent(elementCopy, space=INDENT_SPACES, level=0)

        return self._toString(elementCopy)

    def _toString(self, element: Element) -> str:
        return xmlToString(element, encoding='iso-8859-1', xml_declaration=True).decode('utf-8')
