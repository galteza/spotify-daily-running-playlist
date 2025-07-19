import pandas as pd

if __name__ == '__main__':

    data = {'Query': ['gabby'],
            'BPM': [145]}
    df = pd.DataFrame(data)
    print(df)
    df.to_csv('BPMs.csv', mode='a', index=False, header=False)