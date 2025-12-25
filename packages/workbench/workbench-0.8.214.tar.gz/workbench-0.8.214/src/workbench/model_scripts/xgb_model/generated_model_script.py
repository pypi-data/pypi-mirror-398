# XGBoost Model Template for Workbench
#
# This template handles both classification and regression models with:
# - K-fold cross-validation ensemble training (or single train/val split)
# - Out-of-fold predictions for validation metrics
# - Uncertainty quantification for regression models
# - Sample weights support
# - Categorical feature handling
# - Compressed feature decompression

import argparse
import json
import os

import awswrangler as wr
import joblib
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import KFold, StratifiedKFold, train_test_split
from sklearn.preprocessing import LabelEncoder

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
    "n_folds": 5,  # Number of CV folds (1 = single train/val split)
    # Core tree parameters
    "n_estimators": 200,
    "max_depth": 6,
    "learning_rate": 0.05,
    # Sampling parameters
    "subsample": 0.7,
    "colsample_bytree": 0.6,
    "colsample_bylevel": 0.8,
    # Regularization
    "min_child_weight": 5,
    "gamma": 0.2,
    "reg_alpha": 0.5,
    "reg_lambda": 2.0,
    # Random seed
    "random_state": 42,
}

# Workbench-specific parameters (not passed to XGBoost)
WORKBENCH_PARAMS = {"n_folds"}

