import pandas as pd

def load_all_data():
    df = pd.read_csv("https://raw.githubusercontent.com/mmcalend/USMeaslesData/refs/heads/main/USMeaslesCases.csv", parse_dates=["mmwr_week_start"])
    try:
        df19 = pd.read_csv("https://raw.githubusercontent.com/mmcalend/USMeaslesData/refs/heads/main/NNDSSMeasles2019.csv", encoding="utf-8")
    except UnicodeDecodeError:
        df19 = pd.read_csv("https://raw.githubusercontent.com/mmcalend/USMeaslesData/refs/heads/main/NNDSSMeasles2019.csv", encoding="latin1")

    dfdetails = pd.read_csv("https://raw.githubusercontent.com/mmcalend/USMeaslesData/refs/heads/main/USMeaslesCasesDetails.csv")
    mmr = pd.read_csv("https://raw.githubusercontent.com/mmcalend/USMeaslesData/refs/heads/main/MMR.csv")
    df_schools = pd.read_csv("https://raw.githubusercontent.com/mmcalend/USMeaslesData/refs/heads/main/24-25ADHSMMRKCoverage.csv")

    df_us_cdc = pd.read_csv(
        "https://raw.githubusercontent.com/mmcalend/USMeaslesData/refs/heads/main/CDC_US_WeeklyRashOnset.csv",
        parse_dates=["mmwr_week_start"]
    )

    return df, df19, dfdetails, mmr, df_schools, df_us_cdc
