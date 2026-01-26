import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# --- Configuração da Página ---
st.set_page_config(
    page_title="Gestão Financeira Syssant",
    layout="wide",
    page_icon="🔧"
)

# --- CSS Profissional ---
st.markdown("""
<style>
    .metric-card { background-color: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 5px solid #2980b9; }
    .metric-label { font-size: 12px; color: #7f8fa6; font-weight: bold; text-transform: uppercase; }
    .metric-value { font-size: 24px; color: #2c3e50; font-weight: 800; }
</style>
""", unsafe_allow_html=True)

st.title("🔧 Dashboard Financeiro: Ajuste e Visualização")

# --- 1. Carregamento Seguro ---
# Vamos ler o arquivo SEM pular linhas primeiro, pra você ver o que está acontecendo
file_path = 'dados.xlsx'

try:
    # Lê as primeiras 15 linhas cruas para calibração
    df_raw = pd.read_excel(file_path, engine='openpyxl', header=None, nrows=15)
except FileNotFoundError:
    st.error(f"🚨 Arquivo '{file_path}' não encontrado no GitHub. Verifique o nome.")
    st.stop()

# --- 2. A Ferramenta de Calibração (O Salvador da Pátria) ---
with st.expander("🛠️ CLIQUE AQUI SE OS DADOS ESTIVEREM ESTRANHOS (Calibrar Planilha)", expanded=True):
    st.write("Olhe a tabela abaixo. A linha destacada em **AMARELO** deve conter os títulos (Data, Valor, Status).")
    
    # Slider para escolher a linha de cabeçalho
    header_row_idx = st.number_input(
        "Em qual linha estão os títulos das colunas? (0 é a primeira linha)", 
        min_value=0, max_value=10, value=3, step=1
    )
    
    # Mostra visualmente qual linha está sendo escolhida
    def highlight_row(x):
        color = 'background-color: #f1c40f' if x.name == header_row_idx else ''
        return [color] * len(x)
        
    st.dataframe(df_raw.style.apply(highlight_row, axis=1), use_container_width=True)
    st.caption("Ajuste o número acima até a linha amarela ser a linha dos Títulos.")

# --- 3. Processamento Real ---
# Agora recarregamos o arquivo inteiro usando a linha que VOCÊ escolheu
@st.cache_data(show_spinner=False)
def load_final_data(row_idx):
    try:
        df = pd.read_excel(file_path, engine='openpyxl', header=row_idx)
    except:
        return pd.DataFrame()
    return df

df = load_final_data(header_row_idx)

if df.empty:
    st.warning("Aguardando calibração...")
    st.stop()

# --- 4. Mapeamento de Colunas (Sem erros de Key) ---
# Normaliza nomes
df.columns = df.columns.astype(str).str.lower().str.strip()

# Localiza colunas automaticamente
col_data = next((c for c in df.columns if 'vencimento' in c or 'data' in c), None)
col_valor = next((c for c in df.columns if 'valor' in c or 'original' in c), None)
col_pago = next((c for c in df.columns if 'pago' in c or 'quitado' in c), None)
col_status = next((c for c in df.columns if 'status' in c or 'situação' in c or 'situacao' in c), None)

if not col_data or not col_valor:
    st.error(f"⚠️ Não identifiquei colunas de DATA ou VALOR na linha {header_row_idx}. Mude o número da linha acima.")
    st.stop()

# Renomeia
rename_map = {col_data: 'Data', col_valor: 'Valor'}
if col_pago: rename_map[col_pago] = 'Pago'
if col_status: rename_map[col_status] = 'Status'
df = df.rename(columns=rename_map)

# --- 5. Limpeza de Dados (Versão Anti-Bomba) ---
def clean_money(x):
    if isinstance(x, str):
        clean = x.replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
        try: return float(clean)
        except: return 0.0
    return float(x) if isinstance(x, (int, float)) else 0.0

df['Valor'] = df['Valor'].apply(clean_money)

if 'Pago' not in df.columns: df['Pago'] = 0.0
else: df['Pago'] = df['Pago'].apply(clean_money).fillna(0)

# Define Status se não existir
if 'Status' not in df.columns:
    df['Status'] = df.apply(lambda row: 'Pago' if row['Pago'] >= row['Valor'] * 0.9 else 'Pendente', axis=1)

# Datas
df['Data'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
df = df.dropna(subset=['Data']).sort_values('Data')

# --- 6. O Dashboard Visual ---
st.markdown("---")

# KPIs
total = df['Valor'].sum()
pago = df['Pago'].sum()
aberto = total - pago

c1, c2, c3 = st.columns(3)
def card(col, label, val, color):
    col.markdown(f"""
    <div class="metric-card" style="border-left-color: {color}">
        <div class="metric-label">{label}</div>
        <div class="metric-value">R$ {val:,.2f}</div>
    </div>
    """, unsafe_allow_html=True)

card(c1, "Total Contratado", total, "#2980b9")
card(c2, "Total Pago", pago, "#27ae60")
card(c3, "Saldo Devedor", aberto, "#c0392b")

# Tabela Interativa
st.subheader("📋 Dados da Planilha (Verificados)")
st.dataframe(
    df[['Data', 'Valor', 'Pago', 'Status']].style.format({'Valor': 'R$ {:,.2f}', 'Pago': 'R$ {:,.2f}'}),
    use_container_width=True
)
