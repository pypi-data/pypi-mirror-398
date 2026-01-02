##
# File:  BirdReport.py
# Date:  19-Nov-2010
#
# Updates:
#     03-Feb-2012  Jdw  V3 PRD support --
#     31-Jan-2013  Jdw  Integrated within chemical reference data module
#     14-Jun-2017  jdw. refactored add coordinate handling
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

from mmcif_utils.bird.PdbxPrdIo import PdbxPrdIo
from mmcif_utils.chemcomp.PdbxChemCompIo import PdbxChemCompIo
from mmcif_utils.bird.PdbxPrdUtils import PdbxPrdUtils
from wwpdb.io.locator.ChemRefPathInfo import ChemRefPathInfo
from wwpdb.apps.chem_ref_data.report.ReportUtils import ReportUtils

logger = logging.getLogger(__name__)


class BirdReport(object):
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
        self.__prdId = None
        self.__prdFilePath = None
        self.__prdCcFilePath = None
        self.__prdFileFormat = "cif"
        #
        #
        self.__rU = ReportUtils(verbose=self.__verbose, log=self.__lfh)
        #

    def setPrdId(self, prdId):
        """Set an existing PRD identifier in archive collection as
        the report target
        """
        self.__prdId = str(prdId.upper())
        return self.__getFilePathFromId(self.__prdId)

    def setFilePath(self, prdFilePath, prdFileFormat, prdId):
        self.__prdFilePath = prdFilePath
        self.__prdFileFormat = prdFileFormat
        if not os.access(self.__prdFilePath, os.R_OK):
            return False
        if prdId is not None:
            self.__prdId = str(prdId).upper()
        #
        return True

    def getFilePath(self):
        return self.__prdFilePath

    def __getFilePathFromId(self, prdId):
        """ """
        self.__prdFilePath = self.__crPI.getFilePath(prdId)
        if not os.access(self.__prdFilePath, os.R_OK):
            return False
        self.__prdFileFormat = "cif"
        return True

    #

    def doReport(self):
        """Return content required to render a PRD report."""
        #
        oD = {}
        oD["dataDict"] = {}
        filePath = self.__prdFilePath
        fileFormat = self.__prdFileFormat
        blockId = self.__prdId
        prdCcFilePath = self.__prdCcFilePath
        #
        logger.info("+BirdReport.doReport()  - Starting doReport()")
        logger.info("+BirdReport.doReport()  - file path    %s", filePath)
        logger.info("+BirdReport.doReport()  - file format  %s", fileFormat)
        logger.info("+BirdReport.doReport()  - block Id     %s", blockId)
        #
        #
        # Make local copies of files -
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
            logger.info("+BirdReport.doReport() - Copied input file %s to report session path %s", filePath, localPath)

        #
        # Path context --
        oD["idCode"] = self.__prdId
        oD["filePath"] = filePath
        oD["localPath"] = localPath
        oD["localRelativePath"] = localRelativePath
        oD["sessionId"] = self.__sessionId
        oD["editOpNumber"] = 0
        oD["requestHost"] = self.__reqObj.getValue("request_host")
        oD["imageRelativePath"] = None
        oD["xyzRelativePath"] = None
        #
        pathToImage = None
        try:
            prdR = PdbxPrdIo(verbose=self.__verbose, log=self.__lfh)
            prdR.setFilePath(localPath, prdId=blockId)
            prdR.getPrd()

            prdU = PdbxPrdUtils(prdR, verbose=self.__verbose, log=self.__lfh)
            _rD = prdU.getComponentSequences(addCategory=True)  # noqa: F841  Might have side effects
            #
            if self.__prdId.startswith("PRD_"):
                tD = prdU.getChemCompIds()
                logger.info("For PRD %r CHEMICAL COMPONENT IDS are %r", self.__prdId, tD.items())
                tId = tD[self.__prdId]
                pathToImage = self.__crPI.getFilePath(tId)
                logger.info("ID for IMAGE is %r file path %r", tId, pathToImage)

                imagePath = os.path.join(self.__sessionPath, tId + ".svg")
                ok = self.__rU.makeImagesFromPathList(pathList=[pathToImage], imagePath=imagePath, rows=1, cols=1, imageX=700, imageY=700)
                if ok:
                    imageRelativePath = os.path.join(self.__sessionRelativePath, tId + ".svg")
                    oD["imageRelativePath"] = imageRelativePath
                else:
                    oD["imageRelativePath"] = None
                #
                if self.__verbose:
                    logger.info("+BirdReport.doReport() - PRD %r CC ID %r path to image %r", self.__prdId, tId, pathToImage)

            oD["blockId"] = prdR.getCurrentContainerId()
            if self.__verbose:
                logger.info("+BirdReport.doReport() - category name list %r", prdR.getCurrentCategoryNameList())
            # for catName in prdR.getCategoryList():
            for catName in prdR.getCurrentCategoryNameList():
                oD["dataDict"][catName] = prdR.getCategory(catName=catName)
        except:  # noqa: E722 pylint: disable=bare-except
            logger.exception("Report preparation failed for:  %s", fileName)

        #
        oD["hasExpt"] = False
        oD["hasIdeal"] = False
        if pathToImage is not None:
            try:
                localPrdCcRelativePath = ""
                prdCcFilePath = pathToImage
                if prdCcFilePath is not None:
                    (_pth, prdCcFileName) = os.path.split(prdCcFilePath)
                    dp = os.path.join(self.__sessionPath, "report")
                    localPrdCcPath = os.path.join(dp, prdCcFileName)
                    localPrdCcRelativePath = os.path.join(self.__sessionRelativePath, "report", prdCcFileName)
                    if prdCcFilePath != localPrdCcPath:
                        if not os.access(dp, os.F_OK):
                            os.makedirs(dp)
                    shutil.copyfile(prdCcFilePath, localPrdCcPath)
                    #
                    logger.info("+BirdReport.doReport() - Copied input PRDCC file %s to report session path %s", prdCcFilePath, localPrdCcPath)

                tD = {}
                tD["dataDict"] = {}
                ccR = PdbxChemCompIo(verbose=self.__verbose, log=self.__lfh)
                ccR.setFilePath(localPrdCcPath, compId=None)

                tD["blockId"] = ccR.getCurrentContainerId()
                logger.info("Category name list %r", ccR.getCurrentCategoryNameList())
                for catName in ccR.getCurrentCategoryNameList():
                    tD["dataDict"][catName] = ccR.getCategory(catName=catName)
                hasExpt, hasIdeal = self.__rU.coordinatesExist(tD["dataDict"])
                oD["hasExpt"] = hasExpt
                oD["hasIdeal"] = hasIdeal
                oD["xyzRelativePath"] = localPrdCcRelativePath
            except:  # noqa: E722 pylint: disable=bare-except
                logger.exception("Failing with fileName %r", fileName)

        return oD
