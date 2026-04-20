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
    # 1. CLEAN DATA: Only use rows that have a valid Yield number
    # This prevents the "NoneType" error
    clean_data = existing_data.dropna(subset=['Yield (%)'])
    
    # Define the Search Space
    search_space = [
        Integer(temp_range[0], temp_range[1], name='Temp'),
        Integer(time_range[0], time_range[1], name='Time'),
        Categorical(catalysts, name='Catalyst')
    ]
    
    opt = Optimizer(search_space, base_estimator="GP", acq_func="EI")

    # 2. CHECK: Only "tell" the optimizer if there is actually data to learn from
    if not clean_data.empty:
        X = clean_data[['Temp', 'Time', 'Catalyst']].values.tolist()
        # Convert to float to ensure mathematical operations work
        y = (-clean_data['Yield (%)'].astype(float)).values.tolist()
        opt.tell(X, y)

    return opt.ask()

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
    
    # 1. Initialize a placeholder for the suggestion if it doesn't exist
    if 'current_suggestion' not in st.session_state:
        st.session_state.current_suggestion = None

    # 2. Data Editor
    st.write("Enter results from the lab below:")
    edited_df = st.data_editor(
        st.session_state.exp_data, 
        num_rows="dynamic",
        key="main_editor" # Adding a key helps Streamlit track state
    )
    st.session_state.exp_data = edited_df

    # 3. Suggestion Logic
    if st.button("🤖 Suggest Next Experiment"):
        if catalysts:
            # Store the suggestion in session_state so it survives the re-run
            st.session_state.current_suggestion = get_next_suggestion(
                st.session_state.exp_data, 
                temp_range, 
                res_time, 
                catalysts
            )
        else:
            st.error("Please select at least one catalyst in the 'Design' tab first.")

    # 4. Display the suggestion (it will now stay visible!)
    if st.session_state.current_suggestion:
        s = st.session_state.current_suggestion
        st.success(f"**Recommended Parameters:**")
        col_a, col_b, col_c = st.columns(3)
        col_a.metric("Temperature", f"{s[0]}°C")
        col_b.metric("Res. Time", f"{s[1]} min")
        col_c.metric("Catalyst", s[2])
        
        st.info("💡 Tip: Enter these values into the table above. The suggestion will stay here until you request a new one.")

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

