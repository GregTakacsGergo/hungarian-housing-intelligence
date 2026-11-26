"""Read-only portfolio dashboard for the original 47-location project."""
from pathlib import Path
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from location_catalog import LOCATION_OPTIONS

st.set_page_config(page_title='Hungarian Housing Intelligence', page_icon='🏙️', layout='wide')
DATA_PATH = Path(__file__).resolve().parent / 'data' / 'housing_prices.csv'
FX_PATH = Path(__file__).resolve().parent / 'data' / 'eur_huf_history.csv'
LABELS = {v: k for k, v in LOCATION_OPTIONS.items()}

@st.cache_data(show_spinner=False)
def read_data(path, modified):
    df = pd.read_csv(path)
    expected = {'snapshot_date', 'location', 'huf_per_sqm', 'sample_count', 'source'}
    missing = expected - set(df.columns)
    if missing:
        raise ValueError('Missing CSV columns: ' + ', '.join(sorted(missing)))
    df['snapshot_date'] = pd.to_datetime(df['snapshot_date'], errors='coerce')
    for col in ['huf_per_sqm', 'sample_count']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df = df.dropna(subset=['snapshot_date', 'location', 'huf_per_sqm'])
    df = df[df['huf_per_sqm'] > 0]
    df['location'] = df['location'].astype(str)
    df['city'] = df['location'].map(LABELS).fillna(df['location'])
    return df.sort_values('snapshot_date')



@st.cache_data(show_spinner=False)
def read_fx_data(path, modified):
    fx = pd.read_csv(path)
    required = {'snapshot_date', 'eur_huf'}
    if required - set(fx.columns):
        raise ValueError('Missing FX CSV columns: ' + ', '.join(sorted(required - set(fx.columns))))
    fx['snapshot_date'] = pd.to_datetime(fx['snapshot_date'], errors='coerce')
    fx['eur_huf'] = pd.to_numeric(fx['eur_huf'], errors='coerce')
    fx = fx.dropna(subset=['snapshot_date', 'eur_huf'])
    fx = fx[fx['eur_huf'] > 0]
    return (fx.sort_values('snapshot_date')
            .drop_duplicates('snapshot_date', keep='last')
            [['snapshot_date', 'eur_huf']])


def fmt_huf(x):
    return f'{x:,.0f}'.replace(',', ' ') + ' Ft/m²'


