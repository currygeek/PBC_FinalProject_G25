# Final Project: crawling stock and doing CAPM, some financial statement analysis
import requests
from bs4 import BeautifulSoup
import json
import pandas as pd
import numpy as np
import time, datetime
import os
from io import StringIO
import matplotlib.pyplot as plotter
import matplotlib.dates as mdates


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
    new_year, new_month = 0, 0
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

# Price_data: dataframe for price, Price_list: list for price
class company_stock():
    def __init__(self, index, name, prop):  # wait for stock price input
        self.index = index
        self.name = name
        self.proportion = prop
        self.stock_path = os.getcwd() + "\\" + str(self.index) + "_" + self.name
        if not os.path.isdir(self.stock_path):
            os.mkdir(self.stock_path)
    
    def crawl_a_month_price(self, str_date):
        price_url = "https://www.twse.com.tw/exchangeReport/STOCK_DAY?response=json&date="+str_date+"&stockNo="+str(self.index)
        price_web = requests.get(price_url)
        print("check")
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
        for i in range(2):  # depend on how many month we want to crawl
            self.crawl_a_month_price(date)
            date = get_last_month_date(date)
        self.price_data = pd.DataFrame(self.price_dict).sort_values(["Date"], ascending=False).reset_index(drop = True)
        self.price_list = [round((o+h+l+c)/4, 4) for o, h, l, c in zip(self.price_data["Opening"], self.price_data["Highest"], self.price_data["Lowest"], self.price_data["Closing"])]
        self.price_mean = round(np.mean(self.price_list), 4)
        self.price_std = round(np.std(self.price_list, ddof=1), 4)  # Sample standard deviation
    
    def crawl_fs(self):
        fs_url = "https://mops.twse.com.tw/server-java/t164sb01?step=1"+"&"+"CO_ID="+str(self.index)+"&SYEAR="+str(year-1)+"&SSEASON=4&REPORT_ID=C"
        fs_web = requests.get(fs_url)
        fs_web.encoding = "big5"
        print("check")  # sucessfully enter the website
        fs_datas = pd.read_html(StringIO(fs_web.text))
        time.sleep(1)
        self.bs_sheet = fs_datas[0]
        self.bs_sheet.columns = ["Code", "Title", str(year-1), str(year-2)]
        self.statement_of_CI = fs_datas[1]
        self.statement_of_CI.columns = ["Code", "Title", str(year-1), str(year-2)]
        self.statement_of_CF = fs_datas[2]
        self.statement_of_CF.columns = ["Code", "Title", "In"+str(year-1), "In"+str(year-2)]
        # Some basic measurements
        # Basic EPS
        EPS_row = self.statement_of_CI.loc[self.statement_of_CI["Title"] == "基本每股盈餘合計　Total basic earnings per share",:]
        self.EPS = float(EPS_row.iloc[0][str(year-1)])
        self.last_EPS = float(EPS_row.iloc[0][str(year-2)])
        # Dividends
        div_row = self.statement_of_CF.loc[self.statement_of_CF["Title"] == "發放現金股利　Cash dividends paid",:]
        self.div = str(div_row.iloc[0]["In"+str(year-1)])
        self.div = int(self.div[1:][:-1].replace(",", ""))
        self.last_div = str(div_row.iloc[0]["In"+str(year-2)])
        self.last_div = int(self.last_div[1:][:-1].replace(",", ""))
        self.div_growth_rate = round(self.div/self.last_div, 4) - 1
        # Capability of adding more financial statement here

    def compute_return_rate(self):  # Return rate on daily basis (or the annual return rate cannot be computed with our data)
        NI_row = self.statement_of_CI.loc[self.statement_of_CI["Title"] == "本期淨利（淨損）Profit (loss)",:]
        EPS_row = self.statement_of_CI.loc[self.statement_of_CI["Title"] == "基本每股盈餘合計　Total basic earnings per share",:]
        this_share = int(float(NI_row.iloc[0][str(year-1)].replace(",", ""))*1000 / float(EPS_row.iloc[0][str(year-1)]))   # Outstanding share
        last_share = int(float(NI_row.iloc[0][str(year-2)].replace(",", ""))*1000 / float(EPS_row.iloc[0][str(year-2)]))
        self.return_rate_list = []
        for i in range(len(self.price_list)-1):
            rate = 0
            if str(self.price_dict["Date"][i])[:4] == str(year) or str(self.price_dict["Date"][i])[:4] == str(year-1):
                rate = round((((self.price_list[i+1]-self.price_list[i]+(self.div/this_share/365)) / self.price_list[i+1])), 10)
            else:
                rate = round((((self.price_list[i]-self.price_list[i+1]+(self.last_div/last_share/365)) / self.price_list[i])), 10)
            self.return_rate_list.append(rate)
        self.risk_premium_list = [r-risk_free_rate for r in self.return_rate_list]
        self.risk_premium_mean = round(np.mean(self.risk_premium_list), 10)
        self.risk_premium_var = round(np.var(self.risk_premium_list, ddof=1), 10)

    def compute_cov_with_market(self, market_return_list):
        self.cov_m = np.cov(self.risk_premium_list, market_return_list)[0][1]
        self.beta_m = round(self.cov_m/(self.risk_premium_var), 4)
        print(self.cov_m, self.beta_m)
    
    def write_price_to_csv(self):
        target_csv = open(self.stock_path + "\\" + "prices" + ".csv","w",newline="", encoding="UTF-8")
        self.price_data.to_csv(target_csv)
        target_csv.close()

    def write_fs_to_csv(self, fs, file_name):
        target_csv = open(self.stock_path + "\\" + file_name + ".csv", "w", newline="", encoding="UTF-8")
        fs.to_csv(target_csv)
        target_csv.close()

    def plot_price(self):
        self.price_dict["Highest"] = [p for _,p in sorted(zip(self.price_dict["Date"], self.price_dict["Highest"]))]
        self.price_dict["Lowest"] = [p for _,p in sorted(zip(self.price_dict["Date"], self.price_dict["Lowest"]))]
        self.price_dict["Date"].sort()
        datetime_list = [datetime.date(int(str(d)[:4]), int(str(d)[4:6]), int(str(d)[6:])) for d in self.price_dict["Date"]]
        plotter.figure()
        plotter.plot(datetime_list, self.price_dict["Highest"], label="Highest", color="red")
        plotter.plot(datetime_list, self.price_dict["Lowest"], label="Lowest", color="lightgreen")
        plotter.title("Stock Index "+str(self.index))
        plotter.legend(loc="upper left")
        plotter.xlabel("Time")
        plotter.xticks(rotation = 80)
        plotter.ylabel("Price")
        plotter.show()
        plotter.close()
        

