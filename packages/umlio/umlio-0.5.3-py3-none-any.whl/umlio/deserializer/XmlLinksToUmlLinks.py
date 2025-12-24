
from typing import Dict
from typing import List
from typing import NewType
from typing import Union
from typing import cast

from logging import Logger
from logging import getLogger

from dataclasses import dataclass

from wx import Point

from untangle import Element

from codeallybasic.SecureConversions import SecureConversions

from umlmodel.Link import Link
from umlmodel.Link import LinkDestination
from umlmodel.Link import LinkSource

from umlmodel.enumerations.LinkType import LinkType

from umlshapes.types.Common import EndPoints

from umlshapes.links.UmlLink import UmlLink
from umlshapes.links.UmlNoteLink import UmlNoteLink
from umlshapes.links.UmlAssociation import UmlAssociation
from umlshapes.links.UmlInheritance import UmlInheritance
from umlshapes.links.UmlComposition import UmlComposition
from umlshapes.links.UmlAggregation import UmlAggregation

from umlshapes.shapes.UmlClass import UmlClass
from umlshapes.shapes.UmlNote import UmlNote
from umlshapes.shapes.UmlUseCase import UmlUseCase
from umlshapes.shapes.UmlActor import UmlActor


from umlshapes.ShapeTypes import LinkableUmlShape
from umlshapes.ShapeTypes import LinkableUmlShapes

from umlio.IOTypes import Elements
from umlio.IOTypes import UmlLinkAttributes
from umlio.IOTypes import UmlLinks
from umlio.IOTypes import umlLinksFactory

from umlio.XMLConstants import XmlConstants

from umlio.deserializer.XmlToUmlModel import XmlToUmlModel


@dataclass
class ConnectedShapes:
    sourceShape:        LinkableUmlShape
    destinationShape:   LinkableUmlShape


UmlAssociationClasses = Union[UmlAssociation, UmlComposition, UmlAggregation]

# AssociationClassDescriptor = type[UmlAssociationClasses] = cast(type[LinkEventHandler], None)

LinkTypeToClass = NewType('LinkTypeToClass', Dict[LinkType, type[UmlAssociationClasses]])

CLASSMAP: LinkTypeToClass = LinkTypeToClass(
    {
        LinkType.ASSOCIATION: UmlAssociation,
        LinkType.AGGREGATION: UmlAggregation,
        LinkType.COMPOSITION: UmlComposition
    }
)
ASSOCIATION_LINK_TYPES: List[LinkType] = [
    LinkType.COMPOSITION, LinkType.AGGREGATION, LinkType.ASSOCIATION
]