def indicators(ohlc):
    df = ohlc.copy()
    df['MA 4 hét'] = df['close'].rolling(4, min_periods=1).mean()
    df['MA 12 hét'] = df['close'].rolling(12, min_periods=1).mean()
    ma = df['close'].rolling(20, min_periods=5).mean()
    sd = df['close'].rolling(20, min_periods=5).std()
    df['BB upper'], df['BB lower'] = ma + 2*sd, ma - 2*sd
    delta = df['close'].diff()
    avg_up = delta.clip(lower=0).rolling(14, min_periods=14).mean()
    avg_down = (-delta.clip(upper=0)).rolling(14, min_periods=14).mean()
    rs = avg_up / avg_down.replace(0, np.nan)
    df['RSI'] = 100 - 100 / (1 + rs)
    ema12 = df['close'].ewm(span=12, adjust=False).mean()
    ema26 = df['close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = ema12 - ema26
    df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    return df

st.title('🏙️ Hungarian Housing Intelligence')
st.caption('47 földrajzi lokációra tervezett, Jófogás-hirdetésekből képzett 50–60 m²-es lakásár-index · Portfólió dashboard')
if not DATA_PATH.exists():
    st.warning('Még nincs feltöltött valódi adatállomány. Előbb futtasd helyben az export_mysql_snapshot.py fájlt, majd helyezd a CSV-t a data/ mappába.')
    st.code('python export_mysql_snapshot.py\nstreamlit run web_app.py', language='bash')
    st.stop()

try:
    data = read_data(str(DATA_PATH), DATA_PATH.stat().st_mtime_ns)
except Exception as exc:
    st.error(f'Nem sikerült beolvasni az adatállományt: {exc}')
    st.stop()
if data.empty:
    st.warning('A CSV-ben nincs megjeleníthető, pozitív árú adatsor.')
    st.stop()

locations = sorted(data['location'].unique(), key=lambda k: LABELS.get(k, k))
with st.sidebar:
    st.header('Szűrők')
    default_key = 'hajdu-bihar/debrecen' if 'hajdu-bihar/debrecen' in locations else locations[0]
    selected = st.selectbox('Város / lokáció', locations, index=locations.index(default_key), format_func=lambda k: LABELS.get(k, k))
    min_day, max_day = data['snapshot_date'].min().date(), data['snapshot_date'].max().date()
    dates = st.date_input('Időszak', value=(min_day, max_day), min_value=min_day, max_value=max_day)
    st.divider()
    st.caption('Csak exportált adatokat olvas. Nincs publikus MySQL- vagy AWS-kapcsolat.')

if isinstance(dates, tuple) and len(dates) == 2:
    begin, end = dates
else:
    begin, end = min_day, max_day
filtered = data[(data['snapshot_date'].dt.date >= begin) & (data['snapshot_date'].dt.date <= end)].copy()
city = filtered[filtered['location'] == selected].sort_values('snapshot_date')

st.info('A mutató **hirdetési kínálati árakból képzett index**, nem lezárt adásvételek átlagára. A historikus debreceni és az új scraper-sorozat módszertana eltérhet.')
if city.empty:
    st.warning('A kiválasztott városhoz nincs adat ebben az időszakban.')
    st.stop()

last = city.iloc[-1]
first = city.iloc[0]
change = (last.huf_per_sqm / first.huf_per_sqm - 1)*100 if len(city)>1 and first.huf_per_sqm else np.nan
m1,m2,m3,m4 = st.columns(4)
m1.metric('Legutóbbi árindex', fmt_huf(last.huf_per_sqm))
m2.metric('Időszaki változás', f'{change:+.1f}%' if pd.notna(change) else '—')
m3.metric('Utolsó mintaszám', f'{last.sample_count:,.0f}' if pd.notna(last.sample_count) else 'n.a.')
m4.metric('Adat utolsó napja', str(last.snapshot_date.date()))

tab1,tab2,tab3,tab4,tab5 = st.tabs(['📈 Idősor', '🕯️ Technikai grafikon', '💶 EUR/HUF összevetés', '🏘️ Lokációk', '📋 Adatok és módszertan'])
with tab1:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=city.snapshot_date, y=city.huf_per_sqm, mode='lines+markers', name=LABELS.get(selected,selected), line=dict(width=3)))
    if city.source.nunique()>1:
        old = city[city.source=='historical']
        new = city[city.source=='47loc']
        if not old.empty and not new.empty:
            fig.add_shape(type='line', x0=new.snapshot_date.min(), x1=new.snapshot_date.min(), y0=0, y1=1, yref='paper', line=dict(dash='dash', color='orange'))
    fig.update_layout(yaxis_title='Ft/m²', xaxis_title='Dátum', hovermode='x unified', height=460)
    st.plotly_chart(fig, width='stretch', config={'modeBarButtonsToRemove': ['toImage']})
    st.caption('Debrecennél a korábbi historikus sorozat az új 47loc sorozat kezdetéig szerepel; az átfedő időpontokat az exportáló levágja.')

