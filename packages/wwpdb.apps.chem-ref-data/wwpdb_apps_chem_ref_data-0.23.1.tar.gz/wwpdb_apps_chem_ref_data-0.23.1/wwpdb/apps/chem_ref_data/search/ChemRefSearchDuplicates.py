#
# File:  ChemRefSearchDuplicates.py
# Date:  19-Jan-2019 E. Peisach
#
# Update:
#
##
"""
Search CCD database for duplicate ligangs

"""

import sys
import datetime
import pickle
from wwpdb.utils.db.MyConnectionBase import MyConnectionBase
from wwpdb.utils.db.MyDbUtil import MyDbQuery

import logging

logger = logging.getLogger(__name__)


class ChemRefSearchDuplicates(MyConnectionBase):
    def __init__(self, verbose=True, log=sys.stderr):
        super(ChemRefSearchDuplicates, self).__init__(verbose=verbose, log=log)
        self.__verbose = verbose
        self.__lfh = log
        self.__dups = []

    def find_duplicates(self):
        """Returns a dictionary of duplcate items"""

        logger.debug("Start locating duplicate CCDs")

        self.setResource(resourceName="CC")
        ok = self.openConnection()
        if not ok:
            logger.error("Could not open connection to server")
            return None
        myq = MyDbQuery(dbcon=self._dbCon, verbose=self.__verbose, log=self.__lfh)

        sqlq = """select e.num, e.c1, c1.pdbx_release_status as status, c1.pdbx_processing_site as site,
                    c1.pdbx_modified_date as moddate,
                    e.c2, c2.pdbx_release_status as status, c2.pdbx_processing_site as site,
                    c2.pdbx_modified_date as moddate
                    from  chem_comp c1, chem_comp c2,(select count(1) as num,max(c.id) as c1,min(c.id) as c2
                    from chem_comp c, pdbx_chem_comp_descriptor  d, pdbx_chem_comp_descriptor d1,
                        pdbx_chem_comp_descriptor d2
                    where d.PROGRAM='CACTVS' and d.TYPE='SMILES_CANONICAL'
                    and d1.PROGRAM='OpenEye OEToolkits' and d1.TYPE='SMILES_CANONICAL'
                    and d2.PROGRAM='InChI' and d2.TYPE='InChI'
                    and c.pdbx_release_status != 'OBS' and c.pdbx_replaced_by = ''
                    and d.component_id=c.component_id and d1.component_id=c.component_id  and
                    d2.component_id = d.component_id
                    group by d.descriptor, d1.descriptor, d2.descriptor having count(1)>1
                        and count(distinct(c.type))<=1) e
                    where e.c1 = c1.id and e.c2 = c2.id order by e.num,e.c1,e.c2
                """

        rows = myq.selectRows(queryString=sqlq)

        self.__dups = []
        for row in rows:
            d = {
                "num": row[0],
                "cid1": row[1],
                "cid1status": row[2],
                "cid1site": row[3],
                "cid1mod": row[4],
                "cid2": row[5],
                "cid2status": row[6],
                "cid2site": row[7],
                "cid2mod": row[8],
            }
            self.__dups.append(d)

        return self.__dups

    @staticmethod
    def _dformat(dtime):
        """Formats date time for output"""
        return dtime.strftime("%d-%b-%y")

    def _rformat(self, row):
        """Formats a row for the report"""
        return "{} {:<3} {:<4} {:<4} {}   {:<3} {:<4} {:<4} {}".format(
            row["num"],
            row["cid1"],
            row["cid1site"],
            row["cid1status"],
            self._dformat(row["cid1mod"]),
            row["cid2"],
            row["cid2site"],
            row["cid2status"],
            self._dformat(row["cid2mod"]),
        )

    @staticmethod
    def _isblacklist(row):
        """If a combination is blacklisted, return explanation else Fasle"""
        blacklist = {
            "UNK,ABA": "Unknown residue",
            "DN,3DR": "Unknown residue",
            "1CR,0CR": "Enantiomers",
            "V7F,V70": "Enantiomers",
            "C7S,C7R": "thiophospho connection isoforms",
            "RKP,0TN": "Metallo compound different arrangements",
            "OY8,OY5": "Diastereomer carboranes",
        }

        key = "%s,%s" % (row["cid1"], row["cid2"])
        if key in blacklist:
            return blacklist[key]

        key = "%s,%s" % (row["cid2"], row["cid1"])
        if key in blacklist:
            return blacklist[key]

        return False

    @staticmethod
    def _deltadays(dtime, recent):
        """Returns True is datetime is within recent days of today"""

        if abs((dtime - datetime.datetime.today()).days) <= recent:
            return True
        return False

    def makereport(self, recentdays=0):
        """Generates a report as a list of strings"""

        rep = []
        blacklist = []
        recent = []

        rep.append("Duplicate ligands (non-obsolete, non-superceded, and non-abmiguous with identical SMILES")
        rep.append("         (both CACTVS and OpenEye) as well as InChI")
        # Error details: 2 1CR RCSB REL 04-JUN-11 0CR RCSB REL 04-JUN-11

        for row in self.__dups:
            blacklisted = self._isblacklist(row)
            if blacklisted:
                blacklist.append("{}   -- {}".format(self._rformat(row), blacklisted))
            else:
                rep.append(self._rformat(row))
                # Do not add blacklisted to recent updates
                if self._deltadays(row["cid1mod"], recentdays) or self._deltadays(row["cid2mod"], recentdays):
                    recent.append(self._rformat(row))

        if recent and recentdays:
            recent = ["Duplicate Ligands created in the last {} days".format(recentdays)] + recent
            rep = recent + ["", ""] + rep

        if len(blacklist) > 0:
            rep.extend(["", "", "Blacklisted known duplicates"])
            rep.extend(blacklist)

        return rep

    def savestate(self, fname):
        """Stores the current state in a pickle file so can see if any changes made"""

        with open(fname, "wb") as fout:
            # Version 1
            pickle.dump([1, self.__dups], fout)

    def restorestate(self, fname):
        """Restores state from pickle file to allow comparisons"""
        try:
            with open(fname, "rb") as fin:
                din = pickle.load(fin)
                if din[0] != 1:
                    raise ImportError("File version number wrong")
                else:
                    self.__dups = din[1]
        except IOError as _e:  # noqa: F841
            # File missing or bad format
            return False

        return True


