##
# File:  ChemCompSearchIndexUtils.py
# Date:  1-Feb-2017 J. Westbrook
#
# Update:
#   20-Apr-2017  overhaul
#    1-May-2017  add search over lists and add range search method
#   27-May-2017  add more performant approximate string comparison
##
"""
Search index of chemical components definitions by component features.

"""

import sys
import time

import jellyfish
from operator import itemgetter

from wwpdb.utils.cc_dict_util.persist.PdbxChemCompDictIndex import PdbxChemCompDictIndex
from wwpdb.utils.config.ConfigInfoApp import ConfigInfoAppCc

import logging

logger = logging.getLogger(__name__)


class ChemCompSearchIndexUtils(object):
    def __init__(self, siteId, verbose=True, log=sys.stderr):
        self.__verbose = verbose
        self.__debug = False
        self.__lfh = log
        self.__siteId = siteId
        self.__cIAppCc = ConfigInfoAppCc(self.__siteId)
        self.__pathCCIndex = self.__cIAppCc.get_cc_index()
        logger.debug("ChemCompSearchIndexUtils index path %r", self.__pathCCIndex)
        #
        dIndx = PdbxChemCompDictIndex(verbose=self.__verbose, log=self.__lfh)
        self.__ccIndx = dIndx.readIndex(indexPath=self.__pathCCIndex)

    def getValue(self, ccId, key):
        try:
            return self.__ccIndx[str(ccId).upper()][key]
        except:  # noqa: E722 pylint: disable=bare-except
            pass
        return None

    def getAttributeValueList(self, myIdList, colList, dspList):
        """For the input id list return a list of dictionaries populated with
        the key values in colList.  Return dictionary keys are taken from
        the corresponding elements of dspList.
        """
        logger.debug("getAttributeValueList myIdList %r", myIdList)
        logger.debug("getAttributeValueList colList %r", colList)
        logger.debug("getAttributeValueList dspList %r", dspList)
        logger.debug("getAttributeValueList length index %r", len(self.__ccIndx))
        rowList = []
        for myId in myIdList:
            d = self.__ccIndx[str(myId).upper()]
            dd = {}
            if self.__debug:
                logger.debug("getAttributeValueList myId %r d %r", myId, d)
            for ii, col in enumerate(colList):
                dd[dspList[ii]] = d[col]
            rowList.append(dd)
        return rowList

    def searchIndexAll(self, key):
        rD = {}
        for ccId, d in self.__ccIndx.items():
            try:
                refV = d[key]
                mL = self.searchIndex(refV, key)
                if len(mL) > 0:  # THIS WAS > 1 - so seach for single row failed
                    rD[ccId] = mL
            except Exception as e:
                logger.exception("Index search failing for key %r  %r", key, str(e))
        return rD

    def searchIndex(self, target, key):
        """ """
        idList = []
        try:
            logger.debug("Search index key %r target %r", key, target)
            startTime = time.time()
            #
            for ccId, d in self.__ccIndx.items():
                # refV = d.get(key, '')
                refV = d[key]
                if isinstance(refV, (list, tuple, set)):
                    for tt in refV:
                        if target == tt:
                            idList.append(ccId)
                            continue
                else:
                    if target == refV:
                        idList.append(ccId)

            endTime = time.time()
            logger.debug("SearchIndex %r %r  match list for length %d in (%.4f seconds)", target, key, len(idList), endTime - startTime)
        except Exception as e:
            logger.exception("Index search failing for key %r target %r %r", key, target, str(e))
        #
        return idList

    def searchIndexSubstring(self, target, key):
        """ """
        idList = []
        try:
            startTime = time.time()
            # Upper and lower bounds for element counts in the input formula.
            #
            for ccId, d in self.__ccIndx.items():
                # refV = d.get(key, '')
                refV = d[key]
                refV = refV if refV is not None else ""
                if isinstance(refV, (list, tuple, set)):
                    for tt in refV:
                        if target in tt:
                            idList.append(ccId)
                            continue
                else:
                    if target in refV:
                        idList.append(ccId)

            endTime = time.time()
            logger.debug("SearchIndexSubstring %r %r  match list for length %d in (%.4f seconds)", target, key, len(idList), endTime - startTime)
        except Exception as e:
            logger.exception("Index substring search failing for key %r target %r %r", key, target, str(e))
        #
        return idList

    def searchIndexRange(self, target, key):
        """ """
        idList = []
        try:
            logger.debug("Search index range  key %r target range %r", key, target)
            startTime = time.time()
            #
            bL = [t.strip() for t in target.split()]
            lowB = float(bL[0])
            upperB = float(bL[1])
            for ccId, d in self.__ccIndx.items():
                # refV = d.get(key, '')
                try:
                    refV = float(str(d[key]))
                except:  # noqa: E722 pylint: disable=bare-except
                    logger.debug("Conversion failure for %r %r %r", key, ccId, d[key])
                    continue
                if lowB <= refV and refV < upperB:
                    idList.append(ccId)

            endTime = time.time()
            logger.debug("SearchIndex %r %r  match list for length %d in (%.4f seconds)", target, key, len(idList), endTime - startTime)
        except Exception as e:
            logger.exception("Index search failing for key %r target %r %r", key, target, str(e))
        #
        return idList

    def parseFormulaInput(self, inpTarget):
        """Standardize the input formula target and return a
        formula string - El## El##  and element count dictionary -
        """
        #
        ed = {}
        target = inpTarget
        try:
            #
            lt = inpTarget.upper().split(" ")
            # standardize counts - add missing unit count
            ll = []
            for el in lt:
                if not el[-1].isdigit():
                    el += "1"
                ll.append(el)

            tt = "".join(ll)
            if len(tt) > 0:
                aa = tt[0]
                for i in range(1, len(tt)):
                    if tt[i - 1].isdigit() and tt[i].isalpha():
                        aa += " "
                    aa += tt[i]
                target = aa
            #
            ed = {}
            ecL = target.upper().split(" ")
            for ec in ecL:
                if len(ec) < 2:
                    logger.info("parseFormulaInput - %r %r format error ", target, ecL)
                    continue
                if ec[1].isalpha():
                    ed[ec[0:2]] = int(ec[2:])
                else:
                    ed[ec[0:1]] = int(ec[1:])
            #
        except:  # noqa: E722 pylint: disable=bare-except
            ed = {}
            logger.exception("parseFormulaInput failed")

        return target, ed

    def searchFormulaBounded(self, elementCounts=None, upperOffset=2, lowerOffset=2, excludeH=False):
        """Bounded formula search - return a list of component identifiers satisfying
        the bounded element count criteria on the input formula.  The input formula
        is represented as a dictionary of element type and count. Upper and lower offsets are
        provided to specify upper and lower bounds for the element count comparison.

        """
        if elementCounts is None:
            elementCounts = {"C": 20, "Cl": 4}
        idList = []
        if len(elementCounts) < 1:
            return idList
        try:
            startTime = time.time()
            # Upper and lower bounds for element counts in the input formula.
            #
            offsetU = upperOffset
            offsetL = lowerOffset
            #
            for ccId, d in self.__ccIndx.items():
                refC = d["typeCounts"]
                if len(refC) < 1:
                    continue
                #
                mOk = True
                for etype, cnt in elementCounts.items():
                    typeU = etype.upper()
                    if excludeH and typeU in ["H", "D", "T"]:
                        continue
                    if typeU in refC:
                        # test out of bounds -
                        if (cnt < refC[typeU] - offsetL) or (cnt > refC[typeU] + offsetU):
                            mOk = False
                            break
                    else:
                        mOk = False
                        break
                if mOk:
                    idList.append(ccId)

            endTime = time.time()
            logger.info("FormulaBounded match list for length %d (%.3f seconds)", len(idList), endTime - startTime)

        except:  # noqa: E722 pylint: disable=bare-except
            logger.exception("Formula search failing")

        return idList

    def searchFormulaSubset(self, elementCounts=None, excludeH=False):
        """The input formula is represented as a dictionary of element type and count.
        Search for an reference formula that are an exact subset of the target.

        """
        if elementCounts is None:
            elementCounts = {"C": 20, "Cl": 4}
        idList = []
        if len(elementCounts) < 1:
            return idList
        try:
            startTime = time.time()
            #
            for ccId, d in self.__ccIndx.items():
                refC = d["typeCounts"]
                if len(refC) < 1:
                    continue
                #
                mOk = True
                for etype, cnt in elementCounts.items():
                    typeU = etype.upper()
                    if excludeH and typeU in ["H", "D", "T"]:
                        continue
                    if typeU in refC:
                        if cnt != refC[typeU]:
                            mOk = False
                            break
                    else:
                        mOk = False
                        break
                if mOk:
                    idList.append(ccId)

            endTime = time.time()
            logger.info("Formula match list for length %d (%.3f seconds)", len(idList), endTime - startTime)

        except:  # noqa: E722 pylint: disable=bare-except
            logger.exception("Formula search failing")

        #
        return idList

    def searchFormulaExact(self, elementCounts=None, excludeH=False):
        """The input formula is represented as a dictionary of element type and count.
        Search for an reference formula that is an exact match of the target.

        """
        if elementCounts is None:
            elementCounts = {"C": 20, "Cl": 4}

        logger.info("ElementCounts %r excludeH %r", elementCounts, excludeH)
        idList = []
        if len(elementCounts) < 1:
            return idList
        try:
            startTime = time.time()
            #
            for ccId, d in self.__ccIndx.items():
                refC = d["typeCounts"]
                if len(refC) < 1:
                    continue
                # Exact match case -
                if not excludeH and len(refC) != len(elementCounts):
                    continue
                elif excludeH:
                    rs = set(refC.keys()) - set(["H", "T", "D"])
                    ts = set(elementCounts.keys()) - set(["H", "T", "D"])
                    if rs != ts:
                        continue
                    # if len(rs) != len(ts):
                    #    continue
                #

                mOk = True
                for etype, cnt in refC.items():
                    #
                    typeU = etype.upper()
                    if excludeH and typeU in ["H", "D", "T"] and len(refC) > 1:
                        continue
                    if typeU in elementCounts:
                        if cnt != elementCounts[typeU]:
                            mOk = False
                            break
                    else:
                        mOk = False
                        break
                if mOk:
                    idList.append(ccId)

            endTime = time.time()
            logger.info("Formula match list for length %d (%.3f seconds)", len(idList), endTime - startTime)

        except:  # noqa: E722 pylint: disable=bare-except
            logger.exception("Formula search failing")
        #
        return idList

    ##
    ##

    def searchEditDistance(self, target, key, DIST_TYPE="JARO_WINKLER"):
        """ """
        if DIST_TYPE == "JARO":
            return self.__searchEditDistanceJaro(target, key, cutOff=0.75)
        elif DIST_TYPE == "JARO_WINKLER":
            return self.__searchEditDistanceJaroWinkler(target, key, cutOff=0.75)
        elif DIST_TYPE == "LEV":
            return self.__searchEditDistanceDmLev(target, key, cutOff=0.5)
        else:
            return []

    def __searchEditDistanceJaro(self, target, key, cutOff=0.7):
        """ """
        cidList = []
        try:
            logger.debug("Edit distance index search key %r target %r", key, target)
            startTime = time.time()
            #
            idList = []
            for ccId, d in self.__ccIndx.items():
                refV = d[key]
                if isinstance(refV, (list, tuple, set)):
                    for tt in refV:
                        ed = jellyfish.jaro_similarity(target.decode("unicode-escape"), tt.decode("unicode-escape"))
                        if ed > cutOff:
                            idList.append((ccId, ed))
                            break
                else:
                    ed = jellyfish.jaro_similarity(target.decode("unicode-escape"), refV.decode("unicode-escape"))
                    if ed > cutOff:
                        idList.append((ccId, ed))

            idList = sorted(idList, key=itemgetter(1), reverse=True)
            cidList = [c for (c, r) in idList]
            endTime = time.time()
            logger.debug("Edit distance result %r %r  match list for length %d in (%.4f seconds)", target, key, len(idList), endTime - startTime)
        except Exception as e:
            logger.exception("Edit distance search failing for key %r target %r %r", key, target, str(e))
        #
        return cidList

    def __searchEditDistanceJaroWinkler(self, target, key, cutOff=0.7):
        """ """
        cidList = []
        try:
            logger.debug("Edit distance index search key %r target %r", key, target)
            startTime = time.time()
            #
            idList = []
            for ccId, d in self.__ccIndx.items():
                refV = d[key]
                if isinstance(refV, (list, tuple, set)):
                    for tt in refV:
                        ed = jellyfish.jaro_winkler_similarity(target, tt)
                        if ed > cutOff:
                            idList.append((ccId, ed))
                            break
                else:
                    ed = jellyfish.jaro_winkler_similarity(target, refV)
                    if ed > cutOff:
                        idList.append((ccId, ed))

            idList = sorted(idList, key=itemgetter(1), reverse=True)
            cidList = [c for (c, r) in idList]
            endTime = time.time()
            logger.debug("Edit distance result %r %r  match list for length %d in (%.4f seconds)", target, key, len(idList), endTime - startTime)
        except Exception as e:
            logger.exception("Edit distance search failing for key %r target %r %r", key, target, str(e))
        #
        return cidList

    def __searchEditDistanceDmLev(self, target, key, cutOff=0.7):
        """ """
        cidList = []
        try:
            logger.debug("Edit distance index search key %r target %r", key, target)
            startTime = time.time()
            #
            idList = []
            for ccId, d in self.__ccIndx.items():
                refV = d[key]
                if isinstance(refV, (list, tuple, set)):
                    for tt in refV:
                        ed = self.__editDistanceNormJF(target.decode("unicode-escape"), tt.decode("unicode-escape"))
                        if ed > cutOff:
                            idList.append((ccId, ed))
                            break
                else:
                    if self.__editDistanceNormJF(target.decode("unicode-escape"), refV.decode("unicode-escape")) > cutOff:
                        idList.append((ccId, ed))
            idList = sorted(idList, key=itemgetter(1), reverse=True)
            cidList = [c for (c, r) in idList]
            endTime = time.time()
            logger.debug("Edit distance result %r %r  match list for length %d in (%.4f seconds)", target, key, len(idList), endTime - startTime)
        except Exception as e:
            logger.exception("Edit distance search failing for key %r target %r %r", key, target, str(e))
        #
        return cidList

    def __editDistanceNormJF(self, s1, s2):
        """
        Compute the Normalized Damerau-Levenshtein distance between two given
        strings (s1 and s2)
        """
        try:
            maxLen = max(len(s1), len(s2))
            ed = jellyfish.damerau_levenshtein_distance(s1, s2)  # pylint: disable=no-member
            edN = float(maxLen - ed) / float(maxLen)
            # logging.debug("s1 %r s2 %r maxLen %r ed %f edN %f " % (s1, s2, maxLen, ed, edN))
            return edN
        except Exception as e:
            logger.exception("Edit distance norm s1 %r s2 %r %r", s1, s2, str(e))
        return 0

    # def __editDistanceNorm(self, s1, s2):
    #     """
    #     Compute the Normalized Damerau-Levenshtein distance between two given
    #     strings (s1 and s2)
    #     """
    #     try:
    #         maxLen = max(len(s1), len(s2))
    #         ed = self.__editDistance(s1, s2)
    #         edN = float(maxLen - ed) / float(maxLen)
    #         # logging.debug("s1 %r s2 %r maxLen %r ed %f edN %f " % (s1, s2, maxLen, ed, edN))
    #         return edN
    #     except Exception as e:
    #         logger.exception("Edit distance norm s1 %r s2 %r %r" % (s1, s2, str(e)))
    #     return 0

    # def __editDistance(self, s1, s2):
    #     """
    #     Compute the Damerau-Levenshtein distance between two given
    #     strings (s1 and s2)
    #     """
    #     d = {}
    #     lenstr1 = len(s1)
    #     lenstr2 = len(s2)
    #     for i in range(-1, lenstr1 + 1):
    #         d[(i, -1)] = i + 1
    #     for j in range(-1, lenstr2 + 1):
    #         d[(-1, j)] = j + 1

    #     for i in range(0, lenstr1):
    #         for j in range(0, lenstr2):
    #             if s1[i] == s2[j]:
    #                 cost = 0
    #             else:
    #                 cost = 1
    #             d[(i, j)] = min(
    #                 d[(i - 1, j)] + 1,  # deletion.
    #                 d[(i, j - 1)] + 1,  # insertion
    #                 d[(i - 1, j - 1)] + cost,  # substitution
    #             )
    #             if i > 1 and j > 1 and s1[i] == s2[j - 1] and s1[i - 1] == s2[j]:
    #                 d[(i, j)] = min(d[(i, j)], d[i - 2, j - 2] + cost)  # transposition

    #     return d[lenstr1 - 1, lenstr2 - 1]
