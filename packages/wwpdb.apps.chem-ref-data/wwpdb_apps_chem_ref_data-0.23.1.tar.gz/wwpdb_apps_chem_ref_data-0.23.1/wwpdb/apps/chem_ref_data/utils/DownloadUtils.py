##
# File:  DownloadUtils.py
# Date:  12-Feb-2013
#
# Updated:
# 14-Feb-2013 jdw reorganize api  method, add fetchFile and fetchId methods.
#
"""
Common methods for managing session files and chemical reference data files for
download.

"""
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "jwest@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.07"

import sys
import os
import os.path
import shutil
import logging

from wwpdb.io.locator.ChemRefPathInfo import ChemRefPathInfo

logger = logging.getLogger(__name__)


class DownloadUtils(object):
    """Common methods for managing session files and chemical reference data files for
    download.
    """

    #

    def __init__(self, reqObj=None, verbose=False, log=sys.stderr):
        """Input request object is used to determine session context."""
        self.__verbose = verbose
        self.__lfh = log
        self.__reqObj = reqObj
        #
        self.__siteId = self.__reqObj.getValue("WWPDB_SITE_ID")
        self.__crPI = ChemRefPathInfo(siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)
        #
        self.__sessionId = self.__reqObj.getSessionId()
        self.__sessionPath = self.__reqObj.getSessionPath()
        #
        self.__sessionDir = "sessions"
        self.__downloadDir = "downloads"
        #
        self.__downloadDirPath = os.path.join(self.__sessionPath, self.__sessionId, self.__downloadDir)
        self.__webDownloadDirPath = os.path.join("/", self.__sessionDir, self.__sessionId, self.__downloadDir)
        self.__webDownloadFilePath = None
        #
        self.__targetFilePath = None
        self.__targetFileName = None
        self.__downloadFilePath = None
        self.__setup()

    def __setup(self):
        if not os.access(self.__downloadDirPath, os.W_OK):
            os.makedirs(self.__downloadDirPath, 0o755)

    def getIdType(self, idCode):
        return self.__crPI.getIdType(idCode=idCode)

    def getIdFromFileName(self, filePath):
        return self.__crPI.assignIdCodeFromFileName(filePath)

    def fetchId(self, idCode):
        filePath = self.__crPI.getFilePath(idCode=idCode)
        return self.fetchFile(filePath)

    def fetchFile(self, filePath):
        """Save input file in session download"""
        try:
            if self.__verbose:
                logger.info("+DownloadUtils.fetchFile() + target file path %s", filePath)
            self.__targetFilePath = filePath
            (_pth, self.__targetFileName) = os.path.split(self.__targetFilePath)
            self.__downloadFilePath = os.path.join(self.__downloadDirPath, self.__targetFileName)
            shutil.copyfile(self.__targetFilePath, self.__downloadFilePath)
            self.__webDownloadFilePath = os.path.join(self.__webDownloadDirPath, self.__targetFileName)
            return True
        except:  # noqa: E722 pylint: disable=bare-except
            if self.__verbose:
                logger.info("+DownloadUtils.fetchFile() + failed for file %s", filePath)
            logger.exception("Failure in fetchFile")
        return False

    def getWebPath(self):
        """ """
        return self.__webDownloadFilePath

    def getDownloadPath(self):
        """ """
        return self.__downloadFilePath

    def getAnchorTag(self, label=None, target="_blank"):
        """Return the anchor tag corresponding the current download file selection."""
        if label is not None and len(label) > 0:
            txt = label
        else:
            txt = self.__targetFileName

        return '<a href="%s" target="%s">%s</a>' % (self.__webDownloadFilePath, target, txt)
