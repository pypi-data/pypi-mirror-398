##
# File:  ChemRefDataWebApp.py
# Date:  5-Nov-2010
#
# Updates:
#  6-Nov-2010 Add rdbms load and cvs sync
#
#  3-Feb-2012 jdw Support for V3 PRD and family files
# 12-Sep-2012 jdw add CVS add and update for PRDCC files --
#
# 25-Nov-2012 jdw migrate to wwPDB new framework
# 24-Jan-2013 jdw add id search options
# 25-Jan-2013 jdw replace scripted cvs sync and dbload with new api calls.
# 28-Jan-2013 jdw replace scripted update/add with new api calls.
# 30-Jan-2013 jdw integrate into chemical reference data package.
#  2-Feb-2013 jdw revise return values for AJAX methods.
#  4-Feb-2013 jdw Add classes ChemRefDataCvsUtils() & ChemRefDataDbUtils() which
#                 support all chemical reference data.
#  4-Feb-2013 jdw Add service methods for chemical component data.
#  *-Feb-2013 jdw Much refactoring for Bootstrap framework.
# 20-Feb-2013 jdw Use common WebRequest module.
# 23-May-2017 jdw Overhaul - strip all old methods
#
##
"""
Chemical Reference Data (CRD) tool web request and response processing modules.

This software was developed as part of the World Wide Protein Data Bank
Common Deposition and Annotation System Project

Copyright (c) wwPDB

This software is provided under a Creative Commons Attribution 3.0 Unported
License described at http://creativecommons.org/licenses/by/3.0/.

"""
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "jwest@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.07"

import os
import sys
import shutil
import types
import ntpath

from wwpdb.io.file.mmCIFUtil import mmCIFUtil
from wwpdb.utils.session.WebRequest import InputRequest, ResponseContent

# from wwpdb.utils.session.UtilDataStore import UtilDataStore
#
from wwpdb.apps.chem_ref_data.report.BirdReport import BirdReport
from wwpdb.apps.chem_ref_data.report.ChemCompReport import ChemCompReport
from wwpdb.apps.chem_ref_data.report.ChemRefReportDepictBootstrap import ChemRefReportDepictBootstrap

#
from wwpdb.apps.chem_ref_data.search.ChemRefSearch import ChemRefSearch
from wwpdb.apps.chem_ref_data.search.ChemRefSearchDepictBootstrap import ChemRefSearchDepictBootstrap

from wwpdb.apps.chem_ref_data.utils.ChemRefDataCvsUtils import ChemRefDataCvsUtils
from wwpdb.apps.chem_ref_data.utils.ChemRefDataDbUtils import ChemRefDataDbUtils
from wwpdb.io.locator.ChemRefPathInfo import ChemRefPathInfo
from wwpdb.apps.chem_ref_data.utils.DownloadUtils import DownloadUtils
from wwpdb.apps.chem_ref_data.utils.ChemRefDataMiscUtils import ChemRefDataMiscUtils

from mmcif_utils.style.PrdCategoryStyle import PrdCategoryStyle
from mmcif_utils.style.ChemCompCategoryStyle import ChemCompCategoryStyle

from wwpdb.utils.config.ConfigInfo import ConfigInfo
from wwpdb.utils.config.ConfigInfoApp import ConfigInfoAppCommon
from wwpdb.utils.dp.RcsbDpUtility import RcsbDpUtility

#
import logging

logger = logging.getLogger(__name__)

#