class XmlLinksToUmlLinks:
    def __init__(self):
        self.logger: Logger = getLogger(__name__)

        self._xmlToUmlModel: XmlToUmlModel = XmlToUmlModel()

    def deserialize(self, umlDiagramElement: Element, linkableUmlShapes: LinkableUmlShapes) -> UmlLinks:

        umlLinks:     UmlLinks = umlLinksFactory()
        linkElements: Elements = cast(Elements, umlDiagramElement.get_elements(XmlConstants.ELEMENT_UML_LINK))

        for linkElement in linkElements:
            self.logger.debug(f'{linkElement=}')
            umlLink: UmlLink = self._umlLinkElementToUmlLink(umlLinkElement=linkElement, linkableUmlShapes=linkableUmlShapes)

            umlLinks.append(umlLink)

        return umlLinks

    def _umlLinkElementToUmlLink(self, umlLinkElement: Element, linkableUmlShapes: LinkableUmlShapes) -> UmlLink:

        linkElements: Elements = cast(Elements, umlLinkElement.get_elements(XmlConstants.ELEMENT_MODEL_LINK))
        assert len(linkElements) == 1, 'There can only be one'

        singleLinkElement: Element = linkElements[0]        # I hate this short cut

        umlLink: UmlLink = self._getUmlLink(umlLinkElement=umlLinkElement,
                                            singleLinkElement=singleLinkElement,
                                            linkableUmlShapes=linkableUmlShapes
                                            )

        return umlLink

    def _getUmlLink(self, umlLinkElement: Element, singleLinkElement: Element, linkableUmlShapes: LinkableUmlShapes) -> UmlLink:

        connectedShapes: ConnectedShapes = self._getConnectedShapes(singleLinkElement, linkableUmlShapes)
        link:            Link            = self._getLink(singleLinkElement, connectedShapes)

        umlLink: UmlLink = self._umlLinkFactory(srcShape=connectedShapes.sourceShape,
                                                link=link,
                                                destShape=connectedShapes.destinationShape,
                                                )

        umlLinkAttributes: UmlLinkAttributes = UmlLinkAttributes.fromGraphicLink(linkElement=umlLinkElement)
        self.logger.debug(f'{umlLinkAttributes}=')

        umlLink.id        = umlLinkAttributes.id
        umlLink.spline    = umlLinkAttributes.spline

        umlLink.MakeLineControlPoints(n=2)       # Make this configurable

        umlLink.endPoints = EndPoints(
            toPosition=umlLinkAttributes.toPosition,
            fromPosition=umlLinkAttributes.fromPosition
        )
        controlPoints: List[Point] = self._getLineControlPoints(umlLinkElement=umlLinkElement)
        for cp in controlPoints:
            umlLink.InsertLineControlPoint(point=cp)

        return umlLink

    def _getLink(self, modelLinkElement: Element, connectedShapes: ConnectedShapes) -> Link:
        """

        Args:
            modelLinkElement:   The Xml Elements
            connectedShapes:    The shapes at the ends of the link

        Returns:    A data model link
        """

        # noinspection PyUnresolvedReferences
        link: Link = self._xmlToUmlModel.linkToModelLink(
            singleLink=modelLinkElement,
            source=self._getLinkSourceModelClass(connectedShapes.sourceShape),
            destination=self._getLinkDestinationModelClass(connectedShapes.destinationShape)
        )
        self.logger.debug(f'{link=}')

        return link

    def _getConnectedShapes(self, linkElement: Element, linkableUmlShapes: LinkableUmlShapes) -> ConnectedShapes:
        """

        Args:
            linkElement:
            linkableUmlShapes:   The dictionary of potential shapes

        Returns:  The connected shapes;  Will assert if it cannot find them
        """
        sourceId: str = linkElement[XmlConstants.ATTRIBUTE_SOURCE_ID]
        dstId:    str = linkElement[XmlConstants.ATTRIBUTE_DESTINATION_ID]

        try:
            sourceShape:      LinkableUmlShape = linkableUmlShapes[sourceId]
            destinationShape: LinkableUmlShape = linkableUmlShapes[dstId]
        except KeyError as ke:
            self.logger.error(f'{linkableUmlShapes=}')
            self.logger.error(f'Developer Error -- {linkElement=}')
            self.logger.error(f'Developer Error -- {sourceId=} {dstId=}  KeyError index: {ke}')
            assert False, 'Developer error'

        return ConnectedShapes(sourceShape=sourceShape, destinationShape=destinationShape)

    def _getLinkSourceModelClass(self, linkableUmlShape: LinkableUmlShape) -> LinkSource:
        """

        Args:
            linkableUmlShape:

        Returns:  The appropriate model class instance
        """

        if isinstance(linkableUmlShape, UmlClass):
            return linkableUmlShape.modelClass
        elif isinstance(linkableUmlShape, UmlNote):
            return linkableUmlShape.modelNote
        # elif isinstance(linkableUmlShape, UmlText):
        #     return linkableUmlShape.modelText
        elif isinstance(linkableUmlShape, UmlActor):
            return linkableUmlShape.modelActor
        else:
            assert False, f'{linkableUmlShape=} is not a source linkable UML Shape'

    def _getLinkDestinationModelClass(self, linkableUmlShape: LinkableUmlShape) -> LinkDestination:
        """

        Args:
            linkableUmlShape:

        Returns: The appropriate model class instance
        """

        if isinstance(linkableUmlShape, UmlClass):
            return linkableUmlShape.modelClass
        elif isinstance(linkableUmlShape, UmlUseCase):
            return linkableUmlShape.modelUseCase
        else:
            assert False, f'{linkableUmlShape=} is not a destination linkable UML Shape'

    def _getLineControlPoints(self, umlLinkElement: Element) -> List[Point]:
        """
         <LineControlPoint x="100" y="100" />

        Args:
            umlLinkElement:

        Returns:
        """

        controlPoints: List[Point] = []

        controlPointElements: Elements = cast(Elements, umlLinkElement.get_elements(XmlConstants.ELEMENT_MODEL_LINE_CONTROL_POINT))
        for controlPointElement in controlPointElements:
            x: int = SecureConversions.secureInteger(controlPointElement[XmlConstants.ATTRIBUTE_X])
            y: int = SecureConversions.secureInteger(controlPointElement[XmlConstants.ATTRIBUTE_Y])

            point: Point = Point(x=x, y=y)
            controlPoints.append(point)

        return controlPoints

    def _umlLinkFactory(self, srcShape: LinkableUmlShape, link: Link, destShape: LinkableUmlShape) -> UmlLink:
        """

        Args:
            srcShape:
            link:
            destShape:

        Returns:  The appropriate UML Link shape

        """
        if link.linkType == LinkType.INHERITANCE:
            # Note dest and source are reversed here
            return UmlInheritance(baseClass=cast(UmlClass, destShape), link=link, subClass=cast(UmlClass, srcShape))
        elif link.linkType in ASSOCIATION_LINK_TYPES:
            umlAssociation = CLASSMAP[link.linkType](link)
            #
            # Need to do this because the shape is not yet on a canvas
            #
            umlAssociation.sourceShape      = srcShape
            umlAssociation.destinationShape = destShape
            return umlAssociation
        elif link.linkType == LinkType.NOTELINK:
            umlNoteLink: UmlNoteLink = UmlNoteLink(link=link)
            umlNoteLink.sourceNote       = cast(UmlNote, srcShape)
            umlNoteLink.destinationClass = cast(UmlClass, destShape)
            return umlNoteLink
        else:
            assert False, f'Unknown link type, {link.linkType=}'
