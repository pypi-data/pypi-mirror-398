import sys
import os
from streamlit.web import cli as stcli
import pandas as pd


def run(filepath="", y="y", positive=1):
    """
    Configures environment variables and launches a Streamlit app.

    This function sets up necessary environment variables for a Streamlit application
    and initiates its execution. It defaults to using the 'adult.csv' dataset if no
    file path is provided.

    Parameters:
    ----------
    filepath : str, optional
        Path to the CSV dataset file. If None, defaults to 'Datasets/adult.csv'
        located in the same directory as this script.
    y : str, optional
        Name of the target column in the dataset. Defaults to "y".
    positive : int or str, optional
        Value considered as the positive class in binary classification. Defaults to 1.

    Returns:
    -------
    None
        This function does not return; it exits the Python interpreter after launching the app.
    """
    this_dir = os.path.dirname(__file__)

    app_path = os.path.join(this_dir, "app.py")
    sys.argv = ["streamlit", "run", app_path]
    sys.exit(stcli.main())
