# -*- coding: utf-8 -*-
"""
Created on Tue Jul 30 16:15:25 2024
structure to create Surrogate models
01.08.2024: for multilayer perceptrons (have proven themselves)
needs a labeled DataFrame with training data

@author: welp
"""
import carbatpy as cb
import pandas as pd
import joblib
import os
import pickle
import numpy as np
import yaml

from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPRegressor
from sklearn.model_selection import RandomizedSearchCV

from datetime import datetime

class Surrogate:
    
    def __init__(self, title):
        self.title = title
                
        
    def _make_xy(self, DF):
        '''
        creates feature and target array and dataframe

        '''
        
        #create X and y from feature and target list
        self.DF_x = DF[self.features_list]  
        self.DF_y = DF[self.targets_list]
     
        self.x_data_arr = self.DF_x.to_numpy(copy=True)
        self.y_data_arr = self.DF_y.to_numpy(copy=True)
        
    def train_surrogate(
            self, DF, features_list, targets_list, split = 0.2, 
            random_state = 42, hypo="def_hyperparameter.yaml", verbose=False):
        """
        train MLP surrogate from dataframe with chosen features and targets,
        uses minmaxscaler and 'r2', 'neg_root_mean_squared_error' for scoring,
        the latter for refitting
        
        Parameters
        ----------
        DF : TYPE
            DESCRIPTION.
        features_list : TYPE
            DESCRIPTION.
        targets_list : TYPE
            DESCRIPTION.
        split : TYPE, optional
            DESCRIPTION. The default is 0.2.
        random_state : TYPE, optional
            DESCRIPTION. The default is 42.
        hypo : TYPE, optional
            DESCRIPTION. The default is "def_hyperparameter.yaml".

        Returns
        -------
        Y_test : TYPE DataFrame
            DESCRIPTION. test targets
        Y_pred : TYPE
            DESCRIPTION. predicted targets

        """
        
        # create train and test set
        self.features_list = features_list
        self.targets_list = targets_list
        self.split = split
        self.random_state = random_state
        
        self.scaler_x = MinMaxScaler()
        self.scaler_y = MinMaxScaler()
        self._make_xy(DF)
    
        X_train, X_test, y_train, y_test = train_test_split(
            self.x_data_arr, self.y_data_arr, test_size=self.split, random_state=self.random_state)
        self.x_range = [np.min(X_train, axis=0), np.max(X_train, axis=0)]
        X_train = self.scaler_x.fit_transform(X_train)
        X_test = self.scaler_x.transform(X_test)
    
        y_train= self.scaler_y.fit_transform(y_train)
        y_test = self.scaler_y.transform(y_test)
    
        with open(hypo, 'r') as file:
            self.parameters = yaml.safe_load(file)
            
        # Define and start hyperparameter optimization
        if hypo ==  "def_hyperparameter.yaml":
            full_set = []
            for i,nhl in enumerate(self.parameters["hidden_layers"]):
                for j, n in enumerate(self.parameters["neurons"]):
                    NN = [n] * nhl
                    NN = list(NN)
                    full_set.append(NN)
            del self.parameters['hidden_layers']
            del self.parameters['neurons']
            self.parameters['hidden_layer_sizes'] = full_set
                
        # Create MLP for all targets
        model = MLPRegressor(max_iter=2000, n_iter_no_change=30)
    
        RS = RandomizedSearchCV(model, self.parameters, 
                            scoring=('r2', 'neg_root_mean_squared_error'), 
                            refit='neg_root_mean_squared_error', n_iter=100,
                            n_jobs = -1, cv=3)
        
        RS.fit(X_train, y_train)
        
        self.RS = RS
        self.model = RS.best_estimator_
        
        if verbose == True:
            print('best parameters: ', RS.best_params_)
            print('best estimator: ', RS.best_estimator_)
            print('best score: ', RS.best_score_)
        
        y_pred = RS.predict(X_test)

        y_pred = self.scaler_y.inverse_transform(y_pred)
        y_test = self.scaler_y.inverse_transform(y_test)
        Y_pred = pd.DataFrame(y_pred, columns=targets_list)
        Y_test = pd.DataFrame(y_test, columns=targets_list)
        return Y_test, Y_pred

        
    def save(self, path="default"):
        """
        save model

        Parameters
        ----------
        path : TYPE, optional
            DESCRIPTION. The default is CARBATPY_RES_DIR

        Returns
        -------
        None.

        """
        
        elements = '-'.join(self.features_list)
        # Get the current date and time
        current_time = datetime.now()
        # Format the date and time as a string
        timestamp = current_time.strftime("%Y-%m-%d_%H-%M-%S")
        if path == "default":
            file_out = cb.CB_DEFAULTS["General"]["RES_DIR"] +'\\surrogates\\MLP-R\\' + elements + '\\' + timestamp + '\\'
        else:
            file_out = path + elements + '\\' + timestamp + '\\'
        try:
            os.makedirs(file_out)
        except: 
            pass    
        
        # Save results
        joblib.dump(self.RS, file_out + 'MLP_RS.pkl')
        joblib.dump(self.RS, file_out + 'MLP_RS.sav')
        joblib.dump(self.scaler_x, file_out + 'MLP_scaler_x.pkl')
        joblib.dump(self.scaler_y, file_out + 'MLP_scaler_y.pkl')
        joblib.dump(self.model, file_out + 'mlp.pkl')  


        self.DF_x.to_csv(file_out + 'X.txt', index=False)
        self.DF_y.to_csv(file_out + 'y.txt', index=False)

        # Creates output file with information and results
        filename = "MLP_Randomized_search_parameter.txt"
        file = open(file_out +  filename, "w")
        for key in range(len(list(self.parameters.keys()))):
            text = list(self.parameters.keys())[key] + ': ' + str(self.parameters[list(self.parameters.keys())[key]])+'\n'
            file.write(text)
        file.close()

        with open(file_out + 'features_list.pkl', 'wb') as file:
            pickle.dump(self.features_list, file)
            
        with open(file_out + 'targets_list.pkl', 'wb') as file:
            pickle.dump(self.targets_list, file)    
        
        with open(file_out + 'random_state.pkl', 'wb') as file:
            pickle.dump(self.random_state, file)
        
        with open(file_out + 'x_range.pkl', 'wb') as file:
            pickle.dump(self.x_range, file)

        # Ergebnisse in eine Textdatei schreiben
        filename = 'MLP_randomized_search_results.txt'
        with open(file_out + filename, "w") as file:
            file.write("Best parameter: {}\n".format(self.RS.best_params_))
            file.write("Best score: {}\n".format(self.RS.best_score_))
            
    def load(self, path):
        # loading ML models
        self.model = joblib.load(path + 'mlp.pkl')
        self.scaler_x = joblib.load(path + 'MLP_scaler_x.pkl')
        self.scaler_y = joblib.load(path + 'MLP_scaler_y.pkl')

        # Loading features and targets
        with open(path + 'features_list.pkl', 'rb') as file:
            self.features_list = pickle.load(file)
            
        with open(path + 'targets_list.pkl', 'rb') as file:
            self.targets_list = pickle.load(file) 
        
        with open(path + 'random_state.pkl', 'rb') as file:
            self.random_state = pickle.load(file)
            
        with open(path + 'x_range.pkl', 'rb') as file:
            self.x_range = pickle.load(file)
    
    def predict(self, DF_new_x):
        """
        use existing surrogate to predict new data

        Parameters
        ----------
        DF_new_x : TYPE
            DESCRIPTION.

        Raises
        ------
        ValueError
            DESCRIPTION. needs to contain features of model
        
            DESCRIPTION. does not extrapolate

        Returns
        -------
        y : TYPE
            DESCRIPTION. target results
        DF_y : TYPE
            DESCRIPTION. target results

        """
        
        try:
            DF_x = DF_new_x[self.features_list] 
        except:
            raise ValueError("features in DF_new_x not in features_list of model")

        X = DF_x.to_numpy(copy=True)
        if np.all(np.all((X >= self.x_range[0]) & (X <= self.x_range[1]), axis=0)) != True:
            raise ValueError(f"""x_predict is outside of data range used for training
                             range of training data:
                                  {self.features_list}
                             min: {self.x_range[0]}
                             max: {self.x_range[1]}""")
        try:
            X_scaled = self.scaler_x.transform(X)
            y_scaled = self.model.predict(X_scaled)
            y = self.scaler_y.inverse_transform(y_scaled)
        except:
            raise 
        DF_y = pd.DataFrame(y)
        DF_y.columns = self.targets_list
        return y, DF_y
        
    
