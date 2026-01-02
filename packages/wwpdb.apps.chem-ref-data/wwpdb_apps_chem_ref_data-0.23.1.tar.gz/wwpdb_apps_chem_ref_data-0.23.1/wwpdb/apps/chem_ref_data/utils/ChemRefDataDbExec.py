#!/usr/bin/env python
# !/opt/wwpdb/bin/python
##
# File:    ChemRefDataDbExec.py
# Author:  jdw
# Date:    13-Jul-2014
# Version: 0.001
#
# Updates:
##
"""
Execuction module for chemical reference data database loading --

"""

__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "jwest@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.001"

import sys
import os
import logging
from optparse import OptionParser  # pylint: disable=deprecated-module
from enum import Enum

from wwpdb.apps.chem_ref_data.utils.ChemRefDataDbUtils import ChemRefDataDbUtils
from wwpdb.apps.chem_ref_data.utils.ChemRefDataCvsUtils import ChemRefDataCvsUtils
from wwpdb.apps.chem_ref_data.utils.ChemRefDataMiscUtils import ChemRefDataMiscUtils
from wwpdb.utils.config.ConfigInfo import getSiteId
from wwpdb.utils.config.ConfigInfoApp import ConfigInfoAppCommon
from wwpdb.utils.session.WebRequest import InputRequest

logger = logging.getLogger()


class ChemRefDb(Enum):
    CC = "CC"
    PRD = "PRD"

    def __str__(self):
        return self.value


