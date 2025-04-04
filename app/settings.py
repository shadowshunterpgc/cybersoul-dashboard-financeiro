import streamlit as st
import pandas as pd
from src.services.asset_service import AssetService

# Initialize the asset service
asset_service = AssetService()

# State to track which asset is being edited
if 'edit_symbol' not in st.session_state:
    st.session_state['edit_symbol'] = None

def settings_page():
    """Display the settings page with asset registration form."""
    st.title("Configurações")
    
    # Initialize 'edit_symbol' in session state if not present
    if 'edit_symbol' not in st.session_state:
        st.session_state['edit_symbol'] = None
    
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
            
            # Add a column for edit and delete buttons
            if 'symbol' in df.columns:
                # Create a unique key for each row
                for i, row in df.iterrows():
                    col1, col2, col3 = st.columns([4, 1, 1])
                    with col1:
                        st.dataframe(pd.DataFrame([row]), use_container_width=True, hide_index=True)
                    with col2:
                        if st.button("✏️", key=f"edit_{row['symbol']}"):
                            st.session_state['edit_symbol'] = row['symbol']
                    with col3:
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
        st.subheader("Adicionar ou Editar Ativo")
        
        # Check if an asset is being edited
        if st.session_state['edit_symbol']:
            asset_to_edit = next((asset for asset in assets if asset['symbol'] == st.session_state['edit_symbol']), None)
            if asset_to_edit:
                symbol = asset_to_edit['symbol']
                name = asset_to_edit['name']
                asset_type = asset_to_edit['type']
                shares = asset_to_edit['shares']
                purchase_price = asset_to_edit['purchase_price']
                purchase_date = pd.to_datetime(asset_to_edit['purchase_date'])
                notes = asset_to_edit['notes']
            else:
                st.session_state['edit_symbol'] = None
                symbol = name = asset_type = notes = ""
                shares = purchase_price = 0.0
                purchase_date = pd.to_datetime("today")
        else:
            symbol = name = asset_type = notes = ""
            shares = purchase_price = 0.0
            purchase_date = pd.to_datetime("today")
        
        with st.form("asset_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                symbol_input = st.text_input("Símbolo (ex: AAPL)", value=symbol, placeholder="AAPL", disabled=bool(st.session_state['edit_symbol']))
                name_input = st.text_input("Nome do Ativo", value=name, placeholder="Apple Inc.")
                asset_type_input = st.selectbox(
                    "Tipo de Ativo",
                    ["Ação", "ETF", "Criptomoeda", "Commodity", "Outro"],
                    index=["Ação", "ETF", "Criptomoeda", "Commodity", "Outro"].index(asset_type) if asset_type else 0
                )
            
            with col2:
                shares_input = st.number_input("Quantidade", value=shares, min_value=0.0, step=0.01, format="%.4f")
                purchase_price_input = st.number_input("Preço de Compra ($)", value=purchase_price, min_value=0.0, step=0.01, format="%.2f")
                purchase_date_input = st.date_input("Data de Compra", value=purchase_date)
            
            notes_input = st.text_area("Observações", value=notes, placeholder="Adicione notas sobre este ativo...")
            
            submitted = st.form_submit_button("Salvar Ativo")
            
            if submitted:
                if symbol_input and name_input and shares_input > 0:
                    updated_asset = {
                        "symbol": symbol_input.upper(),
                        "name": name_input,
                        "type": asset_type_input,
                        "shares": shares_input,
                        "purchase_price": purchase_price_input,
                        "purchase_date": purchase_date_input.strftime("%Y-%m-%d"),
                        "notes": notes_input
                    }
                    
                    if st.session_state['edit_symbol']:
                        success, message = asset_service.update_asset(st.session_state['edit_symbol'], updated_asset)
                        st.session_state['edit_symbol'] = None
                    else:
                        success, message = asset_service.add_asset(updated_asset)
                    
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