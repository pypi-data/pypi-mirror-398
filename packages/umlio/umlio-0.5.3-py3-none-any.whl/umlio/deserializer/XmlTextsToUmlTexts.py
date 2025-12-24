
from typing import cast

from logging import Logger
from logging import getLogger

from untangle import Element

from umlmodel.Text import Text

from umlshapes.shapes.UmlText import UmlText

from umlio.IOTypes import Elements
from umlio.IOTypes import GraphicInformation
from umlio.IOTypes import UmlTexts
from umlio.IOTypes import umlTextsFactory

from umlio.deserializer.XmlToUmlModel import XmlToUmlModel

from umlio.XMLConstants import XmlConstants


class XmlTextsToUmlTexts:
    """
    Yes, I know bad English
    """
    def __init__(self):

        super().__init__()

        self.logger: Logger = getLogger(__name__)

        self._xmlToUmlModel: XmlToUmlModel = XmlToUmlModel()

    def deserialize(self, umlDiagramElement: Element) -> UmlTexts:
        """

        Args:
            umlDiagramElement:  The Element document

        Returns:  deserialized UmlText objects if any exist, else an empty list
        """

        umlTexts:     UmlTexts = umlTextsFactory()
        textElements: Elements = cast(Elements, umlDiagramElement.get_elements(XmlConstants.ELEMENT_UML_TEXT))

        for textElement in textElements:
            self.logger.debug(f'{textElement}')

            graphicInformation: GraphicInformation = GraphicInformation.toGraphicInfo(graphicElement=textElement)
            text:               Text               = self._xmlToUmlModel.textToModelText(umlTextElement=textElement)
            umlText:            UmlText            = UmlText(text=text)

            umlText.id       = graphicInformation.id
            umlText.size     = graphicInformation.size
            umlText.position = graphicInformation.position

            umlTexts.append(umlText)

        return umlTexts
