##
# File:  ChemRefDataCvsUtils.py
# Date:  4-Feb-2013  J. Westbrook
#
# Updated:
#
# 4-Feb-2013 jdw  Generalized from class ChemRefDataCvsUtils() for all chemical reference data repositories.
# 7-Feb-2013 jdw  Add remove method
##
"""
Wrapper for utilities for managing chemical reference data repositories and sandboxes.

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
import time
import logging

from wwpdb.utils.config.ConfigInfo import ConfigInfo
from wwpdb.utils.config.ConfigInfoApp import ConfigInfoAppCc
from wwpdb.io.cvs.CvsAdmin import CvsAdmin, CvsSandBoxAdmin
from rcsb.utils.multiproc.MultiProcUtil import MultiProcUtil
from wwpdb.io.locator.ChemRefPathInfo import ChemRefPathInfo

logger = logging.getLogger(__name__)


class ChemRefDataCvsUtils(object):

    """Wrapper for utilities for managing chemical reference data repositories and sandboxes."""

    #

    def __init__(self, reqObj, verbose=False, log=sys.stderr):
        """ """
        self.__verbose = verbose
        self.__lfh = log
        self.__debug = False
        #
        # Information injected from the request object -
        #
        self.__reqObj = reqObj
        # self.__topPath             = self.__reqObj.getValue("TopPath")
        # self.__topSessioPath       = self.__reqObj.getValue("TopSessionPath")
        #
        self.__sObj = self.__reqObj.getSessionObj()
        self.__sessionPath = self.__sObj.getPath()
        # self.__sessionRelativePath = self.__sObj.getRelativePath()
        # self.__sessionId           = self.__sObj.getId()
        #
        self.__siteId = self.__reqObj.getValue("WWPDB_SITE_ID")
        self.__cI = ConfigInfo(self.__siteId)
        self.__cIAppCc = ConfigInfoAppCc(self.__siteId)
        self.__sbTopPath = self.__cIAppCc.get_site_refdata_top_cvs_sb_path()
        self.__pI = ChemRefPathInfo(siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)
        #
        self.__vc, self.__vcAd = self.__setupCvs()
        #

    def __setupCvs(self):
        #  Assign site specific chemical reference data CVS repository details --
        #
        cvsRepositoryHost = self.__cI.get("SITE_REFDATA_CVS_HOST")
        cvsRepositoryPath = self.__cI.get("SITE_REFDATA_CVS_PATH")
        #
        # Assign authentication details from the request environment -
        #
        # cvsUser = self.__reqObj.getValue("SITE_REFDATA_CVS_USER")
        # cvsPassword = self.__reqObj.getValue("SITE_REFDATA_CVS_PASSWORD")
        #
        cvsUser = self.__cI.get("SITE_REFDATA_CVS_USER")
        cvsPassword = self.__cI.get("SITE_REFDATA_CVS_PASSWORD")
        #
        vc = CvsSandBoxAdmin(tmpPath=self.__sessionPath, verbose=self.__verbose, log=self.__lfh)
        vc.setRepositoryPath(host=cvsRepositoryHost, path=cvsRepositoryPath)
        vc.setAuthInfo(user=cvsUser, password=cvsPassword)
        vc.setSandBoxTopPath(self.__sbTopPath)
        vcAd = CvsAdmin(tmpPath=self.__sessionPath, verbose=self.__verbose, log=self.__lfh)
        vcAd.setRepositoryPath(host=cvsRepositoryHost, path=cvsRepositoryPath)
        vcAd.setAuthInfo(user=cvsUser, password=cvsPassword)

        return vc, vcAd

    def getSandBoxTopPath(self):
        return self.__vc.getSandBoxTopPath()

    def syncBird(self):
        """Update the CVS repositories related to BIRD PRD, family and chemical component definitions."""
        #
        textList = []
        #
        cvsProjectName = self.__pI.assignCvsProjectName(repType="PRD")
        ok1, text = self.__vc.update(projectDir=cvsProjectName, prune=True)
        if self.__verbose:
            logger.info("+ChemRefDataCvsUtils(sync) CVS %s update output is: %s", cvsProjectName, text)
        textList.append(text)
        #
        cvsProjectName = self.__pI.assignCvsProjectName(repType="PRD_FAMILY")
        ok2, text = self.__vc.update(projectDir=cvsProjectName)
        if self.__verbose:
            logger.info("+ChemRefDataCvsUtils(sync) CVS %s update output is: %s", cvsProjectName, text)
        textList.append(text)
        #
        cvsProjectName = self.__pI.assignCvsProjectName(repType="PRDCC")
        ok3, text = self.__vc.update(projectDir=cvsProjectName)
        if self.__verbose:
            logger.info("+ChemRefDataCvsUtils(sync) CVS %s update output is:%s", cvsProjectName, text)
        textList.append(text)
        self.__vc.cleanup()
        #
        ok = ok1 and ok2 and ok3
        return (ok, textList)

    def checkoutChemCompSerial(self):
        """
        checkout the CVS repository for the CCD
        """
        textList = []
        cvsProjectName = self.__pI.assignCvsProjectName(repType="CC")
        ok, text = self.__vc.checkOut(projectPath=cvsProjectName)
        if self.__verbose:
            logger.info("+ChemRefDataCvsUtils(checkout) CVS %s update status is: %r", cvsProjectName, ok)
            # logger.info("+ChemRefDataCvsUtils(sync) CVS %s update output is:\n%s\n" % (cvsProjectName,text[:100]))
        textList.append(text[:100])
        #
        # self.__vc.cleanup()
        #
        return (ok, textList)

    def checkoutPRDSerial(self):
        """
        checkout the CVS repository for the PRD
        """
        textList = []
        cvsProjectName = self.__pI.assignCvsProjectName(repType="PRD")
        ok, text = self.__vc.checkOut(projectPath=cvsProjectName)
        if self.__verbose:
            logger.info("+ChemRefDataCvsUtils(checkout) CVS %s update status is: %r", cvsProjectName, ok)
            # logger.info("+ChemRefDataCvsUtils(sync) CVS %s update output is:\n%s\n" % (cvsProjectName,text[:100]))
        textList.append(text[:100])
        cvsProjectName = self.__pI.assignCvsProjectName(repType="PRD_FAMILY")
        ok, text = self.__vc.checkOut(projectPath=cvsProjectName)
        if self.__verbose:
            logger.info("+ChemRefDataCvsUtils(checkout) CVS %s update status is: %r", cvsProjectName, ok)
            # logger.info("+ChemRefDataCvsUtils(sync) CVS %s update output is:\n%s\n" % (cvsProjectName,text[:100]))
        textList.append(text[:100])
        cvsProjectName = self.__pI.assignCvsProjectName(repType="PRDCC")
        ok, text = self.__vc.checkOut(projectPath=cvsProjectName)
        if self.__verbose:
            logger.info("+ChemRefDataCvsUtils(checkout) CVS %s update status is: %r", cvsProjectName, ok)
            # logger.info("+ChemRefDataCvsUtils(sync) CVS %s update output is:\n%s\n" % (cvsProjectName,text[:100]))
        textList.append(text[:100])
        #
        # self.__vc.cleanup()
        #
        return (ok, textList)

    def syncChemCompSerial(self):
        """Update the CVS repositories related to the chemical component dicitonary."""
        #
        textList = []
        #
        cvsProjectName = self.__pI.assignCvsProjectName(repType="CC")
        ok, text = self.__vc.update(projectDir=cvsProjectName, prune=True)
        if self.__verbose:
            logger.info("+ChemRefDataCvsUtils(sync) CVS %s update status is: %r", cvsProjectName, ok)
            # logger.info("+ChemRefDataCvsUtils(sync) CVS %s update output is:\n%s\n" % (cvsProjectName,text[:100]))
        textList.append(text[:100])
        #
        # self.__vc.cleanup()
        #
        return (ok, textList)

    def syncChemComp(self, numProc=8):
        """Update the CVS repositories related to the chemical component dicitonary."""
        #
        startTime = time.time()
        #
        cvsProjectName = self.__pI.assignCvsProjectName(repType="CC")
        dataS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        dataList = [(cvsProjectName, a, True) for a in dataS]

        # Extended CCD support
        ext_ccd = self.__cIAppCc.get_extended_ccd_supp()
        if ext_ccd:
            dataList += [(cvsProjectName, a + b, True) for a in dataS for b in dataS]

        #
        mpu = MultiProcUtil(verbose=self.__debug)
        mpu.set(workerObj=self.__vc, workerMethod="updateList")
        ok, failList, _resultList, diagList = mpu.runMulti(dataList=dataList, numProc=numProc)
        endTime = time.time()
        if self.__verbose:
            logger.info("+ChemRefDataCvsUtils(syncChemComp) CVS %s update status is: %r in %.2f seconds", cvsProjectName, ok, endTime - startTime)

            if len(failList) > 0:
                logger.info("+ChemRefDataCvsUtils(syncChemComp) diagnostics %r", failList)
        return (ok, diagList)

    def updateFile(self, filePath):
        """Update the input file within the appropriate repository.  File names must obey repository
        naming conventions.

        """
        #
        textList = []
        ok = False
        #
        if not self.checkFileName(filePath):
            textList.append("Unrecognized file name %s" % filePath)
            return ok, textList

        if not self.exists(filePath):
            textList.append("Cannot update nonexistent repository file %s" % filePath)
            return ok, textList

        #
        projName, relPath = self.__pI.getCvsProjectInfo(self.__pI.assignIdCodeFromFileName(filePath))

        dstPath = os.path.join(self.__vc.getSandBoxTopPath(), projName, relPath)
        # (pth, fn) = os.path.split(dstPath)

        if self.__verbose:
            logger.info("+ChemRefDataCvsUtils(updateFile) CVS update %s %s working repository path is %s", projName, relPath, dstPath)

        #
        try:
            # make sure we have the latest version
            self.__vc.checkOut(os.path.join(projName, relPath))
            shutil.copy2(filePath, dstPath)
            ok, text = self.__vc.commit(projName, relPath)

        except:  # noqa: E722 pylint: disable=bare-except
            text = "+ChemRefDataCvsUtils(updateFile) CVS update exception"
            if self.__verbose:
                logger.info("+ChemRefDataCvsUtils(updateFile) CVS update %s %s status %r output is: %s", projName, relPath, ok, text)
                logger.exception("Unknown failued in CVS update")

        textList.append(text)
        if self.__verbose:
            logger.info("+ChemRefDataCvsUtils(updateFile) CVS update %s %s status %r output is: %s", projName, relPath, ok, text)
        self.__vc.cleanup()
        #
        return ok, textList

    def addFile(self, filePath):
        """Add the input file to the appropriate repository.  File names must obey repository
        naming conventions.

        """
        #
        textList = []
        ok = False
        #
        if not self.checkFileName(filePath):
            textList.append("Unrecognized file name %s" % filePath)
            return ok, textList

        if self.exists(filePath):
            textList.append("Cannot add existing repository file name %s" % filePath)
            return ok, textList

        #
        projName, relPath = self.__pI.getCvsProjectInfo(self.__pI.assignIdCodeFromFileName(filePath))

        dstPath = os.path.join(self.__vc.getSandBoxTopPath(), projName, relPath)
        (pth, _fn) = os.path.split(dstPath)

        if self.__verbose:
            logger.info("+ChemRefDataCvsUtils(addFile) CVS add %s %s working repository path is %s", projName, relPath, dstPath)

        # add any missing containing directories for the destination file.
        try:
            if not os.access(pth, os.F_OK):
                os.makedirs(pth)
                head, _tail = os.path.split(relPath)
                self.__vc.add(projName, head)
            shutil.copy2(filePath, dstPath)
            self.__vc.add(projName, relPath)
            ok, text = self.__vc.commit(projName, relPath)

        except:  # noqa: E722 pylint: disable=bare-except
            text = "+ChemRefDataCvsUtils(addFile) CVS add exception"
            if self.__verbose:
                logger.info("+ChemRefDataCvsUtils(addFile) CVS add %s %s status %r output is: %s", projName, relPath, ok, text)
                logger.exception("Failure in CVS add")

        textList.append(text)
        if self.__verbose:
            logger.info("+ChemRefDataCvsUtils(addFile) CVS add %s %s status %r output is: %s", projName, relPath, ok, text)
        self.__vc.cleanup()
        #
        return ok, textList

    def history(self, idCode):
        """Return the version history for the input id code from the appropriate repository.

        Id codes must obey repository naming conventions.

        """
        #
        textList = []
        ok = False
        #
        projName, relPath = self.__pI.getCvsProjectInfo(idCode)
        if projName is None or relPath is None:
            return ok, textList

        if self.__verbose:
            logger.info("+ChemRefDataCvsUtils(history) CVS history id %s project %s  path %s", idCode, projName, relPath)
        #
        try:
            cvsPath = os.path.join(projName, relPath)
            ok, text = self.__vcAd.getHistory(cvsPath)
            textList.append(text)
        except:  # noqa: E722 pylint: disable=bare-except
            textList.append("CVS history exception")
            if self.__verbose:
                logger.info("+ChemRefDataCvsUtils(history) CVS history exception %s %s status %r output is: %s", projName, relPath, ok, textList)
                logger.exception("Failure in CVS history")

        if self.__verbose:
            logger.info("+ChemRefDataCvsUtils(remove) CVS history %s %s status %r output is: %s", projName, relPath, ok, textList)
        self.__vcAd.cleanup()
        #
        return ok, textList

    def checkoutRevisions(self, idCode):
        """Return the pathlist of checked out revisions for the input id code from the appropriate repository.

        Id codes must obey repository naming conventions.

        """
        #
        pathList = []
        revList = []
        ok = False
        #
        projName, relPath = self.__pI.getCvsProjectInfo(idCode)
        if projName is None or relPath is None:
            return ok, pathList

        if self.__verbose:
            logger.info("+ChemRefDataCvsUtils(checkoutRevisions) id %s project %s  path %s", idCode, projName, relPath)
        #
        try:
            cvsPath = os.path.join(projName, relPath)
            ok, revList = self.__vcAd.getRevisionList(cvsPath)

            (_pth, fn) = os.path.split(cvsPath)
            (_base, ext) = os.path.splitext(fn)

            for revId in revList:
                rId = revId[0]
                outPath = os.path.join(self.__sessionPath, idCode + "-" + rId + ext)
                ok, text = self.__vcAd.checkOutFile(cvsPath=cvsPath, outPath=outPath, revId=rId)
                if ok:
                    pathList.append(outPath)
                    logger.info("CVS checkout status %r output %s is: %s", ok, outPath, text)
        except:  # noqa: E722 pylint: disable=bare-except
            pathList.append("Revision checkout exception")
            if self.__verbose:
                logger.info("+ChemRefDataCvsUtils(checkoutRevisions) exception %s %s status %r output is: %s", projName, relPath, ok, pathList)
                logger.exception("Failure in CVS revision checkout")

        if self.__verbose:
            logger.info("+ChemRefDataCvsUtils(checkoutRevisions) done %s %s status %r output is: %s", projName, relPath, ok, pathList)
        self.__vcAd.cleanup()
        #
        return ok, pathList

    def remove(self, idCode):
        """Remove the reference file associated with the input id code from the appropriate repository.
        Id codes must obey repository naming conventions.

        """
        #
        text = ""
        textList = []
        ok = False
        #
        projName, relPath = self.__pI.getCvsProjectInfo(idCode)
        if projName is None or relPath is None:
            return ok, textList

        if self.__verbose:
            logger.info("+ChemRefDataCvsUtils(remove) CVS remove id %s project %s  path %s", idCode, projName, relPath)
        #
        try:
            ok1, text = self.__vc.remove(projName, relPath, saveCopy=True)
            textList.append(text)

            # Remove the containing directory if required.
            repType = self.__pI.getIdType(idCode)
            if repType == "CC":
                (pth, _fn) = os.path.split(relPath)
                ok2, text = self.__vc.removeDir(projName, pth)
                textList.append(text)
                ok = ok1 and ok2
            else:
                ok = ok1
        except:  # noqa: E722 pylint: disable=bare-except
            textList.append("+ChemRefDataCvsUtils(remove) CVS remove exception")
            if self.__verbose:
                logger.info("+ChemRefDataCvsUtils(remove) CVS remove %s %s status %r output is: %s", projName, relPath, ok, text)
                logger.exception("Failure in CVS remove")

        if self.__verbose:
            logger.info("+ChemRefDataCvsUtils(remove) CVS remove %s %s status %r output is: %s", projName, relPath, ok, textList)
        self.__vc.cleanup()
        #
        return ok, textList

    def exists(self, filePath):
        """Test if the input 'filePath' corresponds to an existing entry in one of
        CVS repositories.

        Return True if an existing entry is found or False otherwise
        """
        if (filePath is None) or (len(filePath) < 7):
            return False

        projName, relPath = self.__pI.getCvsProjectInfo(self.__pI.assignIdCodeFromFileName(filePath))
        projPath = self.__pI.getProjectPath(self.__pI.assignIdCodeFromFileName(filePath))
        if projName is None:
            return False

        # check existing for file within the repository sandbox -
        if os.access(os.path.join(projPath, relPath), os.R_OK):
            return True

        return False

    def checkFileName(self, filePath):
        """Test if the input 'filePath' corresponds to the naming conventions of on of the
        CVS repositories.

        Return True for success or False otherwise
        """
        if (filePath is None) or (len(filePath) < 7):
            return False
        projName, _relPath = self.__pI.getCvsProjectInfo(self.__pI.assignIdCodeFromFileName(filePath))
        return projName is not None
