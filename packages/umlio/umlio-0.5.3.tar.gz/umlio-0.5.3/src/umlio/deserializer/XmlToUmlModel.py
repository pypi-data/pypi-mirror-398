
from typing import cast

from dataclasses import dataclass

from logging import Logger
from logging import getLogger

from os import linesep as osLineSep

from umlmodel.UmlModelBase import UmlModelBase
from untangle import Element

from umlmodel.Field import Field
from umlmodel.Field import Fields
from umlmodel.FieldType import FieldType
from umlmodel.Method import Method
from umlmodel.Method import Methods
from umlmodel.Method import Modifiers
from umlmodel.Method import Parameters
from umlmodel.Method import SourceCode
from umlmodel.Modifier import Modifier
from umlmodel.Parameter import Parameter
from umlmodel.ParameterType import ParameterType
from umlmodel.ReturnType import ReturnType
from umlmodel.SDInstance import SDInstance
from umlmodel.enumerations.Visibility import Visibility

from umlmodel.Actor import Actor
from umlmodel.Class import Class
from umlmodel.Link import Link
from umlmodel.Note import Note
from umlmodel.Text import Text
from umlmodel.Link import LinkSource
from umlmodel.UseCase import UseCase
from umlmodel.Interface import Interface
from umlmodel.SDMessage import SDMessage
from umlmodel.Link import LinkDestination

from umlmodel.enumerations.LinkType import LinkType
from umlmodel.enumerations.Stereotype import Stereotype
from umlmodel.enumerations.DisplayMethods import DisplayMethods
from umlmodel.enumerations.DisplayParameters import DisplayParameters

from codeallybasic.Common import XML_END_OF_LINE_MARKER
from codeallybasic.SecureConversions import SecureConversions

from umlio.IOTypes import Elements

from umlio.XMLConstants import XmlConstants


@dataclass
class ConvolutedModelSDMessageInformation:
    """
    This class is necessary because I do not want to mix UML Shapes and UML mode code;  Unfortunately,
    the IDs of the SDInstance are buried and require a lookup

    """
    sdMessage:     SDMessage = cast(SDMessage, None)
    sourceId:      str           = '-1'
    destinationId: str           = '-1'


