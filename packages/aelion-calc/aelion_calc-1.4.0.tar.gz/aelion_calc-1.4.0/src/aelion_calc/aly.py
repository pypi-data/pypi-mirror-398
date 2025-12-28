import math
import random
import csv
import json
import copy
from collections import Counter, defaultdict
import heapq # For Dijkstra algorithm
import pickle # For saving AI models
def _backward_none():
    """Empty function for initialization to satisfy Pickle."""
    pass

# ==========================================
# 1. CORE DATAFRAME (The Pandas Killer)
# ==========================================

class DataFrame:
    def __init__(self, data=None, columns=None):
        """
        A lightweight Data Structure.
        Accepts: List of Dicts OR List of Lists (with columns arg).
        """
        self.data = [] # List of dictionaries
        self.columns = []

        if data:
            if isinstance(data[0], dict):
                self.data = copy.deepcopy(data)
                self.columns = list(data[0].keys())
            elif isinstance(data[0], list):
                if not columns: raise ValueError("Must provide columns for list data")
                self.columns = columns
                for row in data:
                    self.data.append(dict(zip(columns, row)))
    
    def __len__(self):
        return len(self.data)

    def __getitem__(self, col_name):
        """df['age'] returns a list of values."""
        return [row.get(col_name) for row in self.data]

    # --- INSPECTION ---
    def head(self, n=5):
        return DataFrame(self.data[:n])

    def tail(self, n=5):
        return DataFrame(self.data[-n:])
    
    def shape(self):
        return (len(self.data), len(self.columns))

    def info(self):
        print(f"<DataFrame: {len(self.data)} rows, {len(self.columns)} cols>")
        for col in self.columns:
            types = set(type(row.get(col)).__name__ for row in self.data if row.get(col) is not None)
            print(f" - {col}: {', '.join(types)}")

    # --- DATA CLEANING ---
    def dropna(self):
        """Removes rows with None/empty values."""
        clean_data = [row for row in self.data if all(v is not None for v in row.values())]
        return DataFrame(clean_data)

    def fillna(self, value):
        """Replaces None with a specific value."""
        new_data = copy.deepcopy(self.data)
        for row in new_data:
            for k, v in row.items():
                if v is None: row[k] = value
        return DataFrame(new_data)

    # --- MANIPULATION ---
    def sort_values(self, by, reverse=False):
        """Sorts the DataFrame by a column."""
        sorted_data = sorted(self.data, key=lambda x: x.get(by) or 0, reverse=reverse)
        return DataFrame(sorted_data)

    def apply(self, col, func):
        """Applies a function to every value in a column."""
        for row in self.data:
            if row.get(col) is not None:
                row[col] = func(row[col])

    def filter(self, condition):
        """
        Returns filtered DataFrame. 
        Ex: df.filter(lambda r: r['age'] > 20)
        """
        return DataFrame([r for r in self.data if condition(r)])

    def groupby(self, col):
        """Returns a Dictionary of DataFrames grouped by unique values in col."""
        groups = defaultdict(list)
        for row in self.data:
            key = row.get(col)
            groups[key].append(row)
        
        return {k: DataFrame(v) for k, v in groups.items()}

    def to_csv(self, filename):
        with open(filename, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=self.columns)
            writer.writeheader()
            writer.writerows(self.data)

# ==========================================
# 2. STATISTICS ENGINE
# ==========================================

def mean(values):
    values = [v for v in values if v is not None]
    return sum(values) / len(values) if values else 0

def median(values):
    values = sorted([v for v in values if v is not None])
    if not values: return 0
    n = len(values)
    mid = n // 2
    return (values[mid-1] + values[mid])/2 if n % 2 == 0 else values[mid]

def variance(values):
    values = [v for v in values if v is not None]
    if len(values) < 2: return 0
    mu = mean(values)
    return sum((x - mu)**2 for x in values) / (len(values) - 1)

def stdev(values):
    return math.sqrt(variance(values))

def correlation(x, y):
    """Pearson Correlation Coefficient."""
    n = len(x)
    if n != len(y): raise ValueError("Lists must be same length")
    mu_x, mu_y = mean(x), mean(y)
    numerator = sum((x[i] - mu_x) * (y[i] - mu_y) for i in range(n))
    denominator = math.sqrt(sum((x[i]-mu_x)**2 for i in range(n)) * sum((y[i]-mu_y)**2 for i in range(n)))
    return numerator / denominator if denominator != 0 else 0

def describe(df, col):
    """Full stats summary for a column."""
    vals = df[col]
    return {
        "Mean": round(mean(vals), 2),
        "Median": round(median(vals), 2),
        "StdDev": round(stdev(vals), 2),
        "Min": min(vals) if vals else 0,
        "Max": max(vals) if vals else 0
    }

def train_test_split(df, test_size=0.2):
    """Splits DataFrame into Train and Test sets."""
    data = copy.deepcopy(df.data)
    random.shuffle(data)
    split_idx = int(len(data) * (1 - test_size))
    return DataFrame(data[:split_idx]), DataFrame(data[split_idx:])

# ==========================================
# 3. MACHINE LEARNING ENGINE
# ==========================================