# Template parameters (filled in by Workbench)
TEMPLATE_PARAMS = {
    "model_type": "uq_regressor",
    "target": "udm_asy_res_efflux_ratio",
    "features": ['chi2v', 'fr_sulfone', 'chi1v', 'bcut2d_logplow', 'fr_piperzine', 'kappa3', 'smr_vsa1', 'slogp_vsa5', 'fr_ketone_topliss', 'fr_sulfonamd', 'fr_imine', 'fr_benzene', 'fr_ester', 'chi2n', 'labuteasa', 'peoe_vsa2', 'smr_vsa6', 'bcut2d_chglo', 'fr_sh', 'peoe_vsa1', 'fr_allylic_oxid', 'chi4n', 'fr_ar_oh', 'fr_nh0', 'fr_term_acetylene', 'slogp_vsa7', 'slogp_vsa4', 'estate_vsa1', 'vsa_estate4', 'numbridgeheadatoms', 'numheterocycles', 'fr_ketone', 'fr_morpholine', 'fr_guanido', 'estate_vsa2', 'numheteroatoms', 'fr_nitro_arom_nonortho', 'fr_piperdine', 'nocount', 'numspiroatoms', 'fr_aniline', 'fr_thiophene', 'slogp_vsa10', 'fr_amide', 'slogp_vsa2', 'fr_epoxide', 'vsa_estate7', 'fr_ar_coo', 'fr_imidazole', 'fr_nitrile', 'fr_oxazole', 'numsaturatedrings', 'fr_pyridine', 'fr_hoccn', 'fr_ndealkylation1', 'numaliphaticheterocycles', 'fr_phenol', 'maxpartialcharge', 'vsa_estate5', 'peoe_vsa13', 'minpartialcharge', 'qed', 'fr_al_oh', 'slogp_vsa11', 'chi0n', 'fr_bicyclic', 'peoe_vsa12', 'fpdensitymorgan1', 'fr_oxime', 'molwt', 'fr_dihydropyridine', 'smr_vsa5', 'peoe_vsa5', 'fr_nitro', 'hallkieralpha', 'heavyatommolwt', 'fr_alkyl_halide', 'peoe_vsa8', 'fr_nhpyrrole', 'fr_isocyan', 'bcut2d_chghi', 'fr_lactam', 'peoe_vsa11', 'smr_vsa9', 'tpsa', 'chi4v', 'slogp_vsa1', 'phi', 'bcut2d_logphi', 'avgipc', 'estate_vsa11', 'fr_coo', 'bcut2d_mwhi', 'numunspecifiedatomstereocenters', 'vsa_estate10', 'estate_vsa8', 'numvalenceelectrons', 'fr_nh2', 'fr_lactone', 'vsa_estate1', 'estate_vsa4', 'numatomstereocenters', 'vsa_estate8', 'fr_para_hydroxylation', 'peoe_vsa3', 'fr_thiazole', 'peoe_vsa10', 'fr_ndealkylation2', 'slogp_vsa12', 'peoe_vsa9', 'maxestateindex', 'fr_quatn', 'smr_vsa7', 'minestateindex', 'numaromaticheterocycles', 'numrotatablebonds', 'fr_ar_nh', 'fr_ether', 'exactmolwt', 'fr_phenol_noorthohbond', 'slogp_vsa3', 'fr_ar_n', 'sps', 'fr_c_o_nocoo', 'bertzct', 'peoe_vsa7', 'slogp_vsa8', 'numradicalelectrons', 'molmr', 'fr_tetrazole', 'numsaturatedcarbocycles', 'bcut2d_mrhi', 'kappa1', 'numamidebonds', 'fpdensitymorgan2', 'smr_vsa8', 'chi1n', 'estate_vsa6', 'fr_barbitur', 'fr_diazo', 'kappa2', 'chi0', 'bcut2d_mrlow', 'balabanj', 'peoe_vsa4', 'numhacceptors', 'fr_sulfide', 'chi3n', 'smr_vsa2', 'fr_al_oh_notert', 'fr_benzodiazepine', 'fr_phos_ester', 'fr_aldehyde', 'fr_coo2', 'estate_vsa5', 'fr_prisulfonamd', 'numaromaticcarbocycles', 'fr_unbrch_alkane', 'fr_urea', 'fr_nitroso', 'smr_vsa10', 'fr_c_s', 'smr_vsa3', 'fr_methoxy', 'maxabspartialcharge', 'slogp_vsa9', 'heavyatomcount', 'fr_azide', 'chi3v', 'smr_vsa4', 'mollogp', 'chi0v', 'fr_aryl_methyl', 'fr_nh1', 'fpdensitymorgan3', 'fr_furan', 'fr_hdrzine', 'fr_arn', 'numaromaticrings', 'vsa_estate3', 'fr_azo', 'fr_halogen', 'estate_vsa9', 'fr_hdrzone', 'numhdonors', 'fr_alkyl_carbamate', 'fr_isothiocyan', 'minabspartialcharge', 'fr_al_coo', 'ringcount', 'chi1', 'estate_vsa7', 'fr_nitro_arom', 'vsa_estate9', 'minabsestateindex', 'maxabsestateindex', 'vsa_estate6', 'estate_vsa10', 'estate_vsa3', 'fr_n_o', 'fr_amidine', 'fr_thiocyan', 'fr_phos_acid', 'fr_c_o', 'fr_imide', 'numaliphaticrings', 'peoe_vsa6', 'vsa_estate2', 'nhohcount', 'numsaturatedheterocycles', 'slogp_vsa6', 'peoe_vsa14', 'fractioncsp3', 'bcut2d_mwlow', 'numaliphaticcarbocycles', 'fr_priamide', 'nacid', 'nbase', 'naromatom', 'narombond', 'sz', 'sm', 'sv', 'sse', 'spe', 'sare', 'sp', 'si', 'mz', 'mm', 'mv', 'mse', 'mpe', 'mare', 'mp', 'mi', 'xch_3d', 'xch_4d', 'xch_5d', 'xch_6d', 'xch_7d', 'xch_3dv', 'xch_4dv', 'xch_5dv', 'xch_6dv', 'xch_7dv', 'xc_3d', 'xc_4d', 'xc_5d', 'xc_6d', 'xc_3dv', 'xc_4dv', 'xc_5dv', 'xc_6dv', 'xpc_4d', 'xpc_5d', 'xpc_6d', 'xpc_4dv', 'xpc_5dv', 'xpc_6dv', 'xp_0d', 'xp_1d', 'xp_2d', 'xp_3d', 'xp_4d', 'xp_5d', 'xp_6d', 'xp_7d', 'axp_0d', 'axp_1d', 'axp_2d', 'axp_3d', 'axp_4d', 'axp_5d', 'axp_6d', 'axp_7d', 'xp_0dv', 'xp_1dv', 'xp_2dv', 'xp_3dv', 'xp_4dv', 'xp_5dv', 'xp_6dv', 'xp_7dv', 'axp_0dv', 'axp_1dv', 'axp_2dv', 'axp_3dv', 'axp_4dv', 'axp_5dv', 'axp_6dv', 'axp_7dv', 'c1sp1', 'c2sp1', 'c1sp2', 'c2sp2', 'c3sp2', 'c1sp3', 'c2sp3', 'c3sp3', 'c4sp3', 'hybratio', 'fcsp3', 'num_stereocenters', 'num_unspecified_stereocenters', 'num_defined_stereocenters', 'num_r_centers', 'num_s_centers', 'num_stereobonds', 'num_e_bonds', 'num_z_bonds', 'stereo_complexity', 'frac_defined_stereo', 'tertiary_amine_count', 'type_i_pattern_count', 'type_ii_pattern_count', 'aromatic_interaction_score', 'molecular_axis_length', 'molecular_asymmetry', 'molecular_volume_3d', 'radius_of_gyration', 'asphericity', 'charge_centroid_distance', 'nitrogen_span', 'amide_count', 'hba_hbd_ratio', 'intramolecular_hbond_potential', 'amphiphilic_moment'],
    "id_column": "udm_mol_bat_id",
    "compressed_features": [],
    "model_metrics_s3_path": "s3://ideaya-sageworks-bucket/models/caco2-er-reg-purple-all/training",
    "hyperparameters": None,
}


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

    print(f"Target: {target}")
    print(f"Features: {features}")
    print(f"Hyperparameters: {hyperparameters}")

    # -------------------------------------------------------------------------
    # Preprocessing: Categorical features and decompression
    # -------------------------------------------------------------------------
    all_df, category_mappings = convert_categorical_types(all_df, features)

    if compressed_features:
        print(f"Decompressing features: {compressed_features}")
        all_df, features = decompress_features(all_df, features, compressed_features)

    # -------------------------------------------------------------------------
    # Classification setup: Encode target labels
    # -------------------------------------------------------------------------
    label_encoder = None
    if model_type == "classifier":
        label_encoder = LabelEncoder()
        all_df[target] = label_encoder.fit_transform(all_df[target])
        print(f"Class labels: {label_encoder.classes_.tolist()}")

    # -------------------------------------------------------------------------
    # Cross-validation setup
    # -------------------------------------------------------------------------
    n_folds = hyperparameters["n_folds"]
    xgb_params = {k: v for k, v in hyperparameters.items() if k not in WORKBENCH_PARAMS}
    print(f"XGBoost params: {xgb_params}")

    if n_folds == 1:
        # Single train/val split
        if "training" in all_df.columns:
            print("Using 'training' column for train/val split")
            train_idx = np.where(all_df["training"])[0]
            val_idx = np.where(~all_df["training"])[0]
        else:
            print("WARNING: No 'training' column found, using random 80/20 split")
            indices = np.arange(len(all_df))
            train_idx, val_idx = train_test_split(indices, test_size=0.2, random_state=42)
        folds = [(train_idx, val_idx)]
    else:
        # K-fold cross-validation
        if model_type == "classifier":
            kfold = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=42)
            folds = list(kfold.split(all_df, all_df[target]))
        else:
            kfold = KFold(n_splits=n_folds, shuffle=True, random_state=42)
            folds = list(kfold.split(all_df))

    print(f"Training {'single model' if n_folds == 1 else f'{n_folds}-fold ensemble'}...")

    # -------------------------------------------------------------------------
    # Training loop
    # -------------------------------------------------------------------------
    # Initialize out-of-fold storage
    oof_predictions = np.full(len(all_df), np.nan, dtype=np.float64)
    if model_type == "classifier":
        num_classes = len(label_encoder.classes_)
        oof_proba = np.full((len(all_df), num_classes), np.nan, dtype=np.float64)
    else:
        oof_proba = None

    # Check for sample weights
    has_sample_weights = "sample_weight" in all_df.columns
    if has_sample_weights:
        sw = all_df["sample_weight"]
        print(f"Using sample weights: min={sw.min():.2f}, max={sw.max():.2f}, mean={sw.mean():.2f}")

    # Train ensemble
    ensemble_models = []
    for fold_idx, (train_idx, val_idx) in enumerate(folds):
        print(f"\n{'='*50}")
        print(f"Fold {fold_idx + 1}/{len(folds)} - Train: {len(train_idx)}, Val: {len(val_idx)}")
        print(f"{'='*50}")

        # Prepare fold data
        X_train = all_df.iloc[train_idx][features]
        y_train = all_df.iloc[train_idx][target]
        X_val = all_df.iloc[val_idx][features]
        sample_weights = all_df.iloc[train_idx]["sample_weight"] if has_sample_weights else None

        # Create model with fold-specific random state for diversity
        fold_params = {**xgb_params, "random_state": xgb_params.get("random_state", 42) + fold_idx}
        if model_type == "classifier":
            model = xgb.XGBClassifier(enable_categorical=True, **fold_params)
        else:
            model = xgb.XGBRegressor(enable_categorical=True, **fold_params)

        # Train
        model.fit(X_train, y_train, sample_weight=sample_weights)
        ensemble_models.append(model)

        # Out-of-fold predictions
        oof_predictions[val_idx] = model.predict(X_val)
        if model_type == "classifier":
            oof_proba[val_idx] = model.predict_proba(X_val)

    print(f"\nTraining complete! Trained {len(ensemble_models)} model(s).")

    # -------------------------------------------------------------------------
    # Prepare validation results
    # -------------------------------------------------------------------------
    if n_folds == 1:
        # Single fold: only validation rows
        val_mask = ~np.isnan(oof_predictions)
        df_val = all_df[val_mask].copy()
        predictions = oof_predictions[val_mask]
        if oof_proba is not None:
            oof_proba = oof_proba[val_mask]
    else:
        # K-fold: all rows have out-of-fold predictions
        df_val = all_df.copy()
        predictions = oof_predictions

    # Decode labels for classification
    if model_type == "classifier":
        df_val[target] = label_encoder.inverse_transform(df_val[target].astype(int))
        df_val["prediction"] = label_encoder.inverse_transform(predictions.astype(int))
        if oof_proba is not None:
            df_val["pred_proba"] = [p.tolist() for p in oof_proba]
            df_val = expand_proba_column(df_val, label_encoder.classes_)
    else:
        df_val["prediction"] = predictions

    # -------------------------------------------------------------------------
    # Compute and print metrics
    # -------------------------------------------------------------------------
    y_true = df_val[target].values
    y_pred = df_val["prediction"].values

    if model_type == "classifier":
        label_names = label_encoder.classes_
        score_df = compute_classification_metrics(y_true, y_pred, label_names, target)
        print_classification_metrics(score_df, target, label_names)
        print_confusion_matrix(y_true, y_pred, label_names)
    else:
        metrics = compute_regression_metrics(y_true, y_pred)
        print_regression_metrics(metrics)

        # Compute ensemble prediction_std
        if n_folds > 1:
            all_preds = np.stack([m.predict(all_df[features]) for m in ensemble_models])
            df_val["prediction_std"] = np.std(all_preds, axis=0)
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
    # Ensemble models
    for idx, ens_model in enumerate(ensemble_models):
        joblib.dump(ens_model, os.path.join(args.model_dir, f"xgb_model_{idx}.joblib"))
    print(f"Saved {len(ensemble_models)} XGBoost model(s)")

    # Metadata files
    with open(os.path.join(args.model_dir, "ensemble_metadata.json"), "w") as f:
        json.dump({"n_ensemble": len(ensemble_models), "n_folds": n_folds}, f)

    with open(os.path.join(args.model_dir, "feature_columns.json"), "w") as f:
        json.dump(orig_features, f)

    with open(os.path.join(args.model_dir, "category_mappings.json"), "w") as f:
        json.dump(category_mappings, f)

    with open(os.path.join(args.model_dir, "hyperparameters.json"), "w") as f:
        json.dump(hyperparameters, f, indent=2)

    if label_encoder:
        joblib.dump(label_encoder, os.path.join(args.model_dir, "label_encoder.joblib"))

    if model_type != "classifier":
        save_uq_models(uq_models, uq_metadata, args.model_dir)

    print(f"\nModel training complete! Artifacts saved to {args.model_dir}")


