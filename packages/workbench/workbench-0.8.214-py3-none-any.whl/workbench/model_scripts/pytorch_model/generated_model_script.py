# PyTorch Tabular Model Template for Workbench
#
# This template handles both classification and regression models with:
# - K-fold cross-validation ensemble training (or single train/val split)
# - Out-of-fold predictions for validation metrics
# - Categorical feature embedding via TabularMLP
# - Compressed feature decompression

import argparse
import json
import os

import awswrangler as wr
import joblib
import numpy as np
import pandas as pd
import torch
from sklearn.model_selection import KFold, StratifiedKFold, train_test_split
from sklearn.preprocessing import LabelEncoder

# Enable Tensor Core optimization for GPUs that support it
torch.set_float32_matmul_precision("medium")

from model_script_utils import (
    check_dataframe,
    compute_classification_metrics,
    compute_regression_metrics,
    convert_categorical_types,
    decompress_features,
    expand_proba_column,
    input_fn,
    match_features_case_insensitive,
    output_fn,
    print_classification_metrics,
    print_confusion_matrix,
    print_regression_metrics,
)
from pytorch_utils import (
    FeatureScaler,
    create_model,
    load_model,
    predict,
    prepare_data,
    save_model,
    train_model,
)
from uq_harness import (
    compute_confidence,
    load_uq_models,
    predict_intervals,
    save_uq_models,
    train_uq_models,
)

# =============================================================================
# Default Hyperparameters
# =============================================================================
DEFAULT_HYPERPARAMETERS = {
    # Training parameters
    "n_folds": 5,
    "max_epochs": 200,
    "early_stopping_patience": 20,
    "batch_size": 128,
    # Model architecture
    "layers": "256-128-64",
    "learning_rate": 1e-3,
    "dropout": 0.1,
    "use_batch_norm": True,
    # Random seed
    "seed": 42,
}