class ChemRefDataWebApp(object):
    """Handle request and response object processing for the chemical reference data services."""

    def __init__(self, parameterDict=None, verbose=False, log=sys.stderr, siteId="WWPDB_DEPLOY_TEST"):
        """
        Create an instance of `ChemRefDataWebApp` to manage a chemical reference data  web requests.

         :param `parameterDict`: dictionary storing parameter information from the web request.
             Storage model for GET and POST parameter data is a dictionary of lists.
         :param `verbose`:  boolean flag to activate verbose logging.
         :param `log`:      stream for logging.

        """
        if parameterDict is None:
            parameterDict = {}

        self.__verbose = verbose
        self.__lfh = log
        self.__debug = False
        self.__siteId = siteId
        #
        self.__cICommon = ConfigInfoAppCommon(self.__siteId)
        self.__topPath = self.__cICommon.get_site_web_apps_top_path()
        self.__topSessionPath = self.__cICommon.get_site_web_apps_top_sessions_path()
        #

        if isinstance(parameterDict, dict):
            self.__myParameterDict = parameterDict
        else:
            self.__myParameterDict = {}

        logger.info("+ChemRefDataWebApp.__init() - STARTING REQUEST ------------------------------------")

        self.__reqObj = InputRequest(self.__myParameterDict, verbose=self.__verbose, log=self.__lfh)

        self.__templatePath = os.path.join(self.__topPath, "htdocs", "chem_ref_data_ui")
        #
        self.__reqObj.setValue("TopSessionPath", self.__topSessionPath)
        self.__reqObj.setValue("TemplatePath", self.__templatePath)
        self.__reqObj.setValue("AppHtdocsPath", self.__templatePath)
        self.__reqObj.setValue("TopPath", self.__topPath)
        self.__reqObj.setValue("WWPDB_SITE_ID", self.__siteId)
        os.environ["WWPDB_SITE_ID"] = self.__siteId

        #
        self.__reqObj.setDefaultReturnFormat(return_format="html")
        #
        if self.__debug:
            self.__reqObj.printIt(ofh=self.__lfh)
            logger.info("+ChemRefDataWebApp.__init() - completed\n---------------------------------------------\n")
            self.__lfh.flush()

    def doOp(self):
        """Execute request and package results in a response dictionary object.

        :returns:
             A dictionary containing response data for the input request.
             Minimally, the content of this dictionary will include the
             keys: CONTENT_TYPE and REQUEST_STRING.

        """
        stw = ChemRefDataWebAppWorker(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
        rC = stw.doOp()
        if self.__debug:
            rqp = self.__reqObj.getRequestPath()
            logger.info("+ChemRefDataWebApp.doOp() request path %s", rqp)
            logger.info("+ChemRefDataWebApp.doOp() return format %s", self.__reqObj.getReturnFormat())
            if rC is not None:
                logger.debug("%s", ("".join(rC.dump())))
            else:
                logger.info("+ChemRefDataWebApp.doOp() return object is empty")
        #
        return rC.get()


class ChemRefDataWebAppWorker(object):
    def __init__(self, reqObj=None, verbose=False, log=sys.stderr):
        """
        Worker methods for the chemical reference data module.

        Performs URL -> application mapping for this module.

        All operations can be driven from this interface which can
        supplied with control information from web application request
        or from a testing application.


        """
        self.__verbose = verbose
        self.__debug = False
        self.__lfh = log
        self.__reqObj = reqObj
        self.__sObj = None
        self.__sessionId = None
        self.__sessionPath = None
        self.__rltvSessionPath = None

        #
        self.__siteId = self.__reqObj.getValue("WWPDB_SITE_ID")
        self.__cI = ConfigInfo(self.__siteId)
        # self.__cICommon = ConfigInfoAppCommon(self.__siteId)
        self.__crPI = ChemRefPathInfo(siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)

        #
        # self.__uds = UtilDataStore(reqObj=self.__reqObj, prefix=None, verbose=self.__verbose, log=self.__lfh)

        #
        # Reference data configuration items include:
        #
        #
        self.__appPathD = {
            "/service/environment/dump": "_dumpOp",
            # -------------------
            "/service/chemref/search": "_chemRefFullSearchOp",
            "/service/chemref/search/autocomplete": "_chemRefFullSearchAutoCompeteOp",
            # -------------------
            "/service/chemref/newsession": "_newSessionOp",
            # '/service/chemref/getsessioninfo':                    '_getSessionInfoOp',
            "/service/chemref/adminops": "_chemRefAdminOps",
            "/service/chemref/inline_idops": "_chemRefInlineIdOps",
            "/service/chemref/inline_fileops": "_chemRefInlineFileOps",
            "/service/chemref/editor": "_chemRefEditorOps",
        }

    def doOp(self):
        """Map operation to path and invoke operation.  Exceptions are caught within this method.

        :returns:

        Operation output is packaged in a ResponseContent() object.

        """
        #
        try:
            reqPath = self.__reqObj.getRequestPath()
            if reqPath not in self.__appPathD:
                # bail out if operation is unknown -
                rC = ResponseContent(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
                rC.setError(errMsg="Unknown operation")
            else:
                mth = getattr(self, self.__appPathD[reqPath], None)
                rC = mth()
            return rC
        except:  # noqa: E722 pylint: disable=bare-except
            logger.exception("doOp failing")
            rC = ResponseContent(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
            rC.setError(errMsg="Operation failure")
            return rC

    # ------------------------------------------------------------------------------------------------------------
    #      Top-level REST methods
    #
    #
    def _dumpOp(self):
        rC = ResponseContent(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
        rC.setHtmlList(self.__reqObj.dump(format="html"))
        return rC

    #
    # ---------------------------------------------------------------------------------------------------
    #
    #                      File-based methods on the ADMIN path implemented with JSON responses -
    #
    def _chemRefInlineFileOps(self):
        """Chemical reference data operations on uploaded files."""
        operation = self.__reqObj.getValue("operation")
        logger.info("+ChemRefDataWebAppWorker._chemRefInlineFileOps() starting with op %s", operation)

        isFile = False
        self.__getSession()
        self.__reqObj.setReturnFormat(return_format="json")
        rC = ResponseContent(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)

        filePath = None
        rootName = None
        if self.__isFileUpload():
            # make a copy of the file in the session directory and set 'fileName'
            self.__uploadFile()
            fileName = self.__reqObj.getValue("fileName")
            filePath = os.path.join(self.__sessionPath, fileName)
            (rootName, _ext) = os.path.splitext(fileName)
            isFile = True

        logger.info("+ChemRefDataWebAppWorker._chemRefInlineFileOps() filePath %s", filePath)

        #
        aTagList = []
        htmlList = []
        webPathList = []
        myIdList = []
        hasDiags = False

        if not isFile or fileName is None or len(fileName) < 1:
            rC.setError(errMsg="File upload failed.")

        elif operation in ["report"]:
            du = DownloadUtils(self.__reqObj, verbose=self.__verbose, log=self.__lfh)
            du.fetchFile(filePath)
            idCode = du.getIdFromFileName(filePath)
            # myIdList.append(idCode)
            repType = du.getIdType(idCode)
            downloadPath = du.getDownloadPath()
            # webPathList.append(du.getWebPath())
            aTagList.append(du.getAnchorTag())
            #
            oL, _, webXyzPath = self.__makeTabularReport(filePath=downloadPath, repositoryType=repType, idCode=idCode, layout="tabs")
            htmlList.extend(oL)
            myIdList.append(idCode)
            webPathList.append(webXyzPath)

            if len(aTagList) > 0:
                rC.setHtmlLinkText('<span class="url-list">View: %s</span>' % ",&nbsp;&nbsp;".join(aTagList))
                rC.setHtmlList(htmlList)
                rC.setStatus(statusMsg="Reports completed")
                rC.set("webPathList", webPathList)
                rC.set("idCodeList", myIdList)
            else:
                rC.setError(errMsg="Report preparation failed")

        elif operation in ["check", "cvsupdate", "cvsadd"]:
            logPath = os.path.join(self.__sessionPath, rootName + "-cif-check.log")
            self.__removeFile(logPath)
            hasDiags = self.__makeCifCheckReport(filePath, logPath)
            if hasDiags:
                du = DownloadUtils(self.__reqObj, verbose=self.__verbose, log=self.__lfh)
                du.fetchFile(logPath)
                aTagList.append(du.getAnchorTag())
                rC.setHtmlLinkText('<span class="url-list">View: %s</span>' % ",&nbsp;&nbsp;".join(aTagList))
                rC.setStatus(statusMsg="Check completed")
            else:
                rC.setHtmlLinkText("")
                rC.setStatus(statusMsg="No diagnostics for %s" % fileName)

        if hasDiags:
            return rC

        if operation == "cvsupdate":
            logPath = os.path.join(self.__sessionPath, rootName + "-cvs-update.log")
            self.__removeFile(logPath)
            ok = self.__doCvsUpdate(filePath, logPath)
            if ok:
                du = DownloadUtils(self.__reqObj, verbose=self.__verbose, log=self.__lfh)
                du.fetchFile(logPath)
                aTagList.append(du.getAnchorTag())
                rC.setHtmlLinkText('<span class="url-list">View: %s</span>' % ",&nbsp;&nbsp;".join(aTagList))
                rC.setStatus(statusMsg="Update completed")
            else:
                rC.setStatus(statusMsg="Update failed for %s" % fileName)
        elif operation == "cvsadd":
            logPath = os.path.join(self.__sessionPath, rootName + "-cvs-add.log")
            self.__removeFile(logPath)
            ok = self.__doCvsAdd(filePath, logPath)
            if ok:
                du = DownloadUtils(self.__reqObj, verbose=self.__verbose, log=self.__lfh)
                du.fetchFile(logPath)
                aTagList.append(du.getAnchorTag())
                rC.setHtmlLinkText('<span class="url-list">View: %s</span>' % ",&nbsp;&nbsp;".join(aTagList))
                rC.setStatus(statusMsg="Add completed")
            else:
                rC.setStatus(statusMsg="Add failed for %s" % fileName)
        elif operation == "annotatecomp":
            logPath = os.path.join(self.__sessionPath, rootName + "-annot-comp.log")
            self.__removeFile(logPath)
            outPath = os.path.join(self.__sessionPath, rootName + "-annot.cif")
            self.__removeFile(outPath)
            ok = self.__doAnnotateChemComp(filePath, outPath, logPath)
            #
            if ok:
                du = DownloadUtils(self.__reqObj, verbose=self.__verbose, log=self.__lfh)
                ok1 = du.fetchFile(outPath)
                if ok1:
                    aTagList.append(du.getAnchorTag())
                ok1 = du.fetchFile(logPath)
                if ok1:
                    aTagList.append(du.getAnchorTag())

                rC.setHtmlLinkText('<span class="url-list">View: %s</span>' % ",&nbsp;&nbsp;".join(aTagList))
                rC.setStatus(statusMsg="Operation completed")
            else:
                rC.setStatus(statusMsg="Operation failed for %s" % fileName)
        else:
            pass

        return rC

    def __removeFile(self, filePath):
        try:
            os.remove(filePath)
        except:  # noqa: E722 pylint: disable=bare-except
            return False
        return True

    def __doCvsUpdate(self, filePath, logPath):
        """ """
        if self.__verbose:
            logger.info("+ChemRefDataWebAppWorker._doCvsUpdate() starting for %s", filePath)

        try:
            crdu = ChemRefDataCvsUtils(self.__reqObj, verbose=self.__verbose, log=self.__lfh)
            ok, textList = crdu.updateFile(filePath)
            ofh = open(logPath, "w")
            ofh.write("%s" % "\n".join(textList))
            ofh.close()
            return ok
        except:  # noqa: E722 pylint: disable=bare-except
            logging.exception("cvs update failing")
            return False

    def __doCvsAdd(self, filePath, logPath):
        """ """
        if self.__verbose:
            logger.info("+ChemRefDataWebAppWorker._doCvsAdd() starting for %s", filePath)

        try:
            crdu = ChemRefDataCvsUtils(self.__reqObj, verbose=self.__verbose, log=self.__lfh)
            ok, textList = crdu.addFile(filePath)
            ofh = open(logPath, "w")
            ofh.write("%s" % "\n".join(textList))
            ofh.close()
            return ok
        except:  # noqa: E722 pylint: disable=bare-except
            logging.exception("cvs add failing")
            return False

    def __doCvsRemove(self, idCode, logPath):
        """ """
        if self.__verbose:
            logger.info("+ChemRefDataWebAppWorker._doCvsRemove() starting for %s", idCode)
        try:
            crdu = ChemRefDataCvsUtils(self.__reqObj, verbose=self.__verbose, log=self.__lfh)
            ok, textList = crdu.remove(idCode)
            ofh = open(logPath, "w")
            ofh.write("%s" % "\n".join(textList))
            ofh.close()
            return ok
        except:  # noqa: E722 pylint: disable=bare-except
            logging.exception("cvs remove failing")
            return False

    def __doCvsHistory(self, idCode, logPath):
        """ """
        if self.__verbose:
            logger.info("+ChemRefDataWebAppWorker._doCvsHistory() starting for %s", idCode)

        try:
            crdu = ChemRefDataCvsUtils(self.__reqObj, verbose=self.__verbose, log=self.__lfh)
            ok, textList = crdu.history(idCode)
            ofh = open(logPath, "w")
            ofh.write("%s" % "\n".join(textList))
            ofh.close()
            return ok
        except:  # noqa: E722 pylint: disable=bare-except
            logging.exception("cvs history failing")
            return False

    def __doCvsCheckoutRevisions(self, idCode, pathList):
        """ """
        if self.__verbose:
            logger.info("+ChemRefDataWebAppWorker._doCvsCheckOutRevisions() starting for %s", idCode)

        try:
            crdu = ChemRefDataCvsUtils(self.__reqObj, verbose=self.__verbose, log=self.__lfh)
            ok, pL = crdu.checkoutRevisions(idCode)
            pathList.extend(pL)
            return ok
        except:  # noqa: E722 pylint: disable=bare-except
            logging.exception("cvs checkout revisions failing")
            return False

    def __makeCifCheckReport(self, filePath, logPath):
        """Create CIF dictionary check on the input file and return diagnostics in logPath.

        Return True if a report is created (logPath exists and has non-zero size)
            or False otherwise
        """
        logger.info("+ChemRefDataWebAppWorker.__makeCifCheckReport() for file %s", filePath)
        logger.info("+ChemRefDataWebAppWorker._cifCheckOp() uploaded file %s", filePath)

        dp = RcsbDpUtility(tmpPath=self.__sessionPath, siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)
        dp.imp(filePath)
        dp.op("check-cif")
        dp.exp(logPath)
        dp.cleanup()
        if os.access(logPath, os.R_OK) and os.stat(logPath).st_size > 0:
            return True
        else:
            return False

    def __doAnnotateChemComp(self, inpPath, outPath, logPath):
        """Add annotations to the input chemical component definition and return the annotated file and diagnostics in logPath.

        Return True if the operation completes (outPath exists and has non-zero size)
            or False otherwise
        """
        logger.info("Starting for chemical component file %s", inpPath)
        #
        dp = RcsbDpUtility(tmpPath=self.__sessionPath, siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)
        dp.setDebugMode(flag=True)
        dp.imp(inpPath)
        dp.op("chem-comp-annotate-comp")
        dp.exp(outPath)
        dp.expLog(logPath)
        # dp.cleanup()
        if os.access(outPath, os.R_OK) and os.stat(outPath).st_size > 0:
            return True
        else:
            return False

    # ----------------------------------------------------------------------------------------------------
    #             ID-based methods on the ADMIN path implemented with JSON responses -
    #             JSON ID-level operations -
    #
    def _chemRefInlineIdOps(self):
        """Chemical reference data operations on id codes."""
        operation = self.__reqObj.getValue("operation")
        logger.info("+ChemRefDataWebAppWorker._chemRefInlineIdOps() starting with op %s", operation)

        idCodes = self.__reqObj.getValue("idcode")
        idCodeList = idCodes.split(" ")

        logger.info("+ChemRefDataWebAppWorker._chemRefInlineIdOps() fetch id(s) %r", idCodeList)
        #
        if operation == "fetch":
            return self.__makeIdListFetchResponse(idCodeList)
        elif operation == "report":
            return self.__makeIdListReportResponse(idCodeList)
        elif operation == "history":
            return self.__makeIdListCvsHistoryResponse(idCodeList)
        elif operation == "revfetch":
            return self.__makeRevisionCheckoutResponse(idCodeList)
        elif operation == "remove":
            return self.__makeIdListCvsRemoveResponse(idCodeList)

        else:
            pass

    def __makeIdListFetchResponse(self, idCodeList):
        """ """
        self.__getSession()
        self.__reqObj.setReturnFormat(return_format="json")
        rC = ResponseContent(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
        #
        du = DownloadUtils(self.__reqObj, verbose=self.__verbose, log=self.__lfh)
        aTagList = []
        for idCode in idCodeList:
            filePath = self.__crPI.getFilePath(idCode=idCode)
            if du.fetchFile(filePath):
                aTagList.append(du.getAnchorTag())

        if len(aTagList) > 0:
            rC.setHtmlLinkText('<span class="url-list">View: %s</span>' % ",&nbsp;&nbsp;".join(aTagList))
            rC.setStatus(statusMsg="Fetch completed")
        else:
            rC.setError(errMsg="No corresponding reference file(s)")
            # do nothing

        return rC

    def __makeIdListCvsHistoryResponse(self, idCodeList):
        """ """
        self.__getSession()
        self.__reqObj.setReturnFormat(return_format="json")
        rC = ResponseContent(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
        #
        aTagList = []
        #
        success = True
        du = DownloadUtils(self.__reqObj, verbose=self.__verbose, log=self.__lfh)
        for idCode in idCodeList:
            logPath = os.path.join(self.__sessionPath, idCode + "-cvs-history.log")
            ok = self.__doCvsHistory(idCode, logPath)
            if not ok:
                success = False
            ok1 = du.fetchFile(logPath)
            if ok1:
                aTagList.append(du.getAnchorTag())

        if len(aTagList) > 0:
            rC.setHtmlLinkText('<span class="url-list">View: %s</span>' % ",&nbsp;&nbsp;".join(aTagList))

        if success:
            rC.setStatus(statusMsg="History operations completed")
        else:
            rC.setError(errMsg="History operations failed")

        return rC

    def __makeRevisionCheckoutResponse(self, idCodeList):
        """ """
        self.__getSession()
        self.__reqObj.setReturnFormat(return_format="json")
        rC = ResponseContent(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
        #
        aTagList = []
        pathList = []
        #
        success = False
        du = DownloadUtils(self.__reqObj, verbose=self.__verbose, log=self.__lfh)
        for idCode in idCodeList:
            ok = self.__doCvsCheckoutRevisions(idCode, pathList)
            if ok:
                for pth in pathList:
                    ok1 = du.fetchFile(pth)
                    if ok1:
                        aTagList.append(du.getAnchorTag())

        if len(aTagList) > 0:
            success = True
            rC.setHtmlLinkText('<span class="url-list">View: %s</span>' % ",&nbsp;&nbsp;".join(aTagList))

        if success:
            rC.setStatus(statusMsg="Revision checkout completed")
        else:
            rC.setError(errMsg="Revision checkout failed")

        return rC

    def __makeIdListCvsRemoveResponse(self, idCodeList):
        """ """
        self.__getSession()
        self.__reqObj.setReturnFormat(return_format="json")
        rC = ResponseContent(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
        #
        errorMessage = ""
        for idCode in idCodeList:
            if len(idCode) > 3:
                continue
            #
            filePath = self.__crPI.getFilePath(idCode=idCode)
            if (not filePath) or (not os.access(filePath, os.R_OK)):
                errorMessage += "Invalid CC ID: " + idCode + "\n"
                continue
            #
            try:
                cifObj = mmCIFUtil(filePath=filePath)
                relStatus = cifObj.GetSingleValue("chem_comp", "pdbx_release_status").strip().upper()
                if relStatus == "REL":
                    errorMessage += "The ligand '" + idCode + "' has REL status and it should not be removed.\n"
                #
            except:  # noqa: E722 pylint: disable=bare-except
                logger.exception("Failure in __makeIdListCvsRemoveResponse")
            #
        #
        if errorMessage:
            rC.setError(errMsg=errorMessage)
            return rC
        #
        aTagList = []
        #
        success = True
        du = DownloadUtils(self.__reqObj, verbose=self.__verbose, log=self.__lfh)
        for idCode in idCodeList:
            logPath = os.path.join(self.__sessionPath, idCode + "-cvs-remove.log")
            ok = self.__doCvsRemove(idCode, logPath)
            if not ok:
                success = False
            ok1 = du.fetchFile(logPath)
            if ok1:
                aTagList.append(du.getAnchorTag())

        if len(aTagList) > 0:
            rC.setHtmlLinkText('<span class="url-list">View: %s</span>' % ",&nbsp;&nbsp;".join(aTagList))

        if success:
            rC.setStatus(statusMsg="Remove operations completed")
        else:
            rC.setError(errMsg="Remove operations failed")

        return rC

    #  ---------------------------------------------------------------------------------------------
    #
    #     Current search methods - searchType = <search_attributes, ...>|<query_type>
    ##
    def __getSearchType(self, searchTypeInput):
        """Return: searchType,queryType, target input type, comparison type"""
        try:
            tL = str(searchTypeInput).split("|")
            if len(tL) > 1:
                return tL[0], tL[1], tL[2], tL[3]
            else:
                return tL[0], None, None, None
        except Exception as e:
            logger.exception("Failing with input %r and %r", searchTypeInput, str(e))

        return None, None, None, None

    def _chemRefFullSearchAutoCompeteOp(self):
        self.__reqObj.setReturnFormat(return_format="jsonData")
        rC = ResponseContent(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
        term = self.__reqObj.getValue("term")

        # searchTarget = self.__reqObj.getValue("searchTarget")
        # searchOp = self.__reqObj.getValue("searchOp")
        searchName = self.__reqObj.getValue("searchName")
        searchTypeInput = self.__reqObj.getValue("searchType")
        searchType, queryType, inputType, compareType = self.__getSearchType(searchTypeInput)

        logger.info("searchType %r queryType %r compareType %r term %r", searchType, queryType, compareType, term)
        vList = []
        try:
            crs = ChemRefSearch(siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)
            crs.setSearch(queryType, searchType, term, searchName, inputType, compareType)
            _, vList = crs.doSearchAutoComplete()
            logger.debug("\n+ChemRefDataWebAppWorker._chemRefFullSearchAutoCompleteOp() -  term %s for type %s length %d", term, searchType, len(vList))
        except Exception as e:
            logger.exception("Failing with %r", str(e))

        rC.setData(vList)
        return rC

    def _chemRefFullSearchOp(self):
        #
        logger.info("+ChemRefDataWebAppWorker._chemRefFullSearchOp() starting")
        #
        #  Form search target value provided by user -
        searchTarget = self.__reqObj.getValue("searchTarget")
        # static hidden title defined in the input form
        # searchTitle = self.__reqObj.getValue("searchTitle")
        # HTML template path -- usually self.__templatePath -
        appsHtdocsPath = self.__reqObj.getValue("AppHtdocsPath")
        # Form selection option name
        searchName = self.__reqObj.getValue("searchName")
        #
        searchTypeInput = self.__reqObj.getValue("searchType")
        searchType, queryType, inputType, compareType = self.__getSearchType(searchTypeInput)
        #
        logger.info(
            "searchType %r queryType %r searchTarget %r inputType %r compareType %r appsHtdocsPath %r", searchType, queryType, searchTarget, inputType, compareType, appsHtdocsPath
        )
        # enable comma-separated lists or hyphen-separated ranges in search box
        if searchType.startswith("CCD_CC_ID") or searchType.startswith("BIRD_PRD_ID"):
            searchTarget = searchTarget.replace(",", " ")
        elif searchType == "CCD_FORMULA_WEIGHT" or searchType == "CCDIDX_FORMULA_WEIGHT_RANGE":
            searchTarget = searchTarget.replace("-", " ")
        #
        self.__getSession()
        self.__reqObj.setReturnFormat(return_format="json")
        rC = ResponseContent(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)

        #
        rD = {}
        try:
            crs = ChemRefSearch(siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)
            crs.setSearch(queryType, searchType, searchTarget, searchName, inputType, compareType)
            rD = crs.doSearch()
        except Exception as e:
            logger.exception("Failing with %r", str(e))
        #
        renderBsTable = True
        ##
        #
        if renderBsTable:
            if len(rD) > 0:
                logger.debug("Rendering bootstrap table style with object length %r", len(rD))
                includePath = os.path.join(appsHtdocsPath, "includes")
                crsdp = ChemRefSearchDepictBootstrap(includePath=includePath, verbose=self.__verbose, log=self.__lfh)
                tableDataD = crsdp.doBsTableRenderCollapsable(rD, searchName=searchName)
                if len(tableDataD) > 0:
                    # Handle the JSON conversion under the hood -
                    # rC.set('resultSetTableData', json.dumps(tableDataD))
                    rC.set("resultSetTableData", tableDataD, asJson=True)
                    rC.set("resultSetId", str(1))
                    rC.setStatus(statusMsg="Search completed")
                else:
                    rC.setStatus(statusMsg="No search results")
            else:
                rC.setStatus(statusMsg="No search results")
        #
        else:
            if len(rD) > 0:
                logger.debug("Rendering with object length %r", len(rD))
                includePath = os.path.join(appsHtdocsPath, "includes")
                crsdp = ChemRefSearchDepictBootstrap(includePath=includePath, verbose=self.__verbose, log=self.__lfh)
                oL = crsdp.doAltRenderCollapsable(rD, searchName=searchName)
                if len(oL) > 0:
                    rC.setHtmlList(oL)
                    rC.setStatus(statusMsg="Search completed")
                else:
                    rC.setStatus(statusMsg="No search results")
            else:
                rC.setStatus(statusMsg="No search results")

        return rC

    def __makeIdListReportResponse(self, idCodeList):
        """Prepare response for a report request for the input Id code list."""
        self.__getSession()
        self.__reqObj.setReturnFormat(return_format="json")
        rC = ResponseContent(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
        #
        du = DownloadUtils(self.__reqObj, verbose=self.__verbose, log=self.__lfh)
        aTagList = []
        htmlList = []
        webPathList = []
        myIdList = []

        for idCode in idCodeList:
            du.fetchId(idCode)
            repType = du.getIdType(idCode)
            downloadPath = du.getDownloadPath()
            aTagList.append(du.getAnchorTag())
            oL, _, webXyzPath = self.__makeTabularReport(filePath=downloadPath, repositoryType=repType, idCode=idCode, layout="tabs")
            htmlList.extend(oL)
            webPathList.append(webXyzPath)
            myIdList.append(idCode)
        if len(aTagList) > 0:
            rC.setHtmlLinkText('<span class="url-list">View: %s</span>' % ",&nbsp;&nbsp;".join(aTagList))
            rC.setHtmlList(htmlList)
            rC.setStatus(statusMsg="Reports completed")
            rC.set("webPathList", webPathList)
            rC.set("idCodeList", myIdList)
        else:
            rC.setError(errMsg="No corresponding reference file(s)")
            # do nothing

        return rC

    def __makeTabularReport(self, filePath, repositoryType, idCode, layout="tabs"):
        """Internal method to create a tabular report corresponding to the input
        chemical reference definition file.

        layout = tabs|accordion|multiaccordion

        Return data as a list of HTML markup for the section containing the tabular report.
        """
        #
        oL = []
        fileFormat = "cif"
        webXyzPath = None
        #
        logger.info("+ChemRefDataWebAppWorker.__makeTabularReport() target file %s id code %s repository %s", filePath, idCode, repositoryType)

        if filePath is not None and repositoryType is not None and idCode is not None:
            if repositoryType in ["CC", "PRDCC"]:
                rd = ChemCompReport(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
                rd.setFilePath(filePath, ccFileFormat=fileFormat, ccId=idCode)
                dd = rd.doReport()
                #
                rdd = ChemRefReportDepictBootstrap(styleObject=ChemCompCategoryStyle(), verbose=self.__verbose, log=self.__lfh)
                oL = rdd.render(dd, style=layout)
                webXyzPath = dd["xyzRelativePath"]
            elif repositoryType in ["PRD", "PRD_FAMILY"]:
                rd = BirdReport(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
                rd.setFilePath(filePath, prdFileFormat=fileFormat, prdId=idCode)
                dd = rd.doReport()
                #
                rdd = ChemRefReportDepictBootstrap(styleObject=PrdCategoryStyle(), verbose=self.__verbose, log=self.__lfh)
                oL = rdd.render(dd, style=layout)
                webXyzPath = dd["xyzRelativePath"]
            if self.__debug:
                logger.info("+ChemRefDataWebAppWorker.__makeTabularReport - generated HTML \n%s", "\n".join(oL))

        return oL, idCode, webXyzPath

    # --------------------------------------------------------------------------------------
    #
    #       Current Admin methods ---
    #
    def _chemRefAdminOps(self):
        """Chemical reference data repository/sandbox level administrative operations."""
        operation = self.__reqObj.getValue("operation")
        logger.info("+ChemRefDataWebAppWorker._chemRefAdminOps() starting with op %s", operation)

        if operation == "updatedatabasebird":
            return self.__chemRefDatabaseUpdateOp(referenceDatabase="BIRD")
        elif operation == "synccvsbird":
            return self.__chemRefSyncCvsOp(repositoryType="BIRD")
        elif operation == "updatedatabasecc":
            return self.__chemRefDatabaseUpdateOp(referenceDatabase="CC")
        elif operation == "synccvscc":
            return self.__chemRefSyncCvsOp(repositoryType="CC")
        elif operation == "updatesupportfiles":
            return self.__chemRefSupportFileUpdateOp()
        elif operation == "updateindexfiles":
            return self.__chemRefIndexFileUpdateOp()
        else:
            return self.__chemRefSyncCvsOp(repositoryType=None)

    def __chemRefSupportFileUpdateOp(self):
        self.__getSession()
        logger.info("+ChemRefDataWebAppWorker._chemRefSupportFileUpdateOp() starting with session %s", self.__sessionPath)

        self.__reqObj.setReturnFormat(return_format="json")
        rC = ResponseContent(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)

        ok = self.__chemRefSupportFiles()

        if ok:
            rC.setStatus(statusMsg="Chemical component support file update completed")
        else:
            rC.setError(errMsg="Chemical component support file update failed")

        return rC

    def __chemRefSupportFiles(self):
        """Update chemical component definition file idList, pathList, concatenated dictionary,
        serialized dictionary, dictionary search index, and several Python serialized object/index files.
        """
        logger.info("Starting")
        try:
            mu = ChemRefDataMiscUtils(self.__reqObj, verbose=self.__verbose, log=self.__lfh)
            ok1 = mu.updateChemCompSupportFiles()
            ok2 = mu.updateChemCompPySupportFiles()
            ok3 = mu.updatePrdSupportFiles()
            ok = ok1 and ok2 and ok3
        except:  # noqa: E722 pylint: disable=bare-except
            logger.exception("Failure in __chemRefSupportFiles")
            ok = False
        return ok

    def __chemRefIndexFileUpdateOp(self):
        self.__getSession()
        logger.info("+ChemRefDataWebAppWorker._chemRefIndexFileUpdateOp() starting with session %s", self.__sessionPath)

        self.__reqObj.setReturnFormat(return_format="json")
        rC = ResponseContent(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)

        ok = self.__chemRefIndexFiles()

        if ok:
            rC.setStatus(statusMsg="Chemical component index file update completed")
        else:
            rC.setError(errMsg="Chemical component index file update failed")

        return rC

    def __chemRefIndexFiles(self):
        """Update Python serialized object and index files."""
        logger.info("Starting")
        ok = False
        try:
            mu = ChemRefDataMiscUtils(self.__reqObj, verbose=self.__verbose, log=self.__lfh)
            ok = mu.updateChemCompPySupportFiles()
        except:  # noqa: E722 pylint: disable=bare-except
            logger.exception("Failure in __chemRefIndexFiles")

        return ok

    def __chemRefSyncCvsOp(self, repositoryType=None):
        """Synchronize the reference data sandbox areas with the reference CVS repository."""
        logger.info("+ChemRefDataWebAppWorker._chemRefSyncCvsOp() starting")

        self.__getSession()
        self.__reqObj.setReturnFormat(return_format="json")
        rC = ResponseContent(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
        crdu = ChemRefDataCvsUtils(self.__reqObj, verbose=self.__verbose, log=self.__lfh)
        #
        if repositoryType in ["CC"]:
            ok, textList = crdu.syncChemComp()
        elif repositoryType in ["PRD", "PRD_FAMILY", "PRDCC", "BIRD"]:
            ok, textList = crdu.syncBird()
        else:
            ok = False
            textList = ["Unknown reference respository"]

        logger.info("+ChemRefDataWebAppWorker._chemRefSyncCvsOp() repository %s completion status is %r", repositoryType, ok)
        #
        if ok:
            rC.setStatus(statusMsg="Repository SYNC completed")
        else:
            if self.__verbose:
                logger.info("+ChemRefDataWebAppWorker._chemRefSyncCvsOp() diagnostics %r", textList)
            hL = []
            for tt in textList:
                tL = tt.split("\n")
                hL.append("<br />".join(tL))

            rC.setError(errMsg="Repository SYNC completed with diagnostics  <br />" + "<br />".join(hL))

        return rC

    def __chemRefDatabaseUpdateOp(self, referenceDatabase="CC"):
        self.__getSession()
        logger.info("+ChemRefDataWebAppWorker._chemRefDatabaseUpdateOp() starting with session %s", self.__sessionPath)

        self.__reqObj.setReturnFormat(return_format="json")
        rC = ResponseContent(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)

        crdbu = ChemRefDataDbUtils(self.__reqObj, verbose=self.__debug, log=self.__lfh)
        if referenceDatabase in ["CC"]:
            ok = crdbu.loadChemCompMulti()
        elif referenceDatabase in ["BIRD", "PRD", "PRD_FAMILY"]:
            ok = crdbu.loadBird()
        else:
            logger.error("referenceDatabase %s unknown", referenceDatabase)
            ok = False

        if ok:
            rC.setStatus(statusMsg="%s database load completed" % referenceDatabase)
        else:
            rC.setError(errMsg="Database load failed")

        return rC

    #
    #  supporting internal methods --
    #
    def X_getFileText(self, filePath):
        self.__reqObj.setReturnFormat(return_format="text")
        rC = ResponseContent(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
        rC.setTextFile(filePath)
        return rC

    def _newSessionOp(self):
        logger.info("+AnnTasksWebAppWorker._newSessionOp() starting")

        self.__getSession(forceNew=True)
        self.__reqObj.setReturnFormat(return_format="json")
        rC = ResponseContent(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
        sId = self.__reqObj.getSessionId()
        if len(sId):
            rC.setHtmlText("Session id %s created." % sId)
        else:
            rC.setError(errMsg="No session created")

        return rC

    def __getSession(self, forceNew=False):
        """Join existing session or create new session as required."""
        #
        sessionId = self.__reqObj.getSessionId()
        logger.info("__getSession() - Starting with session %s", sessionId)
        #
        self.__sObj = self.__reqObj.newSessionObj(forceNew=forceNew)

        self.__sessionId = self.__sObj.getId()
        self.__sessionPath = self.__sObj.getPath()
        self.__rltvSessionPath = self.__sObj.getRelativePath()

        logger.info("__getSession() - Leaving with session %s", self.__sessionId)
        logger.info("__getSession() - Leaving session path %s", self.__sessionPath)
        logger.info("------------------------------------------------------")

    def __isFileUpload(self, fileTag="file"):
        """Generic check for the existence of request paramenter "file"."""
        # Gracefully exit if no file is provide in the request object -
        fs = self.__reqObj.getRawValue(fileTag)
        if sys.version_info[0] < 3:
            if (fs is None) or (isinstance(fs, types.StringType)):  # pylint: disable=no-member
                return False
        else:
            if (fs is None) or isinstance(fs, (str, bytes)):
                return False

        return True

    def __uploadFile(self, fileTag="file", fileTypeTag="filetype"):
        #
        #
        logger.info("+ChemRefDataWebApp.__uploadFile() - file upload starting")

        #
        # Copy upload file to session directory -
        try:
            fs = self.__reqObj.getRawValue(fileTag)
            # fNameInput = str(fs.filename).lower()
            fNameInput = str(fs.filename)
            #
            # Need to deal with some platform issues -
            #
            if fNameInput.find("\\") != -1:
                # likely windows path -
                fName = ntpath.basename(fNameInput)
            else:
                fName = os.path.basename(fNameInput)

            #

            logger.info("+ChemRefDataWebApp.__loadDataFileStart() - upload file %s", fs.filename)
            logger.info("+ChemRefDataWebApp.__loadDataFileStart() - base file   %s", fName)
            #
            # Store upload file in session directory -

            fPathAbs = os.path.join(self.__sessionPath, fName)
            ofh = open(fPathAbs, "wb")
            ofh.write(fs.file.read())
            ofh.close()
            self.__reqObj.setValue("UploadFileName", fName)
            self.__reqObj.setValue("filePath", fPathAbs)
            logger.info("+ChemRefDataWebApp.__uploadFile() Uploaded file %s", str(fName))
        except:  # noqa: E722 pylint: disable=bare-except
            logger.exception("+ChemRefDataWebApp.__uploadFile() File upload processing failed for %s", str(fs.filename))

            return False
        #
        # Verify file name
        #
        fs = self.__reqObj.getRawValue(fileTag)
        fmt = self.__reqObj.getValue(fileTypeTag)
        fType = fmt.lower()
        # fNameInput=str(fs.filename).strip().lower()
        fNameInput = str(fs.filename).strip()
        #
        # Need to deal with some platform issues -
        #
        if fNameInput.find("\\") != -1:
            # likely windows path -
            fName = ntpath.basename(fNameInput)
        else:
            fName = os.path.basename(fNameInput)
        #
        #
        if fName.startswith("rcsb"):
            fId = fName[:10]
        elif fName.startswith("d_"):
            fId = fName[:8]
        else:
            fId = "000000"
            logger.info("+ChemRefDataWebApp.__uploadFile() using default identifier for %s", str(fName))

        self.__reqObj.setValue("identifier", fId)
        self.__reqObj.setValue("fileName", fName)
        #
        if fType in ["cif", "cifeps", "pdb"]:
            self.__reqObj.setValue("fileType", fType)
        else:
            self.__reqObj.setValue("fileType", "unknown")

        logger.info("+ChemRefDataWebApp.__uploadFile() identifier %s", self.__reqObj.getValue("identifier"))
        logger.info("+ChemRefDataWebApp.__uploadFile() UploadFileType  %s", self.__reqObj.getValue("UploadFileType"))
        logger.info("+ChemRefDataWebApp.__uploadFile() UploadFileName  %s", self.__reqObj.getValue("UploadFileName"))
        return True

    def _chemRefEditorOps(self):
        """Launch chemical component editor based on id code."""
        self.__getSession()
        self.__reqObj.setReturnFormat(return_format="json")
        rC = ResponseContent(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
        #
        idCode = self.__reqObj.getValue("idcode")
        logger.info("+ChemRefDataWebAppWorker._chemRefEditorOps() idCode %r", idCode)
        #
        if not idCode:
            rC.setError(errMsg="Please input CC ID")
            return rC
        #
        if len(idCode) > 5:
            rC.setError(errMsg="Invalid CC ID")
            return rC
        #
        filePath = self.__crPI.getFilePath(idCode=idCode)
        if not filePath:
            rC.setError(errMsg="Invalid CC ID")
        else:
            localFilePath = os.path.join(self.__sessionPath, idCode.upper() + ".cif")
            shutil.copyfile(filePath, localFilePath)
            rC.setStatus(statusMsg="Load completed")
            #
            relStatus = ""
            try:
                cifObj = mmCIFUtil(filePath=localFilePath)
                relStatus = cifObj.GetSingleValue("chem_comp", "pdbx_release_status").strip().upper()
            except:  # noqa: E722 pylint: disable=bare-except
                logger.exception("Failure in in _ChemRefEditorOps")
            #
            myD = {}
            myD["sessionid"] = self.__sessionId
            myD["instanceid"] = idCode.upper()
            myD["processing_site"] = self.__cI.get("SITE_NAME").upper()
            myD["urlcifpath"] = os.path.join(self.__rltvSessionPath, idCode.upper() + ".cif")
            if relStatus == "REL":
                myD["ccmodel"] = "compCompModelRel"
            else:
                myD["ccmodel"] = "compCompModel"
            #
            htmlText = self.__processTemplate("templates/cc_edit_tmplt.html", myD)
            #
            htmlFilePath = os.path.join(self.__sessionPath, idCode.upper() + ".html")
            ofh = open(htmlFilePath, "w")
            ofh.write(htmlText + "\n")
            ofh.close()
            #
            rC.setLocation(os.path.join(self.__rltvSessionPath, idCode.upper() + ".html"))
        #
        return rC

    def __processTemplate(self, fn, parameterDict=None):
        """Read the input HTML template data file and perform the key/value substitutions in the
        input parameter dictionary.

        :Params:
            ``parameterDict``: dictionary where
            key = name of subsitution placeholder in the template and
            value = data to be used to substitute information for the placeholder

        :Returns:
            string representing entirety of content with subsitution placeholders now replaced with data
        """
        if parameterDict is None:
            parameterDict = {}

        tPath = self.__reqObj.getValue("TemplatePath")
        fPath = os.path.join(tPath, fn)
        with open(fPath, "r") as ifh:
            sIn = ifh.read()
        return sIn % parameterDict


def main():
    sTool = ChemRefDataWebApp()
    d = sTool.doOp()
    for k, v in d.items():
        sys.stdout.write("Key - %s  value - %r\n" % (k, v))


if __name__ == "__main__":
    main()
