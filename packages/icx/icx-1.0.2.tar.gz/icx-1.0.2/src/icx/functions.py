import pandas as pd
import numpy as np
from gower import gower_matrix
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode
from sklearn.neighbors import NearestNeighbors
import uuid
import os

import construct_graph as cg


def similarity(df, user_inputs, categorical_columns):
    binned_df = df.copy()
    for col in df.columns:
        if not (user_inputs[col] == ""):
            binned_df = bin_column(binned_df, col, user_inputs[col])
            categorical_columns.append(col)
    return binned_df, categorical_columns


def bin_column(df, col_name, bins_str):
    """
    Bins a column into specified bins with range labels and replaces the original column.

    Parameters:
        df (pd.DataFrame): The DataFrame containing the column to bin.
        col_name (str): The column name to bin.
        bins_str (str): A comma-separated string of bin edges (e.g., "10,20,30").

    Returns:
        pd.DataFrame: The DataFrame with the original column replaced by binned values.
    """
    # Convert the comma-separated string into a list of numbers
    bins = [float(x) for x in bins_str.split(",")] + [float('inf')]  # Add infinity as the last bin

    # Generate labels in the format "start-end"
    labels = [f"{int(bins[i])}-{int(bins[i + 1]) - 1 if bins[i + 1] != float('inf') else 'inf'}" for i in
              range(len(bins) - 1)]

    # Replace the original column with binned values
    df[col_name] = pd.cut(df[col_name], bins=bins, labels=labels, right=False)

    return df


# get the k nearest neighbours for all individuals in the test data, and their corresponding distances
# created by me to be able to edit the distance metric used
def get_knn(X, k, categorical_columns):
    # Create a boolean array where True indicates a categorical column
    is_categorical = np.array(X.columns.isin(categorical_columns))

    X_gower = gower_matrix(X.values, cat_features=is_categorical)

    # Create a KNN model and fit it
    k = k + 1
    nbrs = NearestNeighbors(n_neighbors=k, metric='precomputed')
    nbrs.fit(X_gower)

    # Find the k nearest neighbors for all examples
    distances, indices = nbrs.kneighbors(X_gower)
    return distances, indices


def find_similar_inds(df, k, categorical_columns):
    """ Compute the consistency score.

        Individual fairness metric from [#zemel13]_ that measures how similar the
        labels are for similar instances.

        Args:
            X (array-like): Sample features.
            y (array-like): Sample targets.
            k (int): Number of neighbors for the knn
                computation.

        References:
            .. [#zemel13] `R. Zemel, Y. Wu, K. Swersky, T. Pitassi, and C. Dwork,
               "Learning Fair Representations," International Conference on Machine
               Learning, 2013. <http://proceedings.mlr.press/v28/zemel13.html>`_
        """
    X = df.drop(columns=["y"])
    y = df["y"]

    # learn a KNN on the features
    distances, indices = get_knn(X, k, categorical_columns)

    # ADDED code, remove the index (individual) itself
    similar_inds = {}
    sim_ind_distances = {}
    for i in range(len(indices)):
        if i in indices[i]:
            similar_inds[i] = np.delete(indices[i], np.where(indices[i] == i))
            sim_ind_distances[i] = np.delete(distances[i], np.where(indices[i] == i))
        else:
            similar_inds[i] = indices[i][:-1]
            sim_ind_distances[i] = distances[i][:-1]
    return similar_inds, sim_ind_distances


def get_ind_cons(df, sim_inds):
    y = df["y"]
    ind_cons = []
    for key in sim_inds:
        ind_con = (1 - abs(y[key] - y[sim_inds[key]].mean()))
        ind_cons.append(round(ind_con, 2))
    return ind_cons


def get_overall_consistency(ind_cons):
    return round(sum(ind_cons) / len(ind_cons), 3)


def get_licc_score(ind_cons, delta):
    return sum(1 for x in ind_cons if x < delta)


def get_pcc_score(ind_cons, delta):
    count = 0
    for c in ind_cons:
        if round(c, 2) >= delta:
            count = count + 1

    pcc = (count / len(ind_cons))
    return round(pcc, 3)


def get_bcc_score(ind_cons, delta=0.5):
    count = 0
    for c in ind_cons:
        if round(c, 2) >= delta:
            count = count + c

    bcc = (count / len(ind_cons))
    return round(bcc, 3)


