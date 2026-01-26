import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# --- Configuração da Página ---
st.set_page_config(
    page_title="Gestão Financeira: Syssant",
    layout="wide",
    page_icon="💎"
)

# --- Estilo CSS Premium ---
st.markdown("""
<style>
    .metric-card {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        border-left: 6px solid #2c3e50;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 10px;
    }
    .metric-label {
        font-size: 14px;
        color: #7f8fa6;
        font-weight: bold;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .metric-value {
        font-size: 28px;
        color: #2c3e50;
        font-weight: 800;
        margin-top: 5px;
    }
    .metric-sub {
        font-size: 12px;
        color: #95a5a6;
        margin-top: 5px;
    }
    /* Cores das Bordas dos Cards */
    .border-blue { border-left-color: #3498db !important; }
    .border-green { border-left-color: #27ae60 !important; }
    .border-red { border-left-color: #c0392b !important; }
    .border-yellow { border-left-color: #f1c40f !important; }
</style>
""", unsafe_allow_html=True)

# --- Função de Carregamento Inteligente ---
@st.cache_data
def load_data():
    # Nome do arquivo que você vai subir (Excel ou CSV)
    # Se for usar o CSV que você me mandou, mude para .csv
    # Se for o Excel com as abas limpas, mantenha .xlsx
    file_path = 'dados.xlsx' 
    
    try:
        # Tenta ler como Excel primeiro (padrão)
        df = pd.read_excel(file_path, engine='openpyxl')
    except:
        try:
            # Se falhar, tenta ler como CSV (caso você suba o CSV direto)
            df = pd.read_csv('Confissão de Divida - Syssant.xlsx - Parcelas e Status .csv')
        except Exception as e:
            st.error(f"Erro ao ler arquivo. Verifique se 'dados.xlsx' está no GitHub.")
            st.stop()

    # 1. Limpeza de Nomes de Coluna (Remove espaços extras que vi no seu arquivo)
    # Ex: 'Vencimento ' vira 'vencimento'
    df.columns = df.columns.astype(str).str.strip().str.lower()

    # 2. Mapeamento Automático
    col_data = next((c for c in df.columns if 'vencimento' in c or 'data' in c), 'data')
    col_valor = next((c for c in df.columns if 'valor' in c and 'pago' not in c), 'valor')
    col_pago = next((c for c in df.columns if 'pago' in c or 'quitado' in c), 'valor pago')
    col_status = next((c for c in df.columns if 'status' in c), 'status')
    col_hist = next((c for c in df.columns if 'hist' in c or 'obs' in c), 'historico')

    # Renomeia para padronizar
    df = df.rename(columns={
        col_data: 'Data', 
        col_valor: 'Valor', 
        col_pago: 'Pago', 
        col_status: 'Status',
        col_hist: 'Historico'
    })

    # 3. Tratamento de Tipos
    # Garante que é tudo número
    def to_float(x):
        if isinstance(x, str):
            x = x.replace('R$', '').replace('.', '').replace(',', '.')
        return pd.to_numeric(x, errors='coerce')

    df['Valor'] = df['Valor'].apply(to_float).fillna(0)
    df['Pago'] = df['Pago'].apply(to_float).fillna(0)
    
    # Datas
    df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
    df = df.dropna(subset=['Data']).sort_values('Data')

    # Se não tiver histórico, preenche com traço
    if 'Historico' not in df.columns:
        df['Historico'] = '-'
    else:
        df['Historico'] = df['Historico'].fillna('-')

    return df

df = load_data()

# --- Cálculos de Negócio (O que você pediu) ---
hoje = pd.Timestamp.now().normalize() # Data de hoje sem hora

# 1. Total Contratado (Valor Original da Dívida)
total_contratado = df['Valor'].sum()

# 2. Total Já Pago (Efetivado)
total_pago = df['Pago'].sum()

# 3. Cálculo do que falta
df['Saldo_Parcela'] = df['Valor'] - df['Pago']
# Corrige negativos (se pagou a mais por juros, saldo é 0)
df['Saldo_Parcela'] = df['Saldo_Parcela'].apply(lambda x: x if x > 0 else 0)

# Separação: Pendente (Vencido) vs A Faturar (Futuro)
# Pendente = Saldo aberto com Data <= Hoje
total_pendente_atraso = df[df['Data'] < hoje]['Saldo_Parcela'].sum()

# A Faturar = Saldo aberto com Data >= Hoje
total_a_faturar = df[df['Data'] >= hoje]['Saldo_Parcela'].sum()

