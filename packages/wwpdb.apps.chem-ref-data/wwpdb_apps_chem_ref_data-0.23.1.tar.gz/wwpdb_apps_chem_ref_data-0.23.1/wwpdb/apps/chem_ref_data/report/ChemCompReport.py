##
# File:  ChemCompReport.py
# Date:  19-Nov-2010
#
# Updates:
#     03-Feb-2012  Jdw  V3 PRD support --
#     31-Jan-2013  Jdw  Integrated within chemical reference data module
#     14-Jul-2013  jdw  add chemical depiction to report
#     14-Jun-2017  jdw  refactor change coordinate handling -
##
"""
PRD report generator -

"""
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "jwest@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.01"

import os
import sys
import shutil
import logging

from mmcif_utils.chemcomp.PdbxChemCompIo import PdbxChemCompIo
from wwpdb.io.locator.ChemRefPathInfo import ChemRefPathInfo
from wwpdb.apps.chem_ref_data.report.ReportUtils import ReportUtils

logger = logging.getLogger(__name__)


class ChemCompReport(object):
    """PRD report generator functions."""

    def __init__(self, reqObj, verbose=False, log=sys.stderr):
        """PRD report generator.

        :param `verbose`:  boolean flag to activate verbose logging.
        :param `log`:      stream for logging.

        """
        self.__verbose = verbose
        self.__lfh = log
        #
        self.__reqObj = reqObj
        #
        self.__sObj = self.__reqObj.newSessionObj()
        self.__sessionPath = self.__sObj.getPath()
        self.__sessionRelativePath = self.__sObj.getRelativePath()
        self.__sessionId = self.__sObj.getId()
        #
        self.__siteId = self.__reqObj.getValue("WWPDB_SITE_ID")
        self.__crPI = ChemRefPathInfo(siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)

        #
        self.__ccId = None
        self.__ccFilePath = None
        self.__ccFileFormat = "cif"
        #
        self.__rU = ReportUtils(verbose=self.__verbose, log=self.__lfh)
        #

    def setCcId(self, ccId):
        """Set an existing PRD identifier in archive collection as
        the report target
        """
        self.__ccId = str(ccId.upper())
        return self.__getFilePathFromId(self.__ccId)

    def setFilePath(self, ccFilePath, ccFileFormat="cif", ccId=None):
        self.__ccFilePath = ccFilePath
        self.__ccFileFormat = ccFileFormat
        if not os.access(self.__ccFilePath, os.R_OK):
            return False
        if ccId is not None:
            self.__ccId = str(ccId).upper()
        #
        return True

    def getFilePath(self):
        return self.__ccFilePath

    def __getFilePathFromId(self, ccId):
        """ """
        self.__ccFilePath = self.__crPI.getFilePath(ccId)
        if not os.access(self.__ccFilePath, os.R_OK):
            return False
        self.__ccFileFormat = "cif"
        return True

    #

    def doReport(self):
        """Return content required to render a chemical component tabular report."""
        #
        oD = {}
        oD["dataDict"] = {}
        filePath = self.__ccFilePath
        fileFormat = self.__ccFileFormat
        blockId = self.__ccId
        #
        logger.info("+ChemCompReport.doReport()  - Starting doReport()n")
        logger.info("+ChemCompReport.doReport()  - file path    %s", filePath)
        logger.info("+ChemCompReport.doReport()  - file format  %s", fileFormat)
        logger.info("+ChemCompReport.doReport()  - block Id     %s", blockId)

        #
        # make a local copy of the file (if required)
        #
        (_pth, fileName) = os.path.split(filePath)
        dirPath = os.path.join(self.__sessionPath, "report")
        localPath = os.path.join(dirPath, fileName)
        localRelativePath = os.path.join(self.__sessionRelativePath, "report", fileName)
        if filePath != localPath:
            if not os.access(dirPath, os.F_OK):
                os.makedirs(dirPath)
            shutil.copyfile(filePath, localPath)
            #

            logger.info("+ChemCompReport.doReport() - Copied input file %s to report session path %s", filePath, localPath)
        #
        # Path context --
        oD["idCode"] = self.__ccId
        oD["filePath"] = filePath
        oD["localPath"] = localPath
        oD["localRelativePath"] = localRelativePath
        oD["sessionId"] = self.__sessionId
        oD["editOpNumber"] = 0
        oD["requestHost"] = self.__reqObj.getValue("request_host")
        oD["xyzRelativePath"] = localRelativePath
        #
        imagePath = os.path.join(self.__sessionPath, self.__ccId + ".svg")
        ok = self.__rU.makeImagesFromPathList(pathList=[localPath], imagePath=imagePath, rows=1, cols=1, imageX=700, imageY=700)
        if ok:
            imageRelativePath = os.path.join(self.__sessionRelativePath, oD["idCode"] + ".svg")
            oD["imageRelativePath"] = imageRelativePath
        else:
            oD["imageRelativePath"] = None
        #
        try:
            ccR = PdbxChemCompIo(verbose=self.__verbose, log=self.__lfh)
            ccR.setFilePath(localPath, compId=blockId)

            oD["blockId"] = ccR.getCurrentContainerId()
            if self.__verbose:
                logger.info("+ChemCompReport.doReport() - category name list %r", ccR.getCurrentCategoryNameList())
            for catName in ccR.getCurrentCategoryNameList():
                oD["dataDict"][catName] = ccR.getCategory(catName=catName)
            hasExpt, hasIdeal = self.__rU.coordinatesExist(oD["dataDict"])
            oD["hasExpt"] = hasExpt
            oD["hasIdeal"] = hasIdeal
        except:  # noqa: E722 pylint: disable=bare-except
            logger.exception("Failing with fileName %r", fileName)

        return oD
