import os
import pandas as pd
import numpy as np

path = 'C:\\Users\\lj\\Desktop\\schneider'
datanames = os.listdir(path)
print(len(datanames))

df = pd.read_csv('schneider_csv.csv')
df1 = df['file_name']
data = np.array(df1)  # np.ndarray()
l2 = data.tolist()  # list
print(len(set(l2)))

myset = set(l2)
for item in myset:
    if l2.count(item) > 1:
        print(item)


import binwalk



