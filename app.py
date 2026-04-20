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
    
    # 1. Initialize suggestion state if it doesn't exist
    if 'current_suggestion' not in st.session_state:
        st.session_state.current_suggestion = None

    # 2. Data Editor: Shows the log of all experiments
    st.write("### 📋 Experiment Log")
    st.info("The table below tracks your progress. Type your results in the 'Yield (%)' column.")
    
    # We use a key to ensure the editor state is preserved during re-runs
    edited_df = st.data_editor(
        st.session_state.exp_data, 
        num_rows="dynamic",
        key="main_editor",
        use_container_width=True
    )
    st.session_state.exp_data = edited_df

    st.divider()

    # 3. Optimization Logic
    col_btn1, col_btn2 = st.columns([1, 2])
    
    with col_btn1:
        if st.button("🤖 Suggest Next Experiment", use_container_width=True):
            if catalysts:
                # Calls your Bayesian optimizer
                st.session_state.current_suggestion = get_next_suggestion(
                    st.session_state.exp_data, 
                    temp_range, 
                    res_time, 
                    catalysts
                )
            else:
                st.error("Please select at least one catalyst in the 'Design' tab first.")

    # 4. Display Suggestion and "Add to Log" Button
    if st.session_state.current_suggestion:
        s = st.session_state.current_suggestion
        
        st.success("**AI Recommended Parameters Found!**")
        
        # Display the parameters in nice metric boxes
        m1, m2, m3 = st.columns(3)
        m1.metric("Temperature", f"{s[0]} °C")
        m2.metric("Res. Time", f"{s[1]} min")
        m3.metric("Catalyst", s[2])
        
        # Button to automatically move these values into the table
        if st.button("📝 Add This Suggestion to Log", type="primary", use_container_width=True):
            new_row = {
                "Run": len(st.session_state.exp_data) + 1,
                "Temp": s[0],
                "Time": s[1],
                "Catalyst": s[2],
                "Yield (%)": None # User fills this after the lab run
            }
            
            # Update the dataframe
            st.session_state.exp_data = pd.concat([
                st.session_state.exp_data, 
                pd.DataFrame([new_row])
            ], ignore_index=True)
            
            # Clear the suggestion so the UI stays clean
            st.session_state.current_suggestion = None
            
            # Refresh to show new row in the table
            st.rerun()


######################################################################################################################################
with tab3:
    st.subheader("Performance Overview")
    
    if not st.session_state.exp_data.empty:
        # Clean data for plotting (remove rows without yields)
        plot_data = st.session_state.exp_data.dropna(subset=['Yield (%)']).copy()
        
        if not plot_data.empty:
            # 1. Yield vs. Temperature Scatter Chart
            st.write("#### 🌡️ Yield vs. Temperature")
            st.caption("Visualizing how temperature affects the reaction outcome.")
            st.scatter_chart(
                data=plot_data, 
                x="Temp", 
                y="Yield (%)", 
                color="Catalyst",
                use_container_width=True
            )

            st.divider()

            # 2. Optimization Learning Curve
            st.write("#### 📉 Optimization Learning Curve")
            st.info("The green line tracks the 'Best Result' found as the search progresses.")
            
            # Calculate the cumulative maximum (the best yield found up to that run)
            plot_data['Best Yield So Far'] = plot_data['Yield (%)'].cummax()
            
            # Plotting the current yield vs. the best yield
            # We use 'Run' as the X-axis to show progress over time
            st.line_chart(
                data=plot_data, 
                x="Run", 
                y=["Yield (%)", "Best Yield So Far"],
                color=["#FF4B4B", "#28a745"], # Red for current, Green for best
                use_container_width=True
            )
            
            st.divider()

            # 3. Data Export
            st.write("#### 💾 Export Results")
            st.write("Download the complete experiment log for your lab notebook or publication.")
            
            # Convert dataframe to CSV
            csv_data = st.session_state.exp_data.to_csv(index=False).encode('utf-8')
            
            st.download_button(
                label="📥 Download Experiment Log (.csv)",
                data=csv_data,
                file_name='oled_discovery_log.csv',
                mime='text/csv',
                type="secondary",
                use_container_width=True
            )
        else:
            st.warning("Data detected, but 'Yield (%)' column is empty. Please enter results in Tab 2.")
    else:
        st.info("💡 No experiments logged yet. Run some 'Auto-Experiments' in the sidebar or add them manually in Tab 2.")

######################################################################################################################################
# Footer
st.markdown("---")
st.caption("OLED-Flow-Stack | Open Source Research Project | v0.1.0-alpha")

######################################################################################################################################
# --- SIDEBAR: BEST RESULT TROPHY ---
st.sidebar.divider()
st.sidebar.subheader("🏆 Hall of Fame")

# Clean the data to ensure we only look at valid numbers
valid_yields = st.session_state.exp_data.dropna(subset=['Yield (%)'])

if not valid_yields.empty:
    # Find the row with the highest yield
    best_run = valid_yields.loc[valid_yields['Yield (%)'].idxmax()]
    
    # Display the "Trophy"
    st.sidebar.success(f"**Best Yield: {best_run['Yield (%)']}%**")
    
    with st.sidebar.expander("View Best Conditions"):
        st.write(f"**Temp:** {best_run['Temp']} °C")
        st.write(f"**Time:** {best_run['Time']} min")
        st.write(f"**Catalyst:** {best_run['Catalyst']}")
else:
    st.sidebar.info("No successful runs logged yet. Start optimizing!")
######################################################################################################################################    
# --- AUTOMATED TESTING MODULE ---
def simulate_lab_yield(suggestion):
    """
    Simulates a real OLED reaction. 
    Target: 115°C, 12 min, Catalyst: XPhos Pd G3
    """
    s_temp, s_time, s_cat = suggestion
    
    # Calculate 'distance' from ideal conditions
    temp_score = max(0, 100 - abs(s_temp - 115))
    time_score = max(0, 100 - abs(s_time - 12))
    cat_score = 100 if s_cat == "XPhos Pd G3" else 40
    
    # Final yield is an average with some 'random noise' to mimic real lab error
    base_yield = (temp_score + time_score + cat_score) / 3
    yield_with_noise = base_yield + np.random.normal(0, 2)
    
    return round(min(max(yield_with_noise, 0), 99), 1)
######################################################################################################################################
# --- SIDEBAR TESTING UI 
st.sidebar.divider()
st.sidebar.subheader("🧪 Automation & QA")

if st.sidebar.button("Run 5 Auto-Experiments", use_container_width=True):
    # This 'status' block creates a progress indicator and 'locks' the focus
    with st.status("🤖 AI is simulating experiments...", expanded=True) as status:
        for i in range(5):
            st.write(f"Running Experiment {i+1}/5...")
            
            # 1. Get AI Suggestion
            s = get_next_suggestion(
                st.session_state.exp_data, 
                temp_range, 
                res_time, 
                catalysts
            )
            
            # 2. Simulate the 'Lab Result'
            mock_yield = simulate_lab_yield(s)
            
            # 3. Log the data
            new_row = {
                "Run": len(st.session_state.exp_data) + 1,
                "Temp": s[0],
                "Time": s[1],
                "Catalyst": s[2],
                "Yield (%)": mock_yield
            }
            st.session_state.exp_data = pd.concat([
                st.session_state.exp_data, 
                pd.DataFrame([new_row])
            ], ignore_index=True)
            
            # Optional: add a tiny sleep to make the animation visible
            import time
            time.sleep(0.3) 
            
        status.update(label="✅ All 5 Experiments Complete!", state="complete", expanded=False)
    
    st.rerun()


######################################################################################################################################
