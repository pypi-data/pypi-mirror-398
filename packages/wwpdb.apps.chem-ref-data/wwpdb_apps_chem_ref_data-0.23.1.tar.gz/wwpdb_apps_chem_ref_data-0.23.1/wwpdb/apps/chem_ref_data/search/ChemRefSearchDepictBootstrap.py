##
# File:  ChemRefSearchDepictBootstrap.py
# Date:  18-Feb-2013 jdw
#
# Updates:
#    28-Apr-2017  Replace server generated tables wioth BootstrapTable rendering -
#
##
"""
Create HTML depictions for simple chemical reference searches using Bootstrap CSS framework -

"""
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "jwest@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.01"

import sys
import random

#
import logging

# Only for full page rendering -
from wwpdb.apps.chem_ref_data.depict.ChemRefDataDepictBootstrap import ChemRefDataDepictBootstrap

logger = logging.getLogger(__name__)


class ChemRefSearchDepictBootstrap(ChemRefDataDepictBootstrap):
    """Create HTML depictions for simple chemical reference searches using Bootstrap CSS framework -"""

    def __init__(self, includePath=None, verbose=False, log=sys.stderr):
        """

        :param `verbose`:  boolean flag to activate verbose logging.
        :param `log`:      stream for logging.

        """
        super(ChemRefSearchDepictBootstrap, self).__init__(includePath, verbose, log)
        #
        #

    def doRenderPage(self, d=None):
        """Render complete HTML page -"""
        #
        if d is None:
            d = {}
        oL = []
        oL.extend(self.appPageTop(title="Chemical Reference Data Management Module", cssPathList=[]))
        #
        oL.extend(self.doRenderResults(d))
        #
        oL.extend(self.appPageBottom(scriptPathList=[]))
        return oL

    def doAltRenderCollapsable(self, d=None, searchName="Search results", compareType=None, searchTarget=None):
        """Render in collapsable section:

        <
        """
        if d is None:
            d = {}
        oL = []
        if d["count"] < 1:
            return oL
        #
        if "compareType" in d and "searchType" in d:
            myTitle = "Results for: %s <i>%s</i> %s &nbsp;&nbsp; " % (searchName, d["compareType"], d["searchTarget"])
        elif compareType and searchTarget:
            myTitle = "Results for: %s <i>%s</i> %s &nbsp;&nbsp; " % (searchName, compareType, searchTarget)
        else:
            myTitle = "%s for target = %s &nbsp;&nbsp; " % (searchName, d["searchTarget"])

        panelTitle = myTitle
        try:
            oL.extend(self.doAltRenderResults(d, title=panelTitle))
        except Exception as e:
            logger.exception("Failing %s", str(e))

        return oL

    def __panelBegin(self, panelTitle, state="collapsed", toggleStyle="href"):
        """Return the prologue for a collapsed panel - BS3+/FA4"""
        # state controls whether the panel is initially expanded or collapsed
        #
        if state == "collapsed":
            panelState = ("", "collapsed")
        else:
            panelState = ("in", "")

        #
        oL = []
        idPrefix = "subpanel-" + str(random.randint(0, 100000))
        idPanel = idPrefix + "-psec-0"
        idPanelHeader = idPrefix + "-phead-0"
        idPanelCollapsable = idPrefix + "-pcol-0"
        #
        #  Not using this level --
        # oL.append('<div class="panel-group" id="%s" role="tablist" aria-multiselectable="true">' % idPanelGroup)
        # -------------------------
        oL.append('  <div id="%s" class="panel panel-default results-section">' % idPanel)

        #
        oL.append('     <div class="panel-heading" role="tab" id="%s">' % idPanelHeader)
        # add close/dismiss --
        oL.append(
            '         <button type="button" class="close" data-target="#%s" data-dismiss="alert"> <span aria-hidden="true"> <i class="fa fa-times"></i></span><span class="sr-only">Close</span></button>'  # noqa: E501
            % idPanel
        )

        oL.append('        <div class="panel-title">')

        if toggleStyle == "href":
            oL.append(
                '          <a role="button" data-toggle="collapse"  href="#%s" aria-expanded="true" aria-controls="%s" class="%s"><i class="chevron fa fa-fw" ></i></a>%s'
                % (idPanelCollapsable, idPanelCollapsable, panelState[1], panelTitle)
            )
        elif toggleStyle == "chevron":
            oL.append(
                '          <a role="button" data-toggle="collapse" href="#%s" aria-expanded="true" aria-controls="%s" class="%s">%s <i class="chevron fa fa-fw" ></i></a>'
                % (idPanelCollapsable, idPanelCollapsable, panelState[1], panelTitle)
            )
        elif toggleStyle == "button":
            oL.append("<span>%s</span>" % panelTitle)
            buttonTitle = "Toggle view"
            oL.append(
                '<button class="btn btn-primary btn-xs" type="button" data-toggle="collapse" data-target="#%s" aria-expanded="false" aria-controls="%s">%s</button>'
                % (idPanelCollapsable, idPanelCollapsable, buttonTitle)
            )

        oL.append("        </div>")

        oL.append("     </div>")

        oL.append('     <div id="%s" class="panel-collapse collapse %s" role="tabpanel" aria-labelledby="%s">' % (idPanelCollapsable, panelState[0], idPanelHeader))
        oL.append('        <div class="panel-body">')
        return oL

    def __panelEnd(self):
        """ """
        oL = []
        # oL.append('        </div>')
        oL.append("     </div>")
        oL.append("  </div> <!-- end of panel -->")
        # -------------------------
        return oL

    def __filterResultSet(self, rD):
        """Add markup to selected column types -"""
        #
        for result in rD["resultlist"]:
            for cName in rD["columnList"]:
                if cName in result and result[cName]:
                    if cName in ["Family ID", "PRD ID"]:
                        result[cName] = '<a class="app-ref-report"  href="#">%s</a>' % result[cName]
                    elif cName in ["CC ID"]:
                        rpt = '<a class="app-ref-report"  href="#">%s</a>' % result[cName]
                        le = '<a target="_blank" href="http://ligand-expo.rcsb.org/pyapps/ldHandler.py?formid=cc-index-search&operation=ccid&target=%s">(LE)</a>' % result[cName]
                        result[cName] = "%s &nbsp; %s" % (rpt, le)
                    elif cName in ["ID"]:
                        if result[cName].startswith("PRD_") or result[cName].startswith("FAM_"):
                            result[cName] = '<a class="app-ref-report"  href="#">%s</a>' % result[cName]
                        else:
                            rpt = '<a class="app-ref-report"  href="#">%s</a>' % result[cName]
                            le = (
                                '<a target="_blank" href="http://ligand-expo.rcsb.org/pyapps/ldHandler.py?formid=cc-index-search&operation=ccid&target=%s">(LE)</a>' % result[cName]
                            )
                            result[cName] = "%s &nbsp; %s" % (rpt, le)
        return rD

    def __bootstrapTableTemplate(
        self,
        colNameTupList,
        columnWidthList,
        title="Search Results",  # pylint: disable=unused-argument
        tableId="chemref-bst-result-table-1",
        divId="chemref-bst-result-div-1",
        pFunc="pagerFunc",
    ):
        """
        Create table template for BootstrapTable parameters --

        colNameTupList = [(colkey,colDisplayName), ... ]
        pagerFunc = <name of JS pager method >

        """
        tableH = """<div id="%s" class="row">
           <table id="%s" data-classes="table  table-bordered table-condensed table-striped"
           data-sort-name="my_data_count"
           data-sort-order="desc"
           data-search="true"
           data-show-refresh="true"
           data-show-toggle="true"
           data-show-columns="true"
           data-query-params="%s"
           data-pagination="true"
           data-page-size="20"
           data-page-list="[20,50,150]"
           data-show-export="true"
           data-export-types="['csv','excel']"
           data-show-refresh="true"
           data-striped="true"
                     data-show-toggle="true">""" % (
            divId,
            tableId,
            pFunc,
        )
        # omit
        #            data-height="600"
        #
        oL = []
        oL.append(tableH)

        # oL.append('<caption class="text-left"><strong> &nbsp;&nbsp; %s</strong></caption>' % title)
        oL.append("<thead><tr>")
        for ii, tup in enumerate(colNameTupList):
            cw = columnWidthList[ii]
            oL.append('<th data-field="%s" data-width="%s" data-sortable="true">%s</th>' % (tup[0], cw, tup[1]))
        oL.append("</tr></thead></table>")
        oL.append("</div><!-- end or result container -->")

        return oL

    def doBsTableRenderCollapsable(self, d=None, searchName="Search results", compareType=None, searchTarget=None):
        """Render in collapsable section using Bootstrap table style --"""
        oL = []
        if d is None:
            d = {}

        if d["count"] < 1:
            return oL
        #
        if "compareType" in d and "searchType" in d:
            myTitle = "Results for: %s <i>%s</i> %s &nbsp;&nbsp; " % (searchName, d["compareType"], d["searchTarget"])
        elif compareType and searchTarget:
            myTitle = "Results for: %s <i>%s</i> %s &nbsp;&nbsp; " % (searchName, compareType, searchTarget)
        else:
            myTitle = "%s for target = %s &nbsp;&nbsp; " % (searchName, d["searchTarget"])

        panelTitle = myTitle
        logger.info("myTitle is %r", myTitle)
        tableDataD = {}
        try:
            tableDataD = self.doBsTableRenderResults(d, title=panelTitle)
        except Exception as e:
            logger.exception("Failing %s", str(e))

        return tableDataD

    def doBsTableRenderResults(self, d=None, title="Search Results Summary"):
        """ """
        if d is None:
            d = {}
        tableDataD = {}
        for resultSetId in range(1, len(d["resultDictionary"]) + 1):
            rD = d["resultDictionary"][resultSetId]
            if len(rD["resultlist"]) < 1:
                continue
            #
            if ("displayTitle" in rD) and (len(rD["displayTitle"]) > 0):
                t = rD["displayTitle"]
                # t = title + ' (' + rD['displayTitle'] + ')'
            else:
                t = title
            #
            #
            oL = []
            tD = {}
            oL.extend(self.__panelBegin(t, state="collapsed", toggleStyle="href"))
            #
            colNameTupList = [(c, c) for c in rD["columnList"]]
            #
            idSuffix = "acc" + str(random.randint(0, 100000))
            tD["resultSetContainerId"] = "chemref-bst-result-div-%s" % idSuffix
            tD["resultSetTableId"] = "chemref-bst-result-table-%s" % idSuffix
            #
            oL.extend(
                self.__bootstrapTableTemplate(colNameTupList, rD["columnWidthList"], title=t, tableId=tD["resultSetTableId"], divId=tD["resultSetContainerId"], pFunc="pagerFunc")
            )
            #
            rD = self.__filterResultSet(rD)
            tD["resultSetTableData"] = rD["resultlist"]
            tD["resultSetId"] = resultSetId
            #
            # rD['resultlist']  [{rowdict},{rowdict},...]
            # rD['columnList']  display column = col key
            #
            oL.extend(self.__panelEnd())
            #
            tD["resultSetTableTemplate"] = "\n".join(oL)
            tableDataD[resultSetId] = tD

        return tableDataD

    def doAltRenderResults(self, d=None, title="Search Results Summary"):
        """Render in HTML"""
        #
        if d is None:
            d = {}

        # sp = '&nbsp;&nbsp;'
        oL = []
        #
        #
        # oL.append('<h4>%s</h4>' % title)

        # if False:
        #     oL.append('<h4>%s</h4>' % title)
        #     oL.append('<p>')
        #     oL.append('Search type:   <strong>%s</strong> ' % d['searchType'])
        #     oL.append('%s' % sp)
        #     oL.append('Search target: <strong>%s</strong> ' % d['searchTarget'])
        #     oL.append('%s' % sp)
        #     oL.append('Comparison type: <strong>%s</strong> ' % d['searchOp'])
        #     oL.append('%s' % sp)
        #     oL.append('Result count: <strong>%r</strong> ' % d['count'])
        #     oL.append('</p>')
        #     oL.append('<br />')

        #
        for resultSetId in range(1, len(d["resultDictionary"]) + 1):
            rD = d["resultDictionary"][resultSetId]
            if len(rD["resultlist"]) < 1:
                continue
            # -- Wrapper
            if ("displayTitle" in rD) and (len(rD["displayTitle"]) > 0):
                t = title + " (" + rD["displayTitle"] + ")"
            else:
                t = title
            oL.extend(self.__panelBegin(t, state="collapsed", toggleStyle="href"))
            # -- Wrapper
            # oL.append('<h4>%s</h4>' % rD['displayTitle'])
            oL.append('<table class="table  table-bordered table-condensed table-striped">')

            for cWidth in rD["columnWidthList"]:
                oL.append(' <col width="%s" />' % cWidth)

            oL.append("<tr>")
            for cName in rD["columnList"]:
                oL.append(" <th>%s</th>" % cName)
            oL.append("</tr>")
            #
            # Row data -
            #
            i = 0
            for result in rD["resultlist"]:
                i += 1
                oL.append("<tr>")
                for cName in rD["columnList"]:
                    if cName in result and result[cName]:
                        if cName == "Family ID":
                            oL.append('          <td><a class="app-ref-report"  href="#">%s</a></td>' % (result[cName]))
                        elif cName == "PRD ID":
                            oL.append('          <td><a class="app-ref-report"   href="#">%s</a></td>' % (result[cName]))
                        elif (cName == "CC ID") or (cName == "ID"):
                            rpt = '<a class="app-ref-report"  href="#">%s</a>' % result[cName]
                            le = (
                                '<a target="_blank" href="http://ligand-expo.rcsb.org/pyapps/ldHandler.py?formid=cc-index-search&operation=ccid&target=%s">(LE)</a>' % result[cName]
                            )
                            oL.append("          <td>%s &nbsp; %s</td>" % (rpt, le))

                        else:
                            oL.append("          <td>%s</td>" % result[cName])
                    else:
                        oL.append("          <td>&nbsp;</td>")
                oL.append("       </td>")
                oL.append("     </tr>")
            oL.append("</table>")
            # -- Wrapper
            oL.extend(self.__panelEnd())
            # --- Wrapper
            #

        # -------------------------------------

        return oL

    def doRenderCollapsable(self, d=None, title="Search results", compareType=None, searchTarget=None):
        """Render in collapsable section -"""
        oL = []

        if d is None:
            d = {}

        if d["count"] < 1:
            return oL
        idPrefix = "acc" + str(random.randint(0, 100000))
        idTop = idPrefix + "-top"

        #
        active = ""
        if compareType and searchTarget:
            myTitle = "Results for: %s <i>%s</i> %s &nbsp;&nbsp; " % (title, compareType, searchTarget)
        else:
            myTitle = "%s for target = %s &nbsp;&nbsp; " % (title, d["searchTarget"])

        idSection = idPrefix + "-sec-0"
        oL.append('<div class="accordion" id="%s">' % idTop)

        oL.append('<div class="accordion-group">')
        oL.append('<div class="accordion-heading">')
        oL.append('<span>%s</span><a class="accordion-toggle" data-toggle="collapse" data-parent="#%s" href="#%s">(toggle view results)</a>' % (myTitle, idTop, idSection))
        oL.append("</div>")
        oL.append('<div id="%s" class="accordion-body collapse %s">' % (idSection, active))
        oL.append('<div  class="accordion-inner">')

        oL.extend(self.doRenderResults(d))

        oL.append("</div>")
        oL.append("</div> <!-- end of accordion group -->")
        oL.append("</div> <!-- end of accordion -->")

        return oL

    def doRenderResults(self, d=None, title="Search Results Summary"):
        """Render in HTML"""
        #
        if d is None:
            d = {}

        sp = "&nbsp;&nbsp;"
        requestHost = "localhost"

        oL = []
        #
        #
        oL.append("<h4>%s</h4>" % title)
        oL.append("<p>")
        oL.append("Search type:   <strong>%s</strong> " % d["searchType"])
        oL.append("%s" % sp)
        oL.append("Search target: <strong>%s</strong> " % d["searchTarget"])
        oL.append("%s" % sp)
        oL.append("Comparison type: <strong>%s</strong> " % d["searchOp"])
        oL.append("%s" % sp)
        oL.append("Result count: <strong>%r</strong> " % d["count"])
        oL.append("</p>")
        oL.append("<br />")

        #
        for resultSetId in range(1, len(d["resultDictionary"]) + 1):
            rD = d["resultDictionary"][resultSetId]

            if len(rD["resultlist"]) < 1:
                continue

            oL.append("<br /><h4>%s</h4>" % rD["displayTitle"])

            oL.append('<table class="table  table-bordered table-condensed table-striped">')

            for cWidth in rD["columnWidthList"]:
                oL.append('	<col width="%s" />' % cWidth)

            oL.append("<tr>")
            for cName in rD["columnList"]:
                oL.append("	<th>%s</th>" % cName)
            oL.append("</tr>")
            #
            # Row data -
            #
            i = 0
            for result in rD["resultlist"]:
                i += 1
                oL.append("<tr>")
                for cName in rD["columnList"]:
                    if cName in result and result[cName]:
                        if cName == "Family ID":
                            oL.append(
                                '          <td><a class="app-ref-report" target="_blank" href="http://%s/service/chemref/bird/report?prdId=%s&format=%s">%s</a></td>'
                                % (requestHost, result[cName], "html", result[cName])
                            )
                        elif cName == "PRD ID":
                            oL.append(
                                '          <td><a class="app-ref-report"  target="_blank" href="http://%s/service/chemref/bird/report?prdId=%s&format=%s">%s</a></td>'
                                % (requestHost, result[cName], "html", result[cName])
                            )
                        elif (cName == "CC ID") or (cName == "ID"):
                            rpt = '<a class="app-ref-report" target="_blank" href="#">%s</a>' % result[cName]
                            le = (
                                '<a target="_blank" href="http://ligand-expo.rcsb.org/pyapps/ldHandler.py?formid=cc-index-search&operation=ccid&target=%s">(LE)</a>' % result[cName]
                            )
                            oL.append("          <td>%s &nbsp; %s</td>" % (rpt, le))

                        else:
                            oL.append("          <td>%s</td>" % result[cName])
                    else:
                        oL.append("          <td>&nbsp;</td>")
                oL.append("  	  </td>")
                oL.append("     </tr>")
            oL.append("</table>")
            #

        # -------------------------------------

        return oL
