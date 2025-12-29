import numpy as np
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, ConstantKernel as C
from sklearn.preprocessing import StandardScaler
class Kriging:
    '''
    多次元Kriging管理クラス
    '''
    def setData(self,X,W):
        '''
        多次元座標値，値のセット
        X: np.array型の多次元データ
        W: 対応する値
        '''
        # スケーリング
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)
        self.X=X_scaled
        self.W=W
        self.n=len(W)
        self.n_degree=X.shape[1]
    def setData2(self,X,W):
        '''
        多次元座標値，値のセット
        X: np.array型の多次元データ
        W: 対応する値
        '''
        # スケーリング
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)
        self.X=X_scaled
        self.scalerW=StandardScaler()
        W_scaled = self.scalerW.fit_transform(W.reshape(-1, 1)).ravel()
        self.W=W_scaled
        self.n=len(W)
        self.n_degree=X.shape[1]
    def Fit(self,alpha=1e-10):
        '''
        alpha: Krigingの際のノイズの程度。この値を大きくすると収束性が改善する。
        '''
        # クリッギング（ガウス過程回帰）
        kernel = C(1.0, (1e-2, 1e2)) * RBF(length_scale=1.0, length_scale_bounds=(1e-2, 1e2))
        self.gpr = GaussianProcessRegressor(kernel=kernel, n_restarts_optimizer=10, alpha=alpha)
        self.gpr.fit(self.X, self.W)
        # R²スコアの計算
        r2_score = self.gpr.score(self.X, self.W)
        return r2_score        
    def Predict(self,target_point):
        target_scaled=self.scaler.transform(target_point)
        # 3. 任意の点での予測
        w_pred, sigma = self.gpr.predict(target_scaled, return_std=True)
        return w_pred,sigma
    def Predict2(self,target_point):
        target_scaled=self.scaler.transform(target_point)
        # 3. 任意の点での予測
        w_pred_s, sigma_s = self.gpr.predict(target_scaled, return_std=True)
        w_pred=self.scalerW.inverse_transform(w_pred_s.reshape(-1,1)).ravel()
        sigma=sigma_s*self.scalerW.scale_[0]
        return w_pred,sigma
    def Diff(self,target_point,epsilon = 1e-5):
        '''
        epsilon: 勾配計算の際の変動割合
        '''
        target_scaled=self.scaler.transform(target_point)
        # 勾配の計算 (数値微分)
        n_degree=target_point.shape[1]
        grad = np.zeros(n_degree)  # 勾配を格納
        # スケーリング情報
        sigma = self.scaler.scale_  # 各特徴量の標準偏差
        for i in range(n_degree):
            delta = np.zeros_like(target_scaled)
            delta[0, i] = epsilon  # 各次元に微小変化を加える
            p1_scaled=self.gpr.predict(target_scaled + delta)
            p2_scaled=self.gpr.predict(target_scaled - delta)
            grad_scaled= (p1_scaled-p2_scaled) / (2 * epsilon)
            # 元のスケールでの勾配に変換
            grad[i] = grad_scaled / sigma[i]
        return grad
# メインプログラム
if __name__ == "__main__":
    # クラスのインスタンスを作成
    krig=Kriging()
    # 1. データの準備
    # サンプルデータ: (x, y, z) -> 値 w
    np.random.seed(42)
    n_samples = 50
    X = np.random.rand(n_samples, 3)  # 入力データ (x, y, z)
    W = np.sin(X[:, 0]) + np.cos(X[:, 1]) + X[:, 2]**2  # 出力データ (w)
    krig.setData(X,W)
    r2_score=krig.Fit(alpha=1e-5)
    target_point = np.array([[0.5, 0.5, 0.5]])  # 任意の座標 (x, y, z)
    w_pred,sigma=krig.Predict(target_point)
    grad=krig.Diff(target_point) 
    # 結果の表示
    print(f"r2_score={r2_score}")
    print(f"予測値 w({target_point[0]}) = {w_pred[0]},標準偏差={sigma}")
    print(f"勾配 ∂w/∂x = {grad[0]}, ∂w/∂y = {grad[1]}, ∂w/∂z = {grad[2]}")        
    #r2_score=0.9999971250501587
    #予測値 w([0.5 0.5 0.5]) = 1.606729503535007,標準偏差=[0.00135787]
    #勾配 ∂w/∂x = 0.8752025536567988, ∂w/∂y = -0.4744578901539049, ∂w/∂z = 1.0020751941377448