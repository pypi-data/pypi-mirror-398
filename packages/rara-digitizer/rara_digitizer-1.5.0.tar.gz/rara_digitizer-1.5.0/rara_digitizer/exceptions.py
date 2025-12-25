class MissingMETSMetadata(Exception):
    pass


class MissingSupportedMETSSections(Exception):
    pass


class MultipleMETSFilesFound(Exception):
    pass


class NoMETSFileFound(Exception):
    pass


class PathNotFound(Exception):
    pass


class NotLoadedOrEmpty(Exception):
    pass


class UnsupportedFile(Exception):
    pass


class FileTypeOrStructureMismatch(Exception):
    pass


class PageOutOfRange(Exception):
    pass


class ConversionFailed(Exception):
    pass


class DuplicateResourceKey(Exception):
    pass


class InvalidResourceKey(Exception):
    pass


class MissingEpubResource(Exception):
    pass


class UnknownTxtEncoding(Exception):
    pass


class MetsTagNotFound(Exception):
    pass

class XmlFileNotFound(Exception):
    pass