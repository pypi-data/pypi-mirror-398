##
# File:  ReportUtils.py
# Date:  14-Jun-2017 jdw
#
# Updates:
#  14-Jun-2017  jdw refactored common modules
##
"""
Common methods shared by report modules -

"""
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "jwest@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.01"


import sys
import logging

from wwpdb.utils.oe_util.oedepict.OeDepict import OeDepict
from wwpdb.utils.oe_util.build.OeChemCompIoUtils import OeChemCompIoUtils

logger = logging.getLogger(__name__)


class ReportUtils(object):
    """
    Common methods shared by report modules -

    """

    def __init__(self, verbose=False, log=sys.stderr):
        """PRD report generator.

        :param `verbose`:  boolean flag to activate verbose logging.
        :param `log`:      stream for logging.

        """
        self.__verbose = verbose
        self.__lfh = log
        #

    def coordinatesExist(self, cD):
        """Return a tuple of booleans (exptl xyz exist, ideal xyz exist)"""
        hasExpt = False
        hasIdeal = False
        try:
            if "chem_comp" in cD:
                d = cD["chem_comp"][0]
                logger.info("d is %r", d.items())
                if "_chem_comp.pdbx_model_coordinates_missing_flag" in d:
                    hasExpt = d["_chem_comp.pdbx_model_coordinates_missing_flag"] == "N"
                if "_chem_comp.pdbx_ideal_coordinates_missing_flag" in d:
                    hasIdeal = d["_chem_comp.pdbx_ideal_coordinates_missing_flag"] == "N"
        except:  # noqa: E722 pylint: disable=bare-except
            logger.exception("Failed with cD %r", cD.items())

        logger.info("exptl %r ideal %r", hasExpt, hasIdeal)
        return hasExpt, hasIdeal

    def makeImagesFromPathList(self, pathList=None, imagePath="image.png", rows=1, cols=1, imageX=500, imageY=500):
        """Fetch, read, build, and depict the OE molecule from input path list of chemical definitions."""
        logger.info("Starting")
        if pathList is None:
            pathList = []
        try:
            oeMolTitleList = self.__makeOeMols(pathList=pathList)
            oed = OeDepict(verbose=self.__verbose, log=self.__lfh)
            oed.setMolTitleList(oeMolTitleList)
            oed.setDisplayOptions(imageX=imageX, imageY=imageY, labelAtomName=True, labelAtomCIPStereo=True, labelAtomIndex=False, labelBondIndex=False, bondDisplayWidth=0.5)
            oed.setGridOptions(rows=rows, cols=cols)
            oed.prepare()
            oed.write(imagePath)
            return True
        except:  # noqa: E722 pylint: disable=bare-except
            logger.exception("Failing for pathList %r", pathList)
        return False

    def __makeOeMols(self, pathList=None):
        """Create OE molecules from the input chem comp definition path list."""
        if pathList is None:
            pathList = []
        try:
            oemList = []
            idList = []
            oeU = OeChemCompIoUtils(verbose=self.__verbose, log=self.__lfh)
            oemList = oeU.getFromPathList(pathList, use3D=False, coordType="model")
            for oem in oemList:
                title = oem.getTitle()
                idList.append(title)
                logger.info("Title              = %s", title)
                logger.info("SMILES (canonical) = %s", oem.getCanSMILES())
                logger.info("SMILES (isomeric)  = %s", oem.getIsoSMILES())
        except:  # noqa: E722 pylint: disable=bare-except
            logger.exception("Failing for pathList %r", pathList)

        return list(zip(idList, oemList, idList))
