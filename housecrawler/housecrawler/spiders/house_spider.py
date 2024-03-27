from pathlib import Path

import scrapy
from datetime import datetime
import platform
import os
import subprocess
import re
import pandas as pd
import openpyxl

from .table_refresh import ResaleTableRefresh

class CityInfoItem:
    """
    A class to hold information for each city.
    Currently one object of item contains 2 members, which are city name (English) and
    the URL to scrape data from Lianjia.com.
    """
    def __init__(self, city_name, url):
        self.city_name_str = city_name
        self.url_str = url

    @property
    def city_name(self):
        return self.city_name_str

    @property
    def url(self):
        return self.url_str

class CityInfoList:
    """
    A contain to hold all the information of all cities
    """
    def __init__(self):
        self.clist = []

    def add(self, city_name, url):
        cii = CityInfoItem(city_name, url)
        self.clist.append(cii)

    def __len__(self):
        return len(self.clist)

    def get_city_name_list(self):
        return [cii.city_name for cii in self.clist]

    def get_city_url_list(self):
        return [cii.url for cii in self.clist]

    def get_url_dict(self):
        return dict(zip(self.get_city_name_list(), self.get_city_url_list()))

    def provideSpreadSheetFileName(self):
        """
        Provide a xlsx file name to append data.
        The file name has the following format,
        cityDataYear{YearNumber}ReleaseNum{CityNum}.xlsx
        """
        # Get this year number string
        dtime = datetime.now()
        year_str = dtime.strftime("%Y")
        # Xlsx File name
        fname = f"cityDataYear{year_str}ResaleNum{len(self.clist)}.xlsx"
        return fname

    def provideMarkdownFileName(self):
        """
        Provide a markdown file name to append data.
        The file name has the following format,
        releaseNum{YearNumber}.md
        """
        # Get this year number string
        dtime = datetime.now()
        year_str = dtime.strftime("%Y")
        # Markdown file name
        fname = f"resalenumbers{year_str}.md"
        return fname



