
from logging import Logger
from logging import getLogger

from os import linesep as osLineSep

from xml.etree.ElementTree import Element
from xml.etree.ElementTree import SubElement

from codeallybasic.Common import XML_END_OF_LINE_MARKER

from umlmodel.Actor import Actor
from umlmodel.Class import Class
from umlmodel.ClassCommon import ClassCommon
from umlmodel.Field import Field
from umlmodel.Interface import Interface
from umlmodel.Link import Link
from umlmodel.Link import LinkDestination
from umlmodel.Link import LinkSource
from umlmodel.Method import Method
from umlmodel.Method import SourceCode
from umlmodel.ModelTypes import ClassName
from umlmodel.Note import Note
from umlmodel.Parameter import Parameter
from umlmodel.SDInstance import SDInstance
from umlmodel.SDMessage import SDMessage
from umlmodel.Text import Text
from umlmodel.UseCase import UseCase

from umlio.IOTypes import ElementAttributes

from umlio.XMLConstants import XmlConstants


class UmlModelToXml:
    """
    Serializes Um Model classes to DOM
    """

    def __init__(self):
        super().__init__()
        self.logger: Logger = getLogger(__name__)

    def classToXml(self, modelClass: Class, umlClassElement: Element) -> Element:
        """
        Exporting a model class to a miniDom Element.

        Args:
            modelClass:       The model class to serialize
            umlClassElement:  The xml element to update

        Returns:
            A new updated element
        """

        commonAttributes = self._classCommonAttributes(modelClass)
        attributes = {
            XmlConstants.ATTRIBUTE_ID:                     modelClass.id,
            XmlConstants.ATTRIBUTE_NAME:                   modelClass.name,
            XmlConstants.ATTRIBUTE_DISPLAY_METHODS:        str(modelClass.showMethods),
            XmlConstants.ATTRIBUTE_DISPLAY_PARAMETERS:     modelClass.displayParameters.value,
            XmlConstants.ATTRIBUTE_DISPLAY_CONSTRUCTOR:    modelClass.displayConstructor.value,
            XmlConstants.ATTRIBUTE_DISPLAY_DUNDER_METHODS: modelClass.displayDunderMethods.value,
            XmlConstants.ATTRIBUTE_DISPLAY_FIELDS:         str(modelClass.showFields),
            XmlConstants.ATTRIBUTE_DISPLAY_STEREOTYPE:     str(modelClass.displayStereoType),
            XmlConstants.ATTRIBUTE_FILENAME:               modelClass.fileName,
        }

        attributes = attributes | commonAttributes

        classElement: Element = SubElement(umlClassElement, XmlConstants.ELEMENT_MODEL_CLASS, attrib=attributes)

        for method in modelClass.methods:
            self._methodToXml(method=method, classElement=classElement)

        for field in modelClass.fields:
            self._fieldToXml(field=field, classElement=classElement)
        return classElement

    def linkToXml(self, link: Link, umlLinkElement: Element) -> Element:
        """
        Serialize a link to an Element.

        Args:
            link:           The model link to serialize
            umlLinkElement: xml document

        Returns:
            A new minidom element
        """
        src: LinkSource      = link.source
        dst: LinkDestination = link.destination

        srcLinkId:  str = src.id
        destLinkId: str = dst.id

        attributes: ElementAttributes = ElementAttributes({
            XmlConstants.ATTRIBUTE_NAME:           link.name,
            XmlConstants.ATTRIBUTE_LINK_TYPE:      link.linkType.name,
            XmlConstants.ATTRIBUTE_SOURCE_ID:      str(srcLinkId),
            XmlConstants.ATTRIBUTE_DESTINATION_ID: str(destLinkId),
            XmlConstants.ATTRIBUTE_BIDIRECTIONAL:  str(link.bidirectional),
            XmlConstants.ATTRIBUTE_SOURCE_CARDINALITY_VALUE:      link.sourceCardinality,
            XmlConstants.ATTRIBUTE_DESTINATION_CARDINALITY_VALUE: link.destinationCardinality,
        })
        linkElement: Element = SubElement(umlLinkElement, XmlConstants.ELEMENT_MODEL_LINK, attrib=attributes)

        return linkElement

    def interfaceToXml(self, interface: Interface, interface2Element: Element) -> Element:

        classId: str = interface.id

        attributes: ElementAttributes = ElementAttributes({
            XmlConstants.ATTRIBUTE_ID:          classId,
            XmlConstants.ATTRIBUTE_NAME:        interface.name,
            XmlConstants.ATTRIBUTE_DESCRIPTION: interface.description
        })
        interfaceElement: Element = SubElement(interface2Element, XmlConstants.ELEMENT_MODEL_INTERFACE, attrib=attributes)

        for method in interface.methods:
            self._methodToXml(method=method, classElement=interfaceElement)

        for className in interface.implementors:
            self.logger.debug(f'implementing className: {className}')
            self._implementorToXml(className, interfaceElement)

        return interfaceElement

    def noteToXml(self, note: Note, umlNoteElement: Element) -> Element:

        noteId:       str = note.id
        content:      str = note.content
        fixedContent: str = content.replace(osLineSep, XML_END_OF_LINE_MARKER)
        if note.fileName is None:
            note.fileName = ''

        attributes: ElementAttributes = ElementAttributes({
            XmlConstants.ATTRIBUTE_ID:       str(noteId),
            XmlConstants.ATTRIBUTE_CONTENT:  fixedContent,
            XmlConstants.ATTRIBUTE_FILENAME: note.fileName,
        })
        noteElement: Element = SubElement(umlNoteElement, XmlConstants.ELEMENT_MODEL_NOTE, attrib=attributes)

        return noteElement

    def textToXml(self, text: Text, umlTextElement: Element) -> Element:

        textId:       str = text.id
        content:      str = text.content
        fixedContent: str = content.replace(osLineSep, XML_END_OF_LINE_MARKER)

        attributes: ElementAttributes = ElementAttributes({
            XmlConstants.ATTRIBUTE_ID:       textId,
            XmlConstants.ATTRIBUTE_CONTENT:  fixedContent,
        })
        textElement: Element = SubElement(umlTextElement, XmlConstants.ELEMENT_MODEL_TEXT, attrib=attributes)

        return textElement

    def actorToXml(self, actor: Actor, umlActorElement: Element) -> Element:

        actorId:  str = actor.id
        fileName: str = actor.fileName
        if fileName is None:
            fileName = ''

        attributes: ElementAttributes = ElementAttributes({
            XmlConstants.ATTRIBUTE_ID:       actorId,
            XmlConstants.ATTRIBUTE_NAME:     actor.name,
            XmlConstants.ATTRIBUTE_FILENAME: fileName,
        })
        actorElement: Element = SubElement(umlActorElement, XmlConstants.ELEMENT_MODEL_ACTOR, attributes)

        return actorElement

    def useCaseToXml(self, useCase: UseCase, umlUseCaseElement: Element) -> Element:

        useCaseId: str = useCase.id
        fileName:  str = useCase.fileName
        if fileName is None:
            fileName = ''

        attributes: ElementAttributes = ElementAttributes({
            XmlConstants.ATTRIBUTE_ID:       useCaseId,
            XmlConstants.ATTRIBUTE_NAME:     useCase.name,
            XmlConstants.ATTRIBUTE_FILENAME: fileName
        })
        useCaseElement: Element = SubElement(umlUseCaseElement, XmlConstants.ELEMENT_MODEL_USE_CASE, attributes)

        return useCaseElement

    def sdInstanceToXml(self, sdInstance: SDInstance, sdInstanceElement: Element) -> Element:

        sdInstanceId: str = sdInstance.id

        attributes: ElementAttributes = ElementAttributes({
            XmlConstants.ATTRIBUTE_ID:               sdInstanceId,
            XmlConstants.ATTRIBUTE_INSTANCE_NAME:    sdInstance.instanceName,
            XmlConstants.ATTRIBUTE_LIFE_LINE_LENGTH: str(sdInstance.instanceLifeLineLength),
        })

        modelSDInstanceElement: Element = SubElement(sdInstanceElement, XmlConstants.ELEMENT_MODEL_SD_INSTANCE, attrib=attributes)

        return modelSDInstanceElement

    def sdMessageToXml(self, sdMessage: SDMessage, sdMessageElement: Element) -> Element:

        sdMessageId: str = sdMessage.id

        srcInstance: LinkSource      = sdMessage.source
        dstInstance: LinkDestination = sdMessage.destination

        idSrc: str = srcInstance.id
        idDst: str = dstInstance.id

        attributes: ElementAttributes = ElementAttributes({
            XmlConstants.ATTRIBUTE_ID:                        sdMessageId,
            XmlConstants.ATTRIBUTE_MESSAGE:                   sdMessage.message,
            XmlConstants.ATTRIBUTE_SOURCE_TIME:               str(sdMessage.sourceY),
            XmlConstants.ATTRIBUTE_DESTINATION_TIME:          str(sdMessage.destinationY),
            XmlConstants.ATTRIBUTE_SD_MESSAGE_SOURCE_ID:      idSrc,
            XmlConstants.ATTRIBUTE_SD_MESSAGE_DESTINATION_ID: idDst,
        })

        modelSDMessageElement: Element = SubElement(sdMessageElement, XmlConstants.ELEMENT_MODEL_SD_MESSAGE, attrib=attributes)

        return modelSDMessageElement

    def _methodToXml(self, method: Method, classElement: Element) -> Element:
        """
        Exporting a model Method to an Element

        Args:
            method:        Method to serialize
            classElement:  xml document

        Returns:
            The new updated element
        """
        attributes = {
            XmlConstants.ATTRIBUTE_NAME:               method.name,
            XmlConstants.ATTRIBUTE_VISIBILITY:         method.visibility.name,
            XmlConstants.ATTRIBUTE_METHOD_RETURN_TYPE: method.returnType.value,
        }
        methodElement: Element = SubElement(classElement, XmlConstants.ELEMENT_MODEL_METHOD, attrib=attributes)
        for modifier in method.modifiers:
            attributes = {
                XmlConstants.ATTRIBUTE_NAME: modifier.name,
            }
            SubElement(methodElement, XmlConstants.ELEMENT_MODEL_MODIFIER, attrib=attributes)
        self._sourceCodeToXml(method.sourceCode, methodElement)

        for parameter in method.parameters:
            self._parameterToXml(parameter, methodElement)

        return methodElement

    def _classCommonAttributes(self, classCommon: ClassCommon):

        attributes = {
            XmlConstants.ATTRIBUTE_DESCRIPTION: classCommon.description
        }
        return attributes

    def _sourceCodeToXml(self, sourceCode: SourceCode, methodElement: Element):

        codeRoot: Element = SubElement(methodElement, XmlConstants.ELEMENT_MODEL_SOURCE_CODE)

        for code in sourceCode:
            codeElement: Element = SubElement(codeRoot, XmlConstants.ELEMENT_MODEL_CODE)
            codeElement.text = code

        return codeRoot

    def _parameterToXml(self, parameter: Parameter, methodElement: Element) -> Element:

        attributes = {
            XmlConstants.ATTRIBUTE_NAME:           parameter.name,
            XmlConstants.ATTRIBUTE_PARAMETER_TYPE: parameter.type.value,
        }

        defaultValue = parameter.defaultValue
        if defaultValue is not None:
            attributes[XmlConstants.ATTRIBUTE_DEFAULT_VALUE] = parameter.defaultValue

        parameterElement: Element = SubElement(methodElement, XmlConstants.ELEMENT_MODEL_PARAMETER, attrib=attributes)

        return parameterElement

    def _fieldToXml(self, field: Field, classElement: Element) -> Element:
        """
        Serialize a model field to an Element

        Args:
            field:        The model field to serialize
            classElement: The Model Class element to update

        Returns:
            The new updated element
        """
        attributes = {
            XmlConstants.ATTRIBUTE_NAME:          field.name,
            XmlConstants.ATTRIBUTE_VISIBILITY:    field.visibility.name,
            XmlConstants.ATTRIBUTE_FIELD_TYPE:    field.type.value,
            XmlConstants.ATTRIBUTE_DEFAULT_VALUE: field.defaultValue,
        }
        fieldElement: Element = SubElement(classElement, XmlConstants.ELEMENT_MODEL_FIELD, attrib=attributes)

        return fieldElement

    def _implementorToXml(self, className: ClassName, interfaceElement: Element) -> Element:

        attributes: ElementAttributes = ElementAttributes({
            XmlConstants.ATTRIBUTE_IMPLEMENTING_CLASS_NAME: className,
        })
        implementorElement: Element = SubElement(interfaceElement, XmlConstants.ELEMENT_MODEL_IMPLEMENTOR, attrib=attributes)
        return implementorElement
