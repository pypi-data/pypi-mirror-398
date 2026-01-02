##
# File:  ChemRefSearchBase.py
# Date:  22-Apr-2017 J. Westbrook
#
# Update:
#  25-May-2017 jdw allow compareType to have multiple values in concert with searchType -
#  26-May-2017 jdw change organization returned search
#  13-Jun-2017 jdw add left join semantics to sql generator -
#
##
"""
Chemical reference data search base class.

"""

import sys
import copy

#
import logging

from wwpdb.utils.db.MyConnectionBase import MyConnectionBase
from wwpdb.apps.chem_ref_data.search.ChemCompSearchIndexUtils import ChemCompSearchIndexUtils
from wwpdb.utils.oe_util.build.OeDescriptorUtils import OeDescriptorUtils

logger = logging.getLogger(__name__)


class ChemRefSearchBase(MyConnectionBase):
    def __init__(self, siteId=None, verbose=False, log=sys.stderr):
        super(ChemRefSearchBase, self).__init__(siteId=siteId, verbose=verbose, log=log)
        self.__verbose = verbose
        self.__lfh = log
        self.__debug = True
        self.__siteId = siteId
        #
        self._displayTypeDict = {}
        self._keyDict = {}
        self._searchTypeDict = {}
        self._queryTypeDict = {}
        #
        self.__queryTypeInp = None
        self.__searchTargetInp = None
        self.__searchTypeInp = None
        self.__searchNameInp = None
        self.__inputTypeInp = None
        self.__compareTypeInp = None
        #

    def set(self, displayTypeDict, keyDict, searchTypeDict, queryTypeDict):
        self._displayTypeDict = displayTypeDict
        self._keyDict = keyDict
        self._searchTypeDict = searchTypeDict
        self._queryTypeDict = queryTypeDict
        return True

    def setSearch(self, queryType, searchType, searchTarget, searchName, inputType, compareType):
        """Public facing method to configure search -  note that some of these may be multi-valued -"""
        self.__queryTypeInp = queryType
        self.__searchTargetInp = searchTarget
        self.__searchTypeInp = searchType
        self.__searchNameInp = searchName
        self.__inputTypeInp = inputType
        self.__compareTypeInp = compareType

        return True

    def getSearch(self):
        return self.__queryTypeInp, self.__searchTypeInp, self.__searchTargetInp, self.__searchNameInp, self.__inputTypeInp, self.__compareTypeInp

    ##
    def _getQueryClass(self, queryType):
        try:
            return self._queryTypeDict[queryType]["class"]
        except Exception as e:
            logger.exception("failing %s", str(e))
        return None

    def _getQueryAutoComplete(self, queryType):
        try:
            return self._queryTypeDict[queryType]["autocomplete"]
        except Exception as e:
            logger.exception("failing %s", str(e))
        return False

    def _getQueryServiceType(self, queryType):
        try:
            return self._queryTypeDict[queryType]["service"]
        except Exception as e:
            logger.exception("failing %s", str(e))
        return None

    ##
    def _setDisplayList(self, name, displayTupList):
        """
        Internal setters defining an ordered collection of attributes to be returned by a named search -

        For example:

        self._displayTypeDict = {
            'summaryResults': [
                ('pdbx_reference_molecule_list', 'family_prd_id', 'Family ID', '%s', 'str', '18px'),
                ('pdbx_reference_molecule', 'prd_id', 'PRD ID', '%s', 'str', '18px'),
                ('pdbx_reference_molecule', 'name', 'Name', '%s', 'str', '50px'),
                ('pdbx_reference_molecule', 'class', 'Class', '%s', 'str', '20px'),
                ('pdbx_reference_molecule', 'type', 'Type', '%s', 'str', '15px'),
                ('pdbx_reference_molecule', 'formula', 'Formula', '%s', 'str', '25px'),
                ('pdbx_reference_molecule', 'formula_weight', 'Formula weight', '%s', 'str', '10px'),
                ('pdbx_reference_molecule', 'chem_comp_id', 'CC ID', '%s', 'str', '8px')
            ]

        """
        try:
            self._displayTypeDict[name] = displayTupList
            return True
        except Exception as e:
            logger.exception("failing %s", str(e))
        return False

    def _getDisplayList(self, name):
        """ """
        try:
            return self._displayTypeDict[name]
        except Exception as e:
            logger.exception("failing %s", str(e))
        return []

    def _getDisplayTableList(self, name):
        uL = []
        try:
            tL = [tup[0] for tup in self._displayTypeDict[name]]
            uL = list(set(tL))
        except Exception as e:
            logger.exception("failing %s", str(e))

        return uL

    def _getDisplayAsList(self, name):
        try:
            tList = [tup[0] for tup in self._displayTypeDict[name]]
            cList = [tup[1] for tup in self._displayTypeDict[name]]
            dList = [tup[2] for tup in self._displayTypeDict[name]]
            sList = [tup[0] + "." + tup[1] for tup in self._displayTypeDict[name]]
            wdList = [tup[5] for tup in self._displayTypeDict[name]]
            return tList, cList, dList, sList, wdList
        except Exception as e:
            logger.exception("failing %s", str(e))

        return [], [], [], [], []

    ##
    def _setJoinAttributes(self, tableName, attributeList):
        """Internal method to set candidate join attributes to be applied between tables in this
            simple search model.  All attributes are standardly named between tables.

        For example:
           _keyDict = {
            'pdbx_reference_molecule_family': ('family_prd_id'),
            'pdbx_reference_molecule_list': ('family_prd_id', 'prd_id'),
            }

        """
        try:
            self._keyDict[tableName] = attributeList
            return True
        except Exception as e:
            logger.exception("failing %s", str(e))

        return False
        #

    def _getJoinAttributes(self, tableName):
        """

        For example:
           _keyDict = {
            'pdbx_reference_molecule_family': ('family_prd_id'),
            'pdbx_reference_molecule_list': ('family_prd_id', 'prd_id'),
            }

        """
        try:
            return self._keyDict[tableName]
        except Exception as e:
            logger.exception("failing %s", str(e))

        return []

    # --------------------------------------------------------------------------------------
    ##
    def _setSearchDef(self, searchType, resourceId, queryColList, logicalOp, extraConditions, orderByList, displayType, displayTitle=None):
        """ """
        try:
            tD = {
                "queryColList": queryColList,
                "logicalOp": logicalOp,
                "extraConditions": extraConditions,
                "orderByList": orderByList,
                "resourceId": resourceId,
                "displayType": displayType,
                "displayTitle": displayTitle,
            }
            self._searchTypeDict[searchType] = tD
            return True
        except Exception as e:
            logger.exception("failing %s", str(e))
        return False

    def _setSearchDefDict(self, searchType, sD):
        """Internal method to define a search Type via the input dict -"""
        try:
            tD = copy.deepcopy(sD)
            for ky in ["resourceId", "queryColList", "logicalOp", "extraConditions", "orderByList", "displayType", "displayTitle"]:
                if ky not in tD:
                    tD[ky] = None
            self._searchTypeDict[searchType] = tD
            return True
        except Exception as e:
            logger.exception("failing %s", str(e))
        return False

    def _getSearchDefByType(self, searchType):
        try:
            d = self._searchTypeDict[searchType]
            return d["resourceId"], d["queryColList"], d["logicalOp"], d["extraConditions"], d["orderByList"], d["displayType"], d["displayTitle"]
        except Exception as e:
            logger.exception("failing searchType %r with %r", searchType, str(e))

        return None, None, None, None, None, None, None

    def _getSearchDefQueryColList(self, searchType):
        try:
            return self._searchTypeDict[searchType]["queryColList"]
        except Exception as e:
            logger.exception("failing %s", str(e))

        return []

    def _getSearchDefLeftJoinTableList(self, searchType):
        try:
            return self._searchTypeDict[searchType]["leftJoinTableList"]
        except Exception as e:
            logger.exception("failing %s", str(e))

        return []

    def _getSearchDefDisplayType(self, searchType):
        try:
            return self._searchTypeDict[searchType]["displayType"]
        except Exception as e:
            logger.exception("failing %s", str(e))

        return None

    def _getSearchDefDisplayTitle(self, searchType):
        try:
            return self._searchTypeDict[searchType]["displayTitle"]
        except Exception as e:
            logger.exception("failing %s", str(e))

        return None

    def _getSearchDefLogicalOp(self, searchType):
        try:
            return self._searchTypeDict[searchType]["logicalOp"]
        except Exception as e:
            logger.exception("failing %s", str(e))

        return None

    def _getSearchDefResourceId(self, searchType):
        try:
            return self._searchTypeDict[searchType]["resourceId"]
        except Exception as e:
            logger.exception("failing %s", str(e))

        return None

    # -------------------------------------------------------------------------------------
    ##

    def __runAutoCompleteRdbmsQuery(self, searchType, searchTarget, compareType="EXACT"):
        """Return an autocomplete list for the current searchType and searchTarget -"""
        #
        _, qCols, _, _, _, _, _ = self._getSearchDefByType(searchType)
        rList = []
        rD = {}
        logger.debug("searchTarget %r qCols %r", searchTarget, qCols)
        for qCol in qCols:
            pc = "%"
            if compareType == "LIKE":
                tId = pc + searchTarget + pc
            elif compareType in ["EXACT", "EQUAL"]:
                tId = searchTarget + pc
            else:
                logger.error("compareType %s unknown", compareType)
                continue
            queryConditionString = ' WHERE %s LIKE "%s"  ' % (qCol, tId)

            tL = qCol.split(".")
            tName = ".".join(tL[:-1])

            #
            queryString = "SELECT DISTINCT " + qCol + " FROM " + tName + " " + queryConditionString

            curs = self.getCursor()
            #
            logger.debug("SQL Id query: %s", queryString)

            curs.execute(queryString)
            while True:
                result = curs.fetchone()
                if result is not None:
                    rD[str(result[0])] = str(result[0])
                else:
                    break
        uList = sorted(rD.keys())
        # this object packaging was expected by the jQuery plugin
        for ky in uList:
            entry = {}
            entry["id"] = ky
            entry["value"] = ky
            entry["label"] = ky
            rList.append(entry)

        logger.debug("rList %r myKeys %r", rList, uList)
        return rList, uList

    def __getConditionString(self, qCols, searchTarget, compareType, lOp):
        qS = ""
        try:
            qL = []
            sOp = " %s " % lOp
            for qCol in qCols:
                if compareType == "LIKE":
                    pc = "%"
                    tId = pc + searchTarget + pc
                    qL.append(' ( %s LIKE "%s" ) ' % (qCol, tId))
                elif compareType in ["EQ", "EQUAL", "EXACT"]:
                    qL.append(' ( %s = "%s" ) ' % (qCol, searchTarget))
                elif compareType == "LT":
                    qL.append(" ( %s <  %s ) " % (qCol, searchTarget))
                elif compareType == "GT":
                    qL.append(" ( %s >  %s ) " % (qCol, searchTarget))
                elif compareType == "BETWEEN":
                    stL = searchTarget.split()
                    qL.append(" ( %s BETWEEN  %s AND %s ) " % (qCol, stL[0], stL[1]))
                else:
                    pass
            if len(qL) > 1:
                qS = " ( " + sOp.join(qL) + " ) "
            else:
                qS = sOp.join(qL)
        except Exception as e:
            logger.exception("failing searchTarget %r compareType %r with %s", searchTarget, compareType, str(e))

        return qS

    def __runRdbmsQuery(self, searchType, searchTarget, compareType="LIKE"):
        """Generate SQL, execute query and return results for the input search type."""
        _, qCols, lOp, extraConditions, orderByList, displayType, _ = self._getSearchDefByType(searchType)
        #
        #
        qS = self.__getConditionString(qCols, searchTarget, compareType, lOp)
        #
        queryConditionString = qS
        if extraConditions is not None and (len(extraConditions) > 0):
            queryConditionString += " AND " + extraConditions

        tList, _cList, dList, sList, wdList = self._getDisplayAsList(displayType)
        tList = list(set(tList))
        #
        logger.info("Table list %r", tList)
        #
        # Additional join conditions for multiple tables -
        #
        conditionList = []
        joinConditionString = ""
        if len(tList) > 1:
            for i1, t1 in enumerate(tList):
                for i2, t2 in enumerate(tList):
                    if i2 < i1:
                        t1JList = self._getJoinAttributes(t1)
                        t2JList = self._getJoinAttributes(t2)
                        for jPr in [
                            ("family_prd_id", "family_prd_id"),
                            ("prd_id", "prd_id"),
                            ("Structure_ID", "Structure_ID"),
                            ("Structure_ID", "pdb_id"),
                            ("pdb_id", "Structure_ID"),
                        ]:
                            if jPr[0] in t1JList and jPr[1] in t2JList:
                                conditionList.append(t1 + "." + jPr[0] + " = " + t2 + "." + jPr[1])
        #
        logger.info("Condition list %r", conditionList)
        #
        ljtList = self._getSearchDefLeftJoinTableList(searchType)
        logger.info("ljt list: %r", ljtList)
        if len(ljtList) > 0:
            # Assume all conditions are applied to the base table and only join conditions to the LJ tables
            if len(conditionList) > 0:
                joinConditionString = " AND " + " AND ".join(conditionList)
            ttList = []
            for t in tList:
                if t not in ljtList:
                    ttList.append(t)
            if len(conditionList) > 0:
                joinConditionString = " ON " + " AND ".join(conditionList)
            #
            queryString = (
                "SELECT DISTINCT " + ",".join(sList) + " FROM " + ",".join(ttList) + " LEFT JOIN " + ",".join(ljtList) + joinConditionString + " WHERE  " + queryConditionString
            )
        else:
            if len(conditionList) > 0:
                joinConditionString = " AND " + " AND ".join(conditionList)
            #
            queryString = "SELECT DISTINCT " + ",".join(sList) + " FROM " + ",".join(tList) + " WHERE ( " + queryConditionString + joinConditionString + " )"

        if orderByList is not None and len(orderByList) > 0:
            queryString += " ORDER BY " + ",".join(orderByList) + " ASC "

        curs = self.getCursor()
        #
        logger.info("SQL query: %s", queryString)
        rList = []
        curs.execute(queryString)
        while True:
            result = curs.fetchone()
            if result is not None:
                entry = {}
                for ii, col in enumerate(dList):
                    entry[col] = result[ii]
                rList.append(entry)
            else:
                break
        if self.__debug:
            logger.debug("rList %r", rList)
            logger.debug("rList length %r", len(rList))
            logger.debug("dList %r", dList)

        return rList, dList, wdList

    ###
    def __runIndexQuery(self, queryType, searchType, searchTarget):
        """
        'INDEX_MATCH_SUBSTRING': {'autocomplete': False, 'service': 'index', 'class': 'entity'},
        'INDEX_MATCH_EXACT': {'autocomplete': False, 'service': 'index', 'class': 'entity'},
        'INDEX_FORMULA_SUBSET': {'autocomplete': False, 'service': 'index', 'class': 'entity'},
        'INDEX_FORMULA_EXACT': {'autocomplete': False, 'service': 'index', 'class': 'entity'},
        'INDEX_FORMULA_EXACT_SKIPH': {'autocomplete': False, 'service': 'index', 'class': 'entity'},
        'INDEX_FORMULA_BOUNDED': {'autocomplete': False, 'service': 'index', 'class': 'entity'},

        """
        #
        _, qCols, _, _, _, displayType, _ = self._getSearchDefByType(searchType)

        _tList, cList, dList, _sList, wdList = self._getDisplayAsList(displayType)
        #
        logger.debug("qCols %r", qCols)
        logger.debug("queryType %r", queryType)
        logger.debug("searchTarget %r", searchTarget)

        ccsi = ChemCompSearchIndexUtils(siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)

        if queryType.startswith("INDEX_FORMULA_"):
            idList = []
            tf, eD = ccsi.parseFormulaInput(searchTarget)
            logger.info("Search target = %r %r", tf, eD)
            searchCompOp = "Computed"
            if queryType == "INDEX_FORMULA_BOUNDED":
                idList = ccsi.searchFormulaBounded(elementCounts=eD)
            elif queryType == "INDEX_FORMULA_SUBSET":
                idList = ccsi.searchFormulaSubset(elementCounts=eD)
            elif queryType == "INDEX_FORMULA_EXACT":
                idList = ccsi.searchFormulaExact(elementCounts=eD, excludeH=False)
            elif queryType == "INDEX_FORMULA_EXACT_SKIPH":
                idList = ccsi.searchFormulaExact(elementCounts=eD, excludeH=True)
            else:
                logger.info("Unsupported formula index search")
        elif queryType.startswith("INDEX_MATCH"):
            idList = []
            for qCol in qCols:
                tidList = []
                if queryType == "INDEX_MATCH_SUBSTRING":
                    tidList = ccsi.searchIndexSubstring(searchTarget, qCol)
                    searchCompOp = "Substring comparison"
                elif queryType == "INDEX_MATCH_EXACT":
                    logger.debug("Searching field %r target %r", qCol, searchTarget)
                    tidList = ccsi.searchIndex(searchTarget, qCol)
                    searchCompOp = "Exact match"
                elif queryType == "INDEX_MATCH_RANGE_VALUE_PAIR":
                    logger.debug("Searching field %r target range %r", qCol, searchTarget)
                    tidList = ccsi.searchIndexRange(searchTarget, qCol)
                    searchCompOp = "Range match"
                elif queryType == "INDEX_MATCH_SIMILAR":
                    logger.debug("Searching similar field %r target %r", qCol, searchTarget)
                    tidList = ccsi.searchEditDistance(searchTarget, qCol)
                    searchCompOp = "Similar match"
                else:
                    logger.info("Unsupported index matching search")
                idList.extend(tidList)
        else:
            idList = []
            searchCompOp = "unknown"
            logger.info("Unsupported index search")

        logger.debug("idList length %r", len(idList))
        logger.debug("cList %r", cList)
        rList = ccsi.getAttributeValueList(idList, cList, dList)
        #
        return rList, dList, wdList, searchCompOp

    def __standardizedSearchTarget(self, searchTargetInp, searchType):
        searchTargetOut = searchTargetInp
        logger.debug("Standarizing search target '%s' for search type '%s'", searchTargetInp, searchType)
        if searchType.startswith("CCDIDX_SMILES"):
            try:
                logger.info("Input SMILES '%s", searchTargetInp)
                oedu = OeDescriptorUtils()
                searchTargetOut = oedu.standardizeSmiles(searchTargetInp, type="ISOMERIC")
                logger.info("ISOMERIC SMILES '%s'", searchTargetOut)
            except Exception as e:
                logger.exception("Error '%s' occured. Arguments %s.", str(e), e.args)
        #
        return searchTargetOut

    def doSearch(self):
        """Public entry point for chemical reference search -"""
        # Get the input search parameters --
        #              searchType                     | queryType | target input type | comparison type
        #  CCDINST_CC_ID_PUBLIC,CCDINST_CC_ID_INTERNAL|CCD_INSTANCE  |MULTI_VALUE_WS  |EQUAL
        #
        queryType, searchType, searchTarget, searchName, inputType, compareType = self.getSearch()

        #
        retDict = {}
        if searchTarget is None or len(searchTarget) < 1:
            return retDict
        #
        if self.__verbose:
            logger.debug("searchTargetInp             = %s", searchTarget)
            logger.debug("searchTypeInp               = %s", searchType)
            logger.debug("queryTypeInp                = %s", queryType)
            logger.debug("inputTypeInp                = %s", inputType)
            logger.debug("compareTypeInp              = %s", compareType)
            logger.debug("searchNameInp               = %s", searchName)
        #
        if inputType == "MULTI_VALUE_WS":
            searchTargetList = str(searchTarget).split()
        else:
            searchTargetList = [searchTarget]
        #
        searchTypeList = searchType.split(",")
        compareTypeList = compareType.split(",")
        if len(compareTypeList) < len(searchTypeList):
            compareTypeList = compareTypeList * len(searchTypeList)

        searchServiceType = self._getQueryServiceType(queryType)
        count = 0
        sD = {}
        #
        rId = 1
        #
        for sType, cType in zip(searchTypeList, compareTypeList):
            sD[rId] = {}
            # ----
            rList = []
            stdSearchTargetList = []
            trList = []
            cList = []
            wdList = []
            for sTargInp in searchTargetList:
                sTarg = self.__standardizedSearchTarget(sTargInp, sType)
                stdSearchTargetList.append(sTarg)
                if searchServiceType == "rdbms":
                    resourceId = self._getSearchDefResourceId(sType)
                    self.setResource(resourceName=resourceId)
                    ok = self.openConnection()
                    if ok:
                        trList, cList, wdList = self.__runRdbmsQuery(sType, sTarg, compareType=cType)
                    self.closeConnection()
                elif searchServiceType == "index":
                    trList, cList, wdList, _ = self.__runIndexQuery(queryType, sType, sTarg)
                else:
                    trList = []
                    cList = []
                    wdList = []
                rList.extend(trList)
            #
            if cType in ["EQ", "EXACT", "EQUAL"]:
                cTypeD = "equal to"
            elif cType in ["LIKE"]:
                cTypeD = "like"
            elif cType in ["SIMILAR", "COMPUTED"]:
                cTypeD = " - "
            else:
                cTypeD = cType.lower()
            #
            dTitle = self._getSearchDefDisplayTitle(sType)
            if len(dTitle) > 0:
                searchNameD = dTitle
            else:
                searchNameD = searchName
            #
            displayTitle = "Results for: %s <i>%s</i> <span class='stdSearchTargetList'>%s</span> &nbsp;&nbsp; (%d)" % (searchNameD, cTypeD, ",".join(stdSearchTargetList), len(rList))
            # oL = []
            sD[rId]["resultlist"] = rList
            sD[rId]["columnList"] = cList
            sD[rId]["columnWidthList"] = wdList
            sD[rId]["searchType"] = sType
            sD[rId]["compareType"] = cType
            sD[rId]["displayTitle"] = displayTitle
            count += len(rList)
            rId += 1

        # JDW  = legacy searchOp returned for now as compareType
        retDict = {
            "sid": None,
            # "searchTarget": searchTarget,
            "searchTarget": " ".join(stdSearchTargetList),
            "searchTypeList": searchTypeList,
            "compareType": compareTypeList,
            "searchOp": compareTypeList,
            "count": count,
            "searchType": searchType,
            "resultDictionary": sD,
        }

        return retDict

    def doSearchAutoComplete(self):
        """Entry point for reference entity autocomplete search -

        Not all query types may support autocomplete queries -
        """
        rList = []
        uList = []
        queryType, searchType, searchTarget, _, inputType, compareType = self.getSearch()
        #
        if self._getQueryAutoComplete(queryType) and self._getQueryServiceType(queryType) == "rdbms":
            if searchTarget is None or len(searchTarget) < 1:
                return rList
            #
            iL = []
            sTarget = searchTarget
            try:
                if inputType in ["MULTI_VALUE_WS"]:
                    iL = searchTarget.split()
                    sTarget = iL[-1]
            except Exception as e:
                logger.exception("Failing to parse input %r with %r", searchTarget, str(e))

            searchTypeList = searchType.split(",")
            compareTypeList = compareType.split(",")
            if len(compareTypeList) < len(searchTypeList):
                compareTypeList = compareTypeList * len(searchTypeList)

            #
            rList = []
            uList = []
            for sType, cType in zip(searchTypeList, compareTypeList):
                resourceId = self._getSearchDefResourceId(sType)
                self.setResource(resourceName=resourceId)
                if self.__verbose:
                    logger.debug("Query target                   = %s", searchTarget)
                    logger.debug("Query type                     = %s", sType)
                    logger.debug("Query resource id              = %s", resourceId)

                self.openConnection()
                trList, tuList = self.__runAutoCompleteRdbmsQuery(sType, sTarget, cType)
                rList.extend(trList)
                uList.extend(tuList)
                self.closeConnection()
        else:
            pass
        uList = list(set(uList))
        try:
            if inputType in ["MULTI_VALUE_WS"] and len(iL) > 1:
                uList = [" ".join(iL[:-1]) + " " + uL for uL in uList]
        except Exception as e:
            logger.debug("Failing to parse input %r with %r", searchTarget, str(e))
        return rList, uList