# Template parameters (filled in by Workbench)
TEMPLATE_PARAMS = {
    "model_type": "uq_regressor",
    "target": "udm_asy_res_efflux_ratio",
    "features": ['smr_vsa4', 'tpsa', 'numhdonors', 'nhohcount', 'nbase', 'vsa_estate3', 'fr_guanido', 'mollogp', 'peoe_vsa8', 'peoe_vsa1', 'fr_imine', 'vsa_estate2', 'estate_vsa10', 'asphericity', 'xc_3dv', 'smr_vsa3', 'charge_centroid_distance', 'c3sp3', 'nitrogen_span', 'estate_vsa2', 'minpartialcharge', 'hba_hbd_ratio', 'slogp_vsa1', 'axp_7d', 'nocount', 'vsa_estate4', 'vsa_estate6', 'estate_vsa4', 'xc_4dv', 'xc_4d', 'num_s_centers', 'vsa_estate9', 'chi2v', 'axp_5d', 'mi', 'mse', 'bcut2d_mrhi', 'smr_vsa6', 'hallkieralpha', 'balabanj', 'amphiphilic_moment', 'type_ii_pattern_count', 'minabsestateindex', 'bcut2d_mwlow', 'axp_0dv', 'slogp_vsa5', 'axp_2d', 'axp_1dv', 'xch_5d', 'peoe_vsa10', 'molecular_asymmetry', 'kappa3', 'estate_vsa3', 'sse', 'bcut2d_logphi', 'fr_imidazole', 'molecular_volume_3d', 'bertzct', 'maxestateindex', 'aromatic_interaction_score', 'axp_3d', 'radius_of_gyration', 'vsa_estate7', 'si', 'axp_5dv', 'molecular_axis_length', 'estate_vsa6', 'fpdensitymorgan1', 'axp_6d', 'estate_vsa9', 'fpdensitymorgan2', 'xp_0dv', 'xp_6dv', 'molmr', 'qed', 'estate_vsa8', 'peoe_vsa9', 'xch_6dv', 'xp_7d', 'slogp_vsa2', 'xp_5dv', 'bcut2d_chghi', 'xch_6d', 'chi0n', 'slogp_vsa3', 'chi1v', 'chi3v', 'bcut2d_chglo', 'axp_1d', 'mp', 'num_defined_stereocenters', 'xp_3dv', 'bcut2d_mrlow', 'fr_al_oh', 'peoe_vsa7', 'chi2n', 'axp_6dv', 'axp_2dv', 'chi4n', 'xc_3d', 'axp_7dv', 'vsa_estate8', 'xch_7d', 'maxpartialcharge', 'chi1n', 'peoe_vsa2', 'axp_3dv', 'bcut2d_logplow', 'mv', 'xpc_5dv', 'kappa2', 'vsa_estate5', 'xp_5d', 'mm', 'maxabspartialcharge', 'axp_4dv', 'maxabsestateindex', 'axp_4d', 'xch_4dv', 'xp_2dv', 'heavyatommolwt', 'numatomstereocenters', 'xp_7dv', 'numsaturatedheterocycles', 'xp_3d', 'kappa1', 'mz', 'axp_0d', 'chi1', 'xch_4d', 'smr_vsa1', 'xp_2d', 'estate_vsa5', 'phi', 'fr_ether', 'xc_5d', 'c1sp3', 'estate_vsa7', 'estate_vsa1', 'vsa_estate1', 'slogp_vsa4', 'avgipc', 'smr_vsa10', 'numvalenceelectrons', 'xc_5dv', 'peoe_vsa12', 'peoe_vsa6', 'xpc_5d', 'xpc_6d', 'minestateindex', 'chi3n', 'smr_vsa5', 'xp_4d', 'numheteroatoms', 'fpdensitymorgan3', 'xpc_4d', 'sps', 'xp_1d', 'sv', 'fr_ar_n', 'slogp_vsa10', 'c2sp3', 'xpc_4dv', 'chi0v', 'xpc_6dv', 'xp_1dv', 'vsa_estate10', 'sare', 'c2sp2', 'mpe', 'xch_7dv', 'chi4v', 'type_i_pattern_count', 'sp', 'slogp_vsa8', 'amide_count', 'num_stereocenters', 'num_r_centers', 'tertiary_amine_count', 'spe', 'xp_4dv', 'numsaturatedrings', 'mare', 'numhacceptors', 'chi0', 'fractioncsp3', 'fr_nh0', 'xch_5dv', 'fr_aniline', 'smr_vsa7', 'labuteasa', 'c3sp2', 'xp_0d', 'xp_6d', 'peoe_vsa11', 'fr_ar_nh', 'molwt', 'intramolecular_hbond_potential', 'peoe_vsa3', 'fr_nhpyrrole', 'numaliphaticrings', 'hybratio', 'smr_vsa9', 'peoe_vsa13', 'bcut2d_mwhi', 'c1sp2', 'slogp_vsa11', 'numrotatablebonds', 'numaliphaticcarbocycles', 'slogp_vsa6', 'peoe_vsa4', 'numunspecifiedatomstereocenters', 'xc_6d', 'xc_6dv', 'num_unspecified_stereocenters', 'sz', 'minabspartialcharge', 'fcsp3', 'c1sp1', 'fr_piperzine', 'numaliphaticheterocycles', 'numamidebonds', 'fr_benzene', 'numaromaticheterocycles', 'sm', 'fr_priamide', 'fr_piperdine', 'fr_methoxy', 'c4sp3', 'fr_c_o_nocoo', 'exactmolwt', 'stereo_complexity', 'fr_hoccn', 'numaromaticcarbocycles', 'fr_nh2', 'numheterocycles', 'fr_morpholine', 'fr_ketone', 'fr_nh1', 'frac_defined_stereo', 'fr_aryl_methyl', 'fr_alkyl_halide', 'fr_phenol', 'fr_al_oh_notert', 'fr_ar_oh', 'fr_pyridine', 'fr_amide', 'slogp_vsa7', 'fr_halogen', 'numsaturatedcarbocycles', 'slogp_vsa12', 'fr_ndealkylation1', 'xch_3d', 'fr_bicyclic', 'naromatom', 'narombond'],
    "id_column": "udm_mol_bat_id",
    "compressed_features": [],
    "model_metrics_s3_path": "s3://ideaya-sageworks-bucket/models/caco2-er-reg-pytorch/training",
    "hyperparameters": {},
}


