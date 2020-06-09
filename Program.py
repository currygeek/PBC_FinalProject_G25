# Final Project: crawling stock and doing CAPM, some financial statement analysis
import requests
import yfinance as yf
import random
from bs4 import BeautifulSoup
import json
import pandas as pd
import numpy as np
import time, datetime
import os
from io import StringIO
import matplotlib.pyplot as plotter
from sklearn.linear_model import LinearRegression
import tkinter as tk
import tkinter.font as tkFont
import statistics as st

# Processing date
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


def acct_num_str_to_float(str_num):
    if "(" in str_num:
        float_num = -(float(str_num[1:-1]))
    else:
        float_num = float(str_num)
    return float_num

# The market value proportion of all companies

def annualize_daily_rate_of_return(daily_RoR_list):
    annual_RoR_list = [(1+i)**365 - 1 for i in daily_RoR_list]
    return annual_RoR_list


class market_value_table():
    '''
    Member variables:
        mv_table: The market value table in dataframe type, including rank, id, name and proportion
    '''
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
        time.sleep(random.randint(3, 8))
        mv_web.close()
    
    def write_mb_table_to_csv(self):
        now_path = os.getcwd()
        target_csv = open(now_path + "\\" +"Market_Value_Table.csv", "w", newline="", encoding="UTF-8")
        self.mv_table.to_csv(target_csv)
        target_csv.close()