class LinearRegression:
    def __init__(self):
        self.m = 0
        self.b = 0

    def fit(self, x, y):
        """Train the model (Ordinary Least Squares)."""
        # Calculate mean using the statistics engine logic
        x_mean = sum(x) / len(x)
        y_mean = sum(y) / len(y)
        
        num = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(len(x)))
        den = sum((x[i] - x_mean) ** 2 for i in range(len(x)))
        self.m = num / den if den != 0 else 0
        self.b = y_mean - (self.m * x_mean)

    def predict(self, x):
        """Predict single value or list."""
        if isinstance(x, list): return [self.m * val + self.b for val in x]
        return self.m * x + self.b

class LogisticRegression:
    """Binary Classification (0 or 1). Uses Gradient Descent."""
    def __init__(self, learning_rate=0.01, epochs=1000):
        self.lr = learning_rate
        self.epochs = epochs
        self.weights = []
        self.bias = 0

    def _sigmoid(self, z):
        # Clip z to prevent overflow
        if z < -709: return 0
        if z > 709: return 1
        return 1 / (1 + math.exp(-z))

    def fit(self, X, y):
        """X: List of lists (features), y: List of labels (0/1)."""
        n_samples = len(X)
        n_features = len(X[0])
        self.weights = [0.0] * n_features
        self.bias = 0

        for _ in range(self.epochs):
            for i in range(n_samples):
                linear_pred = sum(X[i][j] * self.weights[j] for j in range(n_features)) + self.bias
                y_pred = self._sigmoid(linear_pred)

                error = y_pred - y[i]
                for j in range(n_features):
                    self.weights[j] -= self.lr * error * X[i][j]
                self.bias -= self.lr * error

    def predict(self, X):
        predictions = []
        for row in X:
            linear_pred = sum(row[j] * self.weights[j] for j in range(len(row))) + self.bias
            y_pred = self._sigmoid(linear_pred)
            predictions.append(1 if y_pred > 0.5 else 0)
        return predictions

class KNN:
    """K-Nearest Neighbors Classifier."""
    def __init__(self, k=3):
        self.k = k
        self.X_train = []
        self.y_train = []

    def fit(self, X, y):
        self.X_train = X
        self.y_train = y

    def _euclidean_distance(self, row1, row2):
        distance = 0.0
        for i in range(len(row1)):
            distance += (row1[i] - row2[i])**2
        return math.sqrt(distance)

    def predict(self, X):
        predictions = []
        for row in X:
            # 1. Calculate distances to all training points
            distances = []
            for i, train_row in enumerate(self.X_train):
                dist = self._euclidean_distance(row, train_row)
                distances.append((dist, self.y_train[i]))
            
            # 2. Sort by distance and take top K
            distances.sort(key=lambda x: x[0])
            neighbors = distances[:self.k]
            
            # 3. Vote
            classes = [n[1] for n in neighbors]
            most_common = Counter(classes).most_common(1)[0][0]
            predictions.append(most_common)
        return predictions

class KMeans:
    """Unsupervised Clustering."""
    def __init__(self, k=3, max_iters=100):
        self.k = k
        self.max_iters = max_iters
        self.centroids = []

    def _euclidean_distance(self, row1, row2):
        return math.sqrt(sum((row1[i] - row2[i])**2 for i in range(len(row1))))

    def fit(self, X):
        # 1. Randomly initialize centroids
        self.centroids = random.sample(X, self.k)
        
        for _ in range(self.max_iters):
            # 2. Assign clusters
            clusters = [[] for _ in range(self.k)]
            for point in X:
                distances = [self._euclidean_distance(point, c) for c in self.centroids]
                closest_idx = distances.index(min(distances))
                clusters[closest_idx].append(point)

            # 3. Update centroids
            prev_centroids = copy.deepcopy(self.centroids)
            for i in range(self.k):
                if clusters[i]:
                    n_features = len(X[0])
                    # Calculate mean of cluster points manually
                    means = []
                    for j in range(n_features):
                        col_values = [p[j] for p in clusters[i]]
                        means.append(sum(col_values) / len(col_values))
                    self.centroids[i] = means
            
            # 4. Check convergence
            if prev_centroids == self.centroids:
                break
        
        return self.centroids

# --- ADVANCED NON-LINEAR MODELS ---

class DecisionNode:
    """Helper struct for the Tree."""
    def __init__(self, feature_idx=None, threshold=None, left=None, right=None, value=None):
        self.feature_idx = feature_idx
        self.threshold = threshold
        self.left = left
        self.right = right
        self.value = value

