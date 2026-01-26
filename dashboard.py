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

# --- Estilo CSS Premium (Mantendo o seu estilo) ---
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
    # Tenta ler o Excel ou CSV (garante que funciona com o que você subir)
    file_path = 'dados.xlsx' 
    try:
        df = pd.read_excel(file_path, engine='openpyxl')
    except:
        try:
            # Fallback para CSV se necessário
            df = pd.read_csv('dados.csv') # Ajuste se subir como csv
        except:
            st.error("Erro ao ler dados. Verifique se 'dados.xlsx' está no GitHub.")
            st.stop()

    # 1. Limpeza de Nomes de Coluna
    df.columns = df.columns.astype(str).str.strip().str.lower()

    # 2. Mapeamento Automático (Detecta a nova coluna 'valor original')
    col_data = next((c for c in df.columns if 'vencimento' in c or 'data' in c), 'Data')
    
    # A coluna 'Valor da Parcela ' (com ajuste) é o que deve ser pago
    col_valor_ajustado = next((c for c in df.columns if 'valor da parcela' in c), 'Valor Ajustado')
    
    # A coluna 'Valor Original' (sem ajuste) é para exibição
    col_valor_base = next((c for c in df.columns if 'valor original' in c), 'Valor Base')
    
    col_pago = next((c for c in df.columns if 'pago' in c or 'quitado' in c), 'Pago')
    col_status = next((c for c in df.columns if 'status' in c), 'Status')
    col_hist = next((c for c in df.columns if 'hist' in c or 'obs' in c), 'Historico')

    # Renomeia
    df = df.rename(columns={
        col_data: 'Data', 
        col_valor_ajustado: 'Valor Ajustado',
        col_valor_base: 'Valor Base',
        col_pago: 'Pago', 
        col_status: 'Status',
        col_hist: 'Historico'
    })

    # 3. Tratamento Numérico
    def to_float(x):
        if isinstance(x, str):
            x = x.replace('R$', '').replace('.', '').replace(',', '.')
        return pd.to_numeric(x, errors='coerce')

    df['Valor Ajustado'] = df['Valor Ajustado'].apply(to_float).fillna(0)
    df['Valor Base'] = df['Valor Base'].apply(to_float).fillna(0)
    df['Pago'] = df['Pago'].apply(to_float).fillna(0)
    
    # Datas
    df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
    df = df.dropna(subset=['Data']).sort_values('Data')

    if 'Historico' not in df.columns: df['Historico'] = '-'
    else: df['Historico'] = df['Historico'].fillna('-')

    return df

df = load_data()

# --- Cálculos de Negócio ---
hoje = pd.Timestamp.now().normalize()

# 1. Total Contratado (FIXO CONFORME SEU PEDIDO)
# Mesmo que a soma dê diferente, mostraremos esse valor oficial.
total_contratado = 1362800.00 

# 2. Total Já Pago
total_pago = df['Pago'].sum()

# 3. Saldo da Parcela (Baseado no valor AJUSTADO, pois é o que se paga de fato)
df['Saldo_Parcela'] = df['Valor Ajustado'] - df['Pago']
df['Saldo_Parcela'] = df['Saldo_Parcela'].apply(lambda x: x if x > 0 else 0)

# Separação: Pendente vs Futuro
total_pendente_atraso = df[df['Data'] < hoje]['Saldo_Parcela'].sum()
total_a_faturar = df[df['Data'] >= hoje]['Saldo_Parcela'].sum()

# Progresso (Pago sobre o Total Contratado Fixo)
progresso = (total_pago / total_contratado * 100)

# --- DASHBOARD ---
st.title("💎 Dashboard Executivo de Dívida")
st.markdown(f"**Posição Atualizada em:** {hoje.strftime('%d/%m/%Y')}")
st.divider()

# Linha 1: KPIs
c1, c2, c3, c4 = st.columns(4)

def kpi(col, label, value, sub, border_class):
    col.markdown(f"""
    <div class="metric-card {border_class}">
        <div class="metric-label">{label}</div>
        <div class="metric-value">R$ {value:,.2f}</div>
        <div class="metric-sub">{sub}</div>
    </div>
    """, unsafe_allow_html=True)

kpi(c1, "Total Contratado", total_contratado, "Valor Original do Contrato (Base)", "border-blue")
kpi(c2, "Total Quitado", total_pago, f"{progresso:.1f}% amortizado do contrato", "border-green")
kpi(c3, "Pendente / Vencido / Atrasado", total_pendente_atraso, "Atenção Imediata", "border-red")
kpi(c4, "A Faturar (Pré-Correção)", total_a_faturar, "Fluxo de Caixa Futuro", "border-yellow")

st.write("")

# Linha 2: Gráficos
col_g1, col_g2 = st.columns([2, 1])

with col_g1:
    st.subheader("📅 Cronograma de Pagamentos")
    fig = go.Figure()
    
    # Barra Verde: Parte Paga
    fig.add_trace(go.Bar(x=df['Data'], y=df['Pago'], name='Valor Quitado', marker_color='#27ae60'))
    
    # Barra Cinza/Vermelha: Parte que Falta
    colors = ['#c0392b' if d < hoje else '#95a5a6' for d in df['Data']]
    fig.add_trace(go.Bar(x=df['Data'], y=df['Saldo_Parcela'], name='Saldo em Aberto', marker_color=colors))
    
    fig.update_layout(
        barmode='stack', 
        template='plotly_white', 
        height=400,
        legend=dict(orientation="h", y=1.1),
        xaxis_title="Vencimento",
        yaxis_title="Valor (R$)"
    )
    st.plotly_chart(fig, use_container_width=True)

with col_g2:
    st.subheader("📊 Composição do Saldo")
    labels = ['Quitado', 'A Faturar', 'Pendente']
    values = [total_pago, total_a_faturar, total_pendente_atraso]
    colors = ['#27ae60', '#f1c40f', '#c0392b']
    
    fig_pie = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.6, marker_colors=colors)])
    fig_pie.update_layout(height=400, showlegend=True, legend=dict(orientation="h", y=-0.1))
    st.plotly_chart(fig_pie, use_container_width=True)

# Linha 3: Tabela Detalhada
st.divider()
st.subheader("📋 Detalhamento Analítico")

# Tabela
df_show = df.copy()
df_show['Vencimento'] = df_show['Data'].dt.strftime('%d/%m/%Y')
df_show['Valor Base'] = df_show['Valor Base'].apply(lambda x: f"R$ {x:,.2f}") # Coluna Nova
df_show['Valor Ajustado (Devido)'] = df_show['Valor Ajustado'].apply(lambda x: f"R$ {x:,.2f}")
df_show['Valor Pago'] = df_show['Pago'].apply(lambda x: f"R$ {x:,.2f}")
df_show['Saldo Aberto'] = df_show['Saldo_Parcela'].apply(lambda x: f"R$ {x:,.2f}")

cols_order = ['Vencimento', 'Valor Base', 'Valor Ajustado (Devido)', 'Valor Pago', 'Saldo Aberto', 'Status', 'Historico']

st.dataframe(
    df_show[cols_order],
    use_container_width=True,
    hide_index=True,
    column_config={
        "Historico": st.column_config.TextColumn("Histórico", width="large"),
        "Status": st.column_config.Column("Status", width="small"),
        "Valor Base": st.column_config.Column("Vlr Original (Base)", help="Valor antes da correção IPCA+1%")
    }
)
