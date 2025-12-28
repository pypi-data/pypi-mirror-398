class FileNotOpenError(IOError):
    """Raised when a method requires the file to be open"""
    pass


class FileAlreadyOpenedError(IOError):
    """Raised when a method cannot be called while file is opened"""
    pass


class FileAlreadyOpenedForReadError(FileAlreadyOpenedError):
    """Raised when file is already opened for reading"""
    pass


class FileAlreadyOpenedForWriteError(FileAlreadyOpenedError):
    """Raised when file is already opened for writing"""
    pass