def get_bcc_penalty_score(ind_cons, delta, penalty=-1):
    count = 0
    for c in ind_cons:
        if round(c, 2) >= delta:
            count = count + c
        else:
            count = count + penalty

    bcc = (count / len(ind_cons))
    return round(bcc, 3)


# Function to highlight rows based on consistencies
def highlight_rows():
    return JsCode("""
                function(params) {
                    if (params.data.c <= params.data.delta) {
                        return {
                            'color': 'black',
                            'backgroundColor': 'lightyellow'
                        }
                    }
                };
                """)


def highlight_first_row():
    return JsCode("""function(params) {
        if (params.node.rowIndex === 0) {
            return { 'background-color': 'lightyellow', 'font-weight': 'bold' };
        }
    }""")


def get_ordered(df, col, sorted_attributes):
    # Create a mapping dictionary {value: order_index}
    order_mapping = {val: idx for idx, val in enumerate(sorted_attributes)}

    # Replace values in df['Category'] with their order
    df[col] = df[col].map(order_mapping)
    return df


def get_value_order(df, col, sorted_attributes):
    # Create a mapping dictionary {value: order_index}
    order_mapping = {val: f"{idx} ({val})" for idx, val in enumerate(sorted_attributes)}
    # Replace values in df['Category'] with their order
    df[col] = df[col].map(order_mapping)
    return df


def replace_data(binned_df, df_display):
    # Find columns where the data types are different
    differing_cols = [col for col in binned_df.columns if
                      binned_df[col].dtype != df_display[col].dtype and df_display[col].dtype != 'int64']

    # Replace those columns in binned_df with df_display
    binned_df[differing_cols] = df_display[differing_cols]
    return binned_df


def get_draggable_style():
    return """
.sortable-component {
    background-color:rgb(0, 225, 255);
    font-size: 16px;
    counter-reset: item;
}
.sortable-item {
    background-color: gray;
    color: white;
}
"""


def save_button(binned_df, consistency_score, licc_score, pcc_score, bcc_score, bcc_pen_score,
                individual_consistencies):
    st.session_state.individual_consistencies = individual_consistencies

    metrics_df = pd.DataFrame([{
        "Consistency Score": consistency_score,
        "Low Individual Consistency Count": licc_score,
        "Proportional Consistency Score": pcc_score,
        "Balanced Conditioned Consistency": bcc_score,
        "Balanced Conditioned Consistency with Penalty": bcc_pen_score
    }])

    # Join metrics and dataframe into a single CSV file
    csv_data = (
            "Dataset Metrics\n" +
            metrics_df.to_csv(index=False) +
            "\nBinned Data\n" +
            binned_df.to_csv(index=False)
    )

    # ---- 4. DOWNLOAD BUTTON ----
    st.download_button(
        label="💾 Save and Download Dashboard State as CSV",
        data=csv_data,
        file_name="dashboard_state.csv",
        mime="text/csv"
    )


def get_sric_score(individual_consistencies, delta):
    if "individual_consistencies" not in st.session_state:
        st.session_state.individual_consistencies = []

    current = individual_consistencies
    previous = st.session_state.individual_consistencies

    if not previous:
        st.write("Press the save and download button to explore the SRIC Score")
        return

    try:
        current_arr = np.array(current)
        previous_arr = np.array(previous)

        # Defensive check: same length required
        if current_arr.shape != previous_arr.shape:
            raise ValueError(
                f"Ensure the previous saved dataset is the same as the current loaded dataset"
            )

        mask = (
                ((current_arr >= delta) & (previous_arr < delta)) |
                ((current_arr < delta) & (previous_arr >= delta))
        )

        sric_score = mask.sum() / len(current_arr) if len(current_arr) > 0 else 0.0

        st.metric(
            label="SRIC Score",
            value=f"{sric_score:.3f}",
            help=(
                "Proportion of individuals whose individual consistency differs "
                "across a threshold $\\delta$ between the previously saved "
                "similarity definition and the current similarity definition."
            )
        )

    except Exception as e:
        # Error catcher
        st.error("Unable to compute SRIC Score.")
        st.caption(f"Reason: {e}")


