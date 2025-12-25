# Model Imports (this will be replaced with the imports for the template)
None

# Template Placeholders
TEMPLATE_PARAMS = {
    "model_type": "regressor",
    "target_column": "udm_asy_res_efflux_ratio",
    "feature_list": ['chi2v', 'fr_sulfone', 'chi1v', 'bcut2d_logplow', 'fr_piperzine', 'kappa3', 'smr_vsa1', 'slogp_vsa5', 'fr_ketone_topliss', 'fr_sulfonamd', 'fr_imine', 'fr_benzene', 'fr_ester', 'chi2n', 'labuteasa', 'peoe_vsa2', 'smr_vsa6', 'bcut2d_chglo', 'fr_sh', 'peoe_vsa1', 'fr_allylic_oxid', 'chi4n', 'fr_ar_oh', 'fr_nh0', 'fr_term_acetylene', 'slogp_vsa7', 'slogp_vsa4', 'estate_vsa1', 'vsa_estate4', 'numbridgeheadatoms', 'numheterocycles', 'fr_ketone', 'fr_morpholine', 'fr_guanido', 'estate_vsa2', 'numheteroatoms', 'fr_nitro_arom_nonortho', 'fr_piperdine', 'nocount', 'numspiroatoms', 'fr_aniline', 'fr_thiophene', 'slogp_vsa10', 'fr_amide', 'slogp_vsa2', 'fr_epoxide', 'vsa_estate7', 'fr_ar_coo', 'fr_imidazole', 'fr_nitrile', 'fr_oxazole', 'numsaturatedrings', 'fr_pyridine', 'fr_hoccn', 'fr_ndealkylation1', 'numaliphaticheterocycles', 'fr_phenol', 'maxpartialcharge', 'vsa_estate5', 'peoe_vsa13', 'minpartialcharge', 'qed', 'fr_al_oh', 'slogp_vsa11', 'chi0n', 'fr_bicyclic', 'peoe_vsa12', 'fpdensitymorgan1', 'fr_oxime', 'molwt', 'fr_dihydropyridine', 'smr_vsa5', 'peoe_vsa5', 'fr_nitro', 'hallkieralpha', 'heavyatommolwt', 'fr_alkyl_halide', 'peoe_vsa8', 'fr_nhpyrrole', 'fr_isocyan', 'bcut2d_chghi', 'fr_lactam', 'peoe_vsa11', 'smr_vsa9', 'tpsa', 'chi4v', 'slogp_vsa1', 'phi', 'bcut2d_logphi', 'avgipc', 'estate_vsa11', 'fr_coo', 'bcut2d_mwhi', 'numunspecifiedatomstereocenters', 'vsa_estate10', 'estate_vsa8', 'numvalenceelectrons', 'fr_nh2', 'fr_lactone', 'vsa_estate1', 'estate_vsa4', 'numatomstereocenters', 'vsa_estate8', 'fr_para_hydroxylation', 'peoe_vsa3', 'fr_thiazole', 'peoe_vsa10', 'fr_ndealkylation2', 'slogp_vsa12', 'peoe_vsa9', 'maxestateindex', 'fr_quatn', 'smr_vsa7', 'minestateindex', 'numaromaticheterocycles', 'numrotatablebonds', 'fr_ar_nh', 'fr_ether', 'exactmolwt', 'fr_phenol_noorthohbond', 'slogp_vsa3', 'fr_ar_n', 'sps', 'fr_c_o_nocoo', 'bertzct', 'peoe_vsa7', 'slogp_vsa8', 'numradicalelectrons', 'molmr', 'fr_tetrazole', 'numsaturatedcarbocycles', 'bcut2d_mrhi', 'kappa1', 'numamidebonds', 'fpdensitymorgan2', 'smr_vsa8', 'chi1n', 'estate_vsa6', 'fr_barbitur', 'fr_diazo', 'kappa2', 'chi0', 'bcut2d_mrlow', 'balabanj', 'peoe_vsa4', 'numhacceptors', 'fr_sulfide', 'chi3n', 'smr_vsa2', 'fr_al_oh_notert', 'fr_benzodiazepine', 'fr_phos_ester', 'fr_aldehyde', 'fr_coo2', 'estate_vsa5', 'fr_prisulfonamd', 'numaromaticcarbocycles', 'fr_unbrch_alkane', 'fr_urea', 'fr_nitroso', 'smr_vsa10', 'fr_c_s', 'smr_vsa3', 'fr_methoxy', 'maxabspartialcharge', 'slogp_vsa9', 'heavyatomcount', 'fr_azide', 'chi3v', 'smr_vsa4', 'mollogp', 'chi0v', 'fr_aryl_methyl', 'fr_nh1', 'fpdensitymorgan3', 'fr_furan', 'fr_hdrzine', 'fr_arn', 'numaromaticrings', 'vsa_estate3', 'fr_azo', 'fr_halogen', 'estate_vsa9', 'fr_hdrzone', 'numhdonors', 'fr_alkyl_carbamate', 'fr_isothiocyan', 'minabspartialcharge', 'fr_al_coo', 'ringcount', 'chi1', 'estate_vsa7', 'fr_nitro_arom', 'vsa_estate9', 'minabsestateindex', 'maxabsestateindex', 'vsa_estate6', 'estate_vsa10', 'estate_vsa3', 'fr_n_o', 'fr_amidine', 'fr_thiocyan', 'fr_phos_acid', 'fr_c_o', 'fr_imide', 'numaliphaticrings', 'peoe_vsa6', 'vsa_estate2', 'nhohcount', 'numsaturatedheterocycles', 'slogp_vsa6', 'peoe_vsa14', 'fractioncsp3', 'bcut2d_mwlow', 'numaliphaticcarbocycles', 'fr_priamide', 'nacid', 'nbase', 'naromatom', 'narombond', 'sz', 'sm', 'sv', 'sse', 'spe', 'sare', 'sp', 'si', 'mz', 'mm', 'mv', 'mse', 'mpe', 'mare', 'mp', 'mi', 'xch_3d', 'xch_4d', 'xch_5d', 'xch_6d', 'xch_7d', 'xch_3dv', 'xch_4dv', 'xch_5dv', 'xch_6dv', 'xch_7dv', 'xc_3d', 'xc_4d', 'xc_5d', 'xc_6d', 'xc_3dv', 'xc_4dv', 'xc_5dv', 'xc_6dv', 'xpc_4d', 'xpc_5d', 'xpc_6d', 'xpc_4dv', 'xpc_5dv', 'xpc_6dv', 'xp_0d', 'xp_1d', 'xp_2d', 'xp_3d', 'xp_4d', 'xp_5d', 'xp_6d', 'xp_7d', 'axp_0d', 'axp_1d', 'axp_2d', 'axp_3d', 'axp_4d', 'axp_5d', 'axp_6d', 'axp_7d', 'xp_0dv', 'xp_1dv', 'xp_2dv', 'xp_3dv', 'xp_4dv', 'xp_5dv', 'xp_6dv', 'xp_7dv', 'axp_0dv', 'axp_1dv', 'axp_2dv', 'axp_3dv', 'axp_4dv', 'axp_5dv', 'axp_6dv', 'axp_7dv', 'c1sp1', 'c2sp1', 'c1sp2', 'c2sp2', 'c3sp2', 'c1sp3', 'c2sp3', 'c3sp3', 'c4sp3', 'hybratio', 'fcsp3', 'num_stereocenters', 'num_unspecified_stereocenters', 'num_defined_stereocenters', 'num_r_centers', 'num_s_centers', 'num_stereobonds', 'num_e_bonds', 'num_z_bonds', 'stereo_complexity', 'frac_defined_stereo', 'tertiary_amine_count', 'type_i_pattern_count', 'type_ii_pattern_count', 'aromatic_interaction_score', 'molecular_axis_length', 'molecular_asymmetry', 'molecular_volume_3d', 'radius_of_gyration', 'asphericity', 'charge_centroid_distance', 'nitrogen_span', 'amide_count', 'hba_hbd_ratio', 'intramolecular_hbond_potential', 'amphiphilic_moment'],
    "model_class": PyTorch,
    "model_metrics_s3_path": "s3://ideaya-sageworks-bucket/models/caco2-er-reg-pytorch-test/training",
    "train_all_data": False,
}

