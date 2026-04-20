import streamlit as st
import pandas as pd
import numpy as np
from skopt import Optimizer
from skopt.space import Real, Integer, Categorical

#####################################################################################################################################
# --- 1. INITIALIZATION (Must be at the top) ---
if 'exp_data' not in st.session_state:
    # We create an empty dataframe with the correct columns
    st.session_state.exp_data = pd.DataFrame(
        columns=["Run", "Temp", "Time", "Catalyst", "Yield (%)"]
    )
#####################################################################################################################################
# --- OPTIMIZATION ENGINE ---
def get_next_suggestion(existing_data, temp_range, time_range, catalysts):
    # Define the Search Space
    search_space = [
        Integer(temp_range[0], temp_range[1], name='Temp'),
        Integer(time_range[0], time_range[1], name='Time'),
        Categorical(catalysts, name='Catalyst')
    ]
    
    opt = Optimizer(search_space, base_estimator="GP", acq_func="EI") # Expected Improvement

    if not existing_data.empty:
        # Tell the optimizer what we already know
        # Note: skopt minimizes, so we pass (-Yield) to maximize yield
        X = existing_data[['Temp', 'Time', 'Catalyst']].values.tolist()
        y = (-existing_data['Yield (%)']).values.tolist()
        opt.tell(X, y)

    # Ask for the next best point
    next_x = opt.ask()
    return next_x
#####################################################################################################################################


# Page Config
st.set_page_config(page_title="OLED-Flow-Stack", layout="wide")

# Title and Description
st.title("💡 OLED-Flow-Stack")
st.markdown("""
*Open-source orchestrator for autonomous OLED material synthesis.*
Connect your flow hardware to Bayesian Optimization.
""")
######################################################################################################################################

# --- SIDEBAR: REACTOR CONFIGURATION ---
st.sidebar.header("🛠️ Reactor Settings")
reactor_volume = st.sidebar.number_input("Reactor Volume (mL)", value=10.0, step=0.5)
max_pressure = st.sidebar.slider("Max System Pressure (bar)", 0, 100, 20)
######################################################################################################################################

# --- MAIN INTERFACE: TABS ---
tab1, tab2, tab3 = st.tabs(["🧪 Design Experiment", "📈 Live Optimization", "📊 Results Analysis"])
######################################################################################################################################
with tab1:
    st.subheader("Define Chemical Space")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Continuous Variables**")
        temp_range = st.slider("Temperature Range (°C)", 25, 250, (60, 120))
        res_time = st.slider("Residence Time (min)", 1, 60, (5, 20))
        
    with col2:
        st.write("**Categorical Variables**")
        catalysts = st.multiselect("Select Catalysts", 
                                   ["Pd(PPh3)4", "Pd2(dba)3", "XPhos Pd G3", "Ni(cod)2"], 
                                   default=["Pd(PPh3)4"])
        solvents = st.multiselect("Select Solvents", 
                                  ["Toluene", "THF", "DMF", "Dioxane"], 
                                  default=["Toluene"])

    st.divider()
    st.subheader("Stoichiometry Calculator")
    target_conc = st.number_input("Target Concentration (M)", value=0.1, step=0.01)
    st.info(f"💡 Based on a {reactor_volume}mL volume, the flow rates will be auto-calculated for the optimizer.")
######################################################################################################################################
# --- TAB 2  ---
with tab2:
    st.subheader("Active Run Control")
    
    # Editable Data Entry
    st.write("Enter results from the lab below:")
    edited_df = st.data_editor(
        st.session_state.exp_data, 
        num_rows="dynamic",
        column_config={
            "Yield (%)": st.column_config.NumberColumn(format="%d%%", min_value=0, max_value=100)
        }
    )
    st.session_state.exp_data = edited_df

    if st.button("🤖 Suggest Next Experiment"):
        if catalysts: # Ensure user has selected catalysts in Tab 1
            suggestion = get_next_suggestion(
                st.session_state.exp_data, 
                temp_range, 
                res_time, 
                catalysts
            )
            
            st.success(f"**Recommended Parameters:**")
            col_a, col_b, col_c = st.columns(3)
            col_a.metric("Temperature", f"{suggestion[0]}°C")
            col_b.metric("Res. Time", f"{suggestion[1]} min")
            col_c.metric("Catalyst", suggestion[2])
            
            st.info("💡 Run this experiment and enter the yield above to update the model.")
        else:
            st.error("Please select at least one catalyst in the 'Design' tab first.")
######################################################################################################################################
with tab3:
    st.subheader("Performance Overview")
    if not st.session_state.exp_data.empty:
        # Dummy chart for visualization
        chart_data = pd.DataFrame(np.random.randn(20, 2), columns=['Yield', 'Purity'])
        st.scatter_chart(chart_data)
    else:
        st.info("No data available yet. Complete a run in the 'Live Optimization' tab.")
######################################################################################################################################
# Footer
st.markdown("---")
st.caption("OLED-Flow-Stack | Open Source Research Project | v0.1.0-alpha")

