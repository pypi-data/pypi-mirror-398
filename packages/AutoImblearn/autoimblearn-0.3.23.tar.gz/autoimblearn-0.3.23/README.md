# AutoImblearn

**AutoImblearn** is a comprehensive Automated Machine Learning (AutoML) system designed for imbalanced medical data with support for **classification, survival analysis, and unsupervised learning**. It automates the selection of preprocessing techniques, resampling strategies, model selection, and hyperparameter optimization across multiple learning paradigms.

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-BSD--3--Clause-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-0.3.0-orange.svg)](setup.py)

---

## 🌟 Key Features

### Multiple Learning Paradigms
- **Supervised Classification**: Imbalanced binary/multiclass classification
- **Survival Analysis**: Time-to-event analysis with censoring
- **Unsupervised Learning**: Clustering, dimensionality reduction, anomaly detection
- **Hybrid Methods**: Combined resampling and classification
- **AutoML Integration**: Out-of-the-box AutoML frameworks

### Comprehensive Model Library (50+ Models)
- **20+ Classifiers**: Logistic Regression, SVM, Random Forest, XGBoost, Neural Networks, etc.
- **15+ Resampling Methods**: SMOTE variants, undersampling, oversampling, hybrid techniques
- **9 Survival Models**: Cox Proportional Hazards, Random Survival Forest, SVM variants
- **6 Clustering Algorithms**: KMeans, DBSCAN, Hierarchical, GMM, MeanShift, Spectral
- **6 Dimensionality Reduction**: PCA, t-SNE, UMAP, TruncatedSVD, ICA, NMF
- **4 Anomaly Detection**: IsolationForest, OneClassSVM, LOF, EllipticEnvelope
- **5+ Imputation Methods**: Mean, Median, KNN, Iterative, HyperImpute
- **3 AutoML Frameworks**: Auto-sklearn, TPOT, H2O AutoML

### Advanced Capabilities
- **Automated Pipeline Search**: Greedy search with budget controls
- **Docker-Based Architecture**: Isolated, reproducible model training
- **Survival-Aware Processing**: Handles censored data and structured survival arrays
- **Intelligent Caching**: Reuses imputation results across experiments
- **K-Fold Cross-Validation**: Robust performance estimation
- **Multiple Metrics**: AUROC, F1, Precision, Recall, C-index, Silhouette, etc.

---

## 📦 Installation

### Basic Installation
```bash
pip install AutoImblearn
```

### Installation with Optional Dependencies

For specific use cases, install with extras:

```bash
# For web-based visualization (Django frontend)
pip install AutoImblearn[web]

# For advanced imputation methods
pip install AutoImblearn[imputer]

# For all resampling techniques
pip install AutoImblearn[resampler]

# For survival analysis
pip install AutoImblearn[survival]

# For unsupervised learning (UMAP)
pip install AutoImblearn[unsupervised]

# For all features
pip install AutoImblearn[all]
```

### Requirements
- Python ≥ 3.9
- Docker (for model training)
- scikit-learn ≥ 1.3.0
- pandas ≥ 2.0.0
- numpy ≥ 1.24.0

---

## 🚀 Quick Start

### 1. Classification Pipeline

```python
from AutoImblearn.core.runpipe import RunPipe
from AutoImblearn.core.autoimblearn import AutoImblearn

class Args:
    dataset = "diabetes.csv"
    target = "outcome"
    path = "/data"
    metric = "auroc"
    n_splits = 5
    repeat = 0
    train_ratio = 1.0

args = Args()

# Initialize pipeline runner
run_pipe = RunPipe(args)
run_pipe.loadData()

# Run a specific pipeline: [imputer, resampler, classifier]
result = run_pipe.fit(['knn', 'smote', 'lr'])
print(f"AUROC: {result}")

# Or search for best pipeline automatically
automl = AutoImblearn(run_pipe, metric='auroc')
best_pipeline, n_evals, best_score = automl.find_best(max_iterations=50)
print(f"Best Pipeline: {best_pipeline}")
print(f"Best Score: {best_score}")
```

### 2. Survival Analysis Pipeline

