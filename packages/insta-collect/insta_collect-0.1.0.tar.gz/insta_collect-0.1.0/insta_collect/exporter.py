import pandas as pd

def save_to_xlsx(data, filename="instagram_comments.xlsx"):
    df = pd.DataFrame(data)
    df.to_excel(filename, index=False)
    return filename