class SpreadsheetDataKeeper:

    @staticmethod
    def get_cpu_name():
        """
        Check current machine's CPU name
        :return: A string representing current machine's CPU name.
                 If not found, return an empty string
        """
        if platform.system() == "Windows":
            return platform.processor()
        elif platform.system() == "Darwin":
            os.environ['PATH'] = os.environ['PATH'] + os.pathsep + '/usr/sbin'
            command = "sysctl -n machdep.cpu.brand_string"
            return subprocess.check_output(command).strip()
        elif platform.system() == "Linux":
            command = "cat /proc/cpuinfo"
            all_info = subprocess.check_output(command, shell=True).decode().strip()
            for line in all_info.split("\n"):
                if "model name" in line:
                    return re.sub(".*model name.*:", "", line, 1)
        return ""

    @staticmethod
    def get_data_dir_on_this_computer_by_cpu_name():
        cur_is_win = platform.system() == "Windows"
        cpu_name = "n/a"
        if cur_is_win is True:
            # Assume current it is running on Windows
            # For win32com, refer to the link below
            # https://learn.microsoft.com/zh-cn/windows/win32/cimwin32prov/win32-processor
            from win32com.client import GetObject
            root_winmgmts = GetObject("winmgmts:root\cimv2")
            cpus = root_winmgmts.ExecQuery("Select * from Win32_Processor")
            cpu_name = cpus[0].Name
            cpu_name = cpu_name.strip()
        else:
            # Assume current it is running on Linux or other platforms
            cpu_name = SpreadsheetDataKeeper.get_cpu_name()

        # Different CPU names corresponds to different machines
        MyAsusPCCpuName = 'Intel(R) Core(TM) i5-4570 CPU @ 3.20GHz'
        MyLenovoCpuName = 'AMD Ryzen 5 3550H with Radeon Vega Mobile Gfx'
        MySnpsCpuName = '11th Gen Intel(R) Core(TM) i7-1185G7 @ 3.00GHz'

        # Relative directory for RealEstate Under Pyrad Notes directory
        rdir = "source/RealEstate"

        pyradnotes_dir = None
        if cpu_name == MyAsusPCCpuName:
            # If current PC is my ASUS computer
            pyradnotes_dir = f"D:/Gitee/pyradnotes/{rdir}"
        elif cpu_name == MyLenovoCpuName:
            pyradnotes_dir = f"D:/Pyrad/Gitee/pyradnotes/{rdir}"
        elif cpu_name == MySnpsCpuName:
            # If current PC is my work computer from SNSP, don't do anything
            pyradnotes_dir = ""
        else:
            print(f"Can't identify the CPU name ({cpu_name}) for this PC, please verify.")

        return pyradnotes_dir, cpu_name

    def __init__(self, city_list, fname):
        self.city_list = city_list
        spf_dir, _ = self.get_data_dir_on_this_computer_by_cpu_name()
        self.spfname = spf_dir + "/" + fname

    def xlsx_name(self):
        return self.spfname

    def create_city_resale_spreadsheet_with_header(self, spfname, sheet_name="CityResaleNum"):

        if not isinstance(spfname, str):
            return False

        # If file exists, assume this function should not be called
        if os.path.isfile(spfname) is True:
            return False

        dt_cols = ["Date", "Time", "Weekday", "Week"]
        city_cols = self.city_list

        # Header columns, first 4 are date, time, weekday, week, the rest are city names
        # Current there are 16 cities
        header_columns = dt_cols.copy()
        header_columns.extend(city_cols)

        df = pd.DataFrame(columns=header_columns)
        try:
            df.to_excel(spfname, sheet_name=sheet_name, index=False)
        except PermissionError as perr:
            print(f"PermissionError: errono = {perr.errno}")
            print(f"PermissionError: strerror = {perr.strerror}")
            print(f"PermissionError: filename = \'{perr.filename}\'")
        except Exception as e:
            print(e.what())

        return os.path.isfile(spfname)

    @staticmethod
    def get_date_time_value_list():
        #dtime = datetime.date.fromtimestamp(datetime.datetime.now())
        dtime = datetime.now()
        # Date string
        date_str = dtime.strftime("%Y-%m-%d")
        # Time string
        time_str = dtime.strftime("%H:%M:%S")
        # Week day for today
        day_str = dtime.strftime("%A")
        # Which week
        week_str = dtime.strftime("%U") # %w also works

        return [date_str, time_str, day_str, week_str]

    def append_data_row_to_spreadsheet(self, data_row, sheet_name="CityResaleNum"):

        spfname = self.spfname
        assert isinstance(data_row, list) or isinstance(data_row, tuple)

        if not isinstance(spfname, str):
            return False

        if os.path.isfile(spfname) is False:
            if self.create_city_resale_spreadsheet_with_header(spfname, sheet_name) is False:
                return False

        row_val = SpreadsheetDataKeeper.get_date_time_value_list()
        row_val.extend(data_row)
        #print(row_val)

        # Use openpyxl directly to append rows to an existing spreadsheet
        wb = openpyxl.load_workbook(spfname)
        ws = wb.worksheets[0]
        ws.append(row_val)
        wb.save(spfname)

        return True