```python
# For time-to-event analysis with censored data

args.metric = "c_index"  # Concordance index for survival

# Run survival pipeline: [imputer, survival_resampler, survival_model]
result = run_pipe.fit(['median', 'rus', 'CPH'])  # Cox Proportional Hazards
print(f"C-index: {result}")
```

### 3. Unsupervised Learning Pipeline

```python
# Clustering example
args.metric = "silhouette"

# Run clustering pipeline: [imputer, clustering_model]
result = run_pipe.fit(['knn', 'kmeans'])
print(f"Silhouette Score: {result}")

# Dimensionality reduction example
args.metric = "reconstruction"
result = run_pipe.fit(['median', 'pca'])

# Anomaly detection example
args.metric = "f1"
result = run_pipe.fit(['mean', 'isoforest'])
```

### 4. Hybrid Pipeline

```python
# Combined resampling + classification in one step

# Run hybrid pipeline: [imputer, hybrid_method]
result = run_pipe.fit(['median', 'autosmote'])
```

### 5. AutoML Pipeline

```python
# Pure AutoML approach (handles everything internally)

# Run AutoML: [automl_framework]
result = run_pipe.fit_automl(['autosklearn'])
```

---

## 🏗️ Pipeline Types

AutoImblearn supports **8 distinct pipeline types**:

| Pipeline Type | Structure | Example | Use Case |
|--------------|-----------|---------|----------|
| **Classification** | `[imputer, resampler, classifier]` | `['knn', 'smote', 'lr']` | Imbalanced classification |
| **Survival** | `[imputer, survival_resampler, survival_model]` | `['median', 'rus', 'CPH']` | Time-to-event analysis |
| **Hybrid** | `[imputer, hybrid_method]` | `['median', 'autosmote']` | Combined resampling+classification |
| **AutoML** | `[automl_framework]` | `['autosklearn']` | Automated ML |
| **Clustering** | `[imputer, clustering_model]` | `['knn', 'kmeans']` | Pattern discovery |
| **Reduction** | `[imputer, reduction_model]` | `['median', 'pca']` | Dimensionality reduction |
| **Anomaly** | `[imputer, anomaly_model]` | `['mean', 'isoforest']` | Outlier detection |
| **Survival Clustering** | `[imputer, survival_unsupervised]` | `['median', 'survival_tree']` | Risk stratification |

---

## 📊 Available Models

### Imputers (5)
- `mean`, `median`, `knn`, `iter`, `hyperimpute`

### Classifiers (20+)
**Sklearn-based:**
- `lr` - Logistic Regression
- `svm` - Support Vector Machine
- `dt` - Decision Tree
- `rf` - Random Forest
- `ab` - AdaBoost
- `gb` - Gradient Boosting
- `knn_clf` - K-Nearest Neighbors
- `gnb` - Gaussian Naive Bayes
- `mlp` - Multi-Layer Perceptron
- `lda` - Linear Discriminant Analysis
- `qda` - Quadratic Discriminant Analysis

**XGBoost-based:**
- `xgb` - XGBoost Classifier
- `xgb_rf` - XGBoost Random Forest

### Resamplers (15+)
**Imblearn-based:**
- `rus` - Random Under-Sampling
- `ros` - Random Over-Sampling
- `nm` - Near Miss
- `cnn` - Condensed Nearest Neighbor
- `enn` - Edited Nearest Neighbors
- `allknn` - All K-NN
- `smote_enn` - SMOTE + ENN
- `smote_tomek` - SMOTE + Tomek Links

**SMOTE-based:**
- `smote` - SMOTE
- `borderline_smote` - Borderline-SMOTE
- `svm_smote` - SVM-SMOTE
- `adasyn` - ADASYN
- `kmeans_smote` - K-Means SMOTE

### Survival Models (9)
- `CPH` - Cox Proportional Hazards
- `RSF` - Random Survival Forest
- `SVM` - Survival SVM
- `KSVM` - Kernel Survival SVM
- `LASSO` - LASSO Cox
- `L1` - L1-penalized Cox
- `L2` - L2-penalized Cox
- `CSA` - Component-wise Gradient Boosting
- `LRSF` - Linear Random Survival Forest