def display_scores(df, individual_consistencies, delta):
    # Assuming `f` and `individual_consistencies` are defined
    consistency_score = get_overall_consistency(individual_consistencies)
    licc_score = get_licc_score(individual_consistencies, delta)
    pcc_score = get_pcc_score(individual_consistencies, delta)
    bcc_score = get_bcc_score(individual_consistencies, delta)
    bcc_pen_score = get_bcc_penalty_score(individual_consistencies, delta)

    st.markdown("## 📊 Dataset Metrics")

    # Arrange scores in a clean layout
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(label="Consistency Score", value=f"{consistency_score:.3f}",
                  help="Measures the overall level of disparity in a dataset in the classification of individuals with respect to their most similar individuals. Calculated as the average individual consistency score) ")
        get_sric_score(individual_consistencies, delta)
    with col2:
        st.metric(label="LICC Score", value=f"{licc_score}",
                  help="Absolute measure of the total number of individuals in a dataset with decisions deemed unacceptable. Calculated as the count of individuals for which their individual consistency score is less than threshold $\\delta$.")
        st.metric(label="PCS Score", value=f"{pcc_score:.3f}",
                  help="Proportion of individuals in the datasets whose decisions are deemed acceptable. Calculated as the proportion of individuals with an individual consistency score greater than or equal to $\\delta$")
    with col3:
        st.metric(label="BCC Score", value=f"{bcc_score:.3f}",
                  help="Average individual consistency score above a level that is deemed acceptable. Calculated as the sum of the individual consistency scores above or equal some threshold $\\delta$ divided by the total number of individuals.")
        st.metric(label="BCC with Penalty Score", value=f"{bcc_pen_score:.3f}",
                  help="As BCC, but penalises for unacceptable decisions, and hence it is more sensitive to those decisions. Calculated as a modification of BCC score which counts an individual as -1 for each individual consistency score below $\\delta$.")

    save_button(df, consistency_score, licc_score, pcc_score, bcc_score, bcc_pen_score, individual_consistencies)


def format_distances(distances, df):
    # Get number of columns in the DataFrame
    num_columns = df.shape[1] - 1

    # Multiply each distance by the number of columns and format to 3 decimal places
    return [f"{(dist * num_columns):.3f}" for dist in distances]


def display_dataset_stats(df):
    # Dataset shape
    st.markdown("---")
    st.header("🧭 Dataset Explorer")
    col1, col2, col3 = st.columns(3)
    col1.metric("Rows", df.shape[0])
    col2.metric("Columns", df.shape[1])

    if "y" in df.columns:
        # Compute proportion of y == 1
        positive_ratio = (df["y"] == 1).mean() * 100
        col3.metric("Proportion of positive labels", value=f"{positive_ratio:.1f}%")
    else:
        st.warning("⚠️ Column `y` not found in dataset — skipping target distribution.")

    with st.expander("See column data types"):
        st.dataframe(df.dtypes.astype(str).reset_index().rename(columns={"index": "Column", 0: "Type"}))

    '''
    missing = df.isnull().sum()
    missing = missing[missing > 0].sort_values(ascending=False)
    if missing.empty:
        st.success("No missing values found!")
    else:
        st.warning("Columns with missing values:")
        st.dataframe(missing.reset_index().rename(columns={"index": "Column", 0: "Missing Count"}))
    '''


def welcome_message():
    st.markdown("""
    Welcome to the **Individual Consistency Explorer Dashboard**!

    This dashboard can be used to **explore the individual fairness** of a dataset.  
    It allows for **three demo datasets**, which you can use to try out the functionality.

    ---

    We recommend using this dashboard locally with any sensitive data.
    Please use the Python package as detailed [here](https://pypi.org/project/icx/) to upload and analyse your own data.

    ---
    ## 📂 Select a Demo Dataset or Upload Your Own Dataset
    """)

    # Dataset names for dropdown
    dataset_labels = {
        "Adult Census": "adult",
        "German Credit": "german",
        "COMPAS": "compas",
        "Upload Own Dataset": "own_data"
    }

    # Dropdown selection
    selected_label = st.selectbox("Choose a preloaded dataset or upload your own:", options=list(dataset_labels.keys()))
    selected_dataset = dataset_labels[selected_label]

    # Show link to dataset
    dataset_links = {
        "adult": "https://archive.ics.uci.edu/ml/datasets/adult",
        "german": "https://archive.ics.uci.edu/ml/datasets/statlog+(german+credit+data)",
        "compas": "https://www.kaggle.com/datasets/danofer/compass",
        "own_data": None
    }

    if dataset_links[selected_dataset] is not None:
        st.markdown(f"🔗 [View dataset source for **{selected_label}**]({dataset_links[selected_dataset]})")
    return selected_dataset


