##
# File:  ChemRefDataMiscUtils.py
# Date:  16-Mar-2016  Migrated from cc_dict_utils  - J. Westbrook
#
# Updated:
#  18-Mar-2016  jdw adjust mode on data products to g+rw
#  18-Mar-2016  jdw add extra newline between concatenated components
#
"""
Wrapper for utilities for creating and maintaining various resource files containing
chemical reference data content stored in repositories and sandboxes.

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
import scandir
import filecmp
import fnmatch
import logging

from wwpdb.utils.config.ConfigInfo import ConfigInfo
from wwpdb.utils.config.ConfigInfoApp import ConfigInfoAppCc

from rcsb.utils.multiproc.MultiProcUtil import MultiProcUtil

from mmcif_utils.bird.PdbxPrdIo import PdbxPrdIo
from mmcif_utils.bird.PdbxPrdCcIo import PdbxPrdCcIo
from mmcif_utils.bird.PdbxFamilyIo import PdbxFamilyIo

from mmcif_utils.chemcomp.PdbxChemCompIo import PdbxChemCompIo

from wwpdb.utils.dp.RcsbDpUtility import RcsbDpUtility
from wwpdb.io.file.DataFile import DataFile

from wwpdb.utils.cc_dict_util.persist.PdbxChemCompDictUtil import PdbxChemCompDictUtil
from wwpdb.utils.cc_dict_util.persist.PdbxChemCompDictIndex import PdbxChemCompDictIndex

logger = logging.getLogger(__name__)


class ChemRefDataMiscUtils(object):
    """Wrapper for utilities for creating and maintaining various resource files containing
    chemical reference data content stored in repositories and sandboxes.
    """

    def __init__(self, reqObj, verbose=False, log=sys.stderr):
        """ """
        self.__verbose = verbose
        self.__lfh = log
        self.__debug = False
        #
        # Information injected from the request object -
        #
        self.__reqObj = reqObj
        #
        self.__sObj = self.__reqObj.getSessionObj()
        self.__sessionPath = self.__sObj.getPath()
        #

        self.__siteId = self.__reqObj.getValue("WWPDB_SITE_ID")
        self.__cI = ConfigInfo(self.__siteId)
        self.__cIConfigInfoCc = ConfigInfoAppCc(self.__siteId)
        self.__sbTopPath = self.__cIConfigInfoCc.get_site_refdata_top_cvs_sb_path()
        self.__projName = self.__cI.get("SITE_REFDATA_PROJ_NAME_CC")
        self.__ccDictPath = self.__cIConfigInfoCc.get_site_cc_dict_path()
        #
        self.__pathCCDict = self.__cIConfigInfoCc.get_cc_dict()
        self.__pathCCPathList = self.__cIConfigInfoCc.get_cc_path_list()
        self.__pathCCIdList = self.__cIConfigInfoCc.get_cc_id_list()
        self.__pathCCDictSerial = self.__cIConfigInfoCc.get_cc_dict_serial()
        self.__pathCCDictIdx = self.__cIConfigInfoCc.get_cc_dict_idx()
        #
        if sys.version_info[0] > 2:
            self.__pathCCDb = self.__cIConfigInfoCc.get_cc_db()
        else:
            self.__pathCCDb = os.path.join(self.__ccDictPath, "chemcomp.db")
        self.__pathCCIndex = self.__cIConfigInfoCc.get_cc_index()
        self.__pathCCParentIndex = self.__cIConfigInfoCc.get_cc_parent_index()

        self.__pathPrdChemCompCVS = self.__cIConfigInfoCc.get_site_prdcc_cvs_path()
        self.__pathPrdDictRef = self.__cIConfigInfoCc.get_site_prd_dict_path()
        self.__pathPrdDictFile = self.__cIConfigInfoCc.get_prd_dict_file()
        self.__pathPrdDictSerial = self.__cIConfigInfoCc.get_prd_dict_serial()
        self.__pathPrdCcFile = self.__cIConfigInfoCc.get_prd_cc_file()
        self.__pathPrdCcSerial = self.__cIConfigInfoCc.get_prd_cc_serial()
        self.__pathPrdSummary = self.__cIConfigInfoCc.get_prd_summary_cif()
        self.__pathPrdSummarySerial = self.__cIConfigInfoCc.get_prd_summary_sdb()
        self.__pathPrdFamilyMapping = self.__cIConfigInfoCc.get_prd_family_mapping()
        #
        self.__makeTopPaths()

    def __makeTopPaths(self):
        for top_path in (self.__ccDictPath, self.__pathPrdDictRef, self.__pathPrdChemCompCVS):
            if not os.path.exists(top_path):
                os.makedirs(top_path)

    def getBirdPathList(self):
        """Get pathlist for BIRD PRD and PRD Family data."""
        logger.info("+ChemRefDataLoad(getBirdPathList) Starting at %s", time.strftime("%Y %m %d %H:%M:%S", time.localtime()))
        try:
            #
            birdCachePath = self.__cIConfigInfoCc.get_site_prd_cvs_path()
            birdFamilyCachePath = self.__cIConfigInfoCc.get_site_family_cvs_path()
            birdCcCachePath = self.__cIConfigInfoCc.get_site_prdcc_cvs_path()
            #
            #
            prd = PdbxPrdIo(verbose=self.__verbose, log=self.__lfh)
            prd.setCachePath(birdCachePath)
            pathList = prd.makeDefinitionPathList()
            #
            prdFam = PdbxFamilyIo(verbose=self.__verbose, log=self.__lfh)
            prdFam.setCachePath(birdFamilyCachePath)
            familyPathList = prdFam.makeDefinitionPathList()
            #
            prdCc = PdbxPrdCcIo(verbose=self.__verbose, log=self.__lfh)
            prdCc.setCachePath(birdCcCachePath)
            prdCcPathList = prdCc.makeDefinitionPathList()
            #
            return pathList, familyPathList, prdCcPathList
        except:  # noqa: E722 pylint: disable=bare-except
            logger.exception("In getBirdPathList")

        logger.info("+ChemRefDataLoad(getBirdPathList) Completed at %s", time.strftime("%Y %m %d %H:%M:%S", time.localtime()))
        return [], [], []

    def __atomicRename(self, srcPath, dstPath, suffix=".old"):
        """Performs an atomic rename - while keeping the old file open to handle race conditions.
        On NFS, if you have a file open on server B, and server A moves (atomically) a new file onto another, the
        old file is unlinked by server.  Server B wlll then have a stale file handle for the already open file.

        The solution here is to hardlink the old file to a tempoerary, and then atomically move new to old -- the old
        inode is still valid until removed

        srcPath and dstPath must be on the same filesyetem.
        """

        tempPath = dstPath + suffix

        # Remove from previous round
        if os.path.exists(tempPath):
            os.remove(tempPath)

        if os.path.exists(dstPath):
            os.link(dstPath, tempPath)

        os.rename(srcPath, dstPath)

    def __makeTempPath(self, inpPath):
        try:
            pid = str(os.getpid())
            return inpPath + pid
        except:  # noqa: E722 pylint: disable=bare-except
            return inpPath

    def writeList(self, myList, outPath, mode=0o664):  # pylint: disable=unused-argument
        """ """
        try:
            tPath = self.__makeTempPath(outPath)
            ofh = open(tPath, "w")
            for el in myList:
                ofh.write("%s\n" % el)
            ofh.close()
            os.chmod(tPath, 0o664)
            shutil.move(tPath, outPath)
            return True
        except:  # noqa: E722 pylint: disable=bare-except
            return False

    def concatPathList(self, pathList, outPath, mode=0o664):
        """ """
        (ok, _update) = self.concatPathListExt(pathList, outPath, mode)
        return ok

    def concatPathListExt(self, pathList, outPath, mode=0o664, avoidUpdate=False):  # pylint: disable=unused-argument
        """
        Concatenates files in pathList. If avoidUpdate is set, compare temporary file
        vs. destination.

        Returns (status, updated) - status if concatenation good. If True, updated will be
        set of file moved into place.
        """
        try:
            tPath = self.__makeTempPath(outPath)
            with open(tPath, "wb") as outfile:
                for f in pathList:
                    with open(f, "rb") as infile:
                        outfile.write(infile.read())
                        # to handle missing trailing newlines =
                        outfile.write(b"\n")
            os.chmod(tPath, 0o664)

            if avoidUpdate and os.path.exists(outPath):
                if filecmp.cmp(tPath, outPath, shallow=False):
                    os.unlink(tPath)
                    return (True, False)

            shutil.move(tPath, outPath)
            return (True, True)
        except:  # noqa: E722 pylint: disable=bare-except
            logger.exception("In concatPathListExt")
            return (False, False)

    def updateChemCompSupportFiles(self, idMaxLen=5, numProc=4, skipIndex=False):
        """Create full idlist, pathlist, concatenated chemical component dictionary file,
        serialized dictionary, and dictionary index.
        If skipIndex is set, will avoid serialization and indexing operations for testing
        """
        ok1 = ok2 = ok3 = False
        pathList = self.getChemCompPathListMulti(numProc=numProc)
        idList = []
        for pth in pathList:
            (_dn, fn) = os.path.split(pth)
            (ccId, ext) = os.path.splitext(fn)
            if (len(ccId) <= idMaxLen) and (ext == ".cif"):
                idList.append(ccId)
        self.writeList(idList, self.__pathCCIdList)
        self.writeList(pathList, self.__pathCCPathList)
        ok1 = self.concatPathList(pathList, self.__pathCCDict)
        #
        if skipIndex:
            ok2 = True
            ok3 = True
        else:
            ok2 = self.__serializeDictOp()
            ok3 = self.__indexDictOp()
        return ok1 and ok2 and ok3

    def updateChemCompPySupportFiles(self):
        """Create BSD DB of full chemical component dictionary, PRD CC files, index and parent index pickle files."""
        ok = False
        startTime = time.time()
        logger.info("Starting at %s", time.strftime("%Y %m %d %H:%M:%S", time.localtime()))
        try:
            dU = PdbxChemCompDictUtil(verbose=self.__verbose, log=self.__lfh)
            logger.info("Starting full load at %s", time.strftime("%Y %m %d %H:%M:%S", time.localtime()))

            ok = dU.makeStoreFromFile(dictPath=self.__pathCCDict, storePath=self.__pathCCDb)
            logger.info("Finished full load at %s", time.strftime("%Y %m %d %H:%M:%S", time.localtime()))

            # We skip the next - as it incrementally loads the CC definitions into database which is good for low memory machines
            # but terribly slow
            # ok = self.updatePrdCCFiles()
            ok = True
            if ok:
                dIndx = PdbxChemCompDictIndex(verbose=self.__verbose, log=self.__lfh)
                dIndx.makeIndex(storePath=self.__pathCCDb, indexPath=self.__pathCCIndex)
                _pD, _cD = dIndx.makeParentComponentIndex(storePath=self.__pathCCDb, indexPath=self.__pathCCParentIndex)
                ok = True
            else:
                ok = False
        except:  # noqa: E722 pylint: disable=bare-except
            logger.exception("In updateChemCompPySupportFiles")
            ok = False

        endTime = time.time()
        logger.info("Completed at %s (%d seconds)", time.strftime("%Y %m %d %H:%M:%S", time.localtime()), endTime - startTime)
        return ok

    def __getPathList(self, topPath, pattern="*", excludeDirs=None, recurse=True):
        """Return a list of file paths in the input topPath which satisfy the input search criteria.

        This version does not follow symbolic links.
        """
        if excludeDirs is None:
            excludeDirs = []

        pathList = []
        #
        try:
            names = os.listdir(topPath)
        except os.error:
            return pathList

        # expand pattern
        pattern = pattern or "*"
        patternList = pattern.split(";")

        for name in names:
            fullname = os.path.normpath(os.path.join(topPath, name))
            # check for matching files
            for pat in patternList:
                if fnmatch.fnmatch(name, pat):
                    if os.path.isfile(fullname):
                        pathList.append(fullname)
                        continue
            if recurse:
                # recursively scan directories
                if os.path.isdir(fullname) and not os.path.islink(fullname) and (name not in excludeDirs):
                    pathList.extend(self.__getPathList(topPath=fullname, pattern=pattern, excludeDirs=excludeDirs, recurse=recurse))

        return pathList

    def updatePrdCCFiles(self):
        """Update persistent store from a path list of PRD chemical component defintions."""
        ok = False
        startTime = time.time()
        logger.info("Starting at %s", time.strftime("%Y %m %d %H:%M:%S", time.localtime()))
        try:
            ccPathList = self.__getPathList(topPath=self.__pathPrdChemCompCVS, pattern="*.cif", excludeDirs=["CVS", "REMOVED", "FULL"])
            if self.__verbose:
                logger.info("PRD CC pathlist length is %d", len(ccPathList))
            #
            dUtil = PdbxChemCompDictUtil(verbose=self.__verbose, log=self.__lfh)
            logger.info("Starting incremental load at %s", time.strftime("%Y %m %d %H:%M:%S", time.localtime()))
            dUtil.updateStoreByFile(pathList=ccPathList, storePath=self.__pathCCDb)
            logger.info("Finished incremental load at %s", time.strftime("%Y %m %d %H:%M:%S", time.localtime()))
            ok = True
            #
        except:  # noqa: E722 pylint: disable=bare-except
            logger.exception("updatePrdCCFiles")

        endTime = time.time()
        logger.info("Completed at %s (%d seconds)", time.strftime("%Y %m %d %H:%M:%S", time.localtime()), endTime - startTime)
        return ok

    def __indexDictOp(self, minSize=10):
        """Make chemical component dictionary index from serialized dictionary."""
        logger.info("Starting")
        startTime = time.time()
        try:
            outPathTmp = self.__makeTempPath(self.__pathCCDictIdx)
            inpPath = self.__pathCCDictSerial
            logPath = os.path.join(self.__ccDictPath, "chem-comp-dict-makeindex.log")
            dp = RcsbDpUtility(tmpPath=self.__sessionPath, siteId=self.__siteId, verbose=self.__verbose)
            #
            dp.setDebugMode(flag=self.__debug)
            dp.imp(inpPath)
            dp.op("chem-comp-dict-makeindex")
            dp.expLog(logPath)
            dp.exp(outPathTmp)
            fSize = dp.expSize()
            if fSize > minSize:
                os.chmod(outPathTmp, 0o664)
                self.__atomicRename(outPathTmp, self.__pathCCDictIdx)
                os.chmod(self.__pathCCDictIdx, 0o664)
                ok = True
            else:
                ok = False
            if not self.__debug:
                dp.cleanup()
            endTime0 = time.time()
            if self.__verbose:
                logger.info("Dictionary index file size %d  in %.2f seconds", fSize, endTime0 - startTime)
            return ok
        except:  # noqa: E722 pylint: disable=bare-except
            logger.exception("Failure in __indexDictOp")
        return False

    def __serializeDictOp(self, minSize=10):
        """Serialize chemical component dictionary from concatenated dictionary text."""
        logger.info("Starting")
        startTime = time.time()
        try:
            outPathTmp = self.__makeTempPath(self.__pathCCDictSerial)
            inpPath = self.__pathCCDict
            logPath = os.path.join(self.__ccDictPath, "chem-comp-dict-serialize.log")
            dp = RcsbDpUtility(tmpPath=self.__sessionPath, siteId=self.__siteId, verbose=self.__verbose)
            #
            dp.setDebugMode(flag=self.__debug)
            dp.imp(inpPath)
            dp.op("chem-comp-dict-serialize")
            dp.expLog(logPath)
            dp.exp(outPathTmp)
            fSize = dp.expSize()
            if fSize > minSize:
                os.chmod(outPathTmp, 0o664)
                self.__atomicRename(outPathTmp, self.__pathCCDictSerial)
                os.chmod(self.__pathCCDictSerial, 0o664)
                ok = True
            else:
                ok = False
            if not self.__debug:
                dp.cleanup()
            endTime0 = time.time()
            if self.__verbose:
                logger.info("Serialized dictionary file size %d  in %.2f seconds", fSize, endTime0 - startTime)
            return ok
        except:  # noqa: E722 pylint: disable=bare-except
            logger.exception("Failure in __serializeDictOp")
        return False

    def getChemCompPathList(self):
        startTime = time.time()
        logger.info("+ChemRefDataDbUtils(getChemCompPathList) Starting at %s", time.strftime("%Y %m %d %H:%M:%S", time.localtime()))
        try:
            chemCompCachePath = self.__cIConfigInfoCc.get_site_cc_cvs_path()
            #
            #
            cc = PdbxChemCompIo(verbose=self.__verbose, log=self.__lfh)
            cc.setCachePath(chemCompCachePath)
            pathList = cc.makeComponentPathList()
            endTime0 = time.time()
            if self.__verbose:
                logger.info("Path list length %d  in %.2f seconds", len(pathList), endTime0 - startTime)
            return pathList
        except:  # noqa: E722 pylint: disable=bare-except
            logger.exception("In getChemCompPathLisr")

        endTime = time.time()
        logger.info("+ChemRefDataDbUtils(getChemCompPathList) Completed at %s (%.2f seconds)", time.strftime("%Y %m %d %H:%M:%S", time.localtime()), endTime - startTime)
        return []

    def _makeComponentPathListMulti(self, dataList, procName, optionsD, workingDir):  # pylint: disable=unused-argument
        """Return the list of chemical component definition file paths in the current repository."""
        pathList = []
        for subdir in dataList:
            dd = os.path.join(self.__sbTopPath, self.__projName, subdir)
            for root, _dirs, files in scandir.walk(dd, topdown=False):
                if "REMOVE" in root:
                    continue
                for name in files:
                    if name.endswith(".cif") and len(name) <= 9:  # Extends to support 5 character CCD
                        pathList.append(os.path.join(root, name))

        return dataList, pathList, []

    def getChemCompPathListMulti(self, numProc=8):
        """Return path list for all chemical component definition data files - (multiprocessing version)"""
        if self.__verbose:
            logger.info("Starting")
        startTime = time.time()
        try:
            dataS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
            dataList = [a for a in dataS]

            # Extended CCD support
            ext_ccd = self.__cIConfigInfoCc.get_extended_ccd_supp()
            if ext_ccd:
                dataList += [(a + b) for a in dataS for b in dataS]

            mpu = MultiProcUtil(verbose=True)
            mpu.set(workerObj=self, workerMethod="_makeComponentPathListMulti")
            _ok, _failList, retLists, _diagList = mpu.runMulti(dataList=dataList, numProc=numProc, numResults=1)
            pathList = retLists[0]
            endTime0 = time.time()
            if self.__verbose:
                logger.info("Path list length %d  in %.2f seconds", len(pathList), endTime0 - startTime)

            return pathList
        except:  # noqa: E722 pylint: disable=bare-except
            logger.exception("In getChemCompPathListMulti")

        endTime = time.time()
        logger.info("Completed at %s (%.2f seconds)", time.strftime("%Y %m %d %H:%M:%S", time.localtime()), endTime - startTime)
        return []

    def updatePrdSupportFiles(self, idMaxLen=14, numProc=4):  # pylint: disable=unused-argument
        """Create full idlist, pathlist, concatenated PRD dictionary file,
        serialized dictionary, and dictionary index.
        """
        startTime = time.time()
        ok1 = ok2 = ok3 = ok4 = ok5 = ok6 = False
        pathList, familyPathList, ccPathList = self.getBirdPathList()

        #        self.writeList(idList, self.__pathCCIdList)
        #        self.writeList(pathList, self.__pathCCPathList)
        (ok1, updated) = self.concatPathListExt(pathList, self.__pathPrdDictFile, avoidUpdate=True)
        # If prd file updated, then need serial
        if ok1 and updated:
            ok2 = self.__serializePrdDictOp("prd")
        else:
            ok2 = True

        (ok3, updated) = self.concatPathListExt(ccPathList, self.__pathPrdCcFile, avoidUpdate=True)
        if ok3 and updated:
            ok4 = self.__serializePrdDictOp("prdcc")
        else:
            ok4 = True

        # PRD summary files
        ok5 = self.__generatePrdSummaryOp()

        # Get family mappings
        ok6 = self.__generatePrdFamilyMapOp(familyPathList)

        endTime = time.time()
        logger.info("Completed  at %s (%.2f seconds)", time.strftime("%Y %m %d %H:%M:%S", time.localtime()), endTime - startTime)
        #        #
        #        ok2 =
        #        ok3 = self.__indexDictOp()
        #        return ok1 and ok2 and ok3
        return ok1 and ok2 and ok3 and ok4 and ok5 and ok6

    def __serializePrdDictOp(self, which, minSize=10):
        """Serialize chemical component dictionary from concatenated dictionary text."""
        logger.info("Starting %s", which)
        startTime = time.time()

        fList = {
            "prd": [self.__pathPrdDictFile, self.__pathPrdDictSerial, "prd-dict-serialize.log"],
            "prdcc": [self.__pathPrdCcFile, self.__pathPrdCcSerial, "prdcc-dict-serialize.log"],
        }
        try:
            ref = fList[which]
            outPathTmp = self.__makeTempPath(ref[1])
            inpPath = ref[0]
            logPath = os.path.join(self.__pathPrdDictRef, ref[2])
            dp = RcsbDpUtility(tmpPath=self.__sessionPath, siteId=self.__siteId, verbose=self.__verbose)
            #
            dp.setDebugMode(flag=self.__debug)
            dp.imp(inpPath)
            dp.op("chem-comp-dict-serialize")
            dp.expLog(logPath)
            dp.exp(outPathTmp)
            fSize = dp.expSize()
            if fSize > minSize:
                os.chmod(outPathTmp, 0o664)
                shutil.move(outPathTmp, ref[1])
                os.chmod(ref[1], 0o664)
                ok = True
            else:
                ok = False
            if not self.__debug:
                dp.cleanup()
            endTime0 = time.time()
            if self.__verbose:
                logger.info("Serialized dictionary file size %d  in %.2f seconds", fSize, endTime0 - startTime)
            return ok
        except:  # noqa: E722 pylint: disable=bare-except
            logger.exception("In __serializePrdDictOp")
        return False

    def __generatePrdSummaryOp(self, minSize=10):
        """Generate summary cif file and serialize it"""
        logger.info("Starting")
        startTime = time.time()

        ccSDBin = self.__pathCCDictSerial
        prdSDBin = self.__pathPrdDictSerial
        outPathTmp = self.__makeTempPath(self.__pathPrdSummary)
        outPathSerialTmp = self.__makeTempPath(self.__pathPrdSummarySerial)
        fSize = 0

        ok1 = ok2 = False
        try:
            logPath = os.path.join(self.__pathPrdDictRef, "prd-summary.log")
            dp = RcsbDpUtility(tmpPath=self.__sessionPath, siteId=self.__siteId, verbose=self.__verbose)
            dp.setDebugMode(flag=self.__debug)
            dp.imp(prdSDBin)
            dp.addInput(name="ccsdb_path", value=ccSDBin)
            dp.op("prd-summary-serialize")
            dp.expLog(logPath)
            dp.expList([outPathTmp, outPathSerialTmp])
            # If changed....
            updated = False
            f1 = DataFile(outPathTmp)
            if f1.srcFileExists():
                ok1 = True
                fSize = f1.srcFileSize()
                if fSize > minSize:
                    outPath = self.__pathPrdSummary
                    if os.path.exists(outPath):
                        if not filecmp.cmp(outPathTmp, outPath, shallow=False):
                            updated = True
                            os.unlink(outPath)
                    else:
                        updated = True

                    if updated:
                        os.chmod(outPathTmp, 0o664)
                        shutil.move(outPathTmp, outPath)
                        os.chmod(outPath, 0o664)
                    else:
                        f1.remove()
            else:
                ok1 = False

            f1 = DataFile(outPathSerialTmp)
            if updated:
                if f1.srcFileExists():
                    ok2 = True

                    updated = False
                    fSize = f1.srcFileSize()
                    if fSize > minSize:
                        outPath = self.__pathPrdSummarySerial
                        updated = False
                        if os.path.exists(outPath):
                            if not filecmp.cmp(outPathSerialTmp, outPath, shallow=False):
                                os.unlink(outPath)
                                updated = True
                        else:
                            updated = True

                    if updated:
                        os.chmod(outPathSerialTmp, 0o664)
                        shutil.move(outPathSerialTmp, outPath)
                        os.chmod(outPath, 0o664)
                    else:
                        f1.remove()
            else:
                f1.remove()
                ok2 = False

            if not self.__debug:
                dp.cleanup()
            endTime0 = time.time()

            # logger.info("Dictionary summary update ok1 %s ok2 %s", ok1, ok2)
            if self.__verbose:
                logger.info("Dictionary summary file size %d  in %.2f seconds", fSize, endTime0 - startTime)
            return ok1 and ok2

        except:  # noqa: E722 pylint: disable=bare-except
            logger.exception("In generatePrdSummaryOp")

        return False

    def __generatePrdFamilyMapOp(self, familyPathList, minSize=10):
        """Generate family mapping file"""
        logger.info("Starting")

        # We do not retain concatenation when done...
        tempFamilyFile = os.path.join(self.__pathPrdDictRef, "prd-family-temp.cif")
        outPathTmp = self.__makeTempPath(self.__pathPrdFamilyMapping)

        ok = self.concatPathList(familyPathList, tempFamilyFile)

        if ok:
            try:
                logPath = os.path.join(self.__pathPrdDictRef, "prd-family.log")
                dp = RcsbDpUtility(tmpPath=self.__sessionPath, siteId=self.__siteId, verbose=self.__verbose)
                dp.setDebugMode(flag=self.__debug)
                dp.imp(tempFamilyFile)
                dp.op("prd-family-mapping")
                dp.expLog(logPath)
                dp.exp(outPathTmp)
                fSize = dp.expSize()
                if fSize > minSize:
                    outPath = self.__pathPrdFamilyMapping
                    updated = False
                    if os.path.exists(outPath):
                        if not filecmp.cmp(outPathTmp, outPath, shallow=False):
                            os.unlink(outPath)
                            updated = True
                    else:
                        updated = True

                    if updated:
                        os.chmod(outPathTmp, 0o664)
                        shutil.move(outPathTmp, outPath)
                        os.chmod(outPath, 0o664)
                    else:
                        try:
                            os.unlink(outPathTmp)
                        except:  # noqa: E722 pylint: disable=bare-except
                            pass
                    # Remove tempFamilyFile
                    try:
                        os.unlink(tempFamilyFile)
                    except:  # noqa: E722 pylint: disable=bare-except
                        pass

                if not self.__debug:
                    dp.cleanup()
                return True

            except:  # noqa: E722 pylint: disable=bare-except
                logger.exception("Failure in generatePrdMapOp")

        return False
