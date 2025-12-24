
from typing import cast

from logging import Logger
from logging import getLogger

from umlmodel.Class import Class
from untangle import Element

from umlshapes.shapes.UmlClass import UmlClass

from umlio.IOTypes import Elements
from umlio.IOTypes import GraphicInformation
from umlio.IOTypes import UmlClasses
from umlio.IOTypes import umlClassesFactory

from umlio.XMLConstants import XmlConstants

from umlio.deserializer.XmlToUmlModel import XmlToUmlModel


class XmlClassesToUmlClasses:
    def __init__(self):
        self.logger: Logger = getLogger(__name__)

        self._xmlToUmlModel: XmlToUmlModel = XmlToUmlModel()

    def deserialize(self, umlDiagramElement: Element) -> UmlClasses:
        """

        Args:
            umlDiagramElement:  The Element document

        Returns:  deserialized UmlNote objects if any exist, else an empty list
        """
        umlClasses:    UmlClasses = umlClassesFactory()
        classElements: Elements   = cast(Elements, umlDiagramElement.get_elements(XmlConstants.ELEMENT_UML_CLASS))

        for classElement in classElements:
            self.logger.debug(f'{classElement}')

            graphicInformation: GraphicInformation = GraphicInformation.toGraphicInfo(graphicElement=classElement)
            modelClass:         Class              = self._xmlToUmlModel.classToModelClass(umlClassElement=classElement)
            umlClass:           UmlClass           = UmlClass(modelClass=modelClass)

            umlClass.id       = graphicInformation.id
            umlClass.size     = graphicInformation.size
            umlClass.position = graphicInformation.position

            umlClasses.append(umlClass)

        return umlClasses