# =============================================================================
# Model Loading (for SageMaker inference)
# =============================================================================
def model_fn(model_dir: str) -> dict:
    """Load TabularMLP ensemble from the specified directory."""
    # Load ensemble metadata
    metadata_path = os.path.join(model_dir, "ensemble_metadata.joblib")
    if os.path.exists(metadata_path):
        metadata = joblib.load(metadata_path)
        n_ensemble = metadata["n_ensemble"]
    else:
        n_ensemble = 1

    # Determine device
    device = "cuda" if torch.cuda.is_available() else "cpu"

    # Load ensemble models
    ensemble_models = []
    for i in range(n_ensemble):
        model_path = os.path.join(model_dir, f"model_{i}")
        model = load_model(model_path, device=device)
        ensemble_models.append(model)

    print(f"Loaded {len(ensemble_models)} model(s)")

    # Load feature scaler
    scaler = FeatureScaler.load(os.path.join(model_dir, "scaler.joblib"))

    # Load UQ models (regression only)
    uq_models, uq_metadata = None, None
    uq_path = os.path.join(model_dir, "uq_metadata.json")
    if os.path.exists(uq_path):
        uq_models, uq_metadata = load_uq_models(model_dir)

    return {
        "ensemble_models": ensemble_models,
        "n_ensemble": n_ensemble,
        "scaler": scaler,
        "uq_models": uq_models,
        "uq_metadata": uq_metadata,
    }


# =============================================================================
# Inference (for SageMaker inference)
# =============================================================================
def predict_fn(df: pd.DataFrame, model_dict: dict) -> pd.DataFrame:
    """Make predictions with TabularMLP ensemble."""
    model_type = TEMPLATE_PARAMS["model_type"]
    compressed_features = TEMPLATE_PARAMS["compressed_features"]
    model_dir = os.environ.get("SM_MODEL_DIR", "/opt/ml/model")

    # Load artifacts
    ensemble_models = model_dict["ensemble_models"]
    scaler = model_dict["scaler"]
    uq_models = model_dict.get("uq_models")
    uq_metadata = model_dict.get("uq_metadata")

    with open(os.path.join(model_dir, "feature_columns.json")) as f:
        features = json.load(f)
    with open(os.path.join(model_dir, "category_mappings.json")) as f:
        category_mappings = json.load(f)
    with open(os.path.join(model_dir, "feature_metadata.json")) as f:
        feature_metadata = json.load(f)

    continuous_cols = feature_metadata["continuous_cols"]
    categorical_cols = feature_metadata["categorical_cols"]

    label_encoder = None
    encoder_path = os.path.join(model_dir, "label_encoder.joblib")
    if os.path.exists(encoder_path):
        label_encoder = joblib.load(encoder_path)

    print(f"Model Features: {features}")

    # Prepare features
    matched_df = match_features_case_insensitive(df, features)
    matched_df, _ = convert_categorical_types(matched_df, features, category_mappings)

    if compressed_features:
        print("Decompressing features for prediction...")
        matched_df, features = decompress_features(matched_df, features, compressed_features)

    # Track missing features
    missing_mask = matched_df[features].isna().any(axis=1)
    if missing_mask.any():
        print(f"Warning: {missing_mask.sum()} rows have missing features")

    # Initialize output columns
    df["prediction"] = np.nan
    if model_type in ["regressor", "uq_regressor"]:
        df["prediction_std"] = np.nan

    complete_df = matched_df[~missing_mask].copy()
    if len(complete_df) == 0:
        print("Warning: No complete rows to predict on")
        return df

    # Prepare data for inference (with standardization)
    x_cont, x_cat, _, _, _ = prepare_data(
        complete_df, continuous_cols, categorical_cols, category_mappings=category_mappings, scaler=scaler
    )

    # Collect ensemble predictions
    all_preds = []
    for model in ensemble_models:
        preds = predict(model, x_cont, x_cat)
        all_preds.append(preds)

    # Aggregate predictions
    ensemble_preds = np.stack(all_preds, axis=0)
    preds = np.mean(ensemble_preds, axis=0)
    preds_std = np.std(ensemble_preds, axis=0)

    print(f"Inference complete: {len(preds)} predictions, {len(ensemble_models)} ensemble members")

    if label_encoder is not None:
        # Classification: average probabilities, then argmax
        avg_probs = preds  # Already softmax output
        class_preds = np.argmax(avg_probs, axis=1)
        predictions = label_encoder.inverse_transform(class_preds)

        all_proba = pd.Series([None] * len(df), index=df.index, dtype=object)
        all_proba.loc[~missing_mask] = [p.tolist() for p in avg_probs]
        df["pred_proba"] = all_proba
        df = expand_proba_column(df, label_encoder.classes_)
    else:
        # Regression
        predictions = preds.flatten()
        df.loc[~missing_mask, "prediction_std"] = preds_std.flatten()

        # Add UQ intervals if available
        if uq_models and uq_metadata:
            X_complete = complete_df[features]
            df_complete = df.loc[~missing_mask].copy()
            df_complete["prediction"] = predictions  # Set prediction before compute_confidence
            df_complete = predict_intervals(df_complete, X_complete, uq_models, uq_metadata)
            df_complete = compute_confidence(df_complete, uq_metadata["median_interval_width"], "q_10", "q_90")
            # Copy UQ columns back to main dataframe
            for col in df_complete.columns:
                if col.startswith("q_") or col == "confidence":
                    df.loc[~missing_mask, col] = df_complete[col].values

    df.loc[~missing_mask, "prediction"] = predictions
    return df