# =============================================================================
# Model Loading (for SageMaker inference)
# =============================================================================
def model_fn(model_dir: str) -> dict:
    """Load XGBoost ensemble and associated artifacts.

    Args:
        model_dir: Directory containing model artifacts

    Returns:
        Dictionary with ensemble_models, label_encoder, category_mappings, uq_models, etc.
    """
    # Load ensemble metadata
    metadata_path = os.path.join(model_dir, "ensemble_metadata.json")
    if os.path.exists(metadata_path):
        with open(metadata_path) as f:
            metadata = json.load(f)
        n_ensemble = metadata["n_ensemble"]
    else:
        n_ensemble = 1  # Legacy single model

    # Load ensemble models
    ensemble_models = []
    for i in range(n_ensemble):
        model_path = os.path.join(model_dir, f"xgb_model_{i}.joblib")
        if not os.path.exists(model_path):
            model_path = os.path.join(model_dir, "xgb_model.joblib")  # Legacy fallback
        ensemble_models.append(joblib.load(model_path))

    # Load label encoder (classifier only)
    label_encoder = None
    encoder_path = os.path.join(model_dir, "label_encoder.joblib")
    if os.path.exists(encoder_path):
        label_encoder = joblib.load(encoder_path)

    # Load category mappings
    category_mappings = {}
    category_path = os.path.join(model_dir, "category_mappings.json")
    if os.path.exists(category_path):
        with open(category_path) as f:
            category_mappings = json.load(f)

    # Load UQ models (regression only)
    uq_models, uq_metadata = None, None
    uq_path = os.path.join(model_dir, "uq_metadata.json")
    if os.path.exists(uq_path):
        uq_models, uq_metadata = load_uq_models(model_dir)

    return {
        "ensemble_models": ensemble_models,
        "n_ensemble": n_ensemble,
        "label_encoder": label_encoder,
        "category_mappings": category_mappings,
        "uq_models": uq_models,
        "uq_metadata": uq_metadata,
    }


