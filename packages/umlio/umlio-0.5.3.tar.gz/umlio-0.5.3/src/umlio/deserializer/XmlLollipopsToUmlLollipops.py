
from typing import cast

from logging import Logger
from logging import getLogger

from untangle import Element

from codeallybasic.SecureConversions import SecureConversions

from umlmodel.Interface import Interface

from umlshapes.links.UmlLollipopInterface import UmlLollipopInterface
from umlshapes.shapes.UmlClass import UmlClass
from umlshapes.types.Common import AttachmentSide

from umlshapes.ShapeTypes import LinkableUmlShapes

from umlio.IOTypes import Elements
from umlio.IOTypes import UmlLollipopInterfaces
from umlio.IOTypes import umlLollipopInterfacesFactory

from umlio.XMLConstants import XmlConstants

from umlio.deserializer.XmlToUmlModel import XmlToUmlModel


class XmlLollipopsToUmlLollipops:
    def __init__(self):

        self.logger: Logger = getLogger(__name__)

        self._xmlToUmlMode: XmlToUmlModel = XmlToUmlModel()

    def deserialize(self, umlDiagramElement: Element, linkableUmlShapes: LinkableUmlShapes) -> UmlLollipopInterfaces:

        umlLollipops:     UmlLollipopInterfaces = umlLollipopInterfacesFactory()
        lollipopElements: Elements              = cast(Elements, umlDiagramElement.get_elements(XmlConstants.ELEMENT_LOLLIPOP))

        for lollipopElement in lollipopElements:
            self.logger.info(f'{lollipopElement}')
            umlLollipopInterface: UmlLollipopInterface = self._getLollipop(lollipopElement=lollipopElement, linkableUmlShapes=linkableUmlShapes)

            umlLollipops.append(umlLollipopInterface)

        return umlLollipops

    def _getLollipop(self, lollipopElement: Element, linkableUmlShapes: LinkableUmlShapes) -> UmlLollipopInterface:
        """
        <UmlLollipopInterface lineCentum="0.1" attachmentSide="Right" attachedToId="valley.darkness.implementor">

        Args:
            lollipopElement:
            linkableUmlShapes:

        Returns:   A UML Lollipop interface class
        """
        interface: Interface = self._xmlToUmlMode.interfaceToModelInterface(lollipopElement)

        umlLollipopInterface: UmlLollipopInterface = UmlLollipopInterface(interface=interface)

        attachmentSideStr: str      = lollipopElement[XmlConstants.ATTRIBUTE_ATTACHMENT_SIDE]
        attachedToId:      str      = lollipopElement[XmlConstants.ATTRIBUTE_ATTACHED_TO_ID]
        attachedTo:        UmlClass = self._findAttachedToClass(attachedToId=attachedToId, linkableUmlShapes=linkableUmlShapes)

        umlLollipopInterface.lineCentum     = SecureConversions.secureFloat(lollipopElement[XmlConstants.ATTRIBUTE_LINE_CENTUM])
        umlLollipopInterface.attachmentSide = AttachmentSide.toEnum(attachmentSideStr)

        umlLollipopInterface.attachedTo = attachedTo

        return umlLollipopInterface

    def _findAttachedToClass(self, attachedToId: str, linkableUmlShapes: LinkableUmlShapes) -> UmlClass:
        """
        This method is necessary because the linkable shapes dictionary is indexed by the model class ID
        However, the pointer to the attached class is a UmlClass id.  All this came about because
        lollipops reused the model Interface class

        Args:
            attachedToId:
            linkableUmlShapes:

        Returns:  The appropriate UmlClass
        """
        foundClass: UmlClass = cast(UmlClass, None)
        for uc in linkableUmlShapes.values():
            umlClass: UmlClass = cast(UmlClass, uc)
            if umlClass.id == attachedToId:
                foundClass = umlClass
                break

        assert foundClass is not None, 'Developer error, missing class in linkableUmlShapes'
        return foundClass