def main():
    import argparse
    import difflib

    ch = logging.StreamHandler()
    formatter = logging.Formatter("[%(levelname)s] [%(module)s.%(funcName)s] %(message)s")
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    logger.setLevel(logging.INFO)

    parser = argparse.ArgumentParser(description="Detect duplicate ligands based on compv4 database")
    parser.add_argument("--recent", type=int, default=7, help="Highlight duplicates within n days")
    parser.add_argument("--savestate", default=None, help="Filename to load and store state")
    parser.add_argument("--skipsame", default=False, action="store_true", help="Report nothing if same")

    parsed = parser.parse_args()
    # print(parsed)

    prevdatavalid = False
    if parsed.savestate:
        refcrsd = ChemRefSearchDuplicates()
        prevdatavalid = refcrsd.restorestate(parsed.savestate)

    crsd = ChemRefSearchDuplicates()
    crsd.find_duplicates()

    # Calculate reports

    rep = crsd.makereport(recentdays=parsed.recent)

    diffs = []
    if prevdatavalid:
        prevrep = refcrsd.makereport(recentdays=parsed.recent)
        # prevrep.append("High")
        for line in difflib.ndiff(prevrep, rep):
            if line[0] in ["+", "-"]:
                diffs.append(line)
        if len(diffs):
            diffs = ["Differences since last report"] + diffs + ["", ""]
        elif parsed.skipsame:
            sys.exit(0)

    # Create final report....
    finalrep = diffs + rep

    print("\n".join(finalrep))

    if parsed.savestate:
        crsd.savestate(parsed.savestate)


if __name__ == "__main__":
    main()