class DecisionTreeClassifier:
    """
    Splits data based on rules (Gini Impurity). 
    Can handle complex non-linear data.
    """
    def __init__(self, max_depth=10, min_samples_split=2):
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.root = None

    def fit(self, X, y):
        self.root = self._grow_tree(X, y)

    def _gini(self, y):
        m = len(y)
        return 1.0 - sum((count / m) ** 2 for count in Counter(y).values())

    def _grow_tree(self, X, y, depth=0):
        n_samples = len(X)
        n_labels = len(set(y))

        # Stopping criteria
        if (depth >= self.max_depth or n_labels == 1 or n_samples < self.min_samples_split):
            leaf_value = Counter(y).most_common(1)[0][0]
            return DecisionNode(value=leaf_value)

        # Find best split
        n_feats = len(X[0])
        best_feat, best_thresh = None, None
        best_gini = 1.0
        
        # Random subset of features (useful if used in Random Forest later)
        feat_idxs = list(range(n_feats))
        
        for feat_idx in feat_idxs:
            thresholds = set(row[feat_idx] for row in X)
            for thr in thresholds:
                left_idxs = [i for i in range(n_samples) if X[i][feat_idx] <= thr]
                right_idxs = [i for i in range(n_samples) if X[i][feat_idx] > thr]

                if not left_idxs or not right_idxs: continue

                y_left = [y[i] for i in left_idxs]
                y_right = [y[i] for i in right_idxs]
                
                w_l, w_r = len(y_left)/n_samples, len(y_right)/n_samples
                gini = (w_l * self._gini(y_left)) + (w_r * self._gini(y_right))

                if gini < best_gini:
                    best_gini = gini
                    best_feat = feat_idx
                    best_thresh = thr

        if best_feat is None:
            return DecisionNode(value=Counter(y).most_common(1)[0][0])

        # Recurse
        left_idxs = [i for i in range(n_samples) if X[i][best_feat] <= best_thresh]
        right_idxs = [i for i in range(n_samples) if X[i][best_feat] > best_thresh]
        
        left = self._grow_tree([X[i] for i in left_idxs], [y[i] for i in left_idxs], depth+1)
        right = self._grow_tree([X[i] for i in right_idxs], [y[i] for i in right_idxs], depth+1)
        
        return DecisionNode(feature_idx=best_feat, threshold=best_thresh, left=left, right=right)

    def predict(self, X):
        return [self._traverse(x, self.root) for x in X]

    def _traverse(self, x, node):
        if node.value is not None: return node.value
        if x[node.feature_idx] <= node.threshold:
            return self._traverse(x, node.left)
        return self._traverse(x, node.right)

    def print_tree(self, node=None, indent=""):
        """ASCII Visualization."""
        if not node: node = self.root
        if node.value is not None:
            print(f"{indent}--> Predict: {node.value}")
        else:
            print(f"{indent}If Col_{node.feature_idx} <= {node.threshold}:")
            self.print_tree(node.left, indent + "  ")
            print(f"{indent}Else:")
            self.print_tree(node.right, indent + "  ")

class RandomForestClassifier:
    """
    Ensemble Learning: Trains multiple trees on random subsets 
    and averages their votes. Reduces overfitting.
    """
    def __init__(self, n_estimators=10, max_depth=5):
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.trees = []

    def fit(self, X, y):
        self.trees = []
        n_samples = len(X)
        
        for _ in range(self.n_estimators):
            # Bootstrap sampling (random selection with replacement)
            indices = [random.randint(0, n_samples-1) for _ in range(n_samples)]
            X_sample = [X[i] for i in indices]
            y_sample = [y[i] for i in indices]
            
            tree = DecisionTreeClassifier(max_depth=self.max_depth)
            tree.fit(X_sample, y_sample)
            self.trees.append(tree)

    def predict(self, X):
        # Gather predictions from all trees
        tree_preds = [tree.predict(X) for tree in self.trees]
        # Transpose to get predictions per sample
        # [[pred1_tree1, pred1_tree2], [pred2_tree1...]]
        predictions = []
        for i in range(len(X)):
            votes = [preds[i] for preds in tree_preds]
            most_common = Counter(votes).most_common(1)[0][0]
            predictions.append(most_common)
        return predictions
# ==========================================
# 4. VISUALIZATION ENGINE (ASCII)
# ==========================================

def bar_plot(categories, values, title="Bar Plot", width=40):
    """Prints a horizontal bar chart to the terminal."""
    print(f"\n--- {title} ---")
    if not values: return
    max_val = max(values)
    
    for cat, val in zip(categories, values):
        bar_len = int((val / max_val) * width)
        bar = "█" * bar_len
        print(f"{str(cat).ljust(10)} | {bar} {val}")
    print("-" * (width + 15) + "\n")

def scatter_plot(x, y, title="Scatter Plot", width=40, height=15):
    """ASCII Scatter Plot."""
    print(f"\n--- {title} ---")
    if not x or not y: return
    
    x_min, x_max = min(x), max(x)
    y_min, y_max = min(y), max(y)
    
    grid = [[' ' for _ in range(width)] for _ in range(height)]
    
    for xi, yi in zip(x, y):
        # Normalize to grid coordinates
        col = int((xi - x_min) / (x_max - x_min) * (width - 1)) if x_max != x_min else 0
        row = int((yi - y_min) / (y_max - y_min) * (height - 1)) if y_max != y_min else 0
        grid[height - 1 - row][col] = '*' # Flip row because y-axis goes up
        
    # Print Grid
    for row in grid:
        print("|" + "".join(row) + "|")
    print("+" + "-" * width + "+") 
    print(f"X: {x_min:.1f} to {x_max:.1f} | Y: {y_min:.1f} to {y_max:.1f}\n")

# ==========================================
# 5. FILE LOADERS
# ==========================================

def load_csv(filename):
    with open(filename, 'r') as f:
        reader = csv.DictReader(f)
        return DataFrame(list(reader))

