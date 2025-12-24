
from typing import Dict
from typing import List
from typing import NewType

from enum import Enum

from dataclasses import dataclass
from dataclasses import field

from pathlib import Path

from untangle import Element

from codeallybasic.SecureConversions import SecureConversions

from umlshapes.shapes.UmlActor import UmlActor
from umlshapes.shapes.UmlClass import UmlClass
from umlshapes.shapes.UmlNote import UmlNote
from umlshapes.shapes.UmlText import UmlText
from umlshapes.shapes.UmlUseCase import UmlUseCase
from umlshapes.links.UmlLollipopInterface import UmlLollipopInterface

from umlshapes.links.UmlLink import UmlLink
from umlshapes.types.UmlDimensions import UmlDimensions
from umlshapes.types.UmlPosition import UmlPosition

from umlio.XMLConstants import XmlConstants

XML_VERSION: str = '14.0'

PROJECT_SUFFIX: str = '.udt'        # UML Diagramming Tool
XML_SUFFIX:     str = '.xml'


UmlDocumentTitle = NewType('UmlDocumentTitle', str)
UmlClasses       = NewType('UmlClasses',      List[UmlClass])
UmlUseCases      = NewType('UmlUseCases',     List[UmlUseCase])
UmlActors        = NewType('UmlActors',       List[UmlActor])
UmlNotes         = NewType('UmlNotes',        List[UmlNote])
UmlTexts         = NewType('UmlTexts',        List[UmlText])
UmlLinks         = NewType('UmlLinks',        List[UmlLink])

UmlLollipopInterfaces = NewType('UmlLollipopInterfaces', List[UmlLollipopInterface])

ElementAttributes = NewType('ElementAttributes', Dict[str, str])


class UmlDocumentType(Enum):
    CLASS_DOCUMENT    = 'Class Document'
    USE_CASE_DOCUMENT = 'Use Case Document'
    SEQUENCE_DOCUMENT = 'Sequence Document'
    NOT_SET          = 'Not Set'


def umlClassesFactory() -> UmlClasses:
    """
    Factory method to create  the UmlClasses data structure;

    Returns:  A new data structure
    """
    return UmlClasses([])


def umlUseCasesFactory() -> UmlUseCases:
    return UmlUseCases([])


def umlActorsFactory() -> UmlActors:
    return UmlActors([])


def umlNotesFactory() -> UmlNotes:
    return UmlNotes([])


def umlTextsFactory() -> UmlTexts:
    return UmlTexts([])


def umlLinksFactory() -> UmlLinks:
    return UmlLinks([])


def umlLollipopInterfacesFactory() -> UmlLollipopInterfaces:
    return UmlLollipopInterfaces([])


DEFAULT_PROJECT_TITLE:         UmlDocumentTitle = UmlDocumentTitle('NewProject')
DEFAULT_CLASS_DIAGRAM_NAME:    UmlDocumentTitle = UmlDocumentTitle('Class Diagram')
DEFAULT_USE_CASE_DIAGRAM_NAME: UmlDocumentTitle = UmlDocumentTitle('Use Case Diagram')
DEFAULT_SEQUENCE_DIAGRAM_NAME: UmlDocumentTitle = UmlDocumentTitle('Sequence Diagram')

DEFAULT_PROJECT_PATH:       Path             = Path(f'{DEFAULT_PROJECT_TITLE}{PROJECT_SUFFIX}')

@dataclass
class UmlDocument:
    documentType:    UmlDocumentType  = UmlDocumentType.NOT_SET
    documentTitle:   UmlDocumentTitle = UmlDocumentTitle('')
    scrollPositionX: int = 1
    scrollPositionY: int = 1
    pixelsPerUnitX:  int = 1
    pixelsPerUnitY:  int = 1
    umlClasses:      UmlClasses  = field(default_factory=umlClassesFactory)
    umlUseCases:     UmlUseCases = field(default_factory=umlUseCasesFactory)
    umlActors:       UmlActors   = field(default_factory=umlActorsFactory)
    umlNotes:        UmlNotes    = field(default_factory=umlNotesFactory)
    umlTexts:        UmlTexts    = field(default_factory=umlTextsFactory)
    umlLinks:        UmlLinks    = field(default_factory=umlLinksFactory)

    umlLollipopInterfaces: UmlLollipopInterfaces = field(default_factory=umlLollipopInterfacesFactory)

    @classmethod
    def classDocument(cls) -> 'UmlDocument':
        return UmlDocument(
            documentType=UmlDocumentType.CLASS_DOCUMENT,
            documentTitle=DEFAULT_CLASS_DIAGRAM_NAME
        )

    @classmethod
    def useCaseDocument(cls) -> 'UmlDocument':
        return UmlDocument(
            documentType=UmlDocumentType.USE_CASE_DOCUMENT,
            documentTitle=DEFAULT_USE_CASE_DIAGRAM_NAME
        )

    @classmethod
    def sequenceDocument(cls) -> 'UmlDocument':
        return UmlDocument(
            documentType=UmlDocumentType.SEQUENCE_DOCUMENT,
            documentTitle=DEFAULT_SEQUENCE_DIAGRAM_NAME
        )