### Survival Resamplers (3)
- `rus` - Random Under-Sampling (survival-aware)
- `ros` - Random Over-Sampling (survival-aware)
- `smote` - SMOTE (survival-aware)

### Unsupervised Models

**Clustering (6):**
- `kmeans` - K-Means Clustering
- `dbscan` - DBSCAN
- `hierarchical` - Agglomerative Clustering
- `gmm` - Gaussian Mixture Model
- `meanshift` - Mean Shift
- `spectral` - Spectral Clustering

**Dimensionality Reduction (6):**
- `pca` - Principal Component Analysis
- `tsne` - t-SNE
- `umap` - UMAP
- `svd` - Truncated SVD
- `ica` - Independent Component Analysis
- `nmf` - Non-negative Matrix Factorization

**Anomaly Detection (4):**
- `isoforest` - Isolation Forest
- `ocsvm` - One-Class SVM
- `lof` - Local Outlier Factor
- `elliptic` - Elliptic Envelope

**Survival Unsupervised (2):**
- `survival_tree` - Survival Tree (subgroup discovery)
- `survival_kmeans` - K-Means on survival data

### Hybrid Methods (2)
- `autosmote` - AutoSMOTE (adaptive SMOTE with RL)
- `autorsp` - Automated Resampler Selection (macro F1 reinforcement)

### AutoML Frameworks (3)
- `autosklearn` - Auto-sklearn
- `tpot` - TPOT
- `h2o` - H2O AutoML

---

## 🏛️ Architecture

### Docker-Based Design

AutoImblearn uses a **client-server architecture** where each model runs in an isolated Docker container:

```
┌─────────────────┐
│   Python Client │  ←→  Flask REST API in Docker
│   (run.py)      │      (Docker/app.py)
└─────────────────┘
```

**Benefits:**
- **Isolation**: Each model has its own dependencies
- **Reproducibility**: Consistent environment across machines
- **Scalability**: Easy to deploy on clusters
- **Security**: Sandboxed execution

### Pipeline Execution Flow

```
1. Data Loading
   ↓
2. K-Fold Splitting (on raw data)
   ↓
3. For each fold:
   a. Imputation (FIT on train, TRANSFORM both)
   b. Resampling (ONLY on train)
   c. Model Training
   d. Prediction & Evaluation
   ↓
4. Average Results
   ↓
5. Save & Cache
```

### Intelligent Caching

Imputation results are cached per fold to avoid redundant computation:

```python
# Cached file: interim/{dataset}/imp_{imputer}_fold{n}.p
if cached_file_exists:
    load_from_cache()  # Fast!
else:
    run_imputation()
    save_to_cache()
```

---

## 🔧 Configuration

### Metrics Supported

**Classification:**
- `auroc` - Area Under ROC Curve
- `f1` - F1 Score
- `precision` - Precision
- `recall` - Recall
- `accuracy` - Accuracy

**Survival:**
- `c_index` - Concordance Index
- `c_uno` - Uno's C-index

**Unsupervised:**
- `silhouette` - Silhouette Score (clustering)
- `calinski` - Calinski-Harabasz Index (clustering)
- `davies_bouldin` - Davies-Bouldin Index (clustering)
- `reconstruction` - Reconstruction Error (reduction)
- `log_rank` - Log-rank Test (survival clustering)

### Search Budget Controls

```python
automl.find_best(
    max_iterations=100,           # Max pipeline evaluations
    time_budget_seconds=3600,     # Max time (1 hour)
    early_stopping_patience=10    # Stop if no improvement
)
```

---

## 🌐 Web Interface

AutoImblearn includes a **Django web frontend** for interactive pipeline configuration:

### Features:
- **Visual Pipeline Builder**: Drag-and-drop interface
- **Dataset Upload**: CSV file handling
- **Feature Analysis**: Distribution plots and categorical detection
- **Pipeline Type Selection**: Choose from 8 pipeline types
- **Model Selection**: Multi-select from available models
- **Training Dashboard**: Real-time progress tracking
- **Results Visualization**: Performance metrics and comparisons

### Launch Web Interface:
```bash
cd django_frontend
python manage.py runserver
```

Navigate to `http://localhost:8000` to access the interface.

---

## 📚 Advanced Usage