def load_json(filename):
    with open(filename, 'r') as f:
        data = json.load(f)
        return DataFrame(data)
    
    # ==========================================
# 6. PREPROCESSING (Make Data "Model-Ready")
# ==========================================

class StandardScaler:
    """
    Vital for KNN & K-Means. Scales data so big numbers (Salary) 
    don't dominate small numbers (Age).
    Formula: z = (x - mean) / std_dev
    """
    def __init__(self):
        self.mean = []
        self.scale = []

    def fit(self, data):
        """data: List of lists (Matrix)"""
        if not data: return
        n_features = len(data[0])
        # Calculate mean/stdev per column
        self.mean = [mean([row[i] for row in data]) for i in range(n_features)]
        self.scale = [stdev([row[i] for row in data]) for i in range(n_features)]

    def transform(self, data):
        output = []
        for row in data:
            new_row = []
            for i, val in enumerate(row):
                if self.scale[i] == 0:
                    new_row.append(val - self.mean[i])
                else:
                    new_row.append((val - self.mean[i]) / self.scale[i])
            output.append(new_row)
        return output

    def fit_transform(self, data):
        self.fit(data)
        return self.transform(data)

class OneHotEncoder:
    """
    Converts text categories into numbers for ML.
    Example: ["Red", "Blue"] -> [[1, 0], [0, 1]]
    """
    def __init__(self):
        self.categories = []

    def fit(self, values):
        """values: List of strings/categories"""
        self.categories = sorted(list(set(values)))

    def transform(self, values):
        output = []
        for v in values:
            row = [0] * len(self.categories)
            if v in self.categories:
                row[self.categories.index(v)] = 1
            output.append(row)
        return output

# ==========================================
# 7. TIME SERIES (Trend Analysis)
# ==========================================

def moving_average(values, window=3):
    """
    Smooths out noisy data. Great for visualizing trends.
    """
    if len(values) < window: return values
    result = []
    for i in range(len(values) - window + 1):
        subset = values[i : i + window]
        result.append(mean(subset))
    return result

def exponential_moving_average(values, alpha=0.5):
    """
    EMA puts more weight on recent data.
    alpha: 0.1 (smooth) to 0.9 (reactive).
    """
    if not values: return []
    result = [values[0]]
    for i in range(1, len(values)):
        new_val = alpha * values[i] + (1 - alpha) * result[-1]
        result.append(new_val)
    return result

# ==========================================
# 8. MODEL EVALUATION (Did it work?)
# ==========================================

def accuracy_score(y_true, y_pred):
    if not y_true: return 0.0
    correct = sum(1 for t, p in zip(y_true, y_pred) if t == p)
    return correct / len(y_true)

def confusion_matrix(y_true, y_pred):
    """
    Prints a matrix showing exactly where predictions succeeded or failed.
    """
    classes = sorted(list(set(y_true + y_pred)))
    # Create grid: matrix[Actual][Predicted]
    matrix = {c: {c2: 0 for c2 in classes} for c in classes}
    
    for t, p in zip(y_true, y_pred):
        matrix[t][p] += 1
        
    # Pretty Print
    print("\n--- Confusion Matrix ---")
    print("      Predicted ->")
    header = "      " + "  ".join(str(c).ljust(5) for c in classes)
    print(header)
    print("-" * len(header))
    
    for actual in classes:
        row = f"Act {str(actual).ljust(2)}| "
        for pred in classes:
            val = str(matrix[actual][pred]).ljust(5)
            row += f"{val}  "
        print(row)
    return matrix

# ==========================================
# 9. GRAPH THEORY ENGINE (Network Analysis)
# ==========================================

class Graph:
    """
    Analyzes connections between things (Social Networks, Routes, etc.).
    """
    def __init__(self):
        # Adjacency List: {'Alice': {'Bob': 1, 'Charlie': 5}}
        self.edges = defaultdict(dict)
        self.nodes = set()

    def add_edge(self, u, v, weight=1):
        """Adds connection between u and v."""
        self.edges[u][v] = weight
        self.edges[v][u] = weight # Undirected graph
        self.nodes.add(u)
        self.nodes.add(v)

    def bfs(self, start, target=None):
        """
        Breadth-First Search.
        Returns: Path to target OR list of all reachable nodes.
        """
        queue = [[start]]
        visited = set()
        
        while queue:
            path = queue.pop(0)
            node = path[-1]
            
            if node == target:
                return path
            
            if node not in visited:
                visited.add(node)
                for neighbor in self.edges[node]:
                    new_path = list(path)
                    new_path.append(neighbor)
                    queue.append(new_path)
                    
        return list(visited) # Return all visited if no target found

    def shortest_path(self, start, end):
        """
        Dijkstra's Algorithm. Finds the fastest route based on weights.
        """
        # Priority Queue: (cost, current_node, path_taken)
        pq = [(0, start, [])]
        visited = set()
        
        while pq:
            (cost, node, path) = heapq.heappop(pq)
            
            if node in visited: continue
            visited.add(node)
            path = path + [node]
            
            if node == end:
                return (cost, path)
            
            for neighbor, weight in self.edges[node].items():
                if neighbor not in visited:
                    heapq.heappush(pq, (cost + weight, neighbor, path))
                    
        return (float('inf'), [])

    def centrality(self):
        """
        Finds the most "important" nodes (Degree Centrality).
        Returns sorted list of (Node, ConnectionCount).
        """
        scores = [(n, len(self.edges[n])) for n in self.nodes]
        return sorted(scores, key=lambda x: x[1], reverse=True)

