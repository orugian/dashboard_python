import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# --- Configuração da Página ---
st.set_page_config(
    page_title="Gestão de Dívida: Syssant",
    layout="wide",
    page_icon="📊",
    initial_sidebar_state="expanded" # Barra lateral aberta para filtros
)

# --- CSS (Design Limpo e Profissional) ---
st.markdown("""
<style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    h1, h2, h3 { color: #2c3e50; font-family: 'Segoe UI', sans-serif; }
</style>
""", unsafe_allow_html=True)

# --- Carregamento e Inteligência de Dados ---
@st.cache_data
def get_data():
    file_path = 'dados.xlsx' # Mantivemos o nome simples pra não dar erro
    
    try:
        # Tenta ler o Excel. skiprows=3 assume que o cabeçalho está na linha 4
        df = pd.read_excel(file_path, engine='openpyxl', skiprows=3)
    except FileNotFoundError:
        st.error(f"🚨 Arquivo '{file_path}' não encontrado. Verifique o GitHub.")
        st.stop()
    except Exception as e:
        st.error(f"Erro ao ler Excel: {e}")
        st.stop()

    # --- Tratamento de Colunas (O Pulo do Gato para não dar Erro) ---
    # Normaliza nomes das colunas (tudo minusculo)
    df.columns = df.columns.astype(str).str.lower().str.strip()
    
    # Procura colunas chaves por palavras-chave
    col_data = next((c for c in df.columns if 'vencimento' in c or 'data' in c), None)
    col_valor = next((c for c in df.columns if 'valor' in c or 'original' in c), None)
    col_pago = next((c for c in df.columns if 'pago' in c or 'quitado' in c), None)
    col_status = next((c for c in df.columns if 'status' in c or 'situação' in c or 'situacao' in c), None)

    # Se não achar a coluna Data ou Valor, não tem como trabalhar
    if not col_data or not col_valor:
        st.error("⚠️ Não consegui identificar as colunas de 'Data' ou 'Valor' no Excel. Verifique os nomes.")
        st.write("Colunas encontradas:", df.columns.tolist())
        st.stop()

    # Renomeia para o padrão do sistema
    rename_map = {col_data: 'Data', col_valor: 'Valor'}
    if col_pago: rename_map[col_pago] = 'Pago'
    if col_status: rename_map[col_status] = 'Status'
    
    df = df.rename(columns=rename_map)

    # --- Limpeza de Valores ---
    def clean_money(x):
        if isinstance(x, str):
            clean = x.replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
            try: return float(clean)
            except: return 0.0
        return float(x) if isinstance(x, (int, float)) else 0.0

    df['Valor'] = df['Valor'].apply(clean_money)
    
    # Se não existe coluna 'Pago', cria zerada
    if 'Pago' not in df.columns:
        df['Pago'] = 0.0
    else:
        df['Pago'] = df['Pago'].apply(clean_money).fillna(0)

    # Se não existe coluna 'Status', cria baseada no pagamento (Inteligência Artificial de Bolso)
    if 'Status' not in df.columns:
        # Se pagou algo, considera Pago, senão Pendente
        df['Status'] = df.apply(lambda row: 'Pago' if row['Pago'] >= row['Valor'] * 0.9 else 'Pendente', axis=1)
    else:
        # Garante que status vazio seja 'Pendente'
        df['Status'] = df['Status'].fillna('Pendente').astype(str)

    # Datas
    df['Data'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
    df = df.dropna(subset=['Data']).sort_values('Data')

    return df

# Carrega os dados
df_full = get_data()

# --- BARRA LATERAL (Filtros Interativos) ---
st.sidebar.header("🔍 Filtros")

# Filtro de Status
status_options = df_full['Status'].unique()
selected_status = st.sidebar.multiselect("Status da Parcela", options=status_options, default=status_options)

# Filtro de Data (Ano)
years = sorted(df_full['Data'].dt.year.unique())
selected_years = st.sidebar.multiselect("Ano de Vencimento", options=years, default=years)

# Aplica Filtros
df = df_full[
    (df_full['Status'].isin(selected_status)) & 
    (df_full['Data'].dt.year.isin(selected_years))
]

# --- KPIs Principais ---
st.title("📊 Painel de Controle Financeiro")

total_divida = df_full['Valor'].sum() # Valor total independente do filtro (para referência)
total_filtrado = df['Valor'].sum()
pago_filtrado = df['Pago'].sum()
saldo_aberto = total_filtrado - pago_filtrado
qtd_parcelas = len(df)

# Métricas no topo
c1, c2, c3, c4 = st.columns(4)
c1.metric("Saldo em Aberto (Filtro)", f"R$ {saldo_aberto:,.2f}", delta_color="inverse")
c2.metric("Total Quitado (Filtro)", f"R$ {pago_filtrado:,.2f}")
c3.metric("Valor Original (Filtro)", f"R$ {total_filtrado:,.2f}")
c4.metric("Parcelas Listadas", f"{qtd_parcelas}")

st.divider()

# --- VISUALIZAÇÃO GRÁFICA ---
col_left, col_right = st.columns([2, 1])

with col_left:
    st.subheader("📈 Evolução do Saldo Devedor")
    # Calcula o acumulado para mostrar a dívida caindo ou subindo
    df_chart = df.sort_values('Data').copy()
    df_chart['Acumulado'] = df_chart['Valor'].cumsum()
    
    # Gráfico de Linha x Barras
    fig_evolucao = go.Figure()
    fig_evolucao.add_trace(go.Bar(
        x=df_chart['Data'], y=df_chart['Valor'], name='Valor da Parcela', marker_color='#bdc3c7', opacity=0.6
    ))
    fig_evolucao.add_trace(go.Scatter(
        x=df_chart['Data'], y=df_chart['Pago'], mode='markers', name='Pagamentos Realizados', marker=dict(color='green', size=8)
    ))
    fig_evolucao.update_layout(template="plotly_white", height=400, xaxis_title="Vencimento")
    st.plotly_chart(fig_evolucao, use_container_width=True)

with col_right:
    st.subheader("Situação Atual")
    # Gráfico de Rosca
    fig_pie = px.pie(df, names='Status', values='Valor', hole=0.5, color='Status',
                     color_discrete_map={'Pago': '#2ecc71', 'Pendente': '#e74c3c', 'Atrasado': '#f1c40f'})
    fig_pie.update_layout(height=400, legend=dict(orientation="h", y=-0.1))
    st.plotly_chart(fig_pie, use_container_width=True)

# --- TABELA DETALHADA (O que você pediu) ---
st.subheader("📋 Detalhamento das Parcelas")
st.caption("Use os filtros na barra lateral para ver apenas o que está pendente ou pago.")

# Formata para exibir bonito (R$) mas mantém o dado real
df_display = df.copy()
df_display['Data'] = df_display['Data'].dt.strftime('%d/%m/%Y')
df_display['Valor'] = df_display['Valor'].apply(lambda x: f"R$ {x:,.2f}")
df_display['Pago'] = df_display['Pago'].apply(lambda x: f"R$ {x:,.2f}")

# Mostra TODAS as colunas para você ver o que tem lá
st.dataframe(
    df_display, 
    use_container_width=True, 
    hide_index=True,
    column_config={
        "Status": st.column_config.TextColumn(
            "Status",
            help="Situação atual da parcela",
            validate="^(Pago|Pendente)$"
        )
    }
)
