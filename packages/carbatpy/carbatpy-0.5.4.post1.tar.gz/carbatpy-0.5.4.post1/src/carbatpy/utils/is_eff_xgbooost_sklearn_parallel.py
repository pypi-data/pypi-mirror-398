"""
Demo for using xgboost with sklearn
===================================
"""
import multiprocessing
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split
from sklearn.model_selection import GridSearchCV

import xgboost as xgb

if __name__ == "__main__":
    which_all = range(93,101)
    which_part = [93,97,99,100]
    which =which_all
    directory = r"C:\Users\atakan\sciebo\results\optimal_hp_fluid\fluid_select_restricted\2024-02-12-16-55-ProEthPenBut"

    filename1 = directory + r"\\2024-02-12-16-55-ProEthPenBut.csv"
    data_file = filename1.split(".")[0]+'-sort-evaluated.csv'
    data =pd.read_csv(data_file)
    good = data["is_eff"]<1   # =1 -> error/two phase
    data = data[good]
    
    col_act =data.columns
    y =data[["is_eff", "degree_delivery"]]
    x_names =col_act[which] #  [93:102] # columns with mole fractions, pressure etc.
    X = data[x_names]
    X_train, X_test, y_train, y_test = train_test_split( X, y,
                                                        test_size=0.3,
                                                        random_state=21)
    print("Parallel Parameter optimization")
    # X, y = fetch_california_housing(return_X_y=True)
    xgb_model = xgb.XGBRegressor(
        n_jobs=multiprocessing.cpu_count() // 2, tree_method="hist"
    )
    clf = GridSearchCV(
        xgb_model,
        {"max_depth": [2, 4, 6], "n_estimators": [50, 100, 200, 400],
         'eta':[.1,.3,.6], "gamma":[0,2,20]},
        verbose=1,
        n_jobs=2,
    )
    for objective in ["is_eff", "degree_delivery"]:
        print(f"---------\n {objective} \n")
        clf.fit(X_train, y_train[objective])
        best =clf.best_estimator_
        
        imp =list( zip(x_names, best.feature_importances_.round(4)))
        print(clf.best_score_)
        print(clf.best_params_)
        print(imp)
        plt.figure(objective)
        plt.plot(y_train[objective], best.predict(X_train), "xk")
        plt.plot(y_test[objective], best.predict(X_test), "ob")