import awswrangler as wr
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from io import StringIO
import json
import argparse
import joblib
import os
import pandas as pd
from typing import List

# Global model_type for both training and inference
model_type = TEMPLATE_PARAMS["model_type"]


# Function to check if dataframe is empty
def check_dataframe(df: pd.DataFrame, df_name: str) -> None:
    """Check if the DataFrame is empty and raise an error if so."""
    if df.empty:
        msg = f"*** The training data {df_name} has 0 rows! ***STOPPING***"
        print(msg)
        raise ValueError(msg)


# Function to expand probability column into individual class probability columns
def expand_proba_column(df: pd.DataFrame, class_labels: List[str]) -> pd.DataFrame:
    """Expand 'pred_proba' column into separate columns for each class label."""
    proba_column = "pred_proba"
    if proba_column not in df.columns:
        raise ValueError('DataFrame does not contain a "pred_proba" column')

    # Create new columns for each class label's probability
    new_col_names = [f"{label}_proba" for label in class_labels]
    proba_df = pd.DataFrame(df[proba_column].tolist(), columns=new_col_names)

    # Drop the original 'pred_proba' column and reset the index
    df = df.drop(columns=[proba_column]).reset_index(drop=True)

    # Concatenate the new probability columns with the original DataFrame
    df = pd.concat([df, proba_df], axis=1)
    return df


