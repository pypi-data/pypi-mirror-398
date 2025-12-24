
from logging import Logger
from logging import getLogger

from xml.etree.ElementTree import Element
from xml.etree.ElementTree import SubElement

from umlshapes.links.UmlLollipopInterface import UmlLollipopInterface

from umlio.IOTypes import ElementAttributes
from umlio.IOTypes import UmlLollipopInterfaces
from umlio.XMLConstants import XmlConstants
from umlio.serializer.UmlModelToXml import UmlModelToXml


class UmlLollipopsToXml:
    def __init__(self):

        self.logger: Logger = getLogger(__name__)

        self._modelToXml: UmlModelToXml = UmlModelToXml()

    def serialize(self, documentTop: Element, umlLollipops: UmlLollipopInterfaces) -> Element:

        for umlLollipop in umlLollipops:
            self._umlLollipopInterfaceToXml(documentElement=documentTop, umlLollipopInterface=umlLollipop)

        return documentTop

    def _umlLollipopInterfaceToXml(self, documentElement: Element, umlLollipopInterface: UmlLollipopInterface) -> Element:
        """

        Args:
            documentElement:        Xml Element
            umlLollipopInterface:   Lollipop to serialize

        Returns: A new Element
        """
        attachedToId: str = umlLollipopInterface.attachedTo.id
        attributes: ElementAttributes = ElementAttributes({
            XmlConstants.ATTRIBUTE_LINE_CENTUM:     str(umlLollipopInterface.lineCentum),
            XmlConstants.ATTRIBUTE_ATTACHMENT_SIDE: umlLollipopInterface.attachmentSide.value,
            XmlConstants.ATTRIBUTE_ATTACHED_TO_ID:  attachedToId,
        })
        lollipopElement: Element = SubElement(documentElement, XmlConstants.ELEMENT_LOLLIPOP, attrib=attributes)

        self._modelToXml.interfaceToXml(umlLollipopInterface.modelInterface, lollipopElement)

        return lollipopElement