def load_dataset():
    if "dataset" not in st.session_state:
        st.session_state.dataset = None

    st.markdown(
        "Upload your own data from a CSV file: the data should include "
        "attribute names in the first row, and a column for the classification."
    )

    uploaded_file = st.file_uploader("Choose a CSV file:", type="csv")

    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)

        st.write("### Preview of Data")
        st.dataframe(df.head())

        columns = df.columns.tolist()
        default_index = columns.index("y") if "y" in columns else 0
        y_col = st.selectbox("Select the class (y) column", options=df.columns, index=default_index)

        if y_col:
            positive_label = st.selectbox(
                "Select the positive class value",
                options=df[y_col].dropna().unique().tolist()
            )

            if st.button("🔄 Convert Target Column and Upload Data"):
                df[y_col] = (df[y_col] == positive_label).astype(int)
                df.rename(columns={y_col: "y"}, inplace=True)

                st.session_state.dataset = df
                st.session_state.dataset_name = "own_data"

                st.success("Custom dataset loaded successfully.")

    return st.session_state.dataset


def get_dataset(selected_dataset):
    # Base directory where the script is located
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # Path to the Datasets folder
    dataset_dir = os.path.join(base_dir, 'Datasets')

    if selected_dataset == "compas":
        file_path = os.path.join(dataset_dir, "compas.csv")
        df = pd.read_csv(file_path)
        df["y"] = (df["y"] == "Survived").astype(int)
    elif selected_dataset == "german":
        file_path = os.path.join(dataset_dir, "german.csv")
        df = pd.read_csv(file_path)
        df["y"] = (df["y"] == "good").astype(int)
    else:
        file_path = os.path.join(dataset_dir, "adult.csv")
        df = pd.read_csv(file_path).head(1000)
        df["y"] = (df["y"] == ">50K").astype(int)

    return df


def explanation(df, k, selected_id):
    if "explanation_steps" not in st.session_state:
        st.session_state.explanation_steps = []

    if "feedback_response" not in st.session_state:
        st.session_state.feedback_response = None

    # --- Reset explanation state if individual changes ---
    if "active_ind_id" not in st.session_state:
        st.session_state.active_ind_id = selected_id

    if st.button("🔄 Reset explanation") or st.session_state.active_ind_id != selected_id:
        st.session_state.explanation_steps = []
        st.session_state.active_ind_id = selected_id
        st.session_state.feedback_response = None
        st.rerun()

    classification = df["y"].iloc[0]
    if classification == 0:
        classification_text = "negatively"
    else:
        classification_text = "positively"

    queried_ind_id = df["id"].iloc[0] if "id" in df.columns else None

    # Clean dataframe
    df_clean = df.drop(
        columns=[c for c in ["id", "c", "Distance", "delta"] if c in df.columns]
    )

    # Construct graph
    final_weights, weakest_args = cg.construct_graph(df_clean)

    # Handle special cases
    if "consistent" in weakest_args:
        st.info(
            f"The individual with id {queried_ind_id} is {classification_text} classified, "
            f"the same as all {k} similar individuals."
        )
        return

    if not final_weights:
        st.success(
            f"No further reasons were found. The classification of individual "
            f"{queried_ind_id} is considered **fair** compared to {k} similar individuals."
        )
        return

    removed_args = []
    for i, step in enumerate(st.session_state.explanation_steps):
        with st.expander(f"Explanation {i + 1}", expanded=True):
            st.write(step["text"])

            if step.get("justified", False):
                st.success(
                    "You indicated that this explanation is **justified** in your context."
                )
        removed_args.extend(step["args"])

    # Remove previously accepted arguments
    for arg in removed_args:
        final_weights.pop(arg, None)

    min_weight = min(final_weights.values())
    weakest_args = [a for a, w in final_weights.items() if w == min_weight]
    # Handle special cases
    if "consistent" in weakest_args:
        st.info(
            f"The individual with id {queried_ind_id} is {classification_text} classified, "
            f"the same as all {k} similar individuals."
        )
        return
    if min_weight == 1:
        st.success(
            f"There are no remaining reasons for the differing classifications between similar individuals. "
            f"The classification of individual {queried_ind_id} is **fair** in relation to the similarity definition."
        )
        return

    # Display current explanation
    exp_values = ", ".join(weakest_args)
    explanation_text = (
        f"The reason individual with id {queried_ind_id} has been {classification_text} classified "
        f"compared to {k} similar individuals, according to the similarity definition, is the attribute value(s):\n\n"
        f"**{exp_values}**."
    )

    with st.container():
        st.write(explanation_text)

        feedback(
            classification,
            queried_ind_id,
            weakest_args,
            explanation_text
        )