# Function to match DataFrame columns to model features (case-insensitive)
def match_features_case_insensitive(df: pd.DataFrame, model_features: list) -> pd.DataFrame:
    """Match and rename DataFrame columns to match the model's features, case-insensitively."""
    # Create a set of exact matches from the DataFrame columns
    exact_match_set = set(df.columns)

    # Create a case-insensitive map of DataFrame columns
    column_map = {col.lower(): col for col in df.columns}
    rename_dict = {}

    # Build a dictionary for renaming columns based on case-insensitive matching
    for feature in model_features:
        if feature in exact_match_set:
            rename_dict[feature] = feature
        elif feature.lower() in column_map:
            rename_dict[column_map[feature.lower()]] = feature

    # Rename columns in the DataFrame to match model features
    return df.rename(columns=rename_dict)


#
# Training Section
#
if __name__ == "__main__":
    # Template Parameters
    target = TEMPLATE_PARAMS["target_column"]  # Can be None for unsupervised models
    feature_list = TEMPLATE_PARAMS["feature_list"]
    model_class = TEMPLATE_PARAMS["model_class"]
    model_metrics_s3_path = TEMPLATE_PARAMS["model_metrics_s3_path"]
    train_all_data = TEMPLATE_PARAMS["train_all_data"]
    validation_split = 0.2

    # Script arguments for input/output directories
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-dir", type=str, default=os.environ.get("SM_MODEL_DIR", "/opt/ml/model"))
    parser.add_argument("--train", type=str, default=os.environ.get("SM_CHANNEL_TRAIN", "/opt/ml/input/data/train"))
    parser.add_argument(
        "--output-data-dir", type=str, default=os.environ.get("SM_OUTPUT_DATA_DIR", "/opt/ml/output/data")
    )
    args = parser.parse_args()

    # Load training data from the specified directory
    training_files = [os.path.join(args.train, file) for file in os.listdir(args.train) if file.endswith(".csv")]
    all_df = pd.concat([pd.read_csv(file, engine="python") for file in training_files])

    # Check if the DataFrame is empty
    check_dataframe(all_df, "training_df")

    # Initialize the model using the specified model class
    model = model_class()

    # Determine if standardization is needed based on the model type
    needs_standardization = model_type in ["clusterer", "projection"]

    if needs_standardization:
        # Create a pipeline with standardization and the model
        model = Pipeline([("scaler", StandardScaler()), ("model", model)])

    # Handle logic based on the model_type
    if model_type in ["classifier", "regressor"]:
        # Supervised Models: Prepare for training
        if train_all_data:
            # Use all data for both training and validation
            print("Training on all data...")
            df_train = all_df.copy()
            df_val = all_df.copy()
        elif "training" in all_df.columns:
            # Split data based on a 'training' column if it exists
            print("Splitting data based on 'training' column...")
            df_train = all_df[all_df["training"]].copy()
            df_val = all_df[~all_df["training"]].copy()
        else:
            # Perform a random split if no 'training' column is found
            print("Splitting data randomly...")
            df_train, df_val = train_test_split(all_df, test_size=validation_split, random_state=42)

        # Encode the target variable if the model is a classifier
        label_encoder = None
        if model_type == "classifier" and target:
            label_encoder = LabelEncoder()
            df_train[target] = label_encoder.fit_transform(df_train[target])
            df_val[target] = label_encoder.transform(df_val[target])

        # Prepare features and targets for training
        X_train = df_train[feature_list]
        X_val = df_val[feature_list]
        y_train = df_train[target] if target else None
        y_val = df_val[target] if target else None

        # Train the model using the training data
        model.fit(X_train, y_train)

        # Make predictions and handle classification-specific logic
        preds = model.predict(X_val)
        if model_type == "classifier" and target:
            # Get class probabilities and expand them into separate columns
            probs = model.predict_proba(X_val)
            df_val["pred_proba"] = [p.tolist() for p in probs]
            df_val = expand_proba_column(df_val, label_encoder.classes_)

            # Decode the target and prediction labels
            df_val[target] = label_encoder.inverse_transform(df_val[target])
            preds = label_encoder.inverse_transform(preds)

        # Add predictions to the validation DataFrame
        df_val["prediction"] = preds

        # Save the validation predictions to S3
        output_columns = [target, "prediction"] + [col for col in df_val.columns if col.endswith("_proba")]
        wr.s3.to_csv(df_val[output_columns], path=f"{model_metrics_s3_path}/validation_predictions.csv", index=False)

    elif model_type == "clusterer":
        # Unsupervised Clustering Models: Assign cluster labels
        all_df["cluster"] = model.fit_predict(all_df[feature_list])

    elif model_type == "projection":
        # Projection Models: Apply transformation and label first three components as x, y, z
        transformed_data = model.fit_transform(all_df[feature_list])
        num_components = transformed_data.shape[1]

        # Special labels for the first three components, if they exist
        special_labels = ["x", "y", "z"]
        for i in range(num_components):
            if i < len(special_labels):
                all_df[special_labels[i]] = transformed_data[:, i]
            else:
                all_df[f"component_{i + 1}"] = transformed_data[:, i]

    elif model_type == "transformer":
        # Transformer Models: Apply transformation and use generic component labels
        transformed_data = model.fit_transform(all_df[feature_list])
        for i in range(transformed_data.shape[1]):
            all_df[f"component_{i + 1}"] = transformed_data[:, i]

    # Save the trained model and any necessary assets
    joblib.dump(model, os.path.join(args.model_dir, "model.joblib"))
    if model_type == "classifier" and label_encoder:
        joblib.dump(label_encoder, os.path.join(args.model_dir, "label_encoder.joblib"))

    # Save the feature list to validate input during predictions
    with open(os.path.join(args.model_dir, "feature_columns.json"), "w") as fp:
        json.dump(feature_list, fp)


