
from logging import Logger
from logging import getLogger

from pathlib import Path

from untangle import Element
from untangle import parse

from codeallybasic.SecureConversions import SecureConversions

from umlshapes.ShapeTypes import LinkableUmlShapes
from umlshapes.ShapeTypes import linkableUmlShapesFactory

from umlio.IOTypes import UmlActors
from umlio.IOTypes import UmlClasses
from umlio.IOTypes import UmlDocument
from umlio.IOTypes import UmlDocumentTitle
from umlio.IOTypes import UmlDocumentType
from umlio.IOTypes import UmlLinks
from umlio.IOTypes import UmlLollipopInterfaces
from umlio.IOTypes import UmlNotes
from umlio.IOTypes import UmlTexts
from umlio.IOTypes import UmlProject
from umlio.IOTypes import UmlUseCases

from umlio.deserializer.XmlActorsToUmlActors import XmlActorsToUmlActors
from umlio.deserializer.XmlClassesToUmlClasses import XmlClassesToUmlClasses
from umlio.deserializer.XmlLinksToUmlLinks import XmlLinksToUmlLinks
from umlio.deserializer.XmlLollipopsToUmlLollipops import XmlLollipopsToUmlLollipops
from umlio.deserializer.XmlNotesToUmlNotes import XmlNotesToUmlNotes
from umlio.deserializer.XmlTextsToUmlTexts import XmlTextsToUmlTexts
from umlio.deserializer.XmlUseCasesToUmlUseCases import XmlUseCasesToUmlUseCases

from umlio.XMLConstants import XmlConstants


