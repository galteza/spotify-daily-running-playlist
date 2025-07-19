import pandas as pd
import scrapeBPM
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys

chrome_options = Options()
chrome_options.add_argument("--headless")  # Run in headless mode
driver = webdriver.Chrome(options=chrome_options)
# Navigate to the Song BPM website
driver.get("https://songbpm.com/")


df = pd.read_csv('BPMs.csv')
queries = df['Query'].tolist()
bpms = df['BPM'].tolist()
print(queries)
print(bpms)
for i in range(len(queries)):
    if pd.isna(bpms[i]):
        '''
        new_data = {'Query': [queries[i]],
                    'BPM': [scrapeBPM.scrapeBPM(queries[i], driver)]}
        pd.DataFrame(new_data).to_csv('BPMs.csv', mode='a', index=False, header=False)
        '''
        bpms[i] = scrapeBPM.scrapeBPM(queries[i], driver)
        new_data = {'Query': queries,
                    'BPM': bpms}
        pd.DataFrame(new_data).to_csv('BPMs.csv', index=False, header=True)

driver.quit()