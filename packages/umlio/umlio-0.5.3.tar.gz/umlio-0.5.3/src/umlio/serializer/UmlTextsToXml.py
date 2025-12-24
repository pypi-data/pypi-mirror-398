
from typing import cast

from logging import Logger
from logging import getLogger

from xml.etree.ElementTree import Element
from xml.etree.ElementTree import SubElement

from umlshapes.shapes.UmlText import UmlText

from umlio.IOTypes import UmlTexts

from umlio.serializer.BaseUmlToXml import BaseUmlToXml
from umlio.serializer.UmlModelToXml import UmlModelToXml
from umlio.XMLConstants import XmlConstants


class UmlTextsToXml(BaseUmlToXml):
    def __init__(self):
        super().__init__()
        self.logger: Logger = getLogger(__name__)

        self._modelToXml: UmlModelToXml = UmlModelToXml()

    def serialize(self, documentTop: Element, umlTexts: UmlTexts) -> Element:

        for text in umlTexts:
            umlText: UmlText = cast(UmlText, text)
            umlTextElement: Element = self._umlTextToXml(documentTop=documentTop, umlText=umlText)
            self._modelToXml.textToXml(text=umlText.modelText, umlTextElement=umlTextElement)

        return documentTop

    def _umlTextToXml(self, documentTop: Element, umlText: UmlText) -> Element:

        attributes = self._umlBaseAttributes(umlShape=umlText)
        umlTextSubElement: Element = SubElement(documentTop, XmlConstants.ELEMENT_UML_TEXT, attrib=attributes)

        return umlTextSubElement
