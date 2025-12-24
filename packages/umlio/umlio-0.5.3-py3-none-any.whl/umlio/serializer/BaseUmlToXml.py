
from umlshapes.ShapeTypes import UmlShapeGenre

from umlshapes.types.UmlDimensions import UmlDimensions
from umlshapes.types.UmlPosition import UmlPosition

from umlio.IOTypes import ElementAttributes

from umlio.XMLConstants import XmlConstants


class BaseUmlToXml:
    def __init__(self):
        pass

    def _umlBaseAttributes(self, umlShape: UmlShapeGenre) -> ElementAttributes:
        """
        Create the common OglObject attributes

        Args:
            umlShape:  OGL Object

        Returns:
            The updated originalElement
        """
        umlClassId: str           = str(umlShape.id)
        size:       UmlDimensions = umlShape.size
        position:   UmlPosition   = umlShape.position

        w: int = size.width
        h: int = size.height
        x: int = position.x
        y: int = position.y

        attributes: ElementAttributes = ElementAttributes(
            {
                XmlConstants.ATTRIBUTE_ID:     umlClassId,
                XmlConstants.ATTRIBUTE_WIDTH:  str(w),
                XmlConstants.ATTRIBUTE_HEIGHT: str(h),
                XmlConstants.ATTRIBUTE_X:      str(x),
                XmlConstants.ATTRIBUTE_Y:      str(y),
            }
        )

        return attributes