# Saldo Devedor Total (Soma dos dois)
saldo_devedor_total = total_pendente_atraso + total_a_faturar

# Progresso
progresso = (total_pago / total_contratado * 100) if total_contratado > 0 else 0

# --- DASHBOARD ---

st.title("💎 Dashboard Executivo de Dívida")
st.markdown(f"**Posição Atualizada em:** {hoje.strftime('%d/%m/%Y')}")
st.divider()

# Linha 1: KPIs Principais
c1, c2, c3, c4 = st.columns(4)

def kpi(col, label, value, sub, border_class):
    col.markdown(f"""
    <div class="metric-card {border_class}">
        <div class="metric-label">{label}</div>
        <div class="metric-value">R$ {value:,.2f}</div>
        <div class="metric-sub">{sub}</div>
    </div>
    """, unsafe_allow_html=True)

kpi(c1, "Total Contratado", total_contratado, "Valor Original do Contrato", "border-blue")
kpi(c2, "Total Quitado", total_pago, f"{progresso:.1f}% do total amortizado", "border-green")
kpi(c3, "Pendente / Vencido", total_pendente_atraso, "Atenção Imediata", "border-red")
kpi(c4, "A Faturar (Futuro)", total_a_faturar, "Fluxo de Caixa Futuro", "border-yellow")

st.write("")

# Linha 2: Gráficos
col_g1, col_g2 = st.columns([2, 1])

with col_g1:
    st.subheader("📅 Cronograma de Pagamentos")
    
    # Prepara dados pro gráfico
    # Vamos criar duas barras: Uma para o que foi pago, outra para o que falta (empilhadas)
    fig = go.Figure()
    
    # Barra Verde: Parte Paga
    fig.add_trace(go.Bar(
        x=df['Data'], 
        y=df['Pago'], 
        name='Valor Quitado', 
        marker_color='#27ae60'
    ))
    
    # Barra Cinza/Vermelha: Parte que Falta
    # Se a data for passado, pinta de vermelho (Atrasado). Se futuro, cinza (A vencer)
    colors = ['#c0392b' if d < hoje else '#95a5a6' for d in df['Data']]
    
    fig.add_trace(go.Bar(
        x=df['Data'], 
        y=df['Saldo_Parcela'], 
        name='Saldo em Aberto', 
        marker_color=colors
    ))
    
    fig.update_layout(
        barmode='stack', # Empilha pra mostrar o total da parcela
        template='plotly_white', 
        height=400,
        legend=dict(orientation="h", y=1.1),
        xaxis_title="Vencimento",
        yaxis_title="Valor (R$)"
    )
    st.plotly_chart(fig, use_container_width=True)

with col_g2:
    st.subheader("📊 Composição do Saldo")
    # Gráfico de Rosca comparando Pago vs Futuro vs Atrasado
    labels = ['Quitado', 'A Faturar (Futuro)', 'Pendente (Vencido)']
    values = [total_pago, total_a_faturar, total_pendente_atraso]
    colors = ['#27ae60', '#f1c40f', '#c0392b']
    
    fig_pie = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.6, marker_colors=colors)])
    fig_pie.update_layout(height=400, showlegend=True, legend=dict(orientation="h", y=-0.1))
    st.plotly_chart(fig_pie, use_container_width=True)

# Linha 3: Tabela Detalhada
st.divider()
st.subheader("📋 Detalhamento Analítico")
st.info("💡 Passe o mouse sobre a tabela para ver o histórico completo.")

# Prepara tabela bonita
df_show = df.copy()
df_show['Vencimento'] = df_show['Data'].dt.strftime('%d/%m/%Y')
df_show['Valor Original'] = df_show['Valor'].apply(lambda x: f"R$ {x:,.2f}")
df_show['Valor Pago'] = df_show['Pago'].apply(lambda x: f"R$ {x:,.2f}")
df_show['Saldo Aberto'] = df_show['Saldo_Parcela'].apply(lambda x: f"R$ {x:,.2f}")

# Ordena colunas
cols_order = ['Vencimento', 'Valor Original', 'Valor Pago', 'Saldo Aberto', 'Status', 'Historico']

st.dataframe(
    df_show[cols_order],
    use_container_width=True,
    hide_index=True,
    column_config={
        "Historico": st.column_config.TextColumn(
            "Histórico de Pagamentos",
            width="large",
            help="Detalhes de pagamentos parciais e datas"
        ),
        "Status": st.column_config.Column(
            "Status",
            width="small"
        )
    }
)