# ==========================================
# 10. NLP ENGINE (Text Analysis)
# ==========================================

class NLP:
    STOPWORDS = {'the', 'is', 'at', 'which', 'on', 'a', 'an', 'and', 'or', 'of', 'to', 'in'}

    @staticmethod
    def tokenize(text):
        """Splits text into clean words, removing punctuation."""
        text = text.lower()
        # Remove punctuation manually to avoid imports
        for char in '.,!?;:"()[]{}':
            text = text.replace(char, '')
        
        tokens = text.split()
        return [t for t in tokens if t not in NLP.STOPWORDS]

    @staticmethod
    def word_cloud(text_list):
        """Returns frequency dictionary of most common words."""
        all_words = []
        for text in text_list:
            all_words.extend(NLP.tokenize(text))
        return Counter(all_words).most_common(10)

    @staticmethod
    def sentiment_lexicon():
        """Simple rule-based sentiment lexicon."""
        return {
            'good': 1, 'great': 2, 'excellent': 3, 'amazing': 3, 'love': 2,
            'bad': -1, 'terrible': -2, 'awful': -3, 'hate': -2, 'worst': -3
        }

    @staticmethod
    def sentiment(text):
        """
        Basic Sentiment Analysis (-Score to +Score).
        """
        tokens = NLP.tokenize(text)
        lexicon = NLP.sentiment_lexicon()
        score = 0
        for word in tokens:
            score += lexicon.get(word, 0)
        return score

# ==========================================
# 11. PROBABILITY & SIMULATION
# ==========================================

def normal_dist(mean, std_dev, size=100):
    """
    Generates random data following a Bell Curve (Gaussian).
    Uses Box-Muller transform.
    """
    data = []
    for _ in range(size):
        u1 = random.random()
        u2 = random.random()
        z = math.sqrt(-2 * math.log(u1)) * math.cos(2 * math.pi * u2)
        data.append(mean + z * std_dev)
    return data

def t_test(group_a, group_b):
    """
    Performs a T-Test to see if two groups are SIGNIFICANTLY different.
    Returns: t_score. (Large t means different, near 0 means same).
    """
    mean_a, mean_b = mean(group_a), mean(group_b)
    var_a, var_b = variance(group_a), variance(group_b)
    n_a, n_b = len(group_a), len(group_b)
    
    pooled_se = math.sqrt((var_a / n_a) + (var_b / n_b))
    if pooled_se == 0: return 0
    
    t_stat = (mean_a - mean_b) / pooled_se
    return t_stat

# ==========================================
# 12. MATRIX ENGINE (Linear Algebra)
# ==========================================

class Matrix:
    """
    Handles math for grids of numbers (Deep Learning foundation).
    """
    @staticmethod
    def dot(A, B):
        """Matrix Multiplication (Dot Product)."""
        rows_A, cols_A = len(A), len(A[0])
        rows_B, cols_B = len(B), len(B[0])
        
        if cols_A != rows_B:
            raise ValueError(f"Shape mismatch: {cols_A} vs {rows_B}")
            
        result = [[0 for _ in range(cols_B)] for _ in range(rows_A)]
        
        for i in range(rows_A):
            for j in range(cols_B):
                for k in range(cols_A):
                    result[i][j] += A[i][k] * B[k][j]
        return result

    @staticmethod
    def transpose(matrix):
        """Flips rows and columns."""
        return [[matrix[j][i] for j in range(len(matrix))] for i in range(len(matrix[0]))]

    @staticmethod
    def shape(matrix):
        return (len(matrix), len(matrix[0]))

# ==========================================
# 13. DATA QUALITY (Outlier Detection)
# ==========================================

def remove_outliers(data, threshold=2.0):
    """
    Uses Z-Score to remove data that is 'too weird'.
    threshold: 2.0 (Standard), 3.0 (Strict).
    Returns: Cleaned List.
    """
    if not data: return []
    mu = mean(data)
    sigma = stdev(data)
    
    if sigma == 0: return data
    
    clean_data = []
    for x in data:
        z_score = abs((x - mu) / sigma)
        if z_score < threshold:
            clean_data.append(x)
    return clean_data

# ==========================================
# 14. REPORTING (Export to Web/Docs)
# ==========================================

def to_html(df, filename="report.html"):
    """Saves DataFrame as a styled HTML Table."""
    html = """
    <html>
    <head>
        <style>
            table { border-collapse: collapse; width: 100%; font-family: sans-serif; }
            th, td { text-align: left; padding: 12px; border-bottom: 1px solid #ddd; }
            th { background-color: #04AA6D; color: white; }
            tr:hover { background-color: #f5f5f5; }
        </style>
    </head>
    <body>
        <h2>Data Export</h2>
        <table>
            <thead>
                <tr>
    """
    # Headers
    for col in df.columns:
        html += f"<th>{col}</th>"
    html += "</tr></thead><tbody>"
    
    # Rows
    for row in df.data:
        html += "<tr>"
        for col in df.columns:
            html += f"<td>{row.get(col, '')}</td>"
        html += "</tr>"
        
    html += "</tbody></table></body></html>"
    
    with open(filename, "w") as f:
        f.write(html)
    print(f"Exported to {filename}")