# Price_data: dataframe for price, Price_list: list for price
class company_stock():
    '''
    Member variables:
        int index
        str name
        float prop: the prportion of the value in the market
        str stock_path: where to write the data
        dict price_dict: prepare for dataframe
        dataframe price_data: including Date, Open, High, Low, Close, Volume of each transaction date
        list price_list: store all price we've crawled
        float price_mean: mean of price_list
        foat price_std: sample standard deviation of price_list
        dataframe bs_sheet: balance sheet (or Bull Shit)
        dataframe statement_of_CI: statement of comprehensive income
        dataframe statement_of_CF: statement of cash flows
        float EPS: nearest EPS
        float last_EPS: second nearest EPS
        int div: nearest total dividends
        int last_div: second nearest dividends
        float div_growth_rate: growth rate of dividends
        list return_rate_list: return rate of each day
        list risk_premim_list: risk premium of each day
        float risk_premium_mean, float risk_premium_var
    '''
    def __init__(self, index, name, prop):  # wait for stock price input
        self.index = index
        self.name = name
        self.proportion = prop
        self.stock_path = os.getcwd() + "\\" + str(self.index) + "_" + self.name
        if not os.path.isdir(self.stock_path):
            os.mkdir(self.stock_path)
    
    def crawl_a_month_price(self, str_date):
        print("Crawling")
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
            open_price = "".join(row[3].split(","))
            highest_price = "".join(row[4].split(","))
            lowest_price = "".join(row[5].split(","))
            close_price = "".join(row[6].split(","))
            self.price_dict["Open"].append(float(open_price))
            self.price_dict["High"].append(float(highest_price))
            self.price_dict["Low"].append(float(lowest_price))
            self.price_dict["Close"].append(float(close_price))
        time.sleep(random.randint(3, 8))
        price_web.close()

    def crawl_stock_prices(self):
        self.price_dict = {"Date":[], "Open":[], "High":[], "Low":[], "Close":[], "Volume":[]}
        date = now_str_date
        for i in range(3):  # depend on how many month we want to crawl
            self.crawl_a_month_price(date)
            date = get_last_month_date(date)
        self.price_data = pd.DataFrame(self.price_dict).sort_values(["Date"], ascending=False).reset_index(drop = True)
        self.price_list = [round((o+h+l+c)/4, 4) for o, h, l, c in zip(self.price_data["Open"], self.price_data["High"], self.price_data["Low"], self.price_data["Close"])]
        self.price_mean = round(np.mean(self.price_list), 4)
        self.price_std = round(np.std(self.price_list, ddof=1), 4)  # Sample standard deviation

    def crawl_yahoo(self):
        print("Crawling")
        stock = yf.Ticker(str(self.index)+".TW")
        self.price_data = stock.history("2y")
        self.price_data.drop(columns = ["Dividends", "Stock Splits"])
        self.price_data.reset_index(inplace = True)
        self.price_data["Date"] = [int(d.strftime("%Y%m%d")) for d in self.price_data["Date"]]
        self.price_data = self.price_data.sort_values(["Date"], ascending = False)
        self.price_list = [round((o+h+l+c)/4, 4) for o, h, l, c in zip(self.price_data["Open"], self.price_data["High"], self.price_data["Low"], self.price_data["Close"])]
        self.price_mean = round(np.mean(self.price_list), 4)
        self.price_std = round(np.std(self.price_list, ddof=1), 4)  # Sample standard deviation
        # print(self.price_mean, self.price_std)
        
    def crawl_fs(self):
        fs_url = "https://mops.twse.com.tw/server-java/t164sb01?step=1"+"&"+"CO_ID="+str(self.index)+"&SYEAR="+str(year-1)+"&SSEASON=4&REPORT_ID=C"
        fs_web = requests.get(fs_url)
        fs_web.encoding = "big5"
        print("check")  # sucessfully enter the website
        fs_datas = pd.read_html(StringIO(fs_web.text))
        time.sleep(random.randint(3, 8))
        self.bs_sheet = fs_datas[0]
        self.bs_sheet.columns = ["Code", "Title", str(year-1), str(year-2)]
        self.statement_of_CI = fs_datas[1]
        self.statement_of_CI.columns = ["Code", "Title", str(year-1), str(year-2)]
        self.statement_of_CF = fs_datas[2]
        self.statement_of_CF.columns = ["Code", "Title", "In"+str(year-1), "In"+str(year-2)]
        # Some basic measurements
        # Basic EPS
        EPS_row = self.statement_of_CI.loc[self.statement_of_CI["Title"] == "基本每股盈餘合計　Total basic earnings per share",:]
        s_EPS = EPS_row.iloc[0][str(year-1)]
        s_last_EPS = EPS_row.iloc[0][str(year-2)]
        self.EPS = acct_num_str_to_float(s_EPS)
        self.last_EPS = acct_num_str_to_float(s_last_EPS)
        # print(self.EPS, self.last_EPS)
        # Dividends
        div_row = self.statement_of_CF.loc[self.statement_of_CF["Title"] == "發放現金股利　Cash dividends paid",:]
        if div_row.empty:
            self.div = 0
            self.last_div = 0
            self.div_growth_rate = 0
        else:
            self.div = str(div_row.iloc[0]["In"+str(year-1)])
            self.div = int(self.div[1:][:-1].replace(",", ""))
            self.last_div = str(div_row.iloc[0]["In"+str(year-2)])
            self.last_div = int(self.last_div[1:][:-1].replace(",", ""))
            self.div_growth_rate = round(self.div/self.last_div, 4) - 1
        # print(self.div, self.last_div)
        # Capability of adding more financial statement here
        fs_web.close()

    def compute_return_rate(self):  # Return rate on daily basis (or the annual return rate cannot be computed with our data)
        NI_row = self.statement_of_CI.loc[self.statement_of_CI["Title"] == "本期淨利（淨損）Profit (loss)",:]
        EPS_row = self.statement_of_CI.loc[self.statement_of_CI["Title"] == "基本每股盈餘合計　Total basic earnings per share",:]
        this_share = int(acct_num_str_to_float(NI_row.iloc[0][str(year-1)].replace(",", ""))*1000 / acct_num_str_to_float(EPS_row.iloc[0][str(year-1)]))   # Outstanding share
        last_share = int(acct_num_str_to_float(NI_row.iloc[0][str(year-2)].replace(",", ""))*1000 / acct_num_str_to_float(EPS_row.iloc[0][str(year-2)]))
        self.return_rate_list = []
        for i in range(len(self.price_list)-1):
            rate = 0
            if str(self.price_data["Date"][i])[:4] == str(year) or str(self.price_data["Date"][i])[:4] == str(year-1):
                rate = round((((self.price_list[i+1]-self.price_list[i]+(self.div/this_share/365)) / self.price_list[i+1])), 10)
            else:
                rate = round((((self.price_list[i]-self.price_list[i+1]+(self.last_div/last_share/365)) / self.price_list[i])), 10)
            self.return_rate_list.append(rate)
        self.risk_premium_list = [r-daily_rf_rate for r in self.return_rate_list]
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
        self.price_data["High"] = [p for _,p in sorted(zip(self.price_data["Date"], self.price_data["High"]), reverse = True)]
        self.price_data["Low"] = [p for _,p in sorted(zip(self.price_data["Date"], self.price_data["Low"]), reverse = True)]
        datetime_list = [datetime.date(int(str(d)[:4]), int(str(d)[4:6]), int(str(d)[6:])) for d in self.price_data["Date"]]
        plotter.Figure()
        plotter.plot(datetime_list, self.price_data["High"], label="High", color="red")
        plotter.plot(datetime_list, self.price_data["Low"], label="Low", color="lightgreen")
        plotter.title("Stock Index "+str(self.index))
        plotter.legend(loc="upper left")
        plotter.xlabel("Time")
        plotter.xticks(rotation = 80)
        plotter.ylabel("Price")
        plotter.show()
        plotter.close()