# =============================================================================
# Training
# =============================================================================
if __name__ == "__main__":
    # -------------------------------------------------------------------------
    # Setup: Parse arguments and load data
    # -------------------------------------------------------------------------
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-dir", type=str, default=os.environ.get("SM_MODEL_DIR", "/opt/ml/model"))
    parser.add_argument("--train", type=str, default=os.environ.get("SM_CHANNEL_TRAIN", "/opt/ml/input/data/train"))
    parser.add_argument("--output-data-dir", type=str, default=os.environ.get("SM_OUTPUT_DATA_DIR", "/opt/ml/output/data"))
    args = parser.parse_args()

    # Extract template parameters
    target = TEMPLATE_PARAMS["target"]
    features = TEMPLATE_PARAMS["features"]
    orig_features = features.copy()
    id_column = TEMPLATE_PARAMS["id_column"]
    compressed_features = TEMPLATE_PARAMS["compressed_features"]
    model_type = TEMPLATE_PARAMS["model_type"]
    model_metrics_s3_path = TEMPLATE_PARAMS["model_metrics_s3_path"]
    hyperparameters = {**DEFAULT_HYPERPARAMETERS, **(TEMPLATE_PARAMS["hyperparameters"] or {})}

    # Load training data
    training_files = [os.path.join(args.train, f) for f in os.listdir(args.train) if f.endswith(".csv")]
    print(f"Training Files: {training_files}")
    all_df = pd.concat([pd.read_csv(f, engine="python") for f in training_files])
    check_dataframe(all_df, "training_df")

    # Drop rows with missing features
    initial_count = len(all_df)
    all_df = all_df.dropna(subset=features)
    if len(all_df) < initial_count:
        print(f"Dropped {initial_count - len(all_df)} rows with missing features")

    print(f"Target: {target}")
    print(f"Features: {features}")
    print(f"Hyperparameters: {hyperparameters}")

    # -------------------------------------------------------------------------
    # Preprocessing
    # -------------------------------------------------------------------------
    all_df, category_mappings = convert_categorical_types(all_df, features)

    if compressed_features:
        print(f"Decompressing features: {compressed_features}")
        all_df, features = decompress_features(all_df, features, compressed_features)

    # Determine categorical vs continuous columns
    categorical_cols = [c for c in features if all_df[c].dtype.name == "category"]
    continuous_cols = [c for c in features if c not in categorical_cols]
    all_df[continuous_cols] = all_df[continuous_cols].astype("float64")
    print(f"Categorical: {categorical_cols}")
    print(f"Continuous: {len(continuous_cols)} columns")

    # -------------------------------------------------------------------------
    # Classification setup
    # -------------------------------------------------------------------------
    label_encoder = None
    n_outputs = 1
    if model_type == "classifier":
        label_encoder = LabelEncoder()
        all_df[target] = label_encoder.fit_transform(all_df[target])
        n_outputs = len(label_encoder.classes_)
        print(f"Class labels: {label_encoder.classes_.tolist()}")

    # -------------------------------------------------------------------------
    # Cross-validation setup
    # -------------------------------------------------------------------------
    n_folds = hyperparameters["n_folds"]
    task = "classification" if model_type == "classifier" else "regression"
    hidden_layers = [int(x) for x in hyperparameters["layers"].split("-")]

    # Get categorical cardinalities
    categorical_cardinalities = [len(category_mappings.get(col, {})) for col in categorical_cols]

    if n_folds == 1:
        if "training" in all_df.columns:
            print("Using 'training' column for train/val split")
            train_idx = np.where(all_df["training"])[0]
            val_idx = np.where(~all_df["training"])[0]
        else:
            print("WARNING: No 'training' column found, using random 80/20 split")
            train_idx, val_idx = train_test_split(np.arange(len(all_df)), test_size=0.2, random_state=42)
        folds = [(train_idx, val_idx)]
    else:
        if model_type == "classifier":
            kfold = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=42)
            folds = list(kfold.split(all_df, all_df[target]))
        else:
            kfold = KFold(n_splits=n_folds, shuffle=True, random_state=42)
            folds = list(kfold.split(all_df))

    print(f"Training {'single model' if n_folds == 1 else f'{n_folds}-fold ensemble'}...")

    # Fit scaler on all training data (used across all folds)
    scaler = FeatureScaler()
    scaler.fit(all_df, continuous_cols)
    print(f"Fitted scaler on {len(continuous_cols)} continuous features")

    # Determine device
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")

    # -------------------------------------------------------------------------
    # Training loop
    # -------------------------------------------------------------------------
    oof_predictions = np.full((len(all_df), n_outputs), np.nan, dtype=np.float64)

    ensemble_models = []
    for fold_idx, (train_idx, val_idx) in enumerate(folds):
        print(f"\n{'='*50}")
        print(f"Fold {fold_idx + 1}/{len(folds)} - Train: {len(train_idx)}, Val: {len(val_idx)}")
        print(f"{'='*50}")

        df_train = all_df.iloc[train_idx].reset_index(drop=True)
        df_val = all_df.iloc[val_idx].reset_index(drop=True)

        # Prepare data (using pre-fitted scaler)
        train_x_cont, train_x_cat, train_y, _, _ = prepare_data(
            df_train, continuous_cols, categorical_cols, target, category_mappings, scaler=scaler
        )
        val_x_cont, val_x_cat, val_y, _, _ = prepare_data(
            df_val, continuous_cols, categorical_cols, target, category_mappings, scaler=scaler
        )

        # Create model
        torch.manual_seed(hyperparameters["seed"] + fold_idx)
        model = create_model(
            n_continuous=len(continuous_cols),
            categorical_cardinalities=categorical_cardinalities,
            hidden_layers=hidden_layers,
            n_outputs=n_outputs,
            task=task,
            dropout=hyperparameters["dropout"],
            use_batch_norm=hyperparameters["use_batch_norm"],
        )

        # Train
        model, history = train_model(
            model,
            train_x_cont, train_x_cat, train_y,
            val_x_cont, val_x_cat, val_y,
            task=task,
            max_epochs=hyperparameters["max_epochs"],
            patience=hyperparameters["early_stopping_patience"],
            batch_size=hyperparameters["batch_size"],
            learning_rate=hyperparameters["learning_rate"],
            device=device,
        )
        ensemble_models.append(model)

        # Out-of-fold predictions
        fold_preds = predict(model, val_x_cont, val_x_cat)
        oof_predictions[val_idx] = fold_preds

    print(f"\nTraining complete! Trained {len(ensemble_models)} model(s).")

    # -------------------------------------------------------------------------
    # Prepare validation results
    # -------------------------------------------------------------------------
    if n_folds == 1:
        val_mask = ~np.isnan(oof_predictions[:, 0])
        df_val = all_df[val_mask].copy()
        predictions = oof_predictions[val_mask]
    else:
        df_val = all_df.copy()
        predictions = oof_predictions

    # Decode labels for classification
    if model_type == "classifier":
        class_preds = np.argmax(predictions, axis=1)
        df_val[target] = label_encoder.inverse_transform(df_val[target].astype(int))
        df_val["prediction"] = label_encoder.inverse_transform(class_preds)
        df_val["pred_proba"] = [p.tolist() for p in predictions]
        df_val = expand_proba_column(df_val, label_encoder.classes_)
    else:
        df_val["prediction"] = predictions.flatten()

    # -------------------------------------------------------------------------
    # Compute and print metrics
    # -------------------------------------------------------------------------
    y_true = df_val[target].values
    y_pred = df_val["prediction"].values

    if model_type == "classifier":
        score_df = compute_classification_metrics(y_true, y_pred, label_encoder.classes_, target)
        print_classification_metrics(score_df, target, label_encoder.classes_)
        print_confusion_matrix(y_true, y_pred, label_encoder.classes_)
    else:
        metrics = compute_regression_metrics(y_true, y_pred)
        print_regression_metrics(metrics)

        # Compute ensemble prediction_std
        if n_folds > 1:
            # Re-run inference with all models to get std
            x_cont, x_cat, _, _, _ = prepare_data(
                df_val, continuous_cols, categorical_cols, category_mappings=category_mappings, scaler=scaler
            )
            all_preds = [predict(m, x_cont, x_cat).flatten() for m in ensemble_models]
            df_val["prediction_std"] = np.std(np.stack(all_preds), axis=0)
            print(f"Ensemble std - mean: {df_val['prediction_std'].mean():.4f}, max: {df_val['prediction_std'].max():.4f}")
        else:
            df_val["prediction_std"] = 0.0

        # Train UQ models for uncertainty quantification
        print("\n" + "=" * 50)
        print("Training UQ Models")
        print("=" * 50)
        uq_models, uq_metadata = train_uq_models(
            all_df[features], all_df[target], df_val[features], y_true
        )
        df_val = predict_intervals(df_val, df_val[features], uq_models, uq_metadata)
        df_val = compute_confidence(df_val, uq_metadata["median_interval_width"])

    # -------------------------------------------------------------------------
    # Save validation predictions to S3
    # -------------------------------------------------------------------------
    output_columns = []
    if id_column in df_val.columns:
        output_columns.append(id_column)
    output_columns += [target, "prediction"]

    if model_type != "classifier":
        output_columns.append("prediction_std")
        output_columns += [c for c in df_val.columns if c.startswith("q_") or c == "confidence"]

    output_columns += [c for c in df_val.columns if c.endswith("_proba")]

    wr.s3.to_csv(df_val[output_columns], f"{model_metrics_s3_path}/validation_predictions.csv", index=False)

    # -------------------------------------------------------------------------
    # Save model artifacts
    # -------------------------------------------------------------------------
    model_config = {
        "n_continuous": len(continuous_cols),
        "categorical_cardinalities": categorical_cardinalities,
        "hidden_layers": hidden_layers,
        "n_outputs": n_outputs,
        "task": task,
        "dropout": hyperparameters["dropout"],
        "use_batch_norm": hyperparameters["use_batch_norm"],
    }

    for idx, m in enumerate(ensemble_models):
        save_model(m, os.path.join(args.model_dir, f"model_{idx}"), model_config)
    print(f"Saved {len(ensemble_models)} model(s)")

    joblib.dump({"n_ensemble": len(ensemble_models), "n_folds": n_folds}, os.path.join(args.model_dir, "ensemble_metadata.joblib"))

    with open(os.path.join(args.model_dir, "feature_columns.json"), "w") as f:
        json.dump(orig_features, f)

    with open(os.path.join(args.model_dir, "category_mappings.json"), "w") as f:
        json.dump(category_mappings, f)

    with open(os.path.join(args.model_dir, "feature_metadata.json"), "w") as f:
        json.dump({"continuous_cols": continuous_cols, "categorical_cols": categorical_cols}, f)

    with open(os.path.join(args.model_dir, "hyperparameters.json"), "w") as f:
        json.dump(hyperparameters, f, indent=2)

    scaler.save(os.path.join(args.model_dir, "scaler.joblib"))

    if label_encoder:
        joblib.dump(label_encoder, os.path.join(args.model_dir, "label_encoder.joblib"))

    if model_type != "classifier":
        save_uq_models(uq_models, uq_metadata, args.model_dir)

    print(f"\nModel training complete! Artifacts saved to {args.model_dir}")