class HouseSpider(scrapy.Spider):
    # Name must be unique inside this project
    name = "house_resale"
    # You can define a class attribute 'start_urls',
    # thus you don't have to define method 'start_requestes'
    # start_urls = [...]

    def __init__(self, category=None, *args, **kwargs):
        super(HouseSpider, self).__init__(*args, **kwargs)

        cil = CityInfoList()
        cil.add('Beijing',      'https://bj.ke.com/ershoufang/')
        cil.add('Guangzhou',    'https://gz.ke.com/ershoufang/')
        cil.add('Suzhou',       'https://su.ke.com/ershoufang/')
        cil.add('Hangzhou',     'https://hz.ke.com/ershoufang/')
        cil.add('Nanjing',      'https://nj.ke.com/ershoufang/')
        cil.add('Xi_an',        'https://xa.ke.com/ershoufang/')
        cil.add('Chengdu',      'https://cd.ke.com/ershoufang/')
        cil.add('Chongqing',    'https://cq.ke.com/ershoufang/')
        cil.add('Tianjin',      'https://tj.ke.com/ershoufang/')
        cil.add('Hefei',        'https://hf.ke.com/ershoufang/')
        cil.add('Fuzhou',       'https://fz.ke.com/ershoufang/')
        cil.add('Xiamen',       'https://xm.ke.com/ershoufang/')
        cil.add('Changsha',     'https://cs.ke.com/ershoufang/')
        cil.add('Shanghai',     'https://sh.ke.com/ershoufang/')
        cil.add('Shenzhen',     'https://sz.ke.com/ershoufang/')
        cil.add('Wuhan',        'https://wh.ke.com/ershoufang/')

        self.city_info_list = cil
        self.url_dict = cil.get_url_dict()
        self.all_scraped_data = dict()
        self.city_name_list = cil.get_city_name_list()
        self.city_url_list = cil.get_city_url_list()

        # The spreadsheet file name (.xlsx)
        fname = cil.provideSpreadSheetFileName()
        self.ssdk = SpreadsheetDataKeeper(self.city_name_list, fname)


    def get_url_city(self, url_str=None):
        if url_str is None:
            return "N/A"

        if not isinstance(url_str, str):
            return "N/A"

        for city, url in self.url_dict.items():
            if url == url_str:
                return city

        return "N/A"

    def get_markdown_fname(self):
        return self.city_info_list.provideMarkdownFileName()

    def get_xlsx_fname(self):
        return self.city_info_list.provideSpreadSheetFileName()

    def closed(self, reason):
        cnum = len(self.all_scraped_data)
        if cnum == 0:
            return
        print(f"[PYRAD] Total city number = {cnum}")
        for city_name, total_num in self.all_scraped_data.items():
            print(f"[PYARD] {city_name} = {total_num}")

        bj_n = self.all_scraped_data['Beijing']
        sh_n = "-"
        shzh_n = self.all_scraped_data['Shenzhen']
        gz_n = self.all_scraped_data['Guangzhou']
        sz_n = self.all_scraped_data['Suzhou']
        hz_n = self.all_scraped_data['Hangzhou']
        nj_n = self.all_scraped_data['Nanjing'] if 'Nanjing' in self.all_scraped_data.keys() else "-"
        xa_n = self.all_scraped_data['Xi_an']
        cd_n = self.all_scraped_data['Chengdu'] if 'Chengdu' in self.all_scraped_data.keys() else "-"
        cq_n = self.all_scraped_data['Chongqing']
        tj_n = self.all_scraped_data['Tianjin']
        hf_n = self.all_scraped_data['Hefei']
        fz_n = self.all_scraped_data['Fuzhou']
        xm_n = self.all_scraped_data['Xiamen']
        wh_n = "-"
        cs_n = self.all_scraped_data['Changsha']

        # Save the numbers to a xlsx file
        city_resale_nlist = \
            [self.all_scraped_data[city] if not self.all_scraped_data.get(city) is None else -1 \
             for city in self.city_name_list]

        if self.ssdk.append_data_row_to_spreadsheet(city_resale_nlist) is True:
            print(f"[PYRAD] Successfully saved data to spreadsheet {self.ssdk.xlsx_name()}")
        else:
            print(f"[PYRAD] Failed to save data to spreadsheet {self.ssdk.xlsx_name()}")

        # Update the markdown file for resale tables
        ddir, _ = self.ssdk.get_data_dir_on_this_computer_by_cpu_name()
        resale_md_filename = ddir + "/" + self.get_markdown_fname()
        rtr = ResaleTableRefresh(resale_md_filename, self.all_scraped_data)
        rtr.refresh()

        # Print current date & time
        dt = datetime.now()
        dt_string = dt.strftime("$%Y-%m-%d, %H:%M:%S$")
        dt_string1 = dt.strftime("$%Y-%m-%d$")
        # dt_string2 = dt.strftime("$\\text{%Y-}\\text{%m-}\\text{%d-}\\text{%H:}\\text{%M:}\\text{%S}$")
        print(f"{dt_string}")
        print(f"{dt_string1}")
        # print(f"{dt_string2}")

        bj_n_fmtstr = format(bj_n, ",") if isinstance(bj_n, int) else "-"
        gz_n_fmtstr = format(gz_n, ",") if isinstance(gz_n, int) else "-"
        sz_n_fmtstr = format(sz_n, ",") if isinstance(sz_n, int) else "-"
        hz_n_fmtstr = format(hz_n, ",") if isinstance(hz_n, int) else "-"
        nj_n_fmtstr = format(nj_n, ",") if isinstance(nj_n, int) else "-"
        xa_n_fmtstr = format(xa_n, ",") if isinstance(xa_n, int) else "-"
        cd_n_fmtstr = format(cd_n, ",") if isinstance(cd_n, int) else "-"
        cq_n_fmtstr = format(cq_n, ",") if isinstance(cq_n, int) else "-"
        tj_n_fmtstr = format(tj_n, ",") if isinstance(tj_n, int) else "-"
        hf_n_fmtstr = format(hf_n, ",") if isinstance(hf_n, int) else "-"
        fz_n_fmtstr = format(fz_n, ",") if isinstance(fz_n, int) else "-"
        xm_n_fmtstr = format(xm_n, ",") if isinstance(xm_n, int) else "-"
        cs_n_fmtstr = format(cs_n, ",") if isinstance(cs_n, int) else "-"
        sh_n_fmtstr = format(sh_n, ",") if isinstance(sh_n, int) else "-"
        shzh_n_fmtstr = format(shzh_n, ",")  if isinstance(shzh_n, int) else "-"
        wh_n_fmtstr = format(wh_n, ",")  if isinstance(wh_n, int) else "-"

        longstr2 = (f"北京 {bj_n_fmtstr}\n"
                    f"广州 {gz_n_fmtstr}\n"
                    f"苏州 {sz_n_fmtstr}\n"
                    f"杭州 {hz_n_fmtstr}\n"
                    f"南京 {nj_n_fmtstr}\n"
                    f"西安 {xa_n_fmtstr}\n"
                    f"成都 {cd_n_fmtstr}\n"
                    f"重庆 {cq_n_fmtstr}\n"
                    f"天津 {tj_n_fmtstr}\n"
                    f"合肥 {hf_n_fmtstr}\n"
                    f"福州  {fz_n_fmtstr}\n"
                    f"厦门  {xm_n_fmtstr}\n"
                    f"长沙  {cs_n_fmtstr}\n"
                    f"深圳  {shzh_n_fmtstr}\n"
                    f"上海  {sh_n_fmtstr}\n"
                    f"武汉  {wh_n_fmtstr}\n")
        print(longstr2)

        # For git commit message
        dt_string = dt.strftime("%Y-%m-%d %H:%M")
        print("==== Git commit message ====")
        print(f"g commit -am \"Realestate Update resale numbers {dt_string}\"")
        print("============================")


    def start_requests(self):
        # Set urls list for scraping
        urls = [cur_url for _, cur_url in self.url_dict.items()]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):

        """
        Output of the following debug message

        print(f"[PYRAD] type(response.url) = {type(response.url)}")
        print(f"[PYRAD] response.url = {response.url}")
        print(f"[PYARD] Title = {response.css('title')}")
        print(f"[PYARD] Title = {response.css('title').getall()}")
        print(f"[PYARD] Title = {response.css('title::text').getall()}")

        [PYRAD] type(response.url) = <class 'str'>
        [PYRAD] response.url = https://bj.ke.com/ershoufang/
        [PYARD] Title = [<Selector xpath='descendant-or-self::title' data='<title>北京二手房_北京二手房出售买卖信息网【北京贝壳找房】</ti...'>]
        [PYARD] Title = ['<title>北京二手房_北京二手房出售买卖信息网【北京贝壳找房】</title>']
        [PYARD] Title = ['北京二手房_北京二手房出售买卖信息网【北京贝壳找房】']
        """

        # Currently it seems the xpath for the total house numbers of each city is the same,
        # so use it as a single variable
        total_num_xpath = '//*[@id="beike"]/div[1]/div[4]/div[1]/div[2]/div[1]/h2/span' + '/text()'
        city_xpath = '//*[@id="beike"]/div[1]/div[4]/div[1]/div[2]/div[1]/h2/a' + '/text()'

        # print(f"[PYRAD] Current scaping URL: {response.url}")
        # print(f"[PYARD] City = {response.xpath(city_xpath).getall()}")
        # print(f"[PYARD] Total house number = {response.xpath(total_num_xpath).getall()}")

        data_got = response.xpath(city_xpath).getall()
        if len(data_got) > 0:
            city_name = response.xpath(city_xpath).getall()[0]
            total_num = int(response.xpath(total_num_xpath).getall()[0])
            print(f"[PYARD] {city_name} = {total_num}")

            city_name = self.get_url_city(response.url)
            self.all_scraped_data[city_name] = total_num
        else:
            print(f"[PYARD] City name not found for URL: {response.url}")

        # filename = f'test.html'
        # Path(filename).write_bytes(response.body)
        # self.log(f'Saved file {filename}')