class market_portfolio():
    '''
    Member variables:
        int stock_amount: how many companies are there in our market portfolio
        list market_list: companies in our market portfolio
        list price_list, list return_rate_list, list risk_premium_list(mean, var) >> same as company_stock
        dataframe market_price_data
    '''
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
        self.risk_premium_list = [r-daily_rf_rate for r in self.return_rate_list]
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
        return_list = [stock.risk_premium_mean + daily_rf_rate for stock in self.market_list]
        x = range(int(beta_list[0]), int(beta_list[len(beta_list)-1])+2)
        y = [self.risk_premium_mean*b + daily_rf_rate for b in x]
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

    def write_risk_premium_to_csv(self):
        now_path = os.getcwd()
        target_csv = open(now_path + "\\" + "Market_Portfolio_Risk_Premium.csv", "w", newline="", encoding="UTF-8")
        for r in range(len(self.risk_premium_list)):
            if r == 0:
                target_csv.write(str(self.risk_premium_list[r]))
            else:
                target_csv.write("," + str(self.risk_premium_list[r]))
        target_csv.close()

    def write_stock_info_in_market_port_to_csv(self):
        """format: index_1;name1;proportion1,index2;name2;proportion2,..."""
        now_path = os.getcwd()
        with open(now_path + r"\Sotck_Info_In_Market_Portfolio.csv", "w", newline="", encoding="UTF-8") as target_csv:
            for s in range(len(self.market_list)):
                if s == 0:
                    target_csv.write(str(self.market_list[s].index) + ";" + str(self.market_list[s].name) + ";" + str(self.market_list[s].proportion))
                else:
                    target_csv.write("," + str(self.market_list[s].index) + ";" + str(self.market_list[s].name) + ";" + str(self.market_list[s].proportion))


# Main
year = datetime.datetime.now().year
month = datetime.datetime.now().month
day = datetime.datetime.now().day
year = 2020  # The market hasn't open in June!!  
month = 5
day = 29
now_str_date = str(year) + get_str_month(month) + get_str_day(day)
risk_free_rate = 0.00815  # one year time deposit rate for Bank of Taiwan
# SMB = -0.00947  # Last 12 months data from Kenneth R.French - Data Library
# HML = -0.2943

daily_rf_rate = (1 + risk_free_rate) ** (1/365) - 1
'''
Little test for crawling
tsmc = company_stock(2330, "TSMC", 0.22)
tsmc.crawl_yahoo()
tsmc.plot_price()
'''

