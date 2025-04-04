import streamlit as st
import pandas as pd
from src.services.asset_service import AssetService

# Initialize the asset service
asset_service = AssetService()

def settings_page():
    """Display the settings page with asset registration form."""
    st.title("Configurações")
    
    # Explanation for the settings page
    st.markdown("""
    ### Bem-vindo à Tela de Configurações
    Nesta seção, você pode gerenciar seus ativos financeiros. Use o formulário abaixo para adicionar novos ativos ao seu portfólio. 
    Você também pode visualizar, editar ou excluir ativos existentes.
    """)
    
    # Create tabs for different settings
    asset_tab, notification_tab = st.tabs(["Ativos", "Notificações"])
    
    with asset_tab:
        st.header("Cadastro de Ativos")
        
        # Load existing assets
        assets = asset_service.load_assets()
        
        # Display existing assets in a table
        if assets:
            st.subheader("Ativos Cadastrados")
            df = pd.DataFrame(assets)
            
            # Add a column for delete buttons
            if 'symbol' in df.columns:
                # Create a unique key for each row
                for i, row in df.iterrows():
                    col1, col2 = st.columns([5, 1])
                    with col1:
                        st.dataframe(pd.DataFrame([row]), use_container_width=True, hide_index=True)
                    with col2:
                        if st.button("🗑️", key=f"delete_{row['symbol']}"):
                            success, message = asset_service.delete_asset(row['symbol'])
                            if success:
                                st.success(message)
                                st.rerun()
                            else:
                                st.error(message)
                # Explanation for asset deletion
                st.markdown("""
                **Nota:** Clique no ícone de lixeira para excluir um ativo específico. Esta ação é irreversível.
                """)
            else:
                st.dataframe(df, use_container_width=True)
            
            # Add delete all functionality
            if st.button("Limpar Todos os Ativos"):
                if st.checkbox("Confirmar exclusão de todos os ativos"):
                    success, message = asset_service.clear_assets()
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
        else:
            st.info("Nenhum ativo cadastrado ainda.")
        
        # Asset registration form
        st.subheader("Adicionar Novo Ativo")
        
        with st.form("asset_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                symbol = st.text_input("Símbolo (ex: AAPL)", placeholder="AAPL")
                name = st.text_input("Nome do Ativo", placeholder="Apple Inc.")
                asset_type = st.selectbox(
                    "Tipo de Ativo",
                    ["Ação", "ETF", "Criptomoeda", "Commodity", "Outro"]
                )
            
            with col2:
                shares = st.number_input("Quantidade", min_value=0.0, step=0.01, format="%.4f")
                purchase_price = st.number_input("Preço de Compra ($)", min_value=0.0, step=0.01, format="%.2f")
                purchase_date = st.date_input("Data de Compra")
            
            notes = st.text_area("Observações", placeholder="Adicione notas sobre este ativo...")
            
            submitted = st.form_submit_button("Adicionar Ativo")
            
            if submitted:
                if symbol and name and shares > 0:
                    new_asset = {
                        "symbol": symbol.upper(),
                        "name": name,
                        "type": asset_type,
                        "shares": shares,
                        "purchase_price": purchase_price,
                        "purchase_date": purchase_date.strftime("%Y-%m-%d"),
                        "notes": notes
                    }
                    
                    success, message = asset_service.add_asset(new_asset)
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.warning(message)
                else:
                    st.error("Por favor, preencha todos os campos obrigatórios (Símbolo, Nome e Quantidade).")
    
    with notification_tab:
        st.header("Configurações de Notificações")
        st.info("Em desenvolvimento. Em breve você poderá configurar notificações para seus ativos.") 