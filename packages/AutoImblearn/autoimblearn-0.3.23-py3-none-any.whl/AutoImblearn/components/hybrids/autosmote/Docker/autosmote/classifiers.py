from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import LinearSVC
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import AdaBoostClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier

name2f = {
    "knn": KNeighborsClassifier(),
    "svm": LinearSVC(random_state=42),
    "dt": DecisionTreeClassifier(),
    "ada": AdaBoostClassifier(random_state=42),
    "lr": LogisticRegression(random_state=42),
    "mlp": MLPClassifier(random_state=42, max_iter=1000),
}

def get_clf(name):
    return name2f[name]