# =============================================================================
# Inference (for SageMaker inference)
# =============================================================================
def predict_fn(df: pd.DataFrame, models: dict) -> pd.DataFrame:
    """Make predictions with XGBoost ensemble.

    Args:
        df: Input DataFrame with features
        models: Dictionary from model_fn containing ensemble and metadata

    Returns:
        DataFrame with predictions added
    """
    # Load feature columns
    model_dir = os.environ.get("SM_MODEL_DIR", "/opt/ml/model")
    with open(os.path.join(model_dir, "feature_columns.json")) as f:
        features = json.load(f)
    print(f"Model Features: {features}")

    # Extract model components
    ensemble_models = models["ensemble_models"]
    label_encoder = models.get("label_encoder")
    category_mappings = models.get("category_mappings", {})
    uq_models = models.get("uq_models")
    uq_metadata = models.get("uq_metadata")
    compressed_features = TEMPLATE_PARAMS["compressed_features"]

    # Prepare features
    matched_df = match_features_case_insensitive(df, features)
    matched_df, _ = convert_categorical_types(matched_df, features, category_mappings)

    if compressed_features:
        print("Decompressing features for prediction...")
        matched_df, features = decompress_features(matched_df, features, compressed_features)

    X = matched_df[features]

    # Collect ensemble predictions
    all_preds = [m.predict(X) for m in ensemble_models]
    ensemble_preds = np.stack(all_preds, axis=0)

    if label_encoder is not None:
        # Classification: average probabilities, then argmax
        all_probs = [m.predict_proba(X) for m in ensemble_models]
        avg_probs = np.mean(np.stack(all_probs, axis=0), axis=0)
        class_preds = np.argmax(avg_probs, axis=1)

        df["prediction"] = label_encoder.inverse_transform(class_preds)
        df["pred_proba"] = [p.tolist() for p in avg_probs]
        df = expand_proba_column(df, label_encoder.classes_)
    else:
        # Regression: average predictions
        df["prediction"] = np.mean(ensemble_preds, axis=0)
        df["prediction_std"] = np.std(ensemble_preds, axis=0)

        # Add UQ intervals if available
        if uq_models and uq_metadata:
            df = predict_intervals(df, X, uq_models, uq_metadata)
            df = compute_confidence(df, uq_metadata["median_interval_width"], "q_10", "q_90")

    print(f"Inference complete: {len(df)} predictions, {len(ensemble_models)} ensemble members")
    return df
