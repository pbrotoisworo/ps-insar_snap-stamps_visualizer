import altair as alt
import pandas as pd
from datetime import timedelta


def to_altair_datetime(dt):
    dt = pd.to_datetime(dt) - timedelta(60)
    return alt.DateTime(year=dt.year, month=dt.month, date=dt.day,
                        hours=dt.hour, minutes=dt.minute, seconds=dt.second,
                        milliseconds=0.001 * dt.microsecond)


def plot_ts(df):

    highlight = alt.selection_single(on='mouseover', fields=['Date'], nearest=True)
    domain = [to_altair_datetime(df.Date.unique().min() - timedelta(60)),
              to_altair_datetime(df.Date.unique().max() + timedelta(120))]

    # Add trendline
    dates = [x for x in df['Date'].unique()]
    rows = []
    for date in dates:
        mean = df[df['Date'].astype(str) == str(date)]['Displacement'].astype(float).mean()
        rows.append({'ps': 9999, 'Date': date, 'lon': None, 'lat': None, 'Displacement': mean})
    df_reg = pd.DataFrame(columns=['ps', 'Date', 'lon', 'lat', 'Displacement'])
    df_reg = df_reg.append(rows)
    df_reg['Origin'] = 'red'  # Add empty column for encoding
    # df_reg['color'] = 'red'

    reg = alt.Chart(df_reg)\
        .mark_circle(opacity=1.0)\
        .encode(
            x=alt.X('Date:T'),
            y=alt.Y('Displacement:Q'),
            # color='Origin',
            color=alt.Color('Origin', scale=alt.Scale(scheme='reds'), legend=alt.Legend(title="Trends", orient='bottom')),
        )\
        .transform_loess('Date', 'Displacement') \
        .transform_calculate(Origin='" LOESS"')\
        .mark_line(color='red', size=6, strokeDash=[5, 5])

    altC = alt.Chart(df).properties(height=400).mark_line(point=False, opacity=0.5)\
        .encode(
            x=alt.X('Date:T', scale=alt.Scale(domain=domain, clamp=True)),
            y=alt.Y('Displacement:Q', title='Displacement (mm)', scale=alt.Scale(domain=[df.Displacement.min() - 5, df.Displacement.max() + 5], clamp=True)),
            color=alt.Color('ps:N', scale=alt.Scale(scheme='darkmulti'), legend=alt.Legend(title="PS ID", orient='bottom')),
            tooltip=[alt.Tooltip('Date:T'),
                     alt.Tooltip('Displacement:Q', format=',.2f', title='Disp')]
    ).add_selection(highlight).interactive(bind_y=False)

    return alt.layer(altC, reg).resolve_scale(color='independent')
    # return altC + reg