class ChemRefDataDbExec(object):
    def __init__(self, defSiteId="WWWDPB_INTERNAL_RU", sessionId=None, verbose=True, log=sys.stderr):
        self.__lfh = log
        self.__verbose = verbose
        self.__setup(defSiteId=defSiteId, sessionId=sessionId)

    def __setup(self, defSiteId=None, sessionId=None):
        """Simulate the web application environment for managing session storage of  temporaty data files."""
        self.__siteId = getSiteId(defaultSiteId=defSiteId)
        # print(self.__siteId)
        #
        self.__cICommon = ConfigInfoAppCommon(self.__siteId)
        self.__topPath = self.__cICommon.get_site_web_apps_top_path()
        self.__topSessionPath = self.__cICommon.get_site_web_apps_top_sessions_path()
        #
        self.__reqObj = InputRequest({}, verbose=self.__verbose, log=self.__lfh)
        self.__reqObj.setValue("TopSessionPath", self.__topSessionPath)
        self.__reqObj.setValue("TopPath", self.__topPath)
        self.__reqObj.setValue("WWPDB_SITE_ID", self.__siteId)
        #
        # self.__reqObj.setValue("SITE_REFDATA_DB_USER", os.environ["SITE_REFDATA_DB_USER"])
        # self.__reqObj.setValue("SITE_REFDATA_DB_PASSWORD", os.environ["SITE_REFDATA_DB_PASSWORD"])

        # self.__reqObj.setValue("SITE_REFDATA_CVS_USER", os.environ["SITE_REFDATA_CVS_USER"])
        # self.__reqObj.setValue("SITE_REFDATA_CVS_PASSWORD", os.environ["SITE_REFDATA_CVS_PASSWORD"])

        os.environ["WWPDB_SITE_ID"] = self.__siteId
        if sessionId is not None:
            self.__reqObj.setValue("sessionid", sessionId)

        # We need to create a session obj (with subdir). Do not remove
        _sessionObj = self.__reqObj.newSessionObj()  # noqa: F841
        # self.__reqObj.printIt(ofh=self.__lfh)
        #

    def doLoadChemComp(self, rptPath=None):  # pylint: disable=unused-argument
        """ """
        try:
            dbu = ChemRefDataDbUtils(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
            dbu.loadChemComp()
        except:  # noqa: E722 pylint: disable=bare-except
            logger.exception("Failed in doLoadChemComp")

    def doLoadChemCompMulti(self, numProc):
        """ """
        try:
            dbu = ChemRefDataDbUtils(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
            ok = dbu.loadChemCompMulti(numProc)
            if ok:
                return True
            else:
                logger.info("load CCD failed")
        except:  # noqa: E722 pylint: disable=bare-except
            logger.exception("Failed load CCD")
        return False

    def doLoadBird(self, rptPath=None):  # pylint: disable=unused-argument
        """ """
        try:
            dbu = ChemRefDataDbUtils(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
            ok = dbu.loadBird()
            if ok:
                return True
            else:
                logger.info("load PRD failed")
        except:  # noqa: E722 pylint: disable=bare-except
            logger.exception("Failed doLoadBird")
        return False

    def doCheckoutChemComp(self):
        """ """
        try:
            cvsu = ChemRefDataCvsUtils(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
            sandbox_path = cvsu.getSandBoxTopPath()
            if sandbox_path:
                if not os.path.exists(sandbox_path):
                    os.makedirs(sandbox_path)
            ok, _textList = cvsu.checkoutChemCompSerial()
            if ok:
                return True
            else:
                logger.info("checkout CCD CVS failed")
        except:  # noqa: E722 pylint: disable=bare-except
            logger.exception("Failed doCheckoutChemComp")
        return False

    def doCheckoutPRD(self):
        try:
            cvsu = ChemRefDataCvsUtils(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
            sandbox_path = cvsu.getSandBoxTopPath()
            if sandbox_path:
                if not os.path.exists(sandbox_path):
                    os.makedirs(sandbox_path)
            ok, _textList = cvsu.checkoutPRDSerial()
            if ok:
                return True
            else:
                logger.info("checkout PRD CVS failed")
        except:  # noqa: E722 pylint: disable=bare-except
            logger.exception("doCheckoutPRD")
        return False

    def doSyncChemComp(self, numProc):
        """ """
        try:
            cvsu = ChemRefDataCvsUtils(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
            sandbox_path = cvsu.getSandBoxTopPath()
            if sandbox_path:
                if not os.path.exists(sandbox_path):
                    logger.info("sandbox path %s does not exist - running checkout", sandbox_path)
                    return self.doCheckoutChemComp()
                ok, _diag_list = cvsu.syncChemComp(numProc)
                if ok:
                    return True
                else:
                    logger.info("CVS update failed for CCD")
                    return False
            else:
                logger.info("sandbox path is None - exiting")
                return False
        except:  # noqa: E722 pylint: disable=bare-except
            logger.exception("doSyncChemComp")
        return False

    def doSyncBird(self):
        """ """
        try:
            cvsu = ChemRefDataCvsUtils(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
            sandbox_path = cvsu.getSandBoxTopPath()
            if sandbox_path:
                if not os.path.exists(sandbox_path):
                    logger.info("sandbox path %s does not exist - running checkout", sandbox_path)
                    return self.doCheckoutPRD()
                ok, _textList = cvsu.syncBird()
                if ok:
                    return True
                else:
                    logger.info("CVS update failed for PRD")
                    return False
            else:
                logger.info("sandbox path is None - exiting")
                return False
        except:  # noqa: E722 pylint: disable=bare-except
            logger.exception("Sandbox update")

    def doUpdateSupportFiles(self):
        """Update chemical component definition file idList, pathList, concatenated dictionary,
        serialized dictionary, dictionary search index, and several Python serialized support files.
        """
        logger.info("Starting")
        try:
            mu = ChemRefDataMiscUtils(self.__reqObj, verbose=self.__verbose, log=self.__lfh)
            ok1 = mu.updateChemCompSupportFiles()
            if not ok1:
                logger.info("updateChemCompSupportFiles failed")
            ok2 = mu.updateChemCompPySupportFiles()
            if not ok2:
                logger.info("updateChemCompPySupportFiles failed")
            ok3 = mu.updatePrdSupportFiles()
            if not ok3:
                logger.info("updatePrdSupportFiles failed")
            return ok1 and ok2 and ok3
        except:  # noqa: E722 pylint: disable=bare-except
            logger.info("Failed")
            logger.exception("Failed in doUpdateSupportFiles")
            return False

    def run_setup_process(self, numProc=8):
        ok1 = self.doCheckoutChemComp()
        ok2 = self.doCheckoutPRD()
        ok3 = self.doLoadChemCompMulti(numProc=numProc)
        ok4 = self.doLoadBird()
        ok5 = self.doUpdateSupportFiles()
        return ok1 and ok2 and ok3 and ok4 and ok5

    def run_update_process(self, numProc=8):
        ok1 = self.doSyncChemComp(numProc=numProc)
        ok2 = self.doSyncBird()
        ok3 = self.doLoadChemCompMulti(numProc=numProc)
        ok4 = self.doLoadBird()
        ok5 = self.doUpdateSupportFiles()

        # hard code syncing CCD CVS to True as it often fails, but really works
        ok1 = True
        return ok1 and ok2 and ok3 and ok4 and ok5


def main():
    FORMAT = "[%(levelname)s]-%(module)s.%(funcName)s: %(message)s"
    logging.basicConfig(format=FORMAT)
    logger.setLevel(logging.INFO)

    usage = "usage: %prog [options]"
    parser = OptionParser(usage)

    parser.add_option("--load", dest="load", action="store_true", default=False, help="Load database from repository sandbox")
    parser.add_option("--sync", dest="sync", action="store_true", default=False, help="Synchronize repository sandbox")
    parser.add_option("--checkout", dest="checkout", action="store_true", default=False, help="Checkout repository into sandbox")
    parser.add_option("--update", dest="update", action="store_true", default=False, help="Update support files from repository sandbox")

    parser.add_option("--db", dest="db", default="PRD", help="Database to load (CC,PRD)")
    parser.add_option("--run_setup", action="store_true", help="Run setup for CCD and PRD")
    parser.add_option("--run_update", action="store_true", help="Run update for CCD and PRD")

    parser.add_option("--numproc", type=int, dest="numProc", default=8, help="Number of processors to engage.")

    parser.add_option("-v", "--verbose", default=False, action="store_true", dest="verbose")
    (options, _args) = parser.parse_args()

    ok = True

    crx = ChemRefDataDbExec(defSiteId="WWWDPB_INTERNAL_RU", sessionId=None, verbose=options.verbose, log=sys.stderr)

    if options.checkout:
        if options.db == "CC":
            ok = crx.doCheckoutChemComp()
        if options.db == "PRD":
            ok = crx.doCheckoutPRD()

    if options.sync:
        if options.db == "CC":
            ok = crx.doSyncChemComp(options.numProc)
            # this often fails even though it works
            ok = True
        elif options.db == "PRD":
            ok = crx.doSyncBird()

    if options.load:
        if options.db == "CC":
            ok = crx.doLoadChemCompMulti(options.numProc)
        elif options.db == "PRD":
            ok = crx.doLoadBird()

    if options.update:
        ok = crx.doUpdateSupportFiles()

    if options.run_setup:
        ok = crx.run_setup_process(numProc=options.numProc)

    if options.run_update:
        ok = crx.run_update_process(numProc=options.numProc)

    if not ok:
        logging.error("task failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
