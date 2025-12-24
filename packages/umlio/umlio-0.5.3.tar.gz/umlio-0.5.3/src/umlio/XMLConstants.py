
class XmlConstants:
    """
    A `no method` class that just hosts the strings that represent the UML shapes XML strings
    """
    ATTRIBUTE_VERSION: str = 'version'

    ATTRIBUTE_DOCUMENT_TYPE: str = 'documentType'
    ATTRIBUTE_TITLE:         str = 'title'

    ATTRIBUTE_CODE_PATH: str = 'codePath'

    ATTRIBUTE_SCROLL_POSITION_X: str = 'scrollPositionX'
    ATTRIBUTE_SCROLL_POSITION_Y: str = 'scrollPositionY'
    ATTRIBUTE_PIXELS_PER_UNIT_X: str = 'pixelsPerUnitX'
    ATTRIBUTE_PIXELS_PER_UNIT_Y: str = 'pixelsPerUnitY'

    ATTRIBUTE_ID:     str = 'id'

    ATTRIBUTE_WIDTH:  str = 'width'
    ATTRIBUTE_HEIGHT: str = 'height'
    ATTRIBUTE_X:      str = 'x'
    ATTRIBUTE_Y:      str = 'y'
    ATTRIBUTE_NAME:   str = 'name'

    ATTRIBUTE_DISPLAY_STEREOTYPE:     str = 'displayStereotype'
    ATTRIBUTE_DISPLAY_METHODS:        str = 'displayMethods'
    ATTRIBUTE_DISPLAY_FIELDS:         str = 'displayFields'
    ATTRIBUTE_DISPLAY_PARAMETERS:     str = 'displayParameters'
    ATTRIBUTE_DISPLAY_CONSTRUCTOR:    str = 'displayConstructor'
    ATTRIBUTE_DISPLAY_DUNDER_METHODS: str = 'displayDunderMethods'

    ATTRIBUTE_STEREOTYPE:    str = 'stereotype'
    ATTRIBUTE_FILENAME:      str = 'fileName'
    ATTRIBUTE_CONTENT:       str = 'content'
    ATTRIBUTE_DESCRIPTION:   str = 'description'
    ATTRIBUTE_VISIBILITY:    str = 'visibility'
    ATTRIBUTE_MESSAGE:       str = 'message'
    ATTRIBUTE_DEFAULT_VALUE: str = 'defaultValue'
    ATTRIBUTE_METHOD_RETURN_TYPE: str = 'returnType'

    ATTRIBUTE_SOURCE_CARDINALITY_VALUE:      str = 'sourceCardinalityValue'
    ATTRIBUTE_DESTINATION_CARDINALITY_VALUE: str = 'destinationCardinalityValue'

    ATTRIBUTE_DELTA_X: str = 'deltaX'
    ATTRIBUTE_DELTA_Y: str = 'deltaY'

    ATTRIBUTE_LINK_FROM_X: str = 'fromX'
    ATTRIBUTE_LINK_FROM_Y: str = 'fromY'

    ATTRIBUTE_LINK_TO_X: str = 'toX'
    ATTRIBUTE_LINK_TO_Y: str = 'toY'

    ATTRIBUTE_SPLINE:    str = 'spline'
    ATTRIBUTE_LINK_TYPE: str = 'type'       # TODO:  Should be linkType

    ATTRIBUTE_SOURCE_ID:                 str = 'sourceId'
    ATTRIBUTE_DESTINATION_ID:            str = 'destinationId'
    ATTRIBUTE_BIDIRECTIONAL:             str = 'bidirectional'
    ATTRIBUTE_SD_MESSAGE_SOURCE_ID:      str = 'sourceId'
    ATTRIBUTE_SD_MESSAGE_DESTINATION_ID: str = 'destinationId'

    ATTRIBUTE_INSTANCE_NAME:    str = 'instanceName'
    ATTRIBUTE_LIFE_LINE_LENGTH: str = 'lifeLineLength'
    ATTRIBUTE_SOURCE_TIME:      str = 'sourceTime'
    ATTRIBUTE_DESTINATION_TIME: str = 'destinationTime'

    ATTRIBUTE_IMPLEMENTING_CLASS_NAME:   str = 'implementingClassName'
    ATTRIBUTE_LINE_CENTUM:               str = 'lineCentum'
    ATTRIBUTE_ATTACHMENT_SIDE:           str = 'attachmentSide'
    ATTRIBUTE_ATTACHED_TO_ID:            str = 'attachedToId'

    ATTRIBUTE_FIELD_TYPE:     str = 'fieldType'
    ATTRIBUTE_PARAMETER_TYPE: str = 'parameterType'

    ELEMENT_UML_PROJECT:  str = 'UmlProject'
    ELEMENT_UML_DIAGRAM:  str = 'UMLDiagram'
    ELEMENT_UML_CLASS:    str = 'UmlClass'
    ELEMENT_UML_USE_CASE: str = 'UmlUseCase'
    ELEMENT_UML_ACTOR:    str = 'UmlActor'
    ELEMENT_UML_NOTE:     str = 'UmlNote'
    ELEMENT_UML_TEXT:     str = 'UmlText'
    ELEMENT_UML_LINK:     str = 'UmlLink'
    ELEMENT_LOLLIPOP:     str = 'UmlLollipopInterface'

    ELEMENT_ASSOCIATION_LABEL:             str = 'AssociationName'
    ELEMENT_ASSOCIATION_SOURCE_LABEL:      str = 'SourceCardinality'
    ELEMENT_ASSOCIATION_DESTINATION_LABEL: str = 'DestinationCardinality'

    ELEMENT_MODEL_CLASS:       str = 'ModelClass'
    ELEMENT_MODEL_TEXT:        str = 'ModelText'
    ELEMENT_MODEL_NOTE:        str = 'ModelNote'
    ELEMENT_MODEL_ACTOR:       str = 'ModelActor'
    ELEMENT_MODEL_USE_CASE:    str = 'ModelUseCase'
    ELEMENT_MODEL_LINK:        str = 'ModelLink'
    ELEMENT_MODEL_INTERFACE:   str = 'ModelInterface'
    ELEMENT_MODEL_IMPLEMENTOR: str = 'Implementor'

    ELEMENT_MODEL_IMPLEMENTING_CLASS_NAME: str = 'implementingClassName'

    ELEMENT_MODEL_METHOD:      str = 'ModelMethod'
    ELEMENT_MODEL_PARAMETER:   str = 'ModelParameter'
    ELEMENT_MODEL_FIELD:       str = 'ModelField'
    ELEMENT_MODEL_MODIFIER:    str = 'Modifier'
    ELEMENT_MODEL_SOURCE_CODE: str = 'SourceCode'
    ELEMENT_MODEL_CODE:        str = 'Code'

    ELEMENT_MODEL_SD_INSTANCE:   str = 'ModelSDInstance'
    ELEMENT_MODEL_SD_MESSAGE:    str = 'ModelSDMessage'

    ELEMENT_MODEL_LINE_CONTROL_POINT: str = 'LineControlPoint'