#
# Inference Section
#
def model_fn(model_dir):
    """Load and return the model from the specified directory."""
    return joblib.load(os.path.join(model_dir, "model.joblib"))


def input_fn(input_data, content_type):
    """Parse input data and return a DataFrame."""
    if not input_data:
        raise ValueError("Empty input data is not supported!")

    # Decode bytes to string if necessary
    if isinstance(input_data, bytes):
        input_data = input_data.decode("utf-8")

    if "text/csv" in content_type:
        return pd.read_csv(StringIO(input_data))
    elif "application/json" in content_type:
        return pd.DataFrame(json.loads(input_data))  # Assumes JSON array of records
    else:
        raise ValueError(f"{content_type} not supported!")


def output_fn(output_df, accept_type):
    """Supports both CSV and JSON output formats."""
    if "text/csv" in accept_type:
        csv_output = output_df.fillna("N/A").to_csv(index=False)  # CSV with N/A for missing values
        return csv_output, "text/csv"
    elif "application/json" in accept_type:
        return output_df.to_json(orient="records"), "application/json"  # JSON array of records (NaNs -> null)
    else:
        raise RuntimeError(f"{accept_type} accept type is not supported by this script.")


def predict_fn(df, model):
    """Make predictions or apply transformations using the model and return the DataFrame with results."""
    model_dir = os.environ.get("SM_MODEL_DIR", "/opt/ml/model")

    # Load feature columns from the saved file
    with open(os.path.join(model_dir, "feature_columns.json")) as fp:
        model_features = json.load(fp)

    # Load label encoder if available (for classification models)
    label_encoder = None
    if os.path.exists(os.path.join(model_dir, "label_encoder.joblib")):
        label_encoder = joblib.load(os.path.join(model_dir, "label_encoder.joblib"))

    # Match features in a case-insensitive manner
    matched_df = match_features_case_insensitive(df, model_features)

    # Initialize a dictionary to store the results
    results = {}

    # Determine how to handle the model based on its available methods
    if hasattr(model, "predict"):
        # For supervised models (classifier or regressor)
        predictions = model.predict(matched_df[model_features])
        results["prediction"] = predictions

    elif hasattr(model, "fit_predict"):
        # For clustering models (e.g., DBSCAN)
        clusters = model.fit_predict(matched_df[model_features])
        results["cluster"] = clusters

    elif hasattr(model, "fit_transform") and not hasattr(model, "predict"):
        # For transformation/projection models (e.g., t-SNE, PCA)
        transformed_data = model.fit_transform(matched_df[model_features])

        # Handle 2D projection models specifically
        if model_type == "projection" and transformed_data.shape[1] == 2:
            results["x"] = transformed_data[:, 0]
            results["y"] = transformed_data[:, 1]
        else:
            # General case for any number of components
            for i in range(transformed_data.shape[1]):
                results[f"component_{i + 1}"] = transformed_data[:, i]

    else:
        # Raise an error if the model does not support the expected methods
        raise ValueError("Model does not support predict, fit_predict, or fit_transform methods.")

    # Decode predictions if using a label encoder (for classification)
    if label_encoder and "prediction" in results:
        results["prediction"] = label_encoder.inverse_transform(results["prediction"])

    # Add the results to the DataFrame
    for key, value in results.items():
        df[key] = value

    # Add probability columns if the model supports it (for classification)
    if hasattr(model, "predict_proba"):
        probs = model.predict_proba(matched_df[model_features])
        df["pred_proba"] = [p.tolist() for p in probs]
        df = expand_proba_column(df, label_encoder.classes_)

    # Return the modified DataFrame
    return df
