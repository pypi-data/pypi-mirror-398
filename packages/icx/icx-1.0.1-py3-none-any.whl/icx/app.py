import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode
from streamlit_sortables import sort_items

import functions as f

st.set_page_config(layout="wide")
"# Individual Consistency eXplorer (ICX)"

selected_dataset = f.welcome_message()

# Initialise session state
if "dataset" not in st.session_state:
    st.session_state.dataset = None

if "dataset_name" not in st.session_state:
    st.session_state.dataset_name = None

# Dataset selection logic
if selected_dataset == "own_data":
    df = f.load_dataset()  # returns None until upload is confirmed
else:
    # Only reload if dataset actually changed
    if st.session_state.dataset_name != selected_dataset:
        st.session_state.dataset = f.get_dataset(selected_dataset)
        st.session_state.dataset_name = selected_dataset

    df = st.session_state.dataset

f.display_dataset_stats(df)

delta=0.5

simple_style = f.get_draggable_style()

# Sidebar inputs
st.sidebar.text("Similarity definition")
k = st.sidebar.text_input("Enter number of similar individuals to select", value=5)
st.sidebar.text("Define attribute types and categorisations", help="For each attribute in the dataset, decide how the distance between values should be calculated by choosing the types and categorisations.")


# Dictionary to store user inputs
user_inputs = {}
attr_types = {}
categorical_columns = []
df_display = df.copy()

# Create an input box for each column in the DataFrame
for col in df.columns:
    if (df[col].dtype == "int64" or df[col].dtype == "float64") and col != "y":
        # Dropdown menu in the main page
        attr_types[col] = st.sidebar.selectbox(
            f"Choose type for attribute `{col}`",
            ["Original numerical values", "Values as categorical", "Choose discretisation"], key = col
        )
        if attr_types[col] == "Values as categorical":
            user_inputs[col] = ""
            categorical_columns.append(col)
        elif attr_types[col] == "Choose discretisation":
            user_inputs[col] = st.sidebar.text_input(f"Enter discretisation for {col} (e.g. 0,18,65)", help="0,18,65 corresponds to the attribute bins of $\\ <18, 18-64, \geq 65$")
            categorical_columns.append(col)
        else:
            user_inputs[col] = ""
    elif col != "y":
        attr_types[col] = st.sidebar.selectbox(
            f"Choose type for attribute `{col}`",
            ["Original categorical values", "Choose ordering of values"], key=col
        )
        if attr_types[col] == "Choose ordering of values":
            st.sidebar.text("Order categorical values", help="Drag the values in the preferred ordering (left-most values is given a numerical value of 0, right-most is given value of 1)")
            # Create a draggable UI
            with st.sidebar:
                sorted_attributes = sort_items(df[col].unique().tolist(), direction="horizontal", custom_style=simple_style)
            df = f.get_ordered(df, col, sorted_attributes)
            df_display = f.get_value_order(df_display, col, sorted_attributes)
            user_inputs[col] = ""
        else:
            user_inputs[col] = ""
            categorical_columns.append(col)
    else:
        user_inputs[col] = ""

# set definition of similarity
binned_df, new_categorical_columns = f.similarity(df, user_inputs, categorical_columns)

similar_individuals, similar_individuals_distances = f.find_similar_inds(binned_df, int(k), new_categorical_columns)
individual_consistencies = f.get_ind_cons(binned_df, similar_individuals)

binned_df = f.replace_data(binned_df, df_display)
binned_df['c'] = individual_consistencies
binned_df.insert(0, "id", binned_df.index)

col1, col2 = st.columns([1, 1])


with col1:
    st.subheader("Individual consistency score")
    "The proportion of an individual's similar individuals who share the same classification."
    "$\\delta$ defines the proportion considered 'acceptable'."

with col2:
    delta = st.slider(
        'Select $\\delta$',
        min_value=0.00,
        max_value=1.00,
        step=0.05,
        value=0.5
    )

    f"The highlighted individuals below are those with individual consistency less than or equal to {delta}"

binned_df["delta"] = delta
# Configure Ag-Grid options
builder = GridOptionsBuilder.from_dataframe(binned_df)
builder.configure_column("delta", hide=True)
builder.configure_column('c', header_name="Individual consistency")
builder.configure_column('y', header_name="Classification")
builder.configure_selection("single", use_checkbox=True)

jscode = f.highlight_rows()

grid_options = builder.build()
grid_options['getRowStyle'] = jscode

grid_response = AgGrid(binned_df, gridOptions=grid_options, update_mode="selection_changed",
                           allow_unsafe_jscode=True)

st.markdown("---")
f.display_scores(binned_df, individual_consistencies, delta)

# Get selected row data
selected_row = grid_response["selected_rows"]

ind = pd.DataFrame(selected_row)
if ind.empty:  # Ensure a row is selected
    ind = binned_df.iloc[[0]]
selected_id = ind.index  # Extract the 'id' of the selected row

# Display the selected row below
st.markdown("---")
st.markdown("## 🔍 Inspect a Specific Individual")
st.markdown("Select an individual in the dataset view above to explore its classification compared to similar individuals as defined in the left panel.")

st.markdown(f"Selected individual with id={selected_id[0]} and its {k} most similar individuals:", help="In cases where individuals have the same distance, the ones selected are arbitrary")

# Find the matching row in similar_individuals
matched_rows = similar_individuals[int(selected_id[0])]

# Use the index to find matching rows in binned_data
matched_binned_data = binned_df.iloc[matched_rows]

# Combine selected row with the matching binned_data
combined_df = pd.concat([ind, matched_binned_data], ignore_index=True)

distances = similar_individuals_distances.get(int(selected_id[0])) # Lookup in dictionary
distances2 = [0] + distances.tolist()
distances3 = f.format_distances(distances2, df)
combined_df["Distance"] = distances3 #* len(round(combined_df, 3))

# Configure Ag-Grid options
builder2 = GridOptionsBuilder.from_dataframe(combined_df)
builder2.configure_column("delta", hide=True)
builder2.configure_column("c", hide=True)
builder2.configure_column('y', header_name="Classification")

jscode = f.highlight_first_row()

grid_options = builder2.build()
grid_options['getRowStyle'] = jscode

grid_response = AgGrid(combined_df, gridOptions=grid_options, update_mode="filtering_changed", allow_unsafe_jscode=True)

ind_con = ind["c"][0]
st.markdown(f"Individual consistency score for individual with id={selected_id[0]} is {ind_con}")

st.markdown("### Reason for classification compared to similar individuals")
f.explanation(combined_df, int(k), selected_id)

st.markdown("## 🧩 Group Fairness Analysis")

f.group(binned_df, individual_consistencies, delta)