if __name__ == "__main__":
    mode = 1  # 1: train new, 2: load existing
    
    if mode == 1:
        # first test case
        compressor = Surrogate("piston compressor")   
        DF = pd.read_csv(cb.CB_DEFAULTS['General']['CB_DATA'] + '\\Example_compressor_data.csv')    
        DF = DF[DF.counter < 100]       # filter failed results, iteration stops after 100 trials
        DF = DF[DF.is_eff != 1]         # eliminates 1 (invalid fluid properties)
    
        # choose features and targets
        features_list =  ['p_ve', 'T_e', 'v_e']
        targets_list = ['is_eff', 'degree_delivery', 'T_aus']
        
        compressor.train_surrogate(DF, features_list, targets_list)
        
        #compressor.save()  # not activated (will trash the discspace)
        
        
    elif mode == 2:
        my_new_compressor = Surrogate("my new compressor")
        my_new_compressor.load(cb.CB_DEFAULTS['General']['CB_DATA'] + '\\def_hyperparameter.yaml')
        x_predict = np.array([[7, 290, 0.2], [3, 305, 0.3]])
        x_predict = pd.DataFrame(x_predict)
        x_predict.columns = ['p_ve', 'T_e', 'v_e']
        y, y_DF = my_new_compressor.predict(x_predict)
    
    