UmlDocuments = NewType('UmlDocuments', Dict[UmlDocumentTitle, UmlDocument])


def createUmlDocumentsFactory() -> UmlDocuments:
    return UmlDocuments({})

@dataclass
class ProjectInformation:
    fileName:    Path = Path('')
    version:     str  = XML_VERSION
    codePath:    Path = Path('')


@dataclass
class UmlProject(ProjectInformation):
    umlDocuments: UmlDocuments = field(default_factory=createUmlDocumentsFactory)

    @classmethod
    def emptyProject(cls) -> 'UmlProject':
        umlProject:  UmlProject  = UmlProject(DEFAULT_PROJECT_PATH)
        umlDocument: UmlDocument = UmlDocument(
            documentType=UmlDocumentType.CLASS_DOCUMENT,
            documentTitle=DEFAULT_CLASS_DIAGRAM_NAME,
        )
        umlProject.umlDocuments[DEFAULT_CLASS_DIAGRAM_NAME] = umlDocument

        return umlProject


#
# Untangler helper types
#
Elements = NewType('Elements', List[Element])


@dataclass
class GraphicInformation:
    """
    Internal Class used to move information from a untangler element into Python
    """
    id:       str
    size:     UmlDimensions
    position: UmlPosition

    @classmethod
    def toGraphicInfo(cls, graphicElement: Element) -> 'GraphicInformation':

        graphicInformation: GraphicInformation = GraphicInformation(
            id=graphicElement[XmlConstants.ATTRIBUTE_ID],
            position=UmlPosition(
                x=int(graphicElement[XmlConstants.ATTRIBUTE_X]),
                y=int(graphicElement[XmlConstants.ATTRIBUTE_Y])
            ),
            size=UmlDimensions(
                width=SecureConversions.secureInteger(graphicElement[XmlConstants.ATTRIBUTE_WIDTH]),
                height=SecureConversions.secureInteger(graphicElement[XmlConstants.ATTRIBUTE_HEIGHT])
            )
        )

        return graphicInformation


@dataclass
class UmlLinkAttributes:

    #     f'        <UmlLink id="{UML_LINK_CANONICAL_MONIKER}" fromX="248" fromY="300" toX="190" toY="174" spline="False">\n'
    fromPosition: UmlPosition
    toPosition:   UmlPosition
    id:     str = 'NO ID'
    spline: bool = False

    @classmethod
    def fromGraphicLink(cls, linkElement: Element) -> 'UmlLinkAttributes':

        fromX: int = SecureConversions.secureInteger(linkElement[XmlConstants.ATTRIBUTE_LINK_FROM_X])
        fromY: int = SecureConversions.secureInteger(linkElement[XmlConstants.ATTRIBUTE_LINK_FROM_Y])
        toY:   int = int(linkElement[XmlConstants.ATTRIBUTE_LINK_TO_X])
        toX:   int = int(linkElement[XmlConstants.ATTRIBUTE_LINK_TO_Y])

        shapeId: str  = linkElement[XmlConstants.ATTRIBUTE_ID]
        spline:  bool = SecureConversions.secureBoolean(linkElement[XmlConstants.ATTRIBUTE_SPLINE])

        gla: UmlLinkAttributes = UmlLinkAttributes(
            fromPosition=UmlPosition(x=fromX, y=fromY),
            toPosition=UmlPosition(x=toX, y=toY),
            spline=spline,
            id=shapeId
        )

        return gla
