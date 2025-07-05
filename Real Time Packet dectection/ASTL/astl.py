import os
import json
import numpy as np
import pandas as pd
from datetime import datetime
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
import shutil  
import time
import joblib

def astl_loop(
    model,
    X_labeled, y_labeled,
    X_unlabeled,
    X_val, y_val,
    max_loops=5,
    confidence_threshold=0.95,
    entropy_threshold=0.3,
    min_gain=0.001,
    logs_dir="astl_logs",
    fixed_log_output_path="models/piyush/SQL/astl_log.json"  
):
    os.makedirs(logs_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = os.path.join(logs_dir, f"astl_log_{timestamp}.json")

    prev_acc = accuracy_score(y_val, model.predict(X_val))
    logs = []

    for loop in range(1, max_loops + 1):
        print(f"\n--- Loop {loop} ---")

        probs = model.predict_proba(X_unlabeled)

        confidences = np.max(probs, axis=1)
        entropy = -np.sum(probs * np.log(probs + 1e-12), axis=1)  

        confident_idxs = np.where((confidences >= confidence_threshold) & (entropy <= entropy_threshold))[0]

        if len(confident_idxs) == 0:
            print("No confident samples to add, stopping early.")
            break

        X_pseudo = X_unlabeled.iloc[confident_idxs]
        y_pseudo = model.predict(X_pseudo)

        X_labeled = pd.concat([X_labeled, X_pseudo], ignore_index=True)
        y_labeled = np.concatenate([y_labeled, y_pseudo])

        X_unlabeled = X_unlabeled.drop(X_unlabeled.index[confident_idxs]).reset_index(drop=True)

        model.fit(X_labeled, y_labeled)

        y_val_pred = model.predict(X_val)
        val_acc = accuracy_score(y_val, y_val_pred)
        y_train_pred = model.predict(X_labeled)
        train_acc = accuracy_score(y_labeled, y_train_pred)

        class_counts = {}
        for c in np.unique(y_pseudo):
            class_counts[str(c)] = int(np.sum(y_pseudo == c))  

        loop_log = {
            "loop": loop,
            "validation_accuracy": val_acc,
            "training_accuracy": train_acc,
            "samples_added_this_loop": len(X_pseudo),
            "pseudo_label_class_distribution": class_counts,
            "total_labeled_samples": len(X_labeled),
            "remaining_unlabeled": len(X_unlabeled),
        }

        logs.append(loop_log)

        print(
            f"Validation Accuracy: {val_acc:.4f} | Training Accuracy: {train_acc:.4f}\n"
            f"Samples Added This Loop: {len(X_pseudo)}\n"
            f"Pseudo-label Class Distribution: {class_counts}\n"
            f"Total Labeled Samples: {len(X_labeled)} | Remaining Unlabeled: {len(X_unlabeled)}"
        )

        if abs(val_acc - prev_acc) < min_gain:
            print("Early stopping: accuracy improvement minimal.")
            break
        prev_acc = val_acc

    with open(log_path, "w") as f:
        json.dump(logs, f, indent=4)

    os.makedirs(os.path.dirname(fixed_log_output_path), exist_ok=True)
    shutil.copy(log_path, fixed_log_output_path)
    print(f"\nTraining complete. Logs saved to:\n - {log_path}\n - {fixed_log_output_path}")

    return model


def save_model_with_options(final_model, base_path="models/piyush/SQL", model_name="piyushm2.pkl"):

    print("\nWhat do you want to do with the updated model?")
    print("1) Save as a separate model file (keep old one intact)")
    print("2) Overwrite existing model file")
    print("3) Create/update a symlink to the new model file")
    choice = input("Enter choice (1/2/3): ").strip()

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    new_model_filename = f"piyushm2_astl_{timestamp}.pkl"
    new_model_path = os.path.join(base_path, new_model_filename)
    orig_model_path = os.path.join(base_path, model_name)

    if choice == "1":
        joblib.dump(final_model, new_model_path)
        print(f"Saved updated model as separate file: {new_model_filename}")

    elif choice == "2":
        if os.path.exists(orig_model_path):
            backup_path = orig_model_path.replace(".pkl", f"_backup_{timestamp}.pkl")
            shutil.copy(orig_model_path, backup_path)
            print(f"Backup of old model created: {backup_path}")

        joblib.dump(final_model, orig_model_path)
        print(f"Overwritten existing model with updated model: {model_name}")

    elif choice == "3":
        joblib.dump(final_model, new_model_path)
        
        if os.path.exists(orig_model_path) or os.path.islink(orig_model_path):
            os.remove(orig_model_path)
        os.symlink(new_model_filename, orig_model_path)
        print(f"Saved updated model as {new_model_filename} and symlinked {model_name} to it.")

    else:
        print("Invalid choice! Saving as separate file by default.")
        joblib.dump(final_model, new_model_path)
        print(f"Saved updated model as separate file: {new_model_filename}")



if __name__ == "__main__":
    
    df = pd.read_csv("C:/QVoid-MutantAI/datasets/piyush/SQL/SQL Injection.csv")

    label_col = "Label"

    non_numeric_cols = df.select_dtypes(include=["object"]).columns.tolist()
    non_numeric_cols = [col for col in non_numeric_cols if col != label_col]

    print(f"Columns found: {list(df.columns)}")
    print(f"Using label column: {label_col}")
    print(f"Dropping non-numeric columns: {non_numeric_cols}")

    df = df.drop(columns=non_numeric_cols)
    df = df.dropna()

    X = df.drop(columns=[label_col])
    y = df[label_col].values

    X_train_val, X_unlabeled, y_train_val, _ = train_test_split(X, y, test_size=0.4, stratify=y, random_state=42)
    X_labeled, X_val, y_labeled, y_val = train_test_split(X_train_val, y_train_val, test_size=0.3, stratify=y_train_val, random_state=42)

    print(f"Initial labeled samples: {len(X_labeled)}")
    print(f"Validation samples: {len(X_val)}")
    print(f"Unlabeled samples: {len(X_unlabeled)}")

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_labeled, y_labeled)

    initial_val_pred = model.predict(X_val)
    initial_val_acc = accuracy_score(y_val, initial_val_pred)
    print(f"Initial Validation Accuracy: {initial_val_acc:.4f}")

    final_model = astl_loop(
        model,
        X_labeled.reset_index(drop=True), y_labeled,
        X_unlabeled.reset_index(drop=True),
        X_val.reset_index(drop=True), y_val,
        max_loops=10,
        confidence_threshold=0.95,
        entropy_threshold=0.3,
        min_gain=0.001,
        logs_dir="astl_logs",
        fixed_log_output_path="models/piyush/SQL/astl_log.json"  
    )

    
    save_model_with_options(final_model)