def to_markdown(df):
    """Returns a Markdown formatted table string."""
    if not df.columns: return ""
    
    # Headers
    md = "| " + " | ".join(df.columns) + " |\n"
    md += "| " + " | ".join(["---"] * len(df.columns)) + " |\n"
    
    # Rows
    for row in df.data:
        md += "| " + " | ".join(str(row.get(c, '')) for c in df.columns) + " |\n"
    
    return md
# ==========================================
# 15. NUMPY ENGINE (Vector Math)
# ==========================================

class Vector:
    """
    Simulates a NumPy Array. Allows math on whole lists.
    Usage: Vector([1, 2]) + Vector([3, 4]) = Vector([4, 6])
    """
    def __init__(self, data):
        self.data = data

    def __repr__(self):
        return f"Vec({self.data})"

    def __add__(self, other):
        return self._op(other, lambda x, y: x + y)

    def __sub__(self, other):
        return self._op(other, lambda x, y: x - y)

    def __mul__(self, other):
        return self._op(other, lambda x, y: x * y)

    def __truediv__(self, other):
        return self._op(other, lambda x, y: x / y)

    def _op(self, other, func):
        if isinstance(other, (int, float)):
            # Broadcasting (Vec * Scalar)
            return Vector([func(x, other) for x in self.data])
        elif isinstance(other, Vector):
            # Element-wise (Vec * Vec)
            if len(self.data) != len(other.data):
                raise ValueError("Vectors must be same length")
            return Vector([func(a, b) for a, b in zip(self.data, other.data)])
        else:
            raise TypeError("Operation not supported")

    def sum(self): return sum(self.data)
    def mean(self): return mean(self.data) # Uses your existing mean()

# ==========================================
# 16. PANDAS ENGINE (Merge & Pivot)
# ==========================================

def merge(df1, df2, on, how="inner"):
    """
    SQL-style Joins. Combines two DataFrames.
    how: 'inner' (only matches), 'left' (keep all left), 'outer' (keep all).
    """
    joined_data = []
    # Create lookup table for df2 for speed (Hash Map)
    df2_map = defaultdict(list)
    for row in df2.data:
        key = row.get(on)
        if key is not None:
            df2_map[key].append(row)

    # All columns
    all_cols = list(set(df1.columns + df2.columns))

    for row1 in df1.data:
        key = row1.get(on)
        matches = df2_map.get(key, [])
        
        if not matches:
            if how in ["left", "outer"]:
                # No match found, but keeping row (fill missing with None)
                new_row = row1.copy()
                for col in df2.columns: 
                    if col not in new_row: new_row[col] = None
                joined_data.append(new_row)
        else:
            for match in matches:
                # Merge dictionaries
                new_row = {**row1, **match}
                joined_data.append(new_row)
                
    return DataFrame(joined_data)

def pivot_table(df, index, values, aggfunc=sum):
    """
    Summarizes data. 
    Ex: Sum of 'Sales' (values) grouped by 'Region' (index).
    """
    groups = defaultdict(list)
    for row in df.data:
        key = row.get(index)
        val = row.get(values)
        if key is not None and val is not None:
            groups[key].append(val)
            
    # Aggregate
    summary = []
    for key, val_list in groups.items():
        summary.append({index: key, values: aggfunc(val_list)})
        
    return DataFrame(summary)

# ==========================================
# 17. SKLEARN ENGINE (Save/Load & Validation)
# ==========================================

def save_model(model, filename):
    """Saves a trained AI model to a file (Pickle)."""
    with open(filename, 'wb') as f:
        pickle.dump(model, f)
    print(f"Model saved to {filename}")

def load_model(filename):
    """Loads a trained AI model from a file."""
    with open(filename, 'rb') as f:
        return pickle.load(f)

def cross_val_score(model_class, X, y, cv=5):
    """
    K-Fold Cross Validation.
    Splits data into 'cv' parts, trains on (cv-1), tests on 1.
    Returns: Average Accuracy.
    """
    data_size = len(X)
    fold_size = data_size // cv
    indices = list(range(data_size))
    random.shuffle(indices)
    
    scores = []
    
    for i in range(cv):
        # 1. Split Indices
        test_idx = indices[i*fold_size : (i+1)*fold_size]
        train_idx = [idx for idx in indices if idx not in test_idx]
        
        # 2. Build Data
        X_train = [X[i] for i in train_idx]
        y_train = [y[i] for i in train_idx]
        X_test = [X[i] for i in test_idx]
        y_test = [y[i] for i in test_idx]
        
        # 3. Train & Test
        model = model_class() # Create new instance
        model.fit(X_train, y_train)
        preds = model.predict(X_test)
        
        # 4. Score (Simple Accuracy)
        correct = sum(1 for p, t in zip(preds, y_test) if p == t)
        scores.append(correct / len(y_test))
        
    return sum(scores) / len(scores)