class XmlToUmlShapes:
    def __init__(self):
        self.logger: Logger = getLogger(__name__)

        self._umlProject:  UmlProject  = UmlProject()

    @property
    def umlProject(self) -> UmlProject:
        return self._umlProject

    def deserializeProjectFile(self, fileName: Path):
        pass

    def deserializeXmlFile(self, fileName: Path):
        """
        Untangle the input Xml string to UmlShapes
        Args:
            fileName:  The file name from which the XML came from
        """

        xmlString: str = fileName.read_text()
        self.deserializeXml(xmlString=xmlString, fileName=fileName)

    def deserializeXml(self, xmlString: str, fileName: Path):
        root:       Element = parse(xmlString)
        umlProject: Element = root.UmlProject

        self._umlProject.fileName = fileName
        self._umlProject.version  = umlProject[XmlConstants.ATTRIBUTE_VERSION]
        self._umlProject.codePath = umlProject[XmlConstants.ATTRIBUTE_CODE_PATH]

        for umlDiagramElement in umlProject.UMLDiagram:

            umlDocument: UmlDocument = UmlDocument(
                documentTitle=umlDiagramElement[XmlConstants.ATTRIBUTE_TITLE],
                scrollPositionX=SecureConversions.secureInteger(umlDiagramElement[XmlConstants.ATTRIBUTE_SCROLL_POSITION_X]),
                scrollPositionY=SecureConversions.secureInteger(umlDiagramElement[XmlConstants.ATTRIBUTE_SCROLL_POSITION_Y]),
                pixelsPerUnitX=SecureConversions.secureInteger(umlDiagramElement[XmlConstants.ATTRIBUTE_PIXELS_PER_UNIT_X]),
                pixelsPerUnitY=SecureConversions.secureInteger(umlDiagramElement[XmlConstants.ATTRIBUTE_PIXELS_PER_UNIT_Y])
            )
            umlDocument.documentTitle = UmlDocumentTitle(umlDiagramElement[XmlConstants.ATTRIBUTE_TITLE])

            if umlDiagramElement[XmlConstants.ATTRIBUTE_DOCUMENT_TYPE] == UmlDocumentType.CLASS_DOCUMENT.value:

                umlDocument.documentType = UmlDocumentType.CLASS_DOCUMENT
                umlDocument.umlClasses = self._deserializeUmlClassElements(umlDiagramElement=umlDiagramElement)
                umlDocument.umlNotes   = self._deserializeUmlNoteElements(umlDiagramElement=umlDiagramElement)
                umlDocument.umlTexts   = self._deserializeUmlTextElements(umlDiagramElement=umlDiagramElement)

                linkableUmlShapes: LinkableUmlShapes = self._buildLinkableUmlShapes(umlDocument=umlDocument)

                umlDocument.umlLinks              = self._deserializeUmlLinkElements(umlDiagramElement=umlDiagramElement, linkableUmlShapes=linkableUmlShapes)
                umlDocument.umlLollipopInterfaces = self._deserializeLollipopInterfaces(umlDiagramElement=umlDiagramElement, linkableUmlShapes=linkableUmlShapes)

            elif umlDiagramElement[XmlConstants.ATTRIBUTE_DOCUMENT_TYPE] == UmlDocumentType.USE_CASE_DOCUMENT.value:

                umlDocument.documentType = UmlDocumentType.USE_CASE_DOCUMENT
                umlDocument.umlNotes    = self._deserializeUmlNoteElements(umlDiagramElement=umlDiagramElement)
                umlDocument.umlActors   = self._deserializeUmlActorElements(umlDiagramElement=umlDiagramElement)
                umlDocument.umlUseCases = self._deserializeUmlUseCaseElements(umlDiagramElement=umlDiagramElement)

                linkableUmlShapes = self._buildLinkableUmlShapes(umlDocument=umlDocument)

                umlDocument.umlLinks = self._deserializeUmlLinkElements(umlDiagramElement=umlDiagramElement, linkableUmlShapes=linkableUmlShapes)

            elif umlDiagramElement[XmlConstants.ATTRIBUTE_DOCUMENT_TYPE] == UmlDocumentType.SEQUENCE_DOCUMENT.value:

                umlDocument.documentType = UmlDocumentType.SEQUENCE_DOCUMENT
                umlDocument.umlTexts   = self._deserializeUmlTextElements(umlDiagramElement=umlDiagramElement)
                umlDocument.umlNotes    = self._deserializeUmlNoteElements(umlDiagramElement=umlDiagramElement)

            else:
                assert False, 'Unknown diagram Type - Perhaps corrupted fle'

            self._umlProject.umlDocuments[umlDocument.documentTitle] = umlDocument

    def _deserializeUmlClassElements(self, umlDiagramElement: Element) -> UmlClasses:

        umlClassesDeSerializer: XmlClassesToUmlClasses = XmlClassesToUmlClasses()
        umlClasses:             UmlClasses             = umlClassesDeSerializer.deserialize(umlDiagramElement=umlDiagramElement)

        return umlClasses

    def _deserializeUmlTextElements(self, umlDiagramElement: Element) -> UmlTexts:
        """
        Yeah, yeah, I know bad English;

        Args:
            umlDiagramElement:  The diagram Element

        Returns:  deserialized UmlText objects if any exist, else an empty list
        """
        umlTextDeSerializer: XmlTextsToUmlTexts = XmlTextsToUmlTexts()
        umlTexts: UmlTexts = umlTextDeSerializer.deserialize(umlDiagramElement=umlDiagramElement)

        return umlTexts

    def _deserializeUmlNoteElements(self, umlDiagramElement: Element) -> UmlNotes:
        """

        Args:
            umlDiagramElement:  The diagram Element

        Returns:  deserialized UmlNote objects if any exist, else an empty list
        """
        xmlNotesToUmlNotes: XmlNotesToUmlNotes = XmlNotesToUmlNotes()
        umlNotes: UmlNotes = xmlNotesToUmlNotes.deserialize(umlDiagramElement=umlDiagramElement)

        return umlNotes

    def _deserializeUmlActorElements(self, umlDiagramElement: Element) -> UmlActors:
        """

        Args:
            umlDiagramElement:  The diagram Element

        Returns:  deserialized UmlActor objects if any exist, else an empty list
        """
        xmlActorsToUmlActors: XmlActorsToUmlActors = XmlActorsToUmlActors()

        umlActors: UmlActors = xmlActorsToUmlActors.deserialize(umlDiagramElement=umlDiagramElement)

        return umlActors

    def _deserializeUmlUseCaseElements(self, umlDiagramElement: Element) -> UmlUseCases:
        """

        Args:
            umlDiagramElement:  The diagram Element

        Returns:  deserialized UmlUseCase objects if any exist, else an empty list
        """
        xmlUseCasesToUmlUseCases: XmlUseCasesToUmlUseCases = XmlUseCasesToUmlUseCases()

        umlUseCases: UmlUseCases = xmlUseCasesToUmlUseCases.deserialize(umlDiagramElement=umlDiagramElement)

        return umlUseCases

    def _deserializeUmlLinkElements(self, umlDiagramElement: Element, linkableUmlShapes: LinkableUmlShapes) -> UmlLinks:

        xmlLinksToUmlLinks: XmlLinksToUmlLinks = XmlLinksToUmlLinks()

        umlLinks: UmlLinks = xmlLinksToUmlLinks.deserialize(umlDiagramElement=umlDiagramElement, linkableUmlShapes=linkableUmlShapes)

        return umlLinks

    def _deserializeLollipopInterfaces(self, umlDiagramElement: Element, linkableUmlShapes: LinkableUmlShapes) -> UmlLollipopInterfaces:

        xmlLollipopsToUmLollipops: XmlLollipopsToUmlLollipops = XmlLollipopsToUmlLollipops()

        lollipopInterfaces: UmlLollipopInterfaces = xmlLollipopsToUmLollipops.deserialize(umlDiagramElement=umlDiagramElement,
                                                                                          linkableUmlShapes=linkableUmlShapes
                                                                                          )
        return lollipopInterfaces

    def _buildLinkableUmlShapes(self, umlDocument: UmlDocument) -> LinkableUmlShapes:
        """

        Args:
            umlDocument:   The created document either Use case or class diagram

        Returns:  Linkable UML Shapes Dictionary
        """

        linkableUmlShapes: LinkableUmlShapes = linkableUmlShapesFactory()

        for umlClass in umlDocument.umlClasses:
            linkableUmlShapes[umlClass.modelClass.id] = umlClass

        for umlNote in umlDocument.umlNotes:
            linkableUmlShapes[umlNote.modelNote.id] = umlNote

        for umlUseCase in umlDocument.umlUseCases:
            linkableUmlShapes[umlUseCase.modelUseCase.id] = umlUseCase

        for umlActor in umlDocument.umlActors:
            linkableUmlShapes[umlActor.modelActor.id] = umlActor

        return linkableUmlShapes
