import streamlit as st
import pandas as pd
import numpy as np

# Page Config
st.set_page_config(page_title="OLED-Flow-Stack", layout="wide")

# Title and Description
st.title("💡 OLED-Flow-Stack")
st.markdown("""
*Open-source orchestrator for autonomous OLED material synthesis.*
Connect your flow hardware to Bayesian Optimization.
""")

# --- SIDEBAR: REACTOR CONFIGURATION ---
st.sidebar.header("🛠️ Reactor Settings")
reactor_volume = st.sidebar.number_input("Reactor Volume (mL)", value=10.0, step=0.5)
max_pressure = st.sidebar.slider("Max System Pressure (bar)", 0, 100, 20)

# --- MAIN INTERFACE: TABS ---
tab1, tab2, tab3 = st.tabs(["🧪 Design Experiment", "📈 Live Optimization", "📊 Results Analysis"])

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

with tab2:
    st.subheader("Active Run Control")
    
    # Mock dataframe for current experiments
    if 'exp_data' not in st.session_state:
        st.session_state.exp_data = pd.DataFrame(columns=["Run", "Temp", "Time", "Catalyst", "Yield (%)", "PL Peak (nm)"])

    st.table(st.session_state.exp_data)
    
    if st.button("🤖 Suggest Next Experiment"):
        st.warning("Optimization Engine: Ready. (Awaiting Bayesian logic implementation)")
        # Placeholder for suggestion logic
        new_row = {"Run": len(st.session_state.exp_data)+1, "Temp": 115, "Time": 12, "Catalyst": catalysts[0], "Yield (%)": 0, "PL Peak (nm)": 0}
        st.success(f"Recommended Run: Temp {new_row['Temp']}°C | Time {new_row['Time']}min")

with tab3:
    st.subheader("Performance Overview")
    if not st.session_state.exp_data.empty:
        # Dummy chart for visualization
        chart_data = pd.DataFrame(np.random.randn(20, 2), columns=['Yield', 'Purity'])
        st.scatter_chart(chart_data)
    else:
        st.info("No data available yet. Complete a run in the 'Live Optimization' tab.")

# Footer
st.markdown("---")
st.caption("OLED-Flow-Stack | Open Source Research Project | v0.1.0-alpha")

