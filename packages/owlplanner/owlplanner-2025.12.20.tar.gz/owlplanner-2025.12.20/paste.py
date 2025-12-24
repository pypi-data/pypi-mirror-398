import streamlit as st
import pandas as pd


def text2EarningsRecord(text):
    """
    Convert general text paste to a dataframe of years and earnings.
    Slow but robust. Return a dataframe.
    """
    year = []
    earnings = []

    # Assume lines are separated.
    lines =  text.split("\n")
    for line in lines:
        tokens = line.split()
        if len(tokens) >= 2 and tokens[0].isdigit() and 1950 < int(tokens[0]) < 2050:
            year.append(int(tokens[0]))
            earnings.append(float(tokens[1].replace(",", "").replace("$", "")))

    # Otherwise it is a long list of tokens. Identify those that are year.
    if len(year) == 0:
        yindex = []
        for ind, token in enumerate(lines):
            if token.isdigit() and 1950 < int(token) < 2050:
                yindex.append(ind)
            else:
                continue

        imax = len(lines)
        for i in yindex:
            if i+1 < imax:
                amount = lines[i+1].replace(",", "").replace("$", "")
                if amount.isdigit():
                    earnings.append(float(amount))
                    year.append(int(lines[i]))

    df = pd.DataFrame({"year": year, "earnings ($)": earnings})

    return df

name0 = "Martin"
yob0 = 1950
name1 = "Linda"
yob1 = 1961

col1, col2 = st.columns(2, gap="large")
with col1:
    text = st.text_area(f"Paste {name0}'s data here and hit Ctrl-Enter")
    df = text2EarningsRecord(text)

    st.write(f"{name0}'s earnings records")
    df = df.style.format({"earnings ($)": "${:,.0f}"})
    # edited_df = st.data_editor(df, key="_earnings0", num_rows="dynamic")
    st.dataframe(df, hide_index=True)

with col2:
    text = st.text_area(f"Paste {name1}'s data here and hit Ctrl-Enter")
    df = text2EarningsRecord(text)

    st.write(f"{name1}'s earnings records")
    df = df.style.format({"earnings ($)": "${:,.0f}"})
    # edited_df = st.data_editor(df, key="_earnings1", num_rows="dynamic")
    st.dataframe(df, hide_index=True)


# st.dataframe(edited_df, hide_index=True)

