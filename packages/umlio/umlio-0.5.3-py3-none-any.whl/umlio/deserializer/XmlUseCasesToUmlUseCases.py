
from typing import cast

from logging import Logger
from logging import getLogger

from untangle import Element

from umlmodel.UseCase import UseCase

from umlshapes.shapes.UmlUseCase import UmlUseCase

from umlio.IOTypes import Elements
from umlio.IOTypes import GraphicInformation
from umlio.IOTypes import UmlUseCases
from umlio.IOTypes import umlUseCasesFactory

from umlio.XMLConstants import XmlConstants

from umlio.deserializer.XmlToUmlModel import XmlToUmlModel


class XmlUseCasesToUmlUseCases:
    """
    XML Elements to UML use case shape objects and associated model objects
    """
    def __init__(self):
        self.logger: Logger = getLogger(__name__)

        self._xmlToUmlModel: XmlToUmlModel = XmlToUmlModel()

    def deserialize(self, umlDiagramElement: Element) -> UmlUseCases:

        """

        Args:
            umlDiagramElement:  The Element document

        Returns:  deserialized UmlUseCase objects if any exist, else an empty list
        """
        umlUseCases:     UmlUseCases = umlUseCasesFactory()
        useCaseElements: Elements = cast(Elements, umlDiagramElement.get_elements(XmlConstants.ELEMENT_UML_USE_CASE))

        for useCaseElement in useCaseElements:
            self.logger.debug(f'{useCaseElement}')

            graphicInformation: GraphicInformation = GraphicInformation.toGraphicInfo(graphicElement=useCaseElement)
            useCase:            UseCase            = self._xmlToUmlModel.useCaseToModelUseCase(umlUseCaseElement=useCaseElement)
            umlUseCase:         UmlUseCase         = UmlUseCase(useCase=useCase)

            umlUseCase.id       = graphicInformation.id
            umlUseCase.size     = graphicInformation.size
            umlUseCase.position = graphicInformation.position

            umlUseCases.append(umlUseCase)

        return umlUseCases
