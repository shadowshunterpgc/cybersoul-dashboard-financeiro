import streamlit as st
import pandas as pd
from src.services.asset_service import AssetService
from src.entities.caixa_db import CaixaRepository
from src.entities.caixa_db import CaixaModel

# Initialize the asset service and caixa repository
asset_service = AssetService()
caixa_repo = CaixaRepository()

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
    Nesta seção, você pode gerenciar seus ativos financeiros e configurações do sistema.
    """)
    
    # Create tabs for different settings
    asset_tab, caixa_tab, notification_tab = st.tabs(["Ativos", "Caixa", "Notificações"])
    
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
    
    with caixa_tab:
        st.header("Configuração do Caixa")
        
        # Get current CAIXA value
        current_caixa = caixa_repo.get_latest_caixa()
        current_value = float(current_caixa.valor) if current_caixa else 0.0
        
        # Create tabs for different CAIXA operations
        add_tab, edit_tab, history_tab = st.tabs(["Adicionar", "Editar", "Histórico"])
        
        with add_tab:
            st.markdown("""
            ### Adicionar Novo Registro de Caixa
            Adicione um novo valor ao seu caixa. Este valor será somado ao valor total do seu portfólio.
            """)
            
            with st.form("add_caixa_form"):
                caixa_value = st.number_input(
                    "Valor do Caixa ($)",
                    min_value=0.0,
                    step=0.01,
                    format="%.2f"
                )
                
                submitted = st.form_submit_button("Adicionar Valor ao Caixa")
                
                if submitted:
                    caixa_repo.save_caixa(CaixaModel(valor=caixa_value))
                    st.success(f"Valor de ${caixa_value:.2f} adicionado ao Caixa")
                    st.rerun()
        
        with edit_tab:
            st.markdown("""
            ### Editar Valor do Caixa
            Atualize o valor atual do seu caixa.
            """)
            
            with st.form("edit_caixa_form"):
                caixa_value = st.number_input(
                    "Novo Valor do Caixa ($)",
                    value=current_value,
                    min_value=0.0,
                    step=0.01,
                    format="%.2f"
                )
                
                submitted = st.form_submit_button("Atualizar Valor do Caixa")
                
                if submitted:
                    caixa_repo.update_caixa(caixa_value)
                    st.success(f"Valor do Caixa atualizado para ${caixa_value:.2f}")
                    st.rerun()
            
            # Delete current CAIXA value
            if current_caixa:
                st.markdown("---")
                st.markdown("### Excluir Valor do Caixa")
                if st.button("Excluir Valor Atual", type="secondary"):
                    caixa_repo.delete_caixa(current_caixa.id)
                    st.success("Valor do Caixa excluído com sucesso")
                    st.rerun()
        
        with history_tab:
            st.markdown("""
            ### Histórico do Caixa
            Visualize o histórico de alterações do seu caixa.
            """)
            
            # Get all CAIXA records
            caixa_history = caixa_repo.get_all_caixa()
            
            if caixa_history:
                # Create a DataFrame for better visualization
                history_data = []
                for record in caixa_history:
                    history_data.append({
                        "Data": record.date.strftime("%d/%m/%Y %H:%M:%S"),
                        "Valor (R$)": f"{float(record.valor):.2f}"
                    })
                
                df = pd.DataFrame(history_data)
                st.dataframe(df, use_container_width=True)
                
                # Add option to clear all history
                if st.button("Limpar Todo o Histórico", type="secondary"):
                    if st.checkbox("Confirmar exclusão de todo o histórico"):
                        caixa_repo.clear_history()
                        st.success("Histórico do Caixa limpo com sucesso")
                        st.rerun()
            else:
                st.info("Nenhum registro no histórico do Caixa.")
    
    with notification_tab:
        st.header("Configurações de Notificações")
        st.info("Em desenvolvimento. Em breve você poderá configurar notificações para seus ativos.") 