import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# --- Configuração da Página (Modo Apresentação) ---
st.set_page_config(
    page_title="Relatório Executivo: Syssant",
    layout="wide",
    page_icon="🏢",
    # Esconde a barra lateral pra ficar mais limpo pro chefe
    initial_sidebar_state="collapsed"
)

# --- CSS Estilo "Impresso na Forbes" ---
st.markdown("""
<style>
    .main { background-color: #fdfdfd; }
    h1 { color: #1e3799; font-family: 'Helvetica', sans-serif; }
    .kpi-box {
        background: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        text-align: center;
        border-bottom: 4px solid #1e3799;
    }
    .kpi-label { font-size: 14px; color: #7f8fa6; text-transform: uppercase; letter-spacing: 1px;}
    .kpi-val { font-size: 32px; font-weight: bold; color: #2f3640; }
    .stDataFrame { border-radius: 10px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
</style>
""", unsafe_allow_html=True)

# --- Carregamento Automático (O Segredo) ---


@st.cache_data
def get_data():
    # NOME EXATO DO ARQUIVO QUE VOCÊ VAI SUBIR NO GITHUB
    file_path = 'Confissão de Divida - Syssant.xlsx'

    try:
        # skiprows=3 para pular o cabeçalho sujo
        df = pd.read_excel(file_path, engine='openpyxl', skiprows=3)
    except FileNotFoundError:
        st.error(
            f"🚨 ERRO CRÍTICO: O arquivo '{file_path}' não foi encontrado no servidor.")
        st.stop()

    # --- LIMPEZA E TRATAMENTO (Igual ao anterior) ---
    # 1. Identificar colunas dinamicamente
    cols = df.columns.str.lower()
    mapa = {
        'data': next((c for c in df.columns if 'vencimento' in c.lower() or 'data' in c.lower()), 'Vencimento'),
        'valor': next((c for c in df.columns if 'valor' in c.lower() or 'original' in c.lower()), 'Valor Original'),
        'status': next((c for c in df.columns if 'status' in c.lower() or 'situacao' in c.lower()), 'Status'),
        'pago': next((c for c in df.columns if 'pago' in c.lower()), 'Valor Pago')
    }
    df = df.rename(columns={mapa['data']: 'Data', mapa['valor']                   : 'Valor', mapa['status']: 'Status', mapa['pago']: 'Pago'})

    # 2. Limpar Moeda
    def clean_money(x):
        if isinstance(x, str):
            return float(x.replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.'))
        return x

    if df['Valor'].dtype == 'object':
        df['Valor'] = df['Valor'].apply(clean_money)
    if df['Pago'].dtype == 'object':
        df['Pago'] = df['Pago'].apply(clean_money)

    df['Pago'] = df['Pago'].fillna(0)
    df['Data'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
    df = df.dropna(subset=['Data']).sort_values('Data')

    return df


df = get_data()

# --- Lógica do Dashboard ---
total_bruto = df['Valor'].sum()
total_pago = df['Pago'].sum()
saldo_devedor = total_bruto - total_pago
progresso = (total_pago / total_bruto) if total_bruto > 0 else 0

# --- Interface Visual ---
st.title("📊 Relatório de Posição Financeira")
st.markdown(
    f"**Cliente:** Syssant | **Referência:** {datetime.now().strftime('%B/%Y')}")
st.markdown("---")

# KPIs
col1, col2, col3 = st.columns(3)
col1.markdown(
    f"""<div class="kpi-box"><div class="kpi-label">Dívida Total Contratada</div><div class="kpi-val">R$ {total_bruto:,.2f}</div></div>""", unsafe_allow_html=True)
col2.markdown(
    f"""<div class="kpi-box"><div class="kpi-label">Amortizado (Pago)</div><div class="kpi-val" style="color:#44bd32">R$ {total_pago:,.2f}</div></div>""", unsafe_allow_html=True)
col3.markdown(
    f"""<div class="kpi-box"><div class="kpi-label">Saldo em Aberto</div><div class="kpi-val" style="color:#c23616">R$ {saldo_devedor:,.2f}</div></div>""", unsafe_allow_html=True)

st.write("")  # Espaço

# Gráficos
c_chart1, c_chart2 = st.columns([2, 1])

with c_chart1:
    st.subheader("Cronograma de Desembolso")
    # Gráfico de barras combinadas
    fig = go.Figure()
    fig.add_trace(go.Bar(name='Valor Parcela',
                  x=df['Data'], y=df['Valor'], marker_color='#dcdde1'))
    fig.add_trace(
        go.Bar(name='Pago', x=df['Data'], y=df['Pago'], marker_color='#44bd32'))
    fig.update_layout(barmode='overlay', template='plotly_white',
                      height=400, legend=dict(orientation="h", y=1.1))
    st.plotly_chart(fig, use_container_width=True)

with c_chart2:
    st.subheader("Status Atual")
    fig_pie = px.pie(values=[total_pago, saldo_devedor], names=[
                     'Pago', 'Pendente'], color_discrete_sequence=['#44bd32', '#c23616'], hole=0.6)
    fig_pie.update_layout(showlegend=True, legend=dict(
        orientation="h", y=-0.1), height=400)
    fig_pie.add_annotation(
        text=f"{progresso:.0f}%", font_size=40, showarrow=False)
    st.plotly_chart(fig_pie, use_container_width=True)

# Tabela Simples (O chefe gosta de ver linha por linha as vezes)
with st.expander("Ver Detalhamento das Parcelas"):
    st.dataframe(df[['Data', 'Valor', 'Pago', 'Status']].style.format(
        {'Valor': 'R$ {:,.2f}', 'Pago': 'R$ {:,.2f}'}), use_container_width=True)