# ==========================================
# 18. DEEP LEARNING ENGINE (Mini-PyTorch)
# ==========================================

def _backward_none():
    """Empty function for initialization to satisfy Pickle."""
    pass

class Value:
    """
    A specific number that tracks its own history for Backpropagation.
    Fixed for Pickling (Saving) by removing lambdas.
    """
    def __init__(self, data, _children=(), _op='', label=''):
        self.data = data
        self.grad = 0.0
        self._backward = _backward_none # <--- THE FIX
        self._prev = set(_children)
        self._op = _op
        self.label = label

    def __repr__(self):
        return f"Value(data={self.data})"

    def __add__(self, other):
        other = other if isinstance(other, Value) else Value(other)
        out = Value(self.data + other.data, (self, other), '+')
        def _backward():
            self.grad += 1.0 * out.grad
            other.grad += 1.0 * out.grad
        out._backward = _backward
        return out

    def __radd__(self, other):
        return self + other

    def __mul__(self, other):
        other = other if isinstance(other, Value) else Value(other)
        out = Value(self.data * other.data, (self, other), '*')
        def _backward():
            self.grad += other.data * out.grad
            other.grad += self.data * out.grad
        out._backward = _backward
        return out

    def __rmul__(self, other):
        return self * other

    def __pow__(self, other):
        assert isinstance(other, (int, float))
        out = Value(self.data**other, (self,), f'**{other}')
        def _backward():
            self.grad += other * (self.data ** (other - 1)) * out.grad
        out._backward = _backward
        return out

    def __neg__(self): 
        return self * -1

    def __sub__(self, other): 
        return self + (-other)

    def __truediv__(self, other): 
        return self * other**-1

    def exp(self):
        x = self.data
        out = Value(math.exp(x), (self,), 'exp')
        def _backward():
            self.grad += out.data * out.grad
        out._backward = _backward
        return out

    def log(self):
        x = self.data
        out = Value(math.log(x), (self,), 'log')
        def _backward():
            self.grad += (1 / x) * out.grad
        out._backward = _backward
        return out

    def relu(self):
        out = Value(0 if self.data < 0 else self.data, (self,), 'ReLU')
        def _backward():
            self.grad += (out.data > 0) * out.grad
        out._backward = _backward
        return out

    def backward(self):
        topo = []
        visited = set()
        def build_topo(v):
            if v not in visited:
                visited.add(v)
                for child in v._prev:
                    build_topo(child)
                topo.append(v)
        build_topo(self)
        self.grad = 1.0
        for node in reversed(topo):
            node._backward()

# --- NEURAL NETWORK LAYERS ---

class Neuron:
    def __init__(self, nin):
        self.w = [Value(random.uniform(-1,1)) for _ in range(nin)]
        self.b = Value(random.uniform(-1,1))
    def __call__(self, x):
        act = sum((wi*xi for wi, xi in zip(self.w, x)), self.b)
        return act.relu()
    def parameters(self):
        return self.w + [self.b]

class Layer:
    def __init__(self, nin, nout):
        self.neurons = [Neuron(nin) for _ in range(nout)]
    def __call__(self, x):
        outs = [n(x) for n in self.neurons]
        return outs[0] if len(outs) == 1 else outs
    def parameters(self):
        return [p for n in self.neurons for p in n.parameters()]

class MLP:
    def __init__(self, nin, nouts):
        sz = [nin] + nouts
        self.layers = [Layer(sz[i], sz[i+1]) for i in range(len(nouts))]
    def __call__(self, x):
        for layer in self.layers:
            x = layer(x)
        return x
    def parameters(self):
        return [p for layer in self.layers for p in layer.parameters()]
# ==========================================
# 19. LLM BUILDING BLOCKS (The Transformer)
# ==========================================

def softmax(x):
    """
    Converts raw scores into probabilities.
    Works for both standard lists AND Value() objects for AI training.
    """
    # Check if we are working with AI Nodes or standard numbers
    if x and isinstance(x[0], Value):
        e_x = [val.exp() for val in x]
    else:
        e_x = [math.exp(val) for val in x]
        
    # Sum using Value-compatible start
    sum_e_x = sum(e_x)
    
    return [i / sum_e_x for i in e_x]

class SelfAttention:
    """
    A simplified version of the 'Attention' mechanism in LLMs.
    It decides which words are related to each other.
    """
    @staticmethod
    def attend(query, keys, values):
        """
        Q (Query): What I am looking for?
        K (Keys): What do I have?
        V (Values): What information is inside?
        """
        # 1. Calculate Similarity (Dot Product)
        scores = []
        for key in keys:
            # Simple dot product similarity
            score = sum(q * k for q, k in zip(query, key))
            scores.append(score)
            
        # 2. Convert to Probabilities (Softmax)
        # Now uses the smart softmax that handles backpropagation
        probs = softmax(scores)
        
        # 3. Weighted Sum of Values
        dim = len(values[0])
        
        # We need to initialize output with 0 or Value(0) depending on context
        is_ai = isinstance(values[0][0], Value)
        zero = Value(0.0) if is_ai else 0.0
        output = [zero] * dim
        
        for i, prob in enumerate(probs):
            for j in range(dim):
                output[j] += prob * values[i][j]
                
        return output, probs
