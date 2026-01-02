##
# File:  ChemRefReportDepictBootstrap.py
# Date:  18-Feb-2013  Jdw
#
# Updates:
#   2-Jun-2017 jdw add NGL viewer
#   3-Jun-2017 jdw fix CSS for NGL panes & missing
#  14-Jun-3017 jdw generalize the handling of coordinate files -
#                  change markup of tabbable section to toggle and resist jump scrolling -
#   Jun-2023 james smith add at-a-glance tab
#  27-Aug-2024  zf add "pdbx_chem_comp_pcm" category
#  17-Dec-2025  zf add "pdbx_chem_comp_atom_coordination" and "pdbx_chem_comp_atom_coordination_sphere" categories
##
"""
Create tabular HTML reports from chemical reference definitions.

This version uses Bootstrap CSS framework constructs.

"""
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "jwest@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.01"

import sys
import random
from wwpdb.apps.chem_ref_data.depict.ChemRefDataDepictBootstrap import (
    ChemRefDataDepictBootstrap,
)

import logging

logger = logging.getLogger(__name__)


class ChemRefReportDepictBootstrap(ChemRefDataDepictBootstrap):
    """Create tabular HTML reports from chemical reference definitions.

    This version uses Bootstrap CSS framework constructs.

    """

    def __init__(self, styleObject=None, verbose=False, log=sys.stderr):
        """

        :param `verbose`:  boolean flag to activate verbose logging.
        :param `log`:      stream for logging.

        """
        super(ChemRefReportDepictBootstrap, self).__init__(verbose, log)
        self.__debug = False
        #
        self.__st = styleObject
        #
        self.__setup()

    def __setup(self):
        """Category list --"""
        #
        if self.__st.getStyleId() in ["CHEM_COMP_V1"]:
            self.__reportCategories = [
                ("chem_comp", "chem_comp", "column-wise"),
                ("pdbx_chem_comp_synonyms", "synonyms", "row-wise"),
                ("chem_comp_atom", "chem_comp_atom", "row-wise"),
                ("chem_comp_bond", "chem_comp_bond", "row-wise"),
                ("pdbx_chem_comp_descriptor", "descriptor", "row-wise"),
                ("pdbx_chem_comp_identifier", "identifier", "row-wise"),
                ("pdbx_chem_comp_pcm", "pdbx_chem_comp_pcm", "row-wise"),
                ("pdbx_chem_comp_atom_coordination", "coordination", "row-wise"),
                ("pdbx_chem_comp_atom_coordination_sphere", "coordination_sphere", "row-wise"),
                ("pdbx_chem_comp_related", "related", "row-wise"),
                ("pdbx_chem_comp_atom_related", "atom_related", "row-wise"),
                ("pdbx_chem_comp_audit", "audit", "row-wise"),
            ]
        elif self.__st.getStyleId() in ["BIRD_V1"]:
            self.__reportCategories = [
                ("pdbx_reference_molecule_list", "molecule_list", "row-wise"),
                ("pdbx_reference_molecule_family", "molecule_family", "row-wise"),
                ("pdbx_reference_molecule_synonyms", "molecule_synonyms", "row-wise"),
                (
                    "pdbx_reference_molecule_annotation",
                    "molecule_annotation",
                    "row-wise",
                ),
                ("pdbx_reference_molecule_features", "molecule_features", "row-wise"),
                (
                    "pdbx_reference_molecule_related_structures",
                    "molecule_related_structures",
                    "row-wise",
                ),
                ("pdbx_reference_molecule_details", "details", "row-wise"),
                ("citation", "citation", "row-wise"),
                ("citation_author", "citation_author", "row-wise"),
                ("pdbx_family_prd_audit", "family_prd_audit", "row-wise"),
                #
                ("pdbx_reference_molecule", "molecule", "column-wise"),
                ("pdbx_reference_entity_list", "entity_list", "row-wise"),
                ("pdbx_reference_entity_src_nat", "entity_src_nat", "row-wise"),
                ("pdbx_reference_entity_poly", "entity_poly", "row-wise"),
                ("pdbx_reference_entity_poly_seq", "entity_poly_seq", "row-wise"),
                ("pdbx_reference_entity_sequence", "entity_sequence", "row-wise"),
                (
                    "pdbx_reference_entity_sequence_list",
                    "entity_sequence_list",
                    "row-wise",
                ),
                (
                    "pdbx_reference_entity_subcomponents",
                    "entity_subcomponents",
                    "row-wise",
                ),
                ("pdbx_reference_entity_nonpoly", "entity_nonpoly", "row-wise"),
                ("pdbx_reference_entity_link", "entity_link", "row-wise"),
                ("pdbx_reference_entity_poly_link", "entity_poly_link", "row-wise"),
                ("pdbx_prd_audit", "prd_audit", "row-wise"),
            ]

    def render(self, eD, style="tabs"):
        """ """
        if style in ["tabs"]:
            return self.__doRenderTabs(eD)
        elif style in ["accordion", "multiaccordion"]:
            return self.__doRenderAccordion(eD)
        else:
            return self.__doRenderPage(
                eD
            )  # Due to missing inheritance, and eD variable was missing - never come through here

    def __doRenderTabs(self, eD):
        """Render a tabbed table set.

        Bootstrap markup template  --

        <div class="tabbable"> <!-- Only required for left/right tabs -->
            <ul class="nav nav-tabs">
               <li class="active"><a href="#tab1" data-toggle="tab">Section 1</a></li>
               <li><a href="#tab2" data-toggle="tab">Section 2</a></li>
            </ul>

            <div class="tab-content">
               <div class="tab-pane active" id="tab1">
                   <p>I'm in Section 1.</p>
               </div>
                <div class="tab-pane" id="tab2">
                             <p>Howdy, I'm in Section 2.</p>
                </div>
             </div>
        </div>

        """

        idPrefix = "tab" + str(random.randint(0, 100000))
        catList = self.__reportCategories
        #
        if self.__debug:
            for ii, tup in enumerate(catList):
                logger.debug(
                    "ChemRefReportDepict (doRenderTabs) ii %d  tup %r", ii, tup
                )
            for ii, (x, y, z) in enumerate(catList):
                logger.debug(
                    "ChemRefReportDepict (doRenderTabs) ii %d  values  %s %s %s",
                    ii,
                    x,
                    y,
                    z,
                )
        #
        oL = []
        #
        # need for URL construction --
        cD = eD["dataDict"]
        idCode = eD["idCode"]
        #
        #
        # Write the tabs --
        #
        oL.append(
            '<div id="%s_report_section" class="tabbable results-section">' % idCode
        )
        # add close/dismiss --
        oL.append(
            '<button type="button" class="close" data-target="#%s_report_section" data-dismiss="alert" style="margin:7px; padding:1px;"> '
            % idCode
        )
        oL.append(
            '   <span aria-hidden="true"> <i class="fa fa-times"></i></span><span class="sr-only">Close</span></button>'
        )

        oL.append('<ul class="nav nav-tabs">')
        oL.append(
            '<li><a  class="active" data-target="#%s-tabs-id" data-toggle="tab">%s'
            % (idPrefix, idCode)
        )
        oL.append(
            '   <span aria-hidden="true"> <i class="fa fa-compress"></i></span><span class="sr-only">Close</span></a></li>'
        )
        iSection = 0
        for ii, (catName, catNameAbbrev, catStyle) in enumerate(catList):
            # For only popuated categories
            if catName in cD and (len(cD[catName]) > 0):
                oL.append(
                    '<li><a data-target="#%s-tabs-%d" data-toggle="tab">%s</a></li>'
                    % (idPrefix, ii, catNameAbbrev)
                )
                iSection = ii
        #
        if eD["imageRelativePath"] is not None:
            oL.append(
                '<li><a data-target="#%s-tabs-%d" data-toggle="tab">%s</a></li>'
                % (idPrefix, iSection + 1, "2D")
            )
        if eD["xyzRelativePath"] is not None:
            oL.append(
                '<li><a data-target="#%s-tabs-%d" data-toggle="tab" class="jsmol-section-%s">%s</a></li>'
                % (idPrefix, iSection + 2, idCode, "3D")
            )
        # at-a-glance for cc id
        if (
            eD["imageRelativePath"] is not None
            and eD["xyzRelativePath"] is not None
            and (len(idCode) >= 1 and len(idCode) <= 5)
        ):
            oL.append(
                '<li><a data-target="#%s-tabs-%d" data-toggle="tab" class="ataglance-section-%s">%s</a></li>'
                % (idPrefix, iSection + 3, idCode, "at-a-glance")
            )

        oL.append("</ul>")
        #
        # Write the tables --
        #
        oL.append('<div  class="tab-content"> ')
        #
        oL.append('<div class="tab-pane active"  id="%s-tabs-id"></div>' % (idPrefix))

        iSection = 0
        for ii, (catName, catNameAbbrev, catStyle) in enumerate(catList):
            # For only popuated categories
            if catName in cD and (len(cD[catName]) > 0):
                oL.append('<div class="tab-pane"  id="%s-tabs-%d">' % (idPrefix, ii))
                oL.append(
                    '<table class="table table-striped table-bordered table-condensed" id="%s-%s">'
                    % (idPrefix, catName)
                )
                if catStyle == "column-wise":
                    self.__renderTableColumnWise(catName, cD[catName][0], oL)
                else:
                    self.__renderTableRowWise(catName, cD[catName], oL)

                oL.append("</table>")
                oL.append("</div>")
                iSection = ii
        #  2D image
        if eD["imageRelativePath"] is not None:
            oL.append(
                '<div class="tab-pane"  id="%s-tabs-%d">' % (idPrefix, iSection + 1)
            )
            oL.append(
                '<img src="%s" alt="%s" height="%d" width="%d">'
                % (eD["imageRelativePath"], idCode, 700, 700)
            )
            oL.append("</div>")

        # 3D app
        if eD["xyzRelativePath"] is not None:
            hasExpt = eD["hasExpt"]
            hasIdeal = eD["hasIdeal"]
            oL.append(
                '<div style="overflow:visible;" class="tab-pane tab-flex jsmol-class-expt-%s jsmol-class-ideal-%s" data-payload="%s" id="%s-tabs-%d">'
                % (idCode, idCode, idCode, idPrefix, iSection + 2)
            )

            #             # h5 is ~15px + 20 vert margin
            if hasExpt:
                oL.append(
                    '  <div id="%s_jsmol_expt" style="display:inline-block; float:left; border: 2px solid lightgray; width:645px; height:645px; margin:2px; padding:1px;">'
                    % idCode
                )
                oL.append("  </div>")
            if hasIdeal:
                oL.append(
                    '  <div id="%s_jsmol_ideal" style="display:inline-block; float:left; border: 2px solid lightgray; width:645px; height:645px; margin:2px; padding:1px;">'
                    % idCode
                )
                oL.append("  </div>")

            oL.append("</div>")

        # At-a-glance for cc id
        if (
            eD["imageRelativePath"] is not None
            and eD["xyzRelativePath"] is not None
            and (len(idCode) >= 1 and len(idCode) <= 5)
        ):
            oL.append(
                '<div style="padding:10px;background-color:white;overflow:visible;" class="tab-pane tab-flex" id="%s-tabs-%d">'
                % (idPrefix, iSection + 3)
            )
            oL.append(
                '<table style="position:relative;display:inline-table;max-width:70ch;" id="%s-%s">'
                % (idPrefix, "chem_comp")
            )
            self.__renderTableAtAGlance("chem_comp", cD["chem_comp"][0], oL)
            oL.append("</table>")
            oL.append(
                '<img style="position:relative;display:inline-table;border:1px solid gray;" src="%s" alt="%s" height="%d" width="%d">'
                % (eD["imageRelativePath"], idCode, 500, 500)
            )
            oL.append(
                '<div id="%s_ataglance_ideal" style="position:relative;display:inline-table;border:1px solid lightgray;width:500px;height:500px;">'
                % idCode
            )
            oL.append("</div>")
            oL.append("</div>")
        #
        oL.append("</div>")
        oL.append("</div>")
        #
        return oL

    def __doRenderAccordion(self, eD):
        """
        Bootstrap accordion template  --

        <div class="accordion" id="accordion2">
            <div class="accordion-group">
               <div class="accordion-heading">
                 <a class="accordion-toggle" data-toggle="collapse" data-parent="#accordion2" href="#collapseOne">  Collapsible Group Item #1  </a>
               </div>
               <div id="collapseOne" class="accordion-body collapse in">
                   <div class="accordion-inner">
                         Anim pariatur cliche...
                   </div>
               </div>
             </div>

             <div class="accordion-group">
                 <div class="accordion-heading">
                     <a class="accordion-toggle" data-toggle="collapse" data-parent="#accordion2" href="#collapseTwo"> Collapsible Group Item #2 </a>
                 </div>
                  <div id="collapseTwo" class="accordion-body collapse">
                     <div class="accordion-inner">
                           Anim pariatur cliche...
                     </div>
                  </div>
             </div>
        </div>

        """
        #
        idPrefix = "acc" + str(random.randint(0, 100000))
        oL = []
        catList = self.__reportCategories
        cD = eD["dataDict"]
        #
        idTop = idPrefix + "-top"

        #
        # Write the tables --
        #
        oL.append('<div class="accordion" id="%s">' % idTop)

        #
        isFirst = True
        for ii, (catName, catNameAbbrev, catStyle) in enumerate(catList):
            # For only popuated categories
            if catName in cD and (len(cD[catName]) > 0):
                active = "in" if isFirst else ""
                idSection = idPrefix + "-sec-" + str(ii)
                oL.append('<div class="accordion-group">')
                oL.append('<div class="accordion-heading">')
                oL.append(
                    '<a class="accordion-toggle" data-toggle="collapse" data-parent="#%s" href="#%s">%s</a>'
                    % (idTop, idSection, catNameAbbrev)
                )
                oL.append("</div>")
                oL.append(
                    '<div id="%s" class="accordion-body collapse %s">'
                    % (idSection, active)
                )
                oL.append('<div  class="accordion-inner">')
                #
                oL.append(
                    '<table class="table table-striped table-bordered table-condensed">'
                )
                if catStyle == "column-wise":
                    self.__renderTableColumnWise(catName, cD[catName][0], oL)
                else:
                    self.__renderTableRowWise(catName, cD[catName], oL)
                oL.append("</table>")
                #
                oL.append("</div>")
                oL.append("</div>")
                #
                oL.append("</div> <!-- end of accordion group -->")
        oL.append("</div> <!-- end of accordion -->")
        #
        return oL

    def __doRenderPage(self, eD):
        """Render a full page report with home brewed multi-accordion presentation style"""
        oL = []
        oL.append(self._pragmaXhtml)  # pylint: disable=no-member
        oL.append("<html>")
        oL.append("<head>")
        oL.append(self._jQueryGenericInclude)  # pylint: disable=no-member

        # oL.append(self._jQueryTableInclude)
        oL.append("</head>")

        oL.append('<body class="oneColLiqHdr">')
        oL.append(self._menuCommonIncludeInline)  # pylint: disable=no-member

        tableList = [t[0] for t in self.__reportCategories]
        self.__jQueryReportScript1(tableList, eD, oL)

        oL.append("<h2>Peptide Reference Dictionary Report</h2>")
        oL.append("<br/>")

        #
        cD = eD["dataDict"]

        for catName in ["chem_comp"]:
            if catName in cD and (len(cD[catName]) > 0):
                oL.append('<div class="sectionbar1">')
                oL.append(
                    '  <a class="sectionbar1" href="" id="toggle_section_%s">Show</a> Category: %s'
                    % (catName, catName)
                )
                oL.append("</div>")

                oL.append(
                    '<div style="display: block;" id="d_%s" class="displaynone">'
                    % catName
                )
                oL.append('<table id="%s">' % catName)
                self.__renderTableColumnWise(catName, cD[catName][0], oL)
                oL.append("</table>")
                oL.append("</div>")
        #
        # <div class="sb0"><a class="sb0" href="" id="toggle_section_XXXX">Show</a></div> <div class="sb1">Category:  Entity Reference</div>
        #
        for catName in tableList:
            if catName in cD and (len(cD[catName]) > 0):
                oL.append('<div class="sb0">')
                oL.append(
                    '  <a class="sb0" href="" id="toggle_section_%s">Show</a>' % catName
                )
                oL.append("</div>")
                oL.append('<div class="sb1">Category: %s </div>' % catName)
                oL.append("<br />")

                oL.append(
                    '<div style="display: block;" id="d_%s" class="displaynone">'
                    % catName
                )
                oL.append('<table id="%s">' % catName)
                if catName in ["pdbx_reference_molecule"]:
                    self.__renderTableColumnWise(catName, cD[catName][0], oL)
                else:
                    self.__renderTableRowWise(catName, cD[catName], oL)
                oL.append("</table>")
                oL.append("</div>")

        oL.append(self._trailer)  # pylint: disable=no-member
        oL.append("</body>")
        oL.append("</html>")
        #
        return oL

    def __renderTableColumnWise(self, catName, rD, oL):
        """Render table with unit cardinality.  Columns for the single row are listed vertically
        to the left of column values.
        """

        #
        iCol = 0
        self.__markupRow(catName, rD)
        #
        for itemName, itemDefault in self.__st.getItemNameAndDefaultList(catName):
            if itemName in rD:
                itemValue = rD[itemName]
            else:
                itemValue = itemDefault

            oL.append("<tr>")
            oL.append("<td>%s</td>" % self.__attributePart(itemName))

            oL.append("<td>%s</td>" % (itemValue))
            oL.append("</tr>")
            iCol += 1

    def __renderTableRowWise(self, catName, rL, oL):
        """Render a multirow table."""
        # Column labels --
        oL.append("<tr>")
        for itemName in self.__st.getItemNameList(catName):
            oL.append("<th>%s</th>" % self.__attributePart(itemName))
        oL.append("</tr>")
        #
        # Column data ---
        #
        iRow = 0
        for row in rL:
            self.__markupRow(catName, row)
            self.__renderRow(catName, row, iRow, oL, insertDefault=False)
            iRow += 1
        #
        #

    def __renderTableAtAGlance(self, catName, rD, oL):
        """One-column rendering"""
        #
        # iCol = 0
        self.__markupRow(catName, rD)
        #
        lst = self.__st.getItemNameAndDefaultList(catName)
        d = {k: v for k, v in lst}
        # reorder keys for at-a-glance
        keys = [
            ("_chem_comp.id", "ID"),
            ("_chem_comp.pdbx_release_status", "Status"),
            ("_chem_comp.name", "Name"),
            ("_chem_comp.pdbx_synonyms", "Synonyms"),
            ("_chem_comp.formula", "Formula"),
            ("_chem_comp.formula_weight", "Formula weight"),
            ("_chem_comp.pdbx_formal_charge", "Formal charge"),
            ("_chem_comp.type", "Type"),
            ("_chem_comp.pdbx_type", "Pdbx_type"),
            ("_chem_comp.mon_nstd_parent_comp_id", "Parent"),
            ("_chem_comp.pdbx_subcomponent_list", "Subcomponents"),
            ("_chem_comp.pdbx_replaces", "Replace"),
            ("_chem_comp.pdbx_replaced_by", "Replace by"),
            (
                "_chem_comp.pdbx_model_coordinates_missing_flag",
                "Model coordinates missing",
            ),
            ("_chem_comp.pdbx_model_coordinates_db_code", "Model PDB code"),
            ("_chem_comp.pdbx_initial_date", "Initial date"),
            ("_chem_comp.pdbx_modified_date", "Modified date"),
            ("_chem_comp.pdbx_processing_site", "Site"),
        ]
        for k, v in keys:
            oL.append("<tr>")
            oL.append("<td>%s:&nbsp%s</td>" % (v, rD[k] if k in rD else d[k]))
            oL.append("</tr>")

    def __renderRow(
        self, catName, row, iRow, oL, insertDefault=False
    ):  # pylint: disable=unused-argument
        """Render a row in a multirow table."""
        oL.append("<tr>")
        #
        for itemName, itemDefault in self.__st.getItemNameAndDefaultList(catName):
            if insertDefault:
                itemValue = itemDefault
            elif itemName in row:
                itemValue = row[itemName]
            else:
                itemValue = itemDefault

            oL.append("<td>%s</td>" % (itemValue))
        oL.append("</tr>")
        #

    def __markupLinks(self, cName, cVal):
        """Add markup to selected column types -"""
        #
        rst = cVal
        try:
            if cName in ["family", "prd"]:
                rst = '<a class="app-ref-report"  href="#">%s</a>' % cVal
            elif cName in ["cc"]:
                rpt = '<a class="app-ref-report"  href="#">%s</a>' % cVal
                le = (
                    '<a target="_blank" href="http://ligand-expo.rcsb.org/pyapps/ldHandler.py?formid=cc-index-search&operation=ccid&target=%s">(LE)</a>'
                    % cVal
                )
                rst = "%s &nbsp; %s" % (rpt, le)
            elif cName in ["id"]:
                if cVal.startswith("PRD_") or cVal.startswith("FAM_"):
                    rst = '<a class="app-ref-report"  href="#">%s</a>' % cVal
                else:
                    rpt = '<a class="app-ref-report"  href="#">%s</a>' % cVal
                    le = (
                        '<a target="_blank" href="http://ligand-expo.rcsb.org/pyapps/ldHandler.py?formid=cc-index-search&operation=ccid&target=%s">(LE)</a>'
                        % cVal
                    )
                    rst = "%s &nbsp; %s" % (rpt, le)
        except Exception as e:
            logger.info(
                "ChemRefReportDepict (markuplinks) failing cName %r cVal %r %r",
                cName,
                cVal,
                str(e),
            )
            logger.exception("Failure in __markupLinks")
        return rst

    def __markupRow(self, catName, rD):
        """Markup a row (row dictionary) in the input category."""
        if catName == "pdbx_reference_molecule_list":
            itemName = "_pdbx_reference_molecule_list.prd_id"
            if itemName in rD:
                itemValue = rD[itemName]
                if len(itemValue) > 5 and itemValue.startswith("PRD_"):
                    rD[itemName] = self.__markupLinks("prd", itemValue)
        if catName == "pdbx_reference_molecule_synonyms":
            itemName = "_pdbx_reference_molecule_synonyms.prd_id"
            if itemName in rD:
                itemValue = rD[itemName]
                if len(itemValue) > 5 and itemValue.startswith("PRD_"):
                    rD[itemName] = self.__markupLinks("prd", itemValue)
            itemName = "_pdbx_reference_molecule_synonyms.chem_comp_id"
            if itemName in rD:
                itemValue = rD[itemName]
                if len(itemValue) >= 3:
                    rD[itemName] = self.__markupLinks("cc", itemValue)
        if catName == "pdbx_reference_molecule_features":
            itemName = "_pdbx_reference_molecule_features.prd_id"
            if itemName in rD:
                itemValue = rD[itemName]
                if len(itemValue) > 5 and itemValue.startswith("PRD_"):
                    rD[itemName] = self.__markupLinks("prd", itemValue)
            itemName = "_pdbx_reference_molecule_features.chem_comp_id"
            if itemName in rD:
                itemValue = rD[itemName]
                if len(itemValue) >= 3:
                    rD[itemName] = self.__markupLinks("cc", itemValue)
        if catName == "pdbx_reference_molecule_details":
            itemName1 = "_pdbx_reference_molecule_details.source"
            itemName2 = "_pdbx_reference_molecule_details.source_id"
            if itemName1 in rD:
                srcType = str(rD[itemName1]).upper()
                srcValue = rD[itemName2]
                if srcType == "DOI" and len(srcValue) > 2:
                    rD[
                        itemName2
                    ] = '<a target="_blank" href="http://dx.doi.org/%s">%s</a>' % (
                        srcValue,
                        srcValue,
                    )
                if srcType == "PUBMED" and len(srcValue) > 2:
                    rD[itemName2] = (
                        '<a target="_blank" href="http://www.ncbi.nlm.nih.gov/sites/entrez?cmd=search&db=pubmed&term=%s">%s</a>'
                        % (srcValue, srcValue)
                    )
                if srcType == "DRUGBANK" and len(srcValue) > 2:
                    rD[itemName2] = (
                        '<a target="_blank" href="http://www.drugbank.ca/cgi-bin/getCard.cgi?CARD=%s">%s</a>'
                        % (srcValue, srcValue)
                    )
                if srcType == "PUBCHEM" and len(srcValue) > 2:
                    rD[itemName2] = (
                        '<a target="_blank" href="http://pubchem.ncbi.nlm.nih.gov/summary/summary.cgi?cid=%s">%s</a>'
                        % (srcValue, srcValue)
                    )

                if srcType == "URL" and len(srcValue) > 2:
                    rD[itemName2] = '<a target="_blank" href="%s">%s</a>' % (
                        srcValue,
                        srcValue,
                    )

                if srcType == "PMCID" and len(srcValue) > 2:
                    rD[itemName2] = (
                        '<a target="_blank" href="http://www.ncbi.nlm.nih.gov/pmc/?term=%s">%s</a>'
                        % (srcValue, srcValue)
                    )

                if srcType == "PMC" and len(srcValue) > 2:
                    rD[itemName2] = (
                        '<a target="_blank" href="http://www.ncbi.nlm.nih.gov/pmc/?term=%s">%s</a>'
                        % (srcValue, srcValue)
                    )

                if srcType == "UNIPROT" and len(srcValue) > 2:
                    rD[itemName2] = (
                        '<a target="_blank" href="http://www.uniprot.org/uniprot/%s">%s</a>'
                        % (srcValue, srcValue)
                    )

        if catName == "citation":
            itemName = "_citation.pdbx_database_id_DOI"
            if itemName in rD and len(rD[itemName]) > 1:
                itemValue = rD[itemName]
                rD[
                    itemName
                ] = '<a target="_blank" href="http://dx.doi.org/%s">%s</a>' % (
                    itemValue,
                    itemValue,
                )
            itemName = "_citation.pdbx_database_id_PubMed"
            if itemName in rD and len(rD[itemName]) > 1:
                itemValue = rD[itemName]
                rD[itemName] = (
                    '<a target="_blank" href="http://www.ncbi.nlm.nih.gov/sites/entrez?cmd=search&db=pubmed&term=%s">%s</a>'
                    % (itemValue, itemValue)
                )

        if catName == "pdbx_reference_molecule":
            itemName = "_pdbx_reference_molecule.representative_PDB_id_code"
            if itemName in rD:
                itemValue = rD[itemName]
                if len(itemValue) > 3:
                    rD[itemName] = (
                        '<a target="_blank" href="http://www.rcsb.org/pdb/explore/explore.do?structureId=%s">%s</a>'
                        % (itemValue, itemValue)
                    )

            itemName = "_pdbx_reference_molecule.chem_comp_id"
            if itemName in rD:
                itemValue = rD[itemName]
                if len(itemValue) >= 3:
                    rD[itemName] = self.__markupLinks("cc", itemValue)
        if catName == "pdbx_reference_entity_nonpoly":
            itemName = "_pdbx_reference_entity_nonpoly.chem_comp_id"
            if itemName in rD:
                itemValue = rD[itemName]
                if len(itemValue) >= 3:
                    rD[itemName] = self.__markupLinks("cc", itemValue)
        if catName == "pdbx_reference_entity_poly_seq":
            itemName = "_pdbx_reference_entity_poly_seq.mon_id"
            if itemName in rD:
                itemValue = rD[itemName]
                if len(itemValue) >= 3:
                    rD[itemName] = self.__markupLinks("cc", itemValue)
            itemName = "_pdbx_reference_entity_poly_seq.parent_mon_id"
            if itemName in rD:
                itemValue = rD[itemName]
                if len(itemValue) >= 3:
                    rD[itemName] = self.__markupLinks("cc", itemValue)

    # ------

    def __jQueryReportScript1(self, tableList, eD, oL):
        # Context that will get encoded for call back --
        filePath = eD["filePath"]
        localPath = eD["localPath"]
        localRelativePath = eD["localRelativePath"]
        sessionId = eD["sessionId"]
        editOpNumber = eD["editOpNumber"]
        blockId = eD["blockId"]
        #
        #
        # Report controls
        #
        oL.append('<script type="text/javascript">')
        oL.append("     var editNumber        = %d;" % editOpNumber)
        oL.append('     var filePath          = "%s";' % filePath)
        oL.append('     var localPath         = "%s";' % localPath)
        oL.append('     var localRelativePath = "%s";' % localRelativePath)
        oL.append('     var blockId           = "%s";' % blockId)
        oL.append('     var sessionId         = "%s";' % sessionId)
        oL.append("     var ajaxTimeout       = 60000;")
        oL.append("$(document).ready(function(){")
        #
        oL.append("    $.ajaxSetup({")
        oL.append('        type: "POST",')
        oL.append('        dataType: "json",')
        oL.append("        async: true,")
        oL.append("        timeout: ajaxTimeout,")
        oL.append("        cache: false")
        oL.append("    });")
        #
        #
        # oL.append('	$("#%s").tablesorter();' % tableId)
        #
        #
        dS = ""
        for t in tableList[:-1]:
            dS += "#d_%s, " % t
        dS += "#d_%s" % tableList[-1]
        oL.append('$("%s").hide();' % dS)

        #
        tS = ""
        for t in tableList[:-1]:
            tS += "#toggle_section_%s, " % t
        tS += "#toggle_section_%s" % tableList[-1]

        oL.append('$("%s").click(function() {' % tS)
        oL.append('        myConsoleLog("TOGGLE VALUE "+$(this).text());')
        # oL.append('        $(this).parents("div").filter(":first").next().toggle(400);')
        oL.append(
            '        $(this).parents("div").filter(":first").next().next().next().toggle(400);'
        )
        oL.append('        $(this).text($(this).text() == "Show" ? "Hide" : "Show");')
        oL.append("        return false;")
        oL.append(" });")

        oL.append(' $(".sb0").corner("round");')
        oL.append(' $(".sb1").corner("round");')
        #
        # button controls --
        # self.__jQueryButtonScripts(eD,oL)
        #
        oL.append("});")

        oL.append("</script>")

    def __attributePart(self, name):
        i = name.find(".")
        if i == -1:
            return None
        else:
            return name[i + 1 :]