with tab2:
    st.caption('A heti OHLC-értékek a heti indexmegfigyelésekből állnak elő, nem tőzsdei vagy tranzakciós gyertyák.')
    show_ma = st.checkbox('Mozgóátlagok (4 és 12 hét)', True)
    show_bb = st.checkbox('Bollinger-szalagok (20 hét)', False)
    show_rsi = st.checkbox('RSI (14 hét)', False)
    show_macd = st.checkbox('MACD', False)
    ohlc = city.set_index('snapshot_date')['huf_per_sqm'].resample('W').ohlc().dropna()
    tech = indicators(ohlc)
    rows = 1 + int(show_rsi) + int(show_macd)
    heights = [0.65] + ([0.18] if show_rsi else []) + ([0.2] if show_macd else [])
    fig = make_subplots(rows=rows, cols=1, shared_xaxes=True, vertical_spacing=.06, row_heights=heights)
    fig.add_trace(go.Candlestick(x=tech.index, open=tech.open, high=tech.high, low=tech.low, close=tech.close, name='Heti index', increasing_line_color='#16a34a', decreasing_line_color='#dc2626'),row=1,col=1)
    if show_ma:
        for name in ['MA 4 hét','MA 12 hét']:
            fig.add_trace(go.Scatter(x=tech.index,y=tech[name],name=name,mode='lines'),row=1,col=1)
    if show_bb:
        for name in ['BB upper','BB lower']:
            fig.add_trace(go.Scatter(x=tech.index,y=tech[name],name=name,mode='lines',line=dict(dash='dot')),row=1,col=1)
    row = 2
    if show_rsi:
        fig.add_trace(go.Scatter(x=tech.index,y=tech.RSI,name='RSI'),row=row,col=1)
        fig.add_hline(y=70,line_dash='dot',row=row,col=1)
        fig.add_hline(y=30,line_dash='dot',row=row,col=1)
        row += 1
    if show_macd:
        fig.add_trace(go.Scatter(x=tech.index,y=tech.MACD,name='MACD'),row=row,col=1)
        fig.add_trace(go.Scatter(x=tech.index,y=tech.Signal,name='Signal'),row=row,col=1)
    fig.update_layout(height=650 if rows>1 else 490, xaxis_rangeslider_visible=False, legend=dict(orientation='h'))
    st.plotly_chart(fig, width='stretch', config={'modeBarButtonsToRemove': ['toImage']})
    if len(tech)<20:
        st.caption('Kevés heti adat esetén egyes indikátorok szándékosan hiányosak.')

with tab3:
    st.subheader('EUR/HUF árfolyam és lakásár-index')
    st.caption('A régi debreceni MySQL-adatsorból számított historikus EUR/HUF árfolyam. Nem élő devizaadat; a későbbi időszakokra nem feltétlenül van árfolyam-megfigyelés.')
    if not FX_PATH.exists():
        st.warning('Hiányzik a data/eur_huf_history.csv. Futtasd újra a frissített export_mysql_snapshot.py szkriptet a saját gépeden, majd töltsd fel a CSV-t.')
    else:
        try:
            fx_data = read_fx_data(str(FX_PATH), FX_PATH.stat().st_mtime_ns)
        except Exception as exc:
            st.error(f'Nem sikerült beolvasni az EUR/HUF adatokat: {exc}')
            fx_data = pd.DataFrame(columns=['snapshot_date', 'eur_huf'])
        fx_window = fx_data[(fx_data['snapshot_date'].dt.date >= begin) &
                            (fx_data['snapshot_date'].dt.date <= end)]
        if fx_window.empty:
            st.info('A kiválasztott időszakban nincs historikus EUR/HUF-adat. Próbálj korábbi dátumot választani az oldalsávban.')
        else:
            mode = st.radio('Összehasonlítás típusa',
                            ['Két tengely (Ft/m² és Ft/EUR)', 'Bázisindex (első közös megfigyelés = 100)'],
                            horizontal=True)
            # Az árindex napjaihoz a legutóbbi, nem későbbi FX-megfigyelést párosítjuk.
            # Nem engedünk 7 napnál régebbi árfolyamot, hogy ne tűnjön élő adatnak.
            paired = pd.merge_asof(
                city[['snapshot_date', 'huf_per_sqm']].sort_values('snapshot_date'),
                fx_window[['snapshot_date', 'eur_huf']].sort_values('snapshot_date'),
                on='snapshot_date', direction='backward', tolerance=pd.Timedelta(days=7)
            ).dropna(subset=['eur_huf'])
            if paired.empty:
                st.warning('Nincs közös, legfeljebb 7 nap eltérésű árfolyam- és lakásár-megfigyelés az adott városnál és időszakban.')
            else:
                fx_fig = make_subplots(specs=[[{'secondary_y': True}]])
                label = LABELS.get(selected, selected)
                if mode.startswith('Bázisindex'):
                    price_series = paired['huf_per_sqm'] / paired['huf_per_sqm'].iloc[0] * 100
                    fx_series = paired['eur_huf'] / paired['eur_huf'].iloc[0] * 100
                    fx_fig.add_trace(go.Scatter(x=paired.snapshot_date, y=price_series,
                        mode='lines', name=f'{label} lakásár-index'), secondary_y=False)
                    fx_fig.add_trace(go.Scatter(x=paired.snapshot_date, y=fx_series,
                        mode='lines', name='EUR/HUF (bázisindex)'), secondary_y=False)
                    fx_fig.update_yaxes(title_text='Bázisindex (100 = első közös adat)', secondary_y=False)
                else:
                    fx_fig.add_trace(go.Scatter(x=city.snapshot_date, y=city.huf_per_sqm,
                        mode='lines', name=f'{label} · Ft/m²'), secondary_y=False)
                    fx_fig.add_trace(go.Scatter(x=fx_window.snapshot_date, y=fx_window.eur_huf,
                        mode='lines', name='EUR/HUF · Ft/EUR'), secondary_y=True)
                    fx_fig.update_yaxes(title_text='Lakásár-index (Ft/m²)', secondary_y=False)
                    fx_fig.update_yaxes(title_text='EUR/HUF (Ft/EUR)', secondary_y=True)
                fx_fig.update_layout(height=510, hovermode='x unified',
                    legend=dict(orientation='h', y=1.1), margin=dict(t=75))
                st.plotly_chart(fx_fig, width='stretch', config={'modeBarButtonsToRemove': ['toImage']})
                st.caption(f'Párosított árindex-megfigyelések: {len(paired)}. Az EUR/HUF a historikus forrásból származik; az ábrázolt lakásár-adatok dátumához legfeljebb 7 nappal korábbi árfolyamot párosítunk.')