def feedback(classification, queried_ind_id, weakest_args, explanation_text):
    step_idx = len(st.session_state.explanation_steps)

    st.write(f"Is this a justified reason for the classification of the selected individual with id  {queried_ind_id} "
             "in your context?")

    col1, col2 = st.columns(2)

    yes_key = f"feedback_yes_{queried_ind_id}_{step_idx}"
    no_key = f"feedback_no_{queried_ind_id}_{step_idx}"

    with col1:
        yes_clicked = st.button("✅ Yes", key=yes_key)

    with col2:
        no_clicked = st.button("❌ No", key=no_key)

    if no_clicked:
        st.session_state.feedback_response = "no"
        st.error(
            "You indicated that this explanation is **not justified** for the classification in your context.\n\n"
            "The classification may therefore be considered **unfair**, and we recommend changing the classification  "
            "or investigating the classification further."
        )
        return

    if yes_clicked:
        st.session_state.feedback_response = "yes"

        # Store this explanation step
        st.session_state.explanation_steps.append({
            "args": weakest_args,
            "text": explanation_text,
            "justified": True
        })

        st.success(
            "You indicated that this explanation is **justified** for the classification in your context. "
            "We will now explore additional reasons for the classification."
        )

        st.rerun()


def group(df, individual_consistencies, delta):
    """
    df: dataset as pandas DataFrame
    """
    df = df.drop(columns=["id", "c", "delta"])

    # -----------------------------
    # 1. Default dropdown selections
    # -----------------------------
    protected_attr_default = "sex" if "sex" in df.columns else df.columns[df.columns != "y"][0]

    # -----------------------------
    # 2. Side-by-side dropdowns
    # -----------------------------
    colA, colB = st.columns(2)

    with colA:
        protected_attr = st.selectbox(
            "Protected Attribute",
            options=[col for col in df.columns if col != 'y'],
            index=[col for col in df.columns if col != 'y'].index(protected_attr_default),
            help="Attribute used to define groups for fairness comparison."
        )

    with colB:
        protected_values = st.multiselect(
            f"Protected Group Values for '{protected_attr}'",
            options=df[protected_attr].unique(),
            help="Individuals with these values are considered the protected (unprivileged) group."
        )

    if not protected_values:
        st.warning("Please select at least one value for the protected group.")
        return

    # -----------------------------
    # 3. Mask definitions
    # -----------------------------
    protected_mask = df[protected_attr].isin(protected_values)
    unprotected_mask = ~protected_mask

    # -----------------------------
    # 4. Compute SPD manually
    # -----------------------------
    p_protected = df.loc[protected_mask, 'y'].mean()
    p_unprotected = df.loc[unprotected_mask, 'y'].mean()

    spd = p_unprotected - p_protected

    # -----------------------------
    # 5. Display SPD nicely
    # -----------------------------

    st.metric(
        label="Demographic Parity",
        value=f"{spd:.3f}",
        help="The difference between the proportions of positive classifications for the protected group versus "
             "the unprotected group. A value near 0 means both groups receive positive outcomes at similar rates."
             " A value greater (less) than 0 means the unprotected (protected) group is favoured over the protected (unprotected) group."
    )

    # -----------------------------
    # 6. Consistency-based metrics for groups
    # -----------------------------

    individual_consistencies = np.array(individual_consistencies)

    ic_protected = individual_consistencies[protected_mask]
    ic_unprotected = individual_consistencies[unprotected_mask]

    consistency_score_protected = get_overall_consistency(ic_protected)
    consistency_score_unprotected = get_overall_consistency(ic_unprotected)
    licc_score_protected = get_licc_score(ic_protected, delta)
    licc_score_unprotected = get_licc_score(ic_unprotected, delta)
    pcc_score_protected = get_pcc_score(ic_protected, delta)
    pcc_score_unprotected = get_pcc_score(ic_unprotected, delta)
    bcc_score_protected = get_bcc_score(ic_protected, delta)
    bcc_score_unprotected = get_bcc_score(ic_unprotected, delta)
    bcc_pen_score_protected = get_bcc_penalty_score(ic_protected, delta)
    bcc_pen_score_unprotected = get_bcc_penalty_score(ic_unprotected, delta)

    st.markdown("### 🔍 Consistency Metrics by Group")

    colP, colU = st.columns(2)

    with colP:
        st.markdown(f"####  Protected Group")
        st.metric(
            label="Overall Consistency",
            value=f"{consistency_score_protected:.3f}",
            help=help_consistency_prot
        )
        st.metric(
            label="LICC Score",
            value=f"{licc_score_protected}",
            help=help_licc_prot
        )
        st.metric(
            label="PCC Score",
            value=f"{pcc_score_protected:.3f}",
            help=help_pcc_prot
        )
        st.metric(
            label="BCC Score",
            value=f"{bcc_score_protected:.3f}",
            help=help_bcc_prot
        )
        st.metric(
            label="BCC Penalty Score",
            value=f"{bcc_pen_score_protected:.3f}",
            help=help_bcc_pen_prot
        )

    with colU:
        st.markdown("#### Unprotected Group")
        st.metric(
            label="Overall Consistency",
            value=f"{consistency_score_unprotected:.3f}",
            help=help_consistency_unprot
        )
        st.metric(
            label="LICC Score",
            value=f"{licc_score_unprotected}",
            help=help_licc_unprot
        )
        st.metric(
            label="PCC Score",
            value=f"{pcc_score_unprotected:.3f}",
            help=help_pcc_unprot
        )
        st.metric(
            label="BCC Score",
            value=f"{bcc_score_unprotected:.3f}",
            help=help_bcc_unprot
        )
        st.metric(
            label="BCC Penalty Score",
            value=f"{bcc_pen_score_unprotected:.3f}",
            help=help_bcc_pen_unprot
        )


