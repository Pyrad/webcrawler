import shutil
import os
from datetime import datetime, timedelta
from enum import Enum
# import tempfile


class TableState(Enum):
    st_none = 0
    st_start = 1
    st_date = 2
    st_time = 3
    st_city_num = 4
    st_city_num_unkown = 5
    st_end = 6

class TableErrorCode(Enum):
    THIS_WEEK_TABLE_NOT_FOUND = 0
    THIS_WEEK_TABLE_DATE_COLUMN_NOT_FOUND = 1
    THIS_WEEK_TABLE_PARSE_SUCCESS = 2
    THIS_WEEK_TABLE_PARSE_FAIL = 3
    ADD_THIS_WEEK_TABLE_SUCCESS = 4
    ADD_THIS_WEEK_TABLE_FAIL = 5
    UPDATE_THIS_WEEK_TABLE_FAIL = 6
    UPDATE_THIS_WEEK_TABLE_SUCCESS = 7


class ResaleTableRefresh:
    """
    Update a specific table for the resale numbers in file
    """
    def __init__(self, fname=None, scraped_data=dict()):
        self.fname = fname
        self.curtime = datetime.now()
        self.city_names = ['北京','广州','苏州','杭州','南京','西安','成都','重庆','天津','合肥','福州','厦门','长沙','深圳','上海','武汉']
        self.en_city_names = ['Beijing','Guangzhou','Suzhou','Hangzhou','Nanjing','Xi_an','Chengdu','Chongqing','Tianjin','Hefei','Fuzhou','Xiamen','Changsha','Shenzhen','Shanghai','Wuhan']
        self.cdata = scraped_data.copy()
        self.table_data_date_time = []
        self.city_number = []
        self.city_number_unknown = []
        self.copy_until_linenum = -1
        self.encoding_style = 'UTF-8'

    def get_en_city_name(self, cn_name):
        if not cn_name in self.city_names:
            return ""
        index = self.city_names.index(cn_name)
        return self.en_city_names[index]

    def get_cn_city_name(self, en_name):
        if not en_name in self.en_city_names:
            return ""
        index = self.en_city_names.index(en_name)
        return self.city_names[index]

    def find_this_week_table(self):
        weeknum = int(self.curtime.strftime("%U"))
        yearnum = self.curtime.year
        table_name = "$\\text{{Year {} Week {}}}$".format(yearnum, weeknum)
        self.copy_until_linenum = -1
        with open(self.fname, 'r', encoding=self.encoding_style) as fp:
            for i, line in enumerate(fp):
                curline = line.strip()
                if curline == table_name:
                    self.copy_until_linenum = i
                    break
        return self.copy_until_linenum

    def add_table_for_this_week(self):
        if not isinstance(self.fname, str):
            return TableErrorCode.ADD_THIS_WEEK_TABLE_FAIL
        N_WEEKDAY = 7
        with open(self.fname, 'a+', encoding=self.encoding_style) as fp:
            # First add 2 empty lines to separate it from the previous table
            fp.write("\n\n")
            cur_week_num = self.curtime.strftime("%U")
            fp.write(f"### Week {cur_week_num}\n")
            fp.write(f"\n$\\text{{Year {self.curtime.year} Week {cur_week_num}}}$\n\n")
            fp.write("$$\n")
            fp.write("\\begin{array}{l|r|r|r|r|r|r|r}\n")
            fp.write("\\hline\n")
            # Date row
            tstart_this_week = self.curtime - timedelta(self.curtime.isoweekday() % N_WEEKDAY)
            dates_this_week = [(tstart_this_week + timedelta(days=i)).strftime("%m-%d") for i in range(7)]
            date_row = "\\mathrm {Date} & " + " & ".join(["\\mathrm{" + dstr + "}" for dstr in dates_this_week])
            fp.write(date_row + " \\\\ \n")
            # Time row
            time_row = "\\mathrm {城市} & " + " & ".join(["\\mathrm{-}"] * N_WEEKDAY)
            fp.write(time_row + " \\\\ \n")
            fp.write("\\hline\n")
            # City number rows
            row_last_part = " & " + " & ".join(["-"] * N_WEEKDAY) + " \\\\"
            for city in self.city_names[:-2]:
                crow = city + row_last_part
                fp.write(crow + "\n")
            fp.write("\\hline\n")
            # City number unkown rows
            for city in self.city_names[-2:]:
                crow = city + row_last_part
                fp.write(crow + "\n")
            fp.write("\\hline\n")
            fp.write("\\end{array}\n")
            fp.write("$$\n\n")

        return TableErrorCode.ADD_THIS_WEEK_TABLE_SUCCESS

    def parse_this_week_table(self):

        TEC = TableErrorCode

        n = self.find_this_week_table()
        if n < 0:
            return TEC.THIS_WEEK_TABLE_NOT_FOUND

        self.city_number.clear()
        self.city_number_unknown.clear()

        st = TableState.st_none
        hline_cnt = 0
        ncol = -1
        with open(self.fname, 'r', encoding=self.encoding_style) as fp:
            for i, line in enumerate(fp):
                if i <= n:
                    continue
                assert isinstance(line, str)
                curline = line.strip()
                hline_cnt += (1 if curline.startswith("\\hline") else 0)
                clist = curline.split()
                #print(f"Line {i}: {curline}")
                if st == TableState.st_none:
                    st = TableState.st_start
                elif st == TableState.st_start:
                    if not curline.startswith("\\begin"):
                        continue
                    st = TableState.st_date
                elif st == TableState.st_date:
                    if not curline.startswith("\\mathrm"):
                        continue
                    st = TableState.st_time
                    #print(f"TableState.st_date len(clist) = {len(clist)}")
                    colstr = self.curtime.strftime("\\mathrm{%m-%d}")
                    if colstr in clist:
                        ncol = clist.index(colstr)
                        #print(f"Found date column is {ncol}")
                        self.table_data_date_time.append(curline)
                    else:
                        return TEC.THIS_WEEK_TABLE_DATE_COLUMN_NOT_FOUND
                elif st == TableState.st_time:
                    if not curline.startswith("\\mathrm"):
                        continue
                    st = TableState.st_city_num
                    #print(f"TableState.st_time len(clist) = {len(clist)}")
                    if ncol >= 0:
                        curtimestr = self.curtime.strftime("\\mathrm{%H:%M}")
                        clist[ncol] = curtimestr
                        self.table_data_date_time.append(' '.join(clist))
                elif st == TableState.st_city_num:
                    if hline_cnt < 2:
                        continue
                    if hline_cnt == 2 and curline.startswith("\\hline"):
                        continue
                    if hline_cnt == 3:
                        st = TableState.st_city_num_unkown
                        continue
                    #print(f"TableState.st_city_num len(clist) = {len(clist)}, clist[0] = {clist[0]}, {clist[0] in self.city_names}")
                    if ncol >= 0:
                        curnum = self.cdata.get(self.get_en_city_name(clist[0]), 0)
                        clist[ncol] = format(curnum, ',')
                        self.city_number.append(' '.join(clist))
                elif st == TableState.st_city_num_unkown:
                    if curline.startswith("\\hline"):
                        st = TableState.st_end
                        continue
                    #print(f"TableState.st_city_num_unkown len(clist) = {len(clist)}, clist[0] = {clist[0]}, {clist[0] in self.city_names}")
                    if ncol >= 0:
                        curnum = self.cdata.get(self.get_en_city_name(clist[0]), 0)
                        clist[ncol] = format(curnum, ',') if curnum > 0 else "-"
                        self.city_number_unknown.append(' '.join(clist))
                else:
                    pass

        return TEC.THIS_WEEK_TABLE_PARSE_SUCCESS if len(self.city_number) != 0 else TEC.THIS_WEEK_TABLE_PARSE_FAIL

    def update_this_week_table(self):
        # Error code class (enum) short hand
        TEC = TableErrorCode

        # Before updating the table file, make sure the table for this week
        # has already been added
        errcode = self.parse_this_week_table()
        if errcode == TEC.THIS_WEEK_TABLE_NOT_FOUND or \
           errcode == TEC.THIS_WEEK_TABLE_DATE_COLUMN_NOT_FOUND:
            return TEC.UPDATE_THIS_WEEK_TABLE_FAIL

        #fp = tempfile.TemporaryFile(mode='w', encoding='utf-8', dir='.')
        tmpfname = "mytemp.md"
        fp = open(tmpfname, "w", encoding=self.encoding_style)

        # Copy tables before this week
        if self.copy_until_linenum >= 0:
            with open(self.fname, 'r', encoding=self.encoding_style) as fpr:
                for i, line in enumerate(fpr):
                    if i <= self.copy_until_linenum:
                        fp.write(line)

        fp.write("$$\n")
        fp.write("\\begin{array}{l|r|r|r|r|r|r|r}\n")
        fp.write("\\hline\n")
        for l in self.table_data_date_time:
            fp.write(l + '\n')
        fp.write("\\hline\n")
        for l in self.city_number:
            fp.write(l + '\n')
        fp.write("\\hline\n")
        for l in self.city_number_unknown:
            fp.write(l + '\n')
        fp.write("\\hline\n")
        fp.write("\\end{array}\n")
        fp.write("$$\n\n")
        fp.close()

        # print(f"fp.name = {fp.name}")
        # print(f"self.fname = {self.fname}")
        # print(f"os.path.abspath(self.fname) = {os.path.abspath(self.fname)}")
        #shutil.copy(self.fname, self.fname + ".bak.md")
        os.remove(self.fname)
        shutil.copy(tmpfname, self.fname)
        os.remove(tmpfname)

        return TEC.UPDATE_THIS_WEEK_TABLE_SUCCESS

    def refresh(self):
        errcode = self.parse_this_week_table()

        TEC = TableErrorCode

        if errcode == TEC.THIS_WEEK_TABLE_NOT_FOUND or \
           errcode == TEC.THIS_WEEK_TABLE_DATE_COLUMN_NOT_FOUND:
            errcode = self.add_table_for_this_week()
        if errcode == TEC.ADD_THIS_WEEK_TABLE_SUCCESS or \
           errcode == TEC.THIS_WEEK_TABLE_PARSE_SUCCESS:
            errcode = self.update_this_week_table()
        if errcode == TEC.UPDATE_THIS_WEEK_TABLE_SUCCESS:
            print(f"[PYRAD] INFO: Successfully updated the resale table for this week")
        else:
            print(f"[PYRAD] ERROR: Failed to update the resale table for this week")


if __name__ == "__main__":
    print(f"This is the __main__ block for module table_refresh.py")
    #fn = f"D:/Pyrad/Gitee/pyradnotes/source/RealEstate/resalenumbers2023.md"
    fn = f"D:/Gitee/pyradnotes/source/RealEstate/resalenumbers2023.md"
    rtr = ResaleTableRefresh(fn)
    #ecode = rtr.add_table_for_this_week()
    ecode = rtr.refresh()
    print(f"Error code is {ecode}")