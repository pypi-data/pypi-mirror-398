
from typing import cast

from logging import Logger
from logging import getLogger

from untangle import Element

from umlmodel.Note import Note

from umlshapes.shapes.UmlNote import UmlNote

from umlio.IOTypes import Elements
from umlio.IOTypes import GraphicInformation
from umlio.IOTypes import UmlNotes
from umlio.IOTypes import umlNotesFactory

from umlio.XMLConstants import XmlConstants

from umlio.deserializer.XmlToUmlModel import XmlToUmlModel


class XmlNotesToUmlNotes:
    def __init__(self):
        self.logger: Logger = getLogger(__name__)

        self._xmlToUmlModel: XmlToUmlModel = XmlToUmlModel()

    def deserialize(self, umlDiagramElement: Element) -> UmlNotes:
        """

        Args:
            umlDiagramElement:  The Element document

        Returns:  deserialized UmlNote objects if any exist, else an empty list
        """
        umlNotes:     UmlNotes = umlNotesFactory()
        noteElements: Elements = cast(Elements, umlDiagramElement.get_elements(XmlConstants.ELEMENT_UML_NOTE))

        for noteElement in noteElements:
            self.logger.debug(f'{noteElement}')

            graphicInformation: GraphicInformation = GraphicInformation.toGraphicInfo(graphicElement=noteElement)
            note:               Note               = self._xmlToUmlModel.noteToModelNote(umlNoteElement=noteElement)
            umlNote:            UmlNote            = UmlNote(note=note)

            umlNote.id       = graphicInformation.id
            umlNote.size     = graphicInformation.size
            umlNote.position = graphicInformation.position

            umlNotes.append(umlNote)

        return umlNotes