help_consistency_prot = (
    "Measures the overall level of disparity **within the protected group** in the "
    "classification of individuals with respect to their most similar individuals. "
    "Calculated as the **average individual consistency score** for this group."
)

help_licc_prot = (
    "Absolute measure of the number of individuals in the **protected group** with "
    "decisions deemed unacceptable. Calculated as the **count of individuals with an "
    "individual consistency score less than threshold δ**."
)

help_pcc_prot = (
    "Proportion of individuals in the **protected group** whose decisions are deemed acceptable. "
    "Calculated as the **share of individuals with a consistency score ≥ δ**."
)

help_bcc_prot = (
    "Average individual consistency score above the acceptable level **within the protected group**. "
    "Calculated as the **sum of consistency scores ≥ δ divided by the number of individuals in this group**."
)

help_bcc_pen_prot = (
    "Penalised BCC score for the **protected group**, more sensitive to unacceptable decisions. "
    "Calculated as a modified BCC where each individual with a consistency score < δ contributes **−1**."
)

help_consistency_unprot = (
    "Measures the overall level of disparity **within the unprotected group** in the "
    "classification of individuals with respect to their most similar individuals. "
    "Calculated as the **average individual consistency score** for this group."
)

help_licc_unprot = (
    "Absolute measure of the number of individuals in the **unprotected group** with "
    "decisions deemed unacceptable. Calculated as the **count of individuals with an "
    "individual consistency score less than threshold δ**."
)

help_pcc_unprot = (
    "Proportion of individuals in the **unprotected group** whose decisions are deemed acceptable. "
    "Calculated as the **share of individuals with a consistency score ≥ δ**."
)

help_bcc_unprot = (
    "Average individual consistency score above the acceptable level **within the unprotected group**. "
    "Calculated as the **sum of consistency scores ≥ δ divided by the number of individuals in this group**."
)

help_bcc_pen_unprot = (
    "Penalised BCC score for the **unprotected group**, more sensitive to unacceptable decisions. "
    "Calculated as a modified BCC where each individual with a consistency score < δ contributes **−1**."
)
