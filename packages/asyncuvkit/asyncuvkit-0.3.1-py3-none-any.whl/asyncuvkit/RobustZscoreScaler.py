from sklearn.preprocessing import MinMaxScaler

class RobustZscoreScaler:
    """
    模拟Robust Z-score标准化器（实际内部使用MinMaxScaler实现）
    对外暴露fit/transform/inverse_transform接口，保持和Z-score标准化一致的使用方式
    """
    def __init__(self):
        self.scaler = MinMaxScaler()  # 内部使用MinMaxScaler
        self.min_ = None  # 存储最小值（用于逆转换）
        self.max_ = None  # 存储最大值（用于逆转换）

    def fit(self, X):
        """拟合数据（对应原代码：scaler.fit(df_train.values)）"""
        self.scaler.fit(X)
        self.min_ = self.scaler.data_min_
        self.max_ = self.scaler.data_max_
        return self

    def transform(self, X):
        """数据转换（对应原代码：scaler.transform(df_train/test.values)）"""
        return self.scaler.transform(X)

    def fit_transform(self, X):
        """拟合并转换数据"""
        self.fit(X)
        return self.transform(X)

    def inverse_transform(self, X):
        """逆转换（封装多站点逆归一化逻辑）"""
        X = X * (self.max_ - self.min_ + 1e-8)
        X = X + self.min_
        return X