# ==========================================
# 20. TRAINING INFRASTRUCTURE (The Trainer)
# ==========================================

class SGD:
    def __init__(self, parameters, lr=0.01):
        self.parameters = parameters
        self.lr = lr
    def step(self):
        for p in self.parameters:
            p.data -= self.lr * p.grad
    def zero_grad(self):
        for p in self.parameters:
            p.grad = 0.0

class Adam:
    """
    The industry-standard optimizer. 
    Much faster/stable convergence than SGD because it adapts 
    the learning rate for every parameter individually.
    """
    def __init__(self, parameters, lr=0.001, beta1=0.9, beta2=0.999, eps=1e-8):
        self.params = parameters
        self.lr = lr
        self.beta1, self.beta2 = beta1, beta2
        self.eps = eps
        self.t = 0
        # Storage for momentum (m) and velocity (v)
        self.m = [0.0] * len(parameters)
        self.v = [0.0] * len(parameters)

    def step(self):
        self.t += 1
        for i, p in enumerate(self.params):
            if p.grad == 0: continue # Skip if no gradient
            grad = p.grad

            # Update biased first moment estimate (Momentum)
            self.m[i] = self.beta1 * self.m[i] + (1 - self.beta1) * grad
            # Update biased second raw moment estimate (Velocity)
            self.v[i] = self.beta2 * self.v[i] + (1 - self.beta2) * (grad ** 2)

            # Compute bias-corrected first moment estimate
            m_hat = self.m[i] / (1 - self.beta1 ** self.t)
            # Compute bias-corrected second raw moment estimate
            v_hat = self.v[i] / (1 - self.beta2 ** self.t)

            # Update parameters
            p.data -= self.lr * m_hat / (math.sqrt(v_hat) + self.eps)

    def zero_grad(self):
        for p in self.params:
            p.grad = 0.0

class MSELoss:
    def __call__(self, y_pred, y_true):
        return sum((yout - ygt)**2 for ygt, yout in zip(y_true, y_pred))

class CrossEntropyLoss:
    """
    Used for Classification.
    Now uses pure Value operations for full backpropagation support.
    """
    def __call__(self, logits, target_idx):
        # 1. Exponentiate (using Value.exp)
        counts = [x.exp() for x in logits]
        
        # 2. Sum (using Value sum)
        total = sum(counts)
        
        # 3. Probabilities
        probs = [c / total for c in counts]
        
        # 4. Negative Log Likelihood
        log_likelihood = probs[target_idx].log()
        
        return -log_likelihood
# ==========================================
# 21. LLM TOKENIZER (Text to Numbers)
# ==========================================

class CharTokenizer:
    """
    Character-level Tokenizer. 
    Essential for training GPTs from scratch on simple text (like Shakespeare).
    """
    def __init__(self):
        self.stoi = {} # String to Integer
        self.itos = {} # Integer to String
        self.vocab_size = 0

    def fit(self, text):
        """Learns the unique characters in the text."""
        chars = sorted(list(set(text)))
        self.vocab_size = len(chars)
        self.stoi = {ch:i for i,ch in enumerate(chars)}
        self.itos = {i:ch for i,ch in enumerate(chars)}

    def encode(self, s):
        """Converts string to list of integers."""
        return [self.stoi[c] for c in s]

    def decode(self, l):
        """Converts list of integers back to string."""
        return ''.join([self.itos[i] for i in l])

# ==========================================
# 22. DATA BATCHING (DataLoader)
# ==========================================

def get_batch(data, block_size, batch_size):
    """
    Generates small chunks of data for training LLMs.
    X: Input chunk
    Y: Target chunk (offset by 1)
    """
    n = len(data)
    ix = [random.randint(0, n - block_size) for _ in range(batch_size)]
    x = [data[i:i+block_size] for i in ix]
    y = [data[i+1:i+block_size+1] for i in ix]
    return x, y
# ==========================================
# 23. PIPELINE ENGINE (The Glue)
# ==========================================

class Pipeline:
    """
    Chains multiple steps together so they behave like a single model.
    Example: Pipeline([('scaler', StandardScaler()), ('model', KNN())])
    """
    def __init__(self, steps):
        self.steps = steps  # List of tuples: [('name', ClassInstance), ...]

    def fit(self, X, y):
        """
        Fits all transformers one by one, transforming the data,
        then fits the final model.
        """
        data = X
        # Iterate through all steps except the last one (the transformers)
        for name, step in self.steps[:-1]:
            if hasattr(step, 'fit_transform'):
                data = step.fit_transform(data)
            else:
                step.fit(data)
                if hasattr(step, 'transform'):
                    data = step.transform(data)
        
        # Fit the final estimator (the actual AI model)
        last_step = self.steps[-1][1]
        last_step.fit(data, y)
        print(f"Pipeline fitted successfully. Steps: {[s[0] for s in self.steps]}")

    def predict(self, X):
        """
        Passes data through all transformers, then predicts with the final model.
        """
        data = X
        for name, step in self.steps[:-1]:
            if hasattr(step, 'transform'):
                data = step.transform(data)
        
        # Predict using the final model
        last_step = self.steps[-1][1]
        return last_step.predict(data)