with tab4:
    latest = filtered.sort_values('snapshot_date').groupby('location',as_index=False).tail(1).copy()
    latest['Város'] = latest['city']
    latest['Ár (Ft/m²)'] = latest['huf_per_sqm'].round().astype(int)
    latest['Mintaszám'] = latest['sample_count']
    latest['Dátum'] = latest['snapshot_date'].dt.strftime('%Y-%m-%d')
    st.caption('Lokációnként a kiválasztott intervallumba eső utolsó elérhető megfigyelés. A dátumok eltérhetnek.')
    st.dataframe(latest[['Város','Ár (Ft/m²)','Mintaszám','Dátum']].sort_values('Ár (Ft/m²)',ascending=False), hide_index=True, width='stretch')
    top = latest.nlargest(20,'huf_per_sqm').sort_values('huf_per_sqm')
    bar = go.Figure(go.Bar(x=top.huf_per_sqm, y=top.city, orientation='h'))
    bar.update_layout(height=640, xaxis_title='Ft/m²', yaxis_title='')
    st.plotly_chart(bar,width='stretch',config={'modeBarButtonsToRemove': ['toImage']})

with tab5:
    st.write(f'**Megfigyelések:** {len(filtered):,} · **Lokációk adattal:** {filtered.location.nunique()}')
    st.dataframe(city[['snapshot_date','huf_per_sqm','source','sample_count']].sort_values('snapshot_date',ascending=False),hide_index=True,width='stretch')
    st.markdown('**Módszertan:** 50–60 m²-es eladó lakások Jófogás-hirdetései; lokációnkénti Ft/m² index, a scraper logikája szerint alsó 10% levágása utáni medián. A mintaszám a levágás utáni elemszám. Ez nem reprezentatív tranzakciós árstatisztika. A historikus Debrecen sorozat külön forráslogika miatt összehasonlíthatósági törést tartalmazhat. A 47 lokáció a célzott lefedettség, nem garantáltan mindegyikhez érkezik érvényes adat.')

st.divider()
st.caption('Python · AWS Lambda · DynamoDB · MySQL · Pandas · Streamlit · Plotly | Bemutató az exportált adatállomány alapján')