class XmlToUmlModel:
    """
    Converts Uml Model Version 14 XML to Uml Model instance
    """
    NOTE_NAME:   str = 'Note'
    noteCounter: int = 0

    def __init__(self):

        self.logger: Logger = getLogger(__name__)

    def classToModelClass(self, umlClassElement: Element) -> Class:
        classElement: Element = umlClassElement.ModelClass

        modelClass: Class = Class()

        modelClass = cast(Class, self._addUmlBaseAttributes(modelElement=classElement, umlModelBase=modelClass))

        displayStr:              str               = classElement[XmlConstants.ATTRIBUTE_DISPLAY_PARAMETERS]
        displayParameters:       DisplayParameters = DisplayParameters(displayStr)
        displayConstructorStr:   str               = classElement[XmlConstants.ATTRIBUTE_DISPLAY_CONSTRUCTOR]
        displayDunderMethodsStr: str               = classElement[XmlConstants.ATTRIBUTE_DISPLAY_DUNDER_METHODS]

        displayConstructor:   DisplayMethods = self._secureDisplayMethods(displayStr=displayConstructorStr)
        displayDunderMethods: DisplayMethods = self._secureDisplayMethods(displayStr=displayDunderMethodsStr)

        showStereotype:     bool = bool(classElement[XmlConstants.ATTRIBUTE_DISPLAY_STEREOTYPE])
        showFields:         bool = bool(classElement[XmlConstants.ATTRIBUTE_DISPLAY_FIELDS])
        showMethods:        bool = bool(classElement[XmlConstants.ATTRIBUTE_DISPLAY_METHODS])
        stereotypeStr:      str  = classElement[XmlConstants.ATTRIBUTE_STEREOTYPE]
        fileName:           str  = classElement[XmlConstants.ATTRIBUTE_FILENAME]

        modelClass.displayParameters    = displayParameters
        modelClass.displayConstructor   = displayConstructor
        modelClass.displayDunderMethods = displayDunderMethods

        modelClass.displayStereoType = showStereotype
        modelClass.showFields        = showFields
        modelClass.showMethods       = showMethods

        modelClass.description = classElement[XmlConstants.ATTRIBUTE_DESCRIPTION]
        modelClass.stereotype  = Stereotype.toEnum(stereotypeStr)
        modelClass.fileName    = fileName

        modelClass.methods = self._methodToModelMethods(classElement=classElement)
        modelClass.fields  = self._fieldToModelFields(classElement=classElement)

        return modelClass

    def textToModelText(self, umlTextElement: Element) -> Text:
        """
        Parses the Text elements

        Args:
            umlTextElement:   Of the form:   <UmlText id="xx.xx.xx"/>

        Returns: A model text Object
        """
        textElement: Element = umlTextElement.ModelText
        text:        Text    = Text()

        text.id  = textElement[XmlConstants.ATTRIBUTE_ID]

        rawContent:   str = textElement['content']
        cleanContent: str = rawContent.replace(XML_END_OF_LINE_MARKER, osLineSep)
        text.content = cleanContent

        return text

    def noteToModelNote(self, umlNoteElement: Element) -> Note:
        """
        Parse Note element

        Args:
            umlNoteElement: of the form:  <UmlNote id="xx.xx.xx"/>

        Returns: A model note object
        """
        noteElement = umlNoteElement.ModelNote

        note: Note = Note()

        # fix line feeds
        note = cast(Note, self._addUmlBaseAttributes(modelElement=noteElement, umlModelBase=note))

        rawContent:   str = noteElement[XmlConstants.ATTRIBUTE_CONTENT]
        cleanContent: str = rawContent.replace(XML_END_OF_LINE_MARKER, osLineSep)
        note.content = cleanContent

        return note

    def interfaceToModelInterface(self, umlInterfaceElement: Element) -> Interface:

        interfaceElement: Element = umlInterfaceElement.ModelInterface

        interfaceId: str = interfaceElement[XmlConstants.ATTRIBUTE_ID]
        name:        str = interfaceElement[XmlConstants.ATTRIBUTE_NAME]
        description: str = interfaceElement[XmlConstants.ATTRIBUTE_DESCRIPTION]

        interface: Interface  = Interface(name=name)
        interface.id          = interfaceId
        interface.description = description

        implementors: Elements = cast(Elements, interfaceElement.get_elements(XmlConstants.ELEMENT_MODEL_IMPLEMENTOR))
        for implementor in implementors:
            interface.addImplementor(implementor[XmlConstants.ELEMENT_MODEL_IMPLEMENTING_CLASS_NAME])

        interface.methods = self._interfaceMethodsToMethods(interface=interfaceElement)

        return interface

    def actorToModelActor(self, umlActorElement: Element) -> Actor:
        """

        Args:
            umlActorElement:   untangle Element in the above format

        Returns:   A model Actor
        """
        actorElement: Element = umlActorElement.ModelActor
        actor:        Actor   = Actor()

        actor = cast(Actor, self._addUmlBaseAttributes(modelElement=actorElement, umlModelBase=actor))

        return actor

    def useCaseToModelUseCase(self, umlUseCaseElement: Element) -> UseCase:
        """

        Args:
            umlUseCaseElement:  An `untangle` Element in the above format

        Returns:  Model Use Case
        """
        useCaseElement: Element = umlUseCaseElement.ModelUseCase
        useCase:    UseCase = UseCase()

        useCase = cast(UseCase, self._addUmlBaseAttributes(modelElement=useCaseElement, umlModelBase=useCase))

        return useCase

    def linkToModelLink(self, singleLink: Element, source: LinkSource, destination: LinkDestination) -> Link:

        linkTypeStr:     str          = singleLink[XmlConstants.ATTRIBUTE_LINK_TYPE]

        linkType:        LinkType = LinkType.toEnum(linkTypeStr)
        cardSrc:         str      = singleLink[XmlConstants.ATTRIBUTE_SOURCE_CARDINALITY_VALUE]
        cardDest:        str      = singleLink[XmlConstants.ATTRIBUTE_DESTINATION_CARDINALITY_VALUE]
        bidir:           bool     = SecureConversions.secureBoolean(singleLink[XmlConstants.ATTRIBUTE_BIDIRECTIONAL])
        linkDescription: str      = singleLink['name']

        link: Link = Link(name=linkDescription,
                          linkType=linkType,
                          cardinalitySource=cardSrc, cardinalityDestination=cardDest,
                          bidirectional=bidir,
                          source=source,
                          destination=destination
                          )

        return link

    def sdInstanceToModelSDInstance(self, umlSDInstanceElement: Element) -> SDInstance:

        instanceElement: Element    = umlSDInstanceElement.ModelSDInstance
        sdInstance:  SDInstance = SDInstance()

        sdInstance.id                     = instanceElement[XmlConstants.ATTRIBUTE_ID]
        sdInstance.instanceName           = instanceElement[XmlConstants.ATTRIBUTE_INSTANCE_NAME]
        sdInstance.instanceLifeLineLength = SecureConversions.secureInteger(instanceElement[XmlConstants.ATTRIBUTE_LIFE_LINE_LENGTH])

        return sdInstance

    def sdMessageToModelSDMessage(self, umlSDMessageElement: Element) -> ConvolutedModelSDMessageInformation:
        """
        TODO:  Need to fix how SD Messages are created
        Args:
            umlSDMessageElement:

        Returns:  Bogus data class
        """
        messageElement: Element = umlSDMessageElement.ModelSDMessage

        sdMessage:  SDMessage = SDMessage()

        sdMessage.id = messageElement[XmlConstants.ATTRIBUTE_ID]
        sdMessage.message = messageElement[XmlConstants.ATTRIBUTE_MESSAGE]
        sdMessage.linkType = LinkType.SD_MESSAGE

        srcID: str = messageElement[XmlConstants.ATTRIBUTE_SD_MESSAGE_SOURCE_ID]
        dstID: str = messageElement[XmlConstants.ATTRIBUTE_SD_MESSAGE_DESTINATION_ID]

        srcTime: int = int(messageElement[XmlConstants.ATTRIBUTE_SOURCE_TIME])
        dstTime: int = int(messageElement[XmlConstants.ATTRIBUTE_DESTINATION_TIME])

        sdMessage.sourceY      = srcTime
        sdMessage.destinationY = dstTime

        bogus: ConvolutedModelSDMessageInformation = ConvolutedModelSDMessageInformation()

        bogus.sdMessage = sdMessage
        bogus.sourceId      = srcID
        bogus.destinationId = dstID

        return bogus

    def _methodToModelMethods(self, classElement: Element) -> Methods:
        """
        The model class may not have methods;

        Args:
            classElement:  The model class element

        Returns:  May return an empty list
        """
        untangledModelMethods: Methods = Methods([])

        methodElements: Elements = cast(Elements, classElement.get_elements(XmlConstants.ELEMENT_MODEL_METHOD))

        for methodElement in methodElements:
            methodName: str        = methodElement['name']
            visibility: Visibility = Visibility.toEnum(methodElement[XmlConstants.ATTRIBUTE_VISIBILITY])
            self.logger.debug(f"{methodName=} - {visibility=}")

            method: Method = Method(name=methodName, visibility=visibility)

            method.modifiers = self._modifierToModelMethodModifiers(methodElement=methodElement)

            returnAttribute = methodElement[XmlConstants.ATTRIBUTE_METHOD_RETURN_TYPE]
            method.returnType = ReturnType(returnAttribute)

            parameters = self._paramToModelParameters(methodElement)
            method.parameters = parameters
            method.sourceCode = self._sourceCodeToModelSourceCode(methodElement=methodElement)

            untangledModelMethods.append(method)

        return untangledModelMethods

    def _fieldToModelFields(self, classElement: Element) -> Fields:
        untangledFields: Fields = Fields([])

        fieldElements: Elements = cast(Elements, classElement.get_elements(XmlConstants.ELEMENT_MODEL_FIELD))

        for fieldElement in fieldElements:
            visibility: Visibility = Visibility.toEnum(fieldElement[XmlConstants.ATTRIBUTE_VISIBILITY])
            fieldName    = fieldElement[XmlConstants.ATTRIBUTE_NAME]
            fieldType    = FieldType(fieldElement[XmlConstants.ATTRIBUTE_FIELD_TYPE])
            defaultValue = fieldElement[XmlConstants.ATTRIBUTE_DEFAULT_VALUE]

            field: Field = Field(name=fieldName, visibility=visibility, type=fieldType, defaultValue=defaultValue)

            untangledFields.append(field)

        return untangledFields

    def _modifierToModelMethodModifiers(self, methodElement: Element) -> Modifiers:
        """
        Should be in this form:

            <Modifier name="Modifier1"/>
            <Modifier name="Modifier2"/>
            <Modifier name="Modifier3"/>
            <Modifier name="Modifier4"/>

        Args:
            methodElement:

        Returns:   A Modifiers list that may be empty.
        """

        modifierElements = methodElement.get_elements('Modifier')

        modifiers: Modifiers = Modifiers([])
        if len(modifierElements) > 0:
            for modifierElement in modifierElements:
                modifierName:           str       = modifierElement['name']
                modifier: Modifier = Modifier(name=modifierName)
                modifiers.append(modifier)

        return modifiers

    def _paramToModelParameters(self, methodElement: Element) -> Parameters:

        parameterElements = methodElement.get_elements(XmlConstants.ELEMENT_MODEL_PARAMETER)

        untangledModelMethodParameters: Parameters = Parameters([])
        for parameterElement in parameterElements:
            name:           str = parameterElement[XmlConstants.ATTRIBUTE_NAME]
            defaultValue:   str = parameterElement[XmlConstants.ATTRIBUTE_DEFAULT_VALUE]

            parameterType:  ParameterType = ParameterType(parameterElement[XmlConstants.ATTRIBUTE_PARAMETER_TYPE])

            parameter: Parameter = Parameter(name=name, type=parameterType, defaultValue=defaultValue)

            untangledModelMethodParameters.append(parameter)

        return untangledModelMethodParameters

    def _sourceCodeToModelSourceCode(self, methodElement: Element) -> SourceCode:

        sourceCodeElements = methodElement.get_elements(XmlConstants.ELEMENT_MODEL_SOURCE_CODE)
        codeElements = sourceCodeElements[0].get_elements(XmlConstants.ELEMENT_MODEL_CODE)
        sourceCode: SourceCode = SourceCode([])
        for codeElement in codeElements:
            self.logger.debug(f'{codeElement.cdata=}')
            codeLine: str = codeElement.cdata
            sourceCode.append(codeLine)
        return sourceCode

    def _interfaceMethodsToMethods(self, interface: Element) -> Methods:

        methods: Methods = self._methodToModelMethods(interface)

        return methods

    def _addUmlBaseAttributes(self, modelElement: Element, umlModelBase: UmlModelBase) -> UmlModelBase:
        """

        Args:
            modelElement: The model Element XML with common keys
            umlModelBase: The base UML Attributes to update

        Returns:  The updated UML instance as
        """

        umlModelBase.id       = modelElement[XmlConstants.ATTRIBUTE_ID]
        umlModelBase.name     = modelElement[XmlConstants.ATTRIBUTE_NAME]
        umlModelBase.fileName = modelElement[XmlConstants.ATTRIBUTE_FILENAME]

        if umlModelBase.name is None:
            XmlToUmlModel.noteCounter += 1
            umlModelBase.name = f'{XmlToUmlModel.NOTE_NAME}-{XmlToUmlModel.noteCounter}'
        return umlModelBase

    def _secureDisplayMethods(self, displayStr: str) -> DisplayMethods:

        if displayStr is not None:
            displayMethods: DisplayMethods = DisplayMethods(displayStr)
        else:
            displayMethods = DisplayMethods.UNSPECIFIED

        return displayMethods
