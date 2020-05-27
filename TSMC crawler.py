# Test for Github and crawling stock
import requests
import csv
import pandas as pd
import time
import datetime
import os
from io import StringIO

year = datetime.datetime.now().year
stock_id = 2330
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