### Custom Pipeline Search

```python
from AutoImblearn.core.autoimblearn import AutoImblearn

# Restrict search space
automl.imputers = ['knn', 'median']
automl.resamplers = ['smote', 'adasyn']
automl.classifiers = ['lr', 'rf', 'xgb']

# Run search with custom space
best_pipeline, n_evals, best_score = automl.find_best(
    max_iterations=30,
    time_budget_seconds=1800
)
```

### Survival Data Format

Survival data requires a **structured array** with two fields:

```python
import numpy as np
from sksurv.util import Surv

# Create survival array
y = Surv.from_arrays(
    event=[True, False, True, False],      # Event occurred?
    time=[100, 200, 150, 300]              # Time to event/censoring
)

# Structured array format:
# dtype=[('Status', bool), ('Survival_in_days', float)]
```

### Direct Model Usage

```python
from AutoImblearn.pipelines import classifiers, resamplers, imputers

# Instantiate specific models
imputer_factory = imputers['knn']
imputer = imputer_factory(data_folder='/data')

resampler_factory = resamplers['smote']
resampler = resampler_factory(data_folder='/data')

classifier_factory = classifiers['lr']
classifier = classifier_factory(data_folder='/data')

# Use models
X_train_imputed = imputer.fit_transform(args, X_train)
X_train_resampled, y_train_resampled = resampler.fit_resample(X_train_imputed, y_train)
classifier.fit(X_train_resampled, y_train_resampled)
predictions = classifier.predict(X_test)
```

---

## 🐛 Development

### Project Structure

```
AutoImblearn/
├── components/
│   ├── classifiers/          # Classification models
│   ├── resamplers/           # Resampling techniques
│   ├── imputers/             # Imputation methods
│   ├── survival/             # Survival analysis models
│   │   ├── _supervised/      # Survival models (CPH, RSF, etc.)
│   │   ├── _resamplers/      # Survival-aware resampling
│   │   └── _unsupervised/    # Survival clustering
│   ├── unsupervised/         # Unsupervised learning
│   │   ├── _clustering/      # Clustering algorithms
│   │   ├── _reduction/       # Dimensionality reduction
│   │   └── _anomaly/         # Anomaly detection
│   ├── automls/              # AutoML frameworks
│   ├── hybrids/              # Hybrid methods
│   └── api/                  # Base API classes
├── core/
│   ├── runpipe.py            # Pipeline execution
│   ├── autoimblearn.py       # AutoML search
│   └── pipeline_strategies.py # Strategy pattern
├── pipelines/                # Pipeline wrappers
├── processing/               # Data preprocessing utilities
└── utils/                    # Helper functions
```

### Building Docker Images

Each model has its own Dockerfile:

```bash
# Build a specific model image
cd AutoImblearn/components/classifiers/_sklearnbased
docker build -t sklearn-classifier-api .

# Build all images
cd AutoImblearn
./build_all_images.sh  # If script exists
```

### Running Tests

```bash
# Install dev dependencies
pip install AutoImblearn[dev]

# Run tests
pytest tests/

# Run with coverage
pytest --cov=AutoImblearn tests/
```

---

## 📖 Citation

If you use AutoImblearn in your research, please cite:

```bibtex
@software{autoimblearn2024,
  title = {AutoImblearn: Automated Machine Learning for Imbalanced Medical Data},
  author = {Wang, Hank},
  year = {2024},
  version = {0.3.0},
  url = {https://github.com/Wanghongkua/Auto-Imblearn2}
}
```

---

## 📄 License

This project is licensed under the **BSD 3-Clause License**. See [LICENSE](LICENSE) for details.

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 🙏 Acknowledgments

- Built on top of **scikit-learn**, **imbalanced-learn**, and **scikit-survival**
- Docker-based architecture inspired by microservices design patterns
- AutoML search adapted from CASH (Combined Algorithm Selection and Hyperparameter optimization)

---

## 📧 Contact

**Author**: Hank Wang
**Email**: hankwang1991@gmail.com

For bug reports and feature requests, please use the [GitHub Issues](https://github.com/Wanghongkua/Auto-Imblearn2/issues) page.

---

**Happy AutoML-ing! 🚀**