class market_portfolio():
    def __init__(self, num,  market_list):
        self.stock_amount = num
        self.market_list = market_list
    
    def compute_market_port(self):
        price_dict = {"Date":[], "Price":[], "Daily_Return":[]}
        self.price_list = []
        self.return_rate_list = []
        date_amount = len(self.market_list[0].price_list)  # How many day did we crawl
        total_proportion = 0
        for stock in self.market_list:
            total_proportion += stock.proportion
        for i in range(date_amount):
            price = 0
            return_rate = 0
            price_dict["Date"].append(int(self.market_list[0].price_data.iloc[i]["Date"]))
            for stock in self.market_list:
                price += ((stock.proportion/total_proportion) * stock.price_list[i])  # weighted average
                price = round(price, 4)
                if not i == date_amount - 1:
                    return_rate += ((stock.proportion/total_proportion) * stock.return_rate_list[i])
                    return_rate = round(return_rate, 10)
            self.return_rate_list.append(return_rate)
            self.price_list.append(price)
        price_dict["Price"] = self.price_list
        price_dict["Daily_Return"] = self.return_rate_list
        self.market_price_data = pd.DataFrame(price_dict)
        self.return_rate_list = self.return_rate_list[:-1]
        self.risk_premium_list = [r-risk_free_rate for r in self.return_rate_list]
        self.risk_premium_mean = np.mean(self.risk_premium_list)
        self.risk_premium_var = np.var(self.risk_premium_list, ddof=1)

        for stock in self.market_list:
            stock.compute_cov_with_market(self.risk_premium_list)
        # print(self.market_price_data)
    
    def write_market_port_to_csv(self):
        now_path = os.getcwd()
        target_csv = open(now_path + "\\" + "Market_Portfolio.csv", "w", newline="", encoding="UTF-8")
        self.market_price_data.to_csv(target_csv)
        target_csv.close()
    
    def plot_SML(self):
        beta_list = [stock.beta_m for stock in self.market_list]
        return_list = [stock.risk_premium_mean + risk_free_rate for stock in self.market_list]
        x = range(int(beta_list[0]), int(beta_list[len(beta_list)-1])+2)
        y = [self.risk_premium_mean*b + risk_free_rate for b in x]
        plotter.figure()
        plotter.plot(beta_list, return_list, "k.", color="olive")
        plotter.plot(x, y, color="orange")
        plotter.title("Security Market Line")
        plotter.xlabel("Beta")
        plotter.ylabel("Expected Return")
        plotter.show()
        plotter.close()
        # print(beta_list)
        # print(return_list)
        # print(self.risk_premium_mean)
        # print(self.market_list[0].risk_premium_mean)
        # print(self.market_list[1].risk_premium_mean)


# Main
year = datetime.datetime.now().year
month = datetime.datetime.now().month
day = datetime.datetime.now().day
year = 2020  # The market hasn't open in June!!  
month = 5
day = 29
now_str_date = str(year) + get_str_month(month) + get_str_day(day)
risk_free_rate = 0.00217  # one year CD rate for Bank of Taiwan

# Crawling market value table
mv_table = market_value_table()
mv_table.crawl_market_value_table()
mv_table.write_mb_table_to_csv()

comany_amount = 2  # How many company do we want to crawl
# Crawling top companies
market_port_com_list = []  # Company in the market portifolio
for i in range(1, comany_amount+1):
    print()
    row = mv_table.mv_table.loc[mv_table.mv_table["Rank"] == i, :]
    this_company = company_stock(int(row.iloc[0]["Stock_id"]), row.iloc[0]["Company_name"], float(row.iloc[0]["Proportion"]))
    market_port_com_list.append(this_company)
    this_company.crawl_stock_prices()
    this_company.write_price_to_csv()
    this_company.crawl_fs()
    this_company.compute_return_rate()
    this_company.plot_price()
    this_company.write_fs_to_csv(this_company.bs_sheet, "bs_sheet")
    this_company.write_fs_to_csv(this_company.statement_of_CI, "Statement_of_Comprehensive_Income")
    this_company.write_fs_to_csv(this_company.statement_of_CF, "Statement_of_Cash_Flows")

# Forming market portfolio
market_port = market_portfolio(comany_amount, market_port_com_list)
market_port.compute_market_port()
market_port.write_market_port_to_csv()
market_port.plot_SML()