update = input("Do you want to update data? [y/n]: ")
if update == "y" or update == "Y":
    # Crawling market value table
    mv_table = market_value_table()
    mv_table.crawl_market_value_table()
    mv_table.write_mb_table_to_csv()

    comany_amount = 20  # How many company do we want to crawl
    # Crawling top companies
    market_port_com_list = []  # Company in the market portifolio
    for i in range(1, comany_amount+1):
        print(i)
        print()
        row = mv_table.mv_table.loc[mv_table.mv_table["Rank"] == i, :]
        this_company = company_stock(int(row.iloc[0]["Stock_id"]), row.iloc[0]["Company_name"], float(row.iloc[0]["Proportion"]))
        market_port_com_list.append(this_company)
        this_company.crawl_yahoo()
        # this_company.crawl_stock_prices()
    ##    this_company.write_price_to_csv()
        this_company.crawl_fs()
        this_company.compute_return_rate()
    ##    this_company.plot_price()
    ##    this_company.write_fs_to_csv(this_company.bs_sheet, "bs_sheet")
    ##    this_company.write_fs_to_csv(this_company.statement_of_CI, "Statement_of_Comprehensive_Income")
    ##    this_company.write_fs_to_csv(this_company.statement_of_CF, "Statement_of_Cash_Flows")

    # Forming market portfolio
    market_port = market_portfolio(comany_amount, market_port_com_list)
    market_port.compute_market_port()
    market_port.write_market_port_to_csv()
    ##market_port.plot_SML()
    market_port.write_risk_premium_to_csv()
    market_port.write_stock_info_in_market_port_to_csv()
    


