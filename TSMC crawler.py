# Test for Github and crawling stock
import requests
from bs4 import BeautifulSoup
import csv, json
import pandas as pd
import time, datetime
import os
from io import StringIO


def get_str_month(month):
    if not month in [10, 11, 12]:
        return "0" + str(month)
    else:
        return str(month)


def get_str_day(day):
    if day in range(1, 10):
        return "0" + str(day)
    else:
        return str(day)


def get_last_month_date(str_date):
    year = int(str_date[:4])
    month = int(str_date[4:6])
    if month == 1:
        new_year = year-1
        new_month = 12
    else:
        new_year = year
        new_month = month - 1
    new_year = str(new_year)
    new_month = get_str_month(new_month)
    return new_year + new_month + "01"


class market_value_table():
    def __init__(self):
        pass

    def crawl_market_value_table(self):
        url = "https://www.taifex.com.tw/cht/9/futuresQADetail"
        mv_web = requests.get(url)
        print("check")
        soup = BeautifulSoup(mv_web.text, "html.parser")
        bs_table = soup.find_all('table')[0]
        l_bs_table = bs_table.text.replace(" ", "").replace("\r", "").split("\n")[10:]
        
        d_table = {"Rank":[], "Stock_id":[], "Company_name":[], "Proportion":[]}
        for i in range(len(l_bs_table)):
            if not i % 5 == 0:
                pass
            else:
                d_table["Rank"].append(int(l_bs_table[i]))
                d_table["Stock_id"].append(int(l_bs_table[i+1]))
                d_table["Company_name"].append(l_bs_table[i+2])
                d_table["Proportion"].append(float(l_bs_table[i+3].replace("%", "")) / 100)
        self.mv_table = pd.DataFrame(d_table).sort_values(["Rank"]).reset_index(drop = True)
        print(self.mv_table)
        time.sleep(1)
    
    def write_mb_table_to_csv(self):
        now_path = os.getcwd()
        target_csv = open(now_path + "\\" +"Market_Value_Table.csv", "w", newline="", encoding="UTF-8")
        self.mv_table.to_csv(target_csv)
        target_csv.close()


class company_stock():
    def __init__(self, year, index, name):  # wait for stock price input
        self.index = index
        self.name = name
        self.fs_url = "https://mops.twse.com.tw/server-java/t164sb01?step=1"+"&"+"CO_ID="+str(index)+"&SYEAR="+str(year-1)+"&SSEASON=4&REPORT_ID=C"
    
    def crawl_a_month_price(self, str_date):
        price_url = "https://www.twse.com.tw/exchangeReport/STOCK_DAY?response=json&date="+str_date+"&stockNo="+str(self.index)
        print("check")
        price_web = requests.get(price_url)
        js_price = json.loads(price_web.text)
        for row in js_price["data"]:
            l_date = row[0].split("/")
            this_year = int(l_date[0]) + 1911  # 109 to 2020
            this_year = str(this_year)
            self.price_dict["Date"].append(int(this_year + l_date[1] + l_date[2]))
            self.price_dict["Volume"].append(int(row[1].replace(",", "")))
            self.price_dict["Trade_value"].append(int(row[2].replace(",", "")))
            self.price_dict["Opening"].append(float(row[3]))
            self.price_dict["Highest"].append(float(row[4]))
            self.price_dict["Lowest"].append(float(row[5]))
            self.price_dict["Closing"].append(float(row[6]))
            if row[7] == "X0.00":
                self.price_dict["Change"].append(0.00)
            else:
                self.price_dict["Change"].append(float(row[7]))
            self.price_dict["Transaction"].append(int(row[8].replace(",", "")))
        time.sleep(1)

    def crawl_stock_prices(self):
        self.price_dict = {"Date":[], "Volume":[], "Trade_value":[], "Opening":[], "Highest":[], "Lowest":[], "Closing":[], "Change":[], "Transaction":[]}
        date = now_str_date
        for i in range(12):  # depend on how many month we want to crawl
            self.crawl_a_month_price(date)
            date = get_last_month_date(date)
        self.price_data = pd.DataFrame(self.price_dict).sort_values(["Date"]).reset_index(drop = True)
        print(self.price_data)
    
    def crawl_fs(self):
        fs_web = requests.get(self.fs_url)
        fs_web.encoding = "big5"
        print("check")  # sucessfully enter the website
        fs_datas = pd.read_html(StringIO(fs_web.text))
        time.sleep(1)
        self.bs_sheet = fs_datas[0]
        self.bs_sheet.columns = ["Code", "Title", str(year-1), str(year-2)]
        print(self.bs_sheet)
        # Capability of adding more financial statement here
    
    def write_price_to_csv(self):
        now_path = os.getcwd()
        target_csv = open(now_path + "\\" + self.name +"_prices" + ".csv","w",newline="", encoding="UTF-8")
        self.price_data.to_csv(target_csv)
        target_csv.close()

    def write_fs_to_csv(self, fs, file_name):
        now_path = os.getcwd()
        target_csv = open(now_path + "\\" + file_name + ".csv","w",newline="", encoding="UTF-8")
        fs.to_csv(target_csv)
        target_csv.close()


year = datetime.datetime.now().year
month = datetime.datetime.now().month
day = datetime.datetime.now().day
now_str_date = str(year) + get_str_month(month) + get_str_day(day)

mv_table = market_value_table()
mv_table.crawl_market_value_table()
mv_table.write_mb_table_to_csv()

stock_id = 2330
tsmc = company_stock(year, stock_id, "TSMC")
tsmc.crawl_stock_prices()
tsmc.write_price_to_csv()

tsmc.crawl_fs()
tsmc.write_fs_to_csv(tsmc.bs_sheet, tsmc.name+"_bs_sheet")






'''
old version
bs_url = "https://mops.twse.com.tw/server-java/t164sb01?step=1"+"&"+"CO_ID="+str(stock_id)+"&SYEAR="+str(year-1)+"&SSEASON=4&REPORT_ID=C"
bs_web = requests.get(bs_url)
bs_web.encoding = "big5"

print("check")
fs_datas = pd.read_html(StringIO(bs_web.text))
bs_sheet = fs_datas[0]

bs_sheet.columns = ["Code", "Title", str(year-1), str(year-2)]
print(bs_sheet)
time.sleep(3)  # Stop for 3 sec

now_path = os.getcwd()
bs_file = open(now_path+"\\TSMC_balance_sheet.csv","w",newline="")
bs_sheet.to_csv(bs_file)


bs_file.close()
'''