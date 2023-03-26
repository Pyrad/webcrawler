from pathlib import Path

import scrapy


class HouseSpider(scrapy.Spider):
    # Name must be unique inside this project
    name = "house_resale"
    # You can define a class attribute 'start_urls',
    # thus you don't have to define method 'start_requestes'
    # start_urls = [...]

    def __init__(self, category=None, *args, **kwargs):
        super(HouseSpider, self).__init__(*args, **kwargs)
        self.url_dict = {
            'Beijing'   : 'https://bj.ke.com/ershoufang/',
            'Guangzhou' : 'https://gz.ke.com/ershoufang/',
            'Suzhou'    : 'https://su.ke.com/ershoufang/',
            'Hangzhou'  : 'https://hz.ke.com/ershoufang/',
            'Nanjing'   : 'https://nj.ke.com/ershoufang/',
            'Xi_an'     : 'https://xa.ke.com/ershoufang/',
            'Chengdu'   : 'https://cd.ke.com/ershoufang/',
            'Chongqing' : 'https://cq.ke.com/ershoufang/',
            'Tianjin'   : 'https://tj.ke.com/ershoufang/',
        }
        # self.url_wait_list = [
        #     'https://bj.ke.com/ershoufang/',
        #     'https://gz.ke.com/ershoufang/',
        #     'https://su.ke.com/ershoufang/',
        #     'https://hz.ke.com/ershoufang/',
        #     'https://nj.ke.com/ershoufang/',
        #     'https://xa.ke.com/ershoufang/',
        #     'https://cd.ke.com/ershoufang/',
        #     'https://cq.ke.com/ershoufang/',
        #     'https://tj.ke.com/ershoufang/',
        # ]
        self.all_scraped_data = dict()

    def get_url_city(self, url_str=None):
        if url_str is None:
            return "N/A"

        if not isinstance(url_str, str):
            return "N/A"

        for city, url in self.url_dict.items():
            if url == url_str:
                return city

        return "N/A"

    def closed(self, reason):
        cnum = len(self.all_scraped_data)
        if cnum == 0:
            return
        print(f"[PYRAD] Total city number = {cnum}")
        for city_name, total_num in self.all_scraped_data.items():
            print(f"[PYARD] {city_name} = {total_num}")

    def start_requests(self):
        # urls = [
        #     'https://bj.ke.com/ershoufang/',
        #     'https://gz.ke.com/ershoufang/',
        #     'https://su.ke.com/ershoufang/',
        #     'https://hz.ke.com/ershoufang/',
        #     'https://nj.ke.com/ershoufang/',
        #     'https://xa.ke.com/ershoufang/',
        #     'https://cd.ke.com/ershoufang/',
        #     'https://cq.ke.com/ershoufang/',
        #     'https://tj.ke.com/ershoufang/',
        # ]
        # urls = self.url_wait_list
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

        city_name = response.xpath(city_xpath).getall()[0]
        total_num = response.xpath(total_num_xpath).getall()[0]
        print(f"[PYARD] {city_name} = {total_num}")

        city_name = self.get_url_city(response.url)
        self.all_scraped_data[city_name] = total_num

        # filename = f'test.html'
        # Path(filename).write_bytes(response.body)
        # self.log(f'Saved file {filename}')
