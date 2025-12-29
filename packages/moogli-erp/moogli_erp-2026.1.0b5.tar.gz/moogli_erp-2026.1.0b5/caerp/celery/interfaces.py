from zope.interface import Interface, Attribute


class IAccountingFileParser(Interface):
    """
    Interface pour les outils de lecture de Grand Livre
    """

    def __init__(self, pyramid_request, file_path):
        """ """


class IAccountingOperationProducer(Interface):
    """
    Produces accounting line data

    From a file or other source (api for example)
    """

    def set_data_source(self, source):
        """
        Set the data source used to produce accounting lines

        source can be :
            - a File buffer (result of open(filepath))
            - api connection data (no implementation yet)
        """

    def stream_lines(self) -> dict:
        """yield accounting operations in dict format"""