# Graphic User Interface
class window(tk.Frame):
    def __init__(self):
        tk.Frame.__init__(self)
        self.grid()
        self.prepare_market_data()
        self.create_widgets()

    def prepare_market_data(self):
        # prepare the info of the stocks in the market portfolio
        self.mrkt_port_info = "- Market Portfolio (Proportion: Stock ID, Company Name) -\n\n"
        now_path = os.getcwd()
        with open(now_path + r"\Sotck_Info_In_Market_Portfolio.csv", "r", encoding="UTF-8") as target_csv:
            info = target_csv.readline().split(",")
            info = [i.split(";") for i in info] 
            total_proportion = 0
            for s in range(len(info)):
                info[s][2] = float(info[s][2])
                total_proportion += info[s][2]
            for s in range(len(info)):
                self.mrkt_port_info += "%05.2f%%: %s, %s\n" % ((info[s][2] / total_proportion * 100), info[s][0], info[s][1])

        # prepare rate of return of the market portfolio for regression
        with open(file=os.getcwd() + r"\Market_Portfolio_Risk_Premium.csv", mode="r", encoding="UTF-8") as fh:
            self.market_port_risk_premium = [float(i) for i in fh.readline().strip().split(",")]
        self.annual_market_port_risk_premium = annualize_daily_rate_of_return(self.market_port_risk_premium)
        self.annual_market_port_risk_premium_gmean = st.geometric_mean([(1+i) for i in self.annual_market_port_risk_premium]) - 1

    def create_widgets(self):
        f1 = tkFont.Font(size=12, family="Courier New")
        self.instrucion1_lbl = tk.Label(self, text="Stock ID: ", height=1, width=12, font=f1)
        self.regression_btn = tk.Button(self, text="Enter", height=1, width=5, font=f1, command=self.regression)
        self.stock_id_txt = tk.Text(self, height=1, width=5, font=f1)
        self.stock_name_lbl = tk.Label(self, text="Stock Name: ", height = 1, width=20, font=f1)
        self.draw_price_btn = tk.Button(self, text="Draw Stock Price", height=1, width=18, font=f1, command=self.draw_price)
        self.alpha_lbl = tk.Label(self, text="α: ", height=2, width=17, font=f1)
        self.beta_lbl = tk.Label(self, text="β: ", height=2, width=17, font=f1)
        self.stddev_residual_lbl = tk.Label(self, text="σ(e): ", height=2, width=17, font=f1)

        self.instrucion1_lbl.grid(row=0, column=0, sticky=tk.E)
        self.regression_btn.grid(row=0, column=4)
        self.stock_id_txt.grid(row=0, column=2, columnspan=2, sticky=tk.NE + tk.SW)
        self.stock_name_lbl.grid(row=1, column=0, columnspan=4)
        self.draw_price_btn.grid(row=1, column=4)
        self.alpha_lbl.grid(row=2, column=0, sticky=tk.W)
        self.beta_lbl.grid(row=2, column=2, sticky=tk.W)
        self.stddev_residual_lbl.grid(row=2, column=4, sticky=tk.W)

        self.empty_lbl_1 = tk.Label(self, text="")
        self.empty_lbl_1.grid(row=3, column=0)

        self.market_port_info_lbl = tk.Label(self, text=self.mrkt_port_info, font=f1)
        self.market_port_info_lbl.grid(row=4, column=0, columnspan=6, sticky=tk.W)

        self.empty_lbl_2 = tk.Label(self, text="")
        self.empty_lbl_2.grid(row=5, column=0)

        self.instrucion2_lbl = tk.Label(self, text="Required annualized RoR: ", height=1, width=25, font=f1)
        self.complete_port_btn = tk.Button(self, text="Enter", height=1, width=5, font=f1, command=self.complete_port)
        self.ror_txt = tk.Text(self, height=1, width=5, font=f1)
        self.ratio_lbl = tk.Label(self, text="Suggest: ", height=2, font=f1)

        self.instrucion2_lbl.grid(row=6, column=0, columnspan=2, sticky=tk.E)
        self.complete_port_btn.grid(row=6, column=4)
        self.ror_txt.grid(row=6, column=2, columnspan=2, sticky=tk.NE + tk.SW)
        self.ratio_lbl.grid(row=7, column=0, columnspan=6, sticky=tk.NW)

    def regression(self):
        """Run regression to find alpha and beta"""
        # choose the target stock
        self.target_stock_id = int(self.stock_id_txt.get("1.0", tk.END))
        now_path = os.getcwd()  # find the selected stock's name
        with open(file=now_path + r"\Market_Value_Table.csv", mode="r", encoding="utf-8") as fh:
            data = pd.read_csv(fh)
            for i in range(len(data["Stock_id"])):
                if data["Stock_id"][i] == self.target_stock_id:
                    self.target_co_name = data["Company_name"][i]
        self.target_co = company_stock(self.target_stock_id, self.target_co_name, "NA")
        self.target_co.crawl_yahoo()
        self.target_co.crawl_fs()
        self.target_co.compute_return_rate()

        # run regression: Capital Asset Pricing Model
        market_port_risk_premium_4lm = np.array(self.market_port_risk_premium).reshape(-1, 1)
        target_co_risk_prmium_4lm = np.array(self.target_co.risk_premium_list).reshape(-1, 1)
        lm = LinearRegression()
        lm.fit(market_port_risk_premium_4lm, target_co_risk_prmium_4lm)
        self.stddev_residual = np.var(target_co_risk_prmium_4lm - lm.predict(market_port_risk_premium_4lm), ddof=1) ** 0.5

        self.alpha_lbl.configure(text="α: %.6f" % lm.intercept_)
        self.beta_lbl.configure(text="β: %.6f" % lm.coef_)
        self.stddev_residual_lbl.configure(text="σ(e): %.6f" % self.stddev_residual)
        self.stock_name_lbl.configure(text="Stock Name: %s" % self.target_co_name)

    def draw_price(self):
        """Please execute the function "regression()" first"""
        self.target_co.plot_price(self.fig)
        

    def complete_port(self):
        """
        Use the Capital Market Line to provide a complete portfolio
        composed of the market portfolio and the risk-free asset
        """
        target_RoR = float(self.ror_txt.get("1.0", tk.END))
        target_rist_premium = target_RoR - risk_free_rate
        rf_asset_ratio = 1 - (target_rist_premium / self.annual_market_port_risk_premium_gmean)
        self.ratio_lbl.configure(text="Suggest: You should put %.4f in risk-free asset,\nand the rest in market portfolio" % rf_asset_ratio)


mywindow = window()
mywindow.master.title("Program")
mywindow.mainloop()
