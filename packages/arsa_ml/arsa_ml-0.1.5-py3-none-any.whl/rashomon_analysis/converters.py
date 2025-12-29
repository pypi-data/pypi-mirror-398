from autogluon.tabular import TabularDataset, TabularPredictor
from autogluon.core.metrics import BINARY_METRICS, MULTICLASS_METRICS
import pandas as pd
from typing import Tuple, Dict
from pathlib import Path
import numpy as np
import os
import h2o
from h2o.automl import H2OAutoML
from sklearn.metrics import accuracy_score, balanced_accuracy_score, precision_score, roc_auc_score, recall_score, f1_score,average_precision_score
from sklearn.preprocessing import LabelEncoder
import pickle
from abc import ABC, abstractmethod
from sklearn.model_selection import train_test_split
BASE_DIR = Path(__file__).resolve().parents[2]
RES_SAVING_DIR = BASE_DIR/"converter_results"

class Converter(ABC):
    '''
    This is an abstract class defining all necessary methods, which have to be implemented in any converter class.
    As converter class uses different framework, tha parameters can be different in each class.
    '''
    @abstractmethod
    def create_predictions_dict(self)-> dict:
        '''Creates the dictionary with model names as keys and their class predictions vectors as values.
            Value vectors should be pandas.Series type for binary and multiclass task types. 
        '''
        pass
    @abstractmethod 
    def create_proba_predictions_dict(self)-> dict:
        '''Creates the dictionary with model names as keys and their probabilistic predictions as values.
            Values should be a pandas.DataFrame type for binary and multiclass task types.
        '''
        pass

    @abstractmethod
    def create_feature_importance_dict(self)->dict:
        '''Creates the dictionary with model names as keys and the list of features sorted by the feature importance as values'''
        pass

    @abstractmethod
    def save_results(self,leaderboard: pd.DataFrame, predictions_dict :dict, proba_predictions_dict:dict, feature_importance_dict:dict, y_true:pd.DataFrame, saving_path : Path = None):
        '''Method for saving results returned by the convert() method in a specified or a default directory'''
        pass
    @abstractmethod
    def convert(self, saving_path:Path)->Tuple[pd.DataFrame, dict, dict, dict, pd.DataFrame]:
        '''Primary method performing all the necessary calculations and returning the converted objects.
            1. pd.DataFrame - leaderboard with all models and their scores 
            2. dict : predictions_dict
            3. dict : proba_predictions_dict
            4. dict : feature_importance_dict
            5. pd.DataFrame : y_true 
        '''
        pass







class PredictorConverter(Converter):
    '''
        Class for performing conversion of Autogluon Predictor object to : 

        1. leaderboard dataframe with all tested models and their evaluation scores, where eval_metric is the primarily minimized metric
        2. model - predictions dictionary containing all models and their prediction vectors (as Series)
        3. model -proba_predictions dictionary containing all models and their proba predictions (as pd.DataFrame)
        4. model - list disctionary containing lists of features sorted by their feature importace for each model
    '''

    MULTICLASS_METRICS = list(MULTICLASS_METRICS.keys())
    BINARY_METRICS = list(BINARY_METRICS.keys())
            
    def __init__(self, predictor : TabularPredictor, test_data : TabularDataset, df_name : str, feature_imp_needed = True):
        '''
            Initializes the converter with given TabularPredictor object and a test dataset, 
            all metrics are set based on the problem type of the predictor.

            Args:
                predictor : trained Autogluon predictor object
                test_data : test dataset for evaluation
                df_name : name of the dataset for saving purposes
                feature_imp_needed : boolean value indicating whether the calculation of feature importances is needed
        '''
        if not isinstance(predictor, TabularPredictor):
            raise TypeError(f'predictor argument must be a TabularPredictor object, got {type(predictor).__name__}')
        if not isinstance(test_data, (TabularDataset, pd.DataFrame)):
            raise TypeError(f'test_data argument must be a TabularDataset object, got {type(test_data).__name__}')
        if not isinstance(df_name, str):
            raise TypeError(f'df_name argument must be a string, got {type(df_name).__name__}')
        
        if not predictor.is_fit:
            raise ValueError("The predictor has not been trained. Call predictor.fit() first.")
        if len(test_data)==0:
            raise ValueError('Test dataset is empty. Please provide a valid test data.')
        if not df_name.strip():
            raise ValueError("df_name must be a non-empty string. Please provide a valid df_name.")
        
        self.predictor = predictor
        self.test_data = test_data
        self.df_name = df_name
        self.feature_imp_needed = feature_imp_needed
        
        if predictor.problem_type == 'binary':
            self.metrics = self.BINARY_METRICS
        elif predictor.problem_type == 'multiclass':
            self.metrics = self.MULTICLASS_METRICS
        else:
            raise ValueError("Unsupported problem type. Only 'binary' and 'multiclass' are supported.")
        self.leaderboard = self.create_leaderboard()


    def create_leaderboard(self)-> pd.DataFrame:
        '''
            Method for creating a leaderboard by dropping and renaming columns from a leaderboard returned by the Predictor.

            Returns:
                pd.DataFrame : cleaned leaderboard 
        '''
        leaderboard = self.predictor.leaderboard(self.test_data, extra_metrics=self.metrics)
        leaderboard = leaderboard.drop(columns= ['pred_time_test_marginal','pac','log_loss','mcc', 'quadratic_kappa','pred_time_val_marginal', 'fit_time_marginal', 'stack_level','can_infer', 'fit_order','score_val','score_test','pred_time_test','pred_time_val','fit_time'])
        return leaderboard
    
    def create_predictions_dict(self)-> dict:
        '''
            Method for saving predictions of each model in dictionary format

            Returns:
                dict : key - model name, value - predictions for model
        '''
        leaderboard = self.leaderboard

        predictions_dict ={}
        for model in leaderboard['model']:
            predictions = self.predictor.predict(self.test_data, model = model)
            predictions_dict[model] = predictions
        return predictions_dict
    
    def create_proba_predictions_dict(self)-> dict:
        '''
            Method for saving probability predictions of each model in dictionary format

            Returns:
                dict : key - model name, value - probability predictions for model

        '''
        leaderboard = self.leaderboard

        predictions_dict ={}
        for model in leaderboard['model']:
            predictions = self.predictor.predict_proba(self.test_data, model = model)
            predictions_dict[model] = predictions
        return predictions_dict
    
    def create_feature_importance_dict(self) -> dict:
        '''
            Method for obtaining feature importance for each model (where it's possible),
            then sorting features based on their importance and storing in a list format.

            Returns:
                dict: key - model name, value - list of sorted features by feature importance (descending order)
        '''
        leaderboard = self.leaderboard
        importance_dict = {}
        for model in leaderboard['model']:
            feature_importance_df = self.predictor.feature_importance(data = self.test_data, model = model).reset_index()
            features_sorted_list = feature_importance_df.sort_values('importance', ascending=False)['index'].tolist()
            importance_dict[model] = features_sorted_list
        return importance_dict
    
    def extract_target_column(self)-> pd.DataFrame:
        '''
            Method for extracting real y values from the test dataset.
        '''
        target_col = self.predictor.label
        y_test = self.test_data[[target_col]]
        return y_test

    def save_results(self,leaderboard: pd.DataFrame, predictions_dict :dict, proba_predictions_dict:dict, feature_importance_dict:dict, y_true:pd.DataFrame, saving_path : Path = None):
        '''
            Method used for saving .convert() method results on disk.
            If saving_path is None then saving_path by default is converter_results/autogluon/df_name 
        '''
        if saving_path is None:
            saving_path = RES_SAVING_DIR/"autogluon"/self.df_name
        saving_dir = Path(saving_path)
        saving_dir.mkdir(parents=True, exist_ok=True)

        leaderboard.to_csv(saving_dir/'leaderboard.csv', index=False)
        y_true.to_csv(saving_dir/'y_true.csv', index=False)

        with open(saving_dir/'predictions_dict.pkl', 'wb') as f:
            pickle.dump(predictions_dict, f)

        with open(saving_dir/'proba_predictions_dict.pkl', 'wb') as f:
            pickle.dump(proba_predictions_dict, f)

        if self.feature_imp_needed:
            with open(saving_dir/'feature_importance_dict.pkl', 'wb') as f:
                pickle.dump(feature_importance_dict, f)
        print(f'Autogluon conversion results saved to: {saving_dir.resolve()}')


    
    def convert(self, saving_path : Path = None) -> Tuple[pd.DataFrame, Dict, Dict, Dict, pd.DataFrame] :
        '''
            Primary method performing all necessary transformations and saving the results. 

            Args:
                saving_path : if saving_path is None then saving_path by default is converter_results/autogluon/df_name 

            Returns:
                pd.DataFrame : leaderboard created in create_leaderboard() method
                dict : predictions dict created in create_predictions_dict() method
                dict: proba_predictions dict created in create_proba_predictions_dict() method
                dict : feature importance dict created in create_feature_importance_dict() method 
        '''
        leaderboard = self.create_leaderboard()
        predictions_dict = self.create_predictions_dict()
        proba_predictions_dict = self.create_proba_predictions_dict()
        y_true = self.extract_target_column()
        if self.feature_imp_needed:
            feature_importance_dict = self.create_feature_importance_dict()
        else:
            feature_importance_dict = None

        self.save_results(leaderboard, predictions_dict, proba_predictions_dict, feature_importance_dict, y_true, saving_path)
        return leaderboard, predictions_dict, proba_predictions_dict, feature_importance_dict, y_true

        

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

class H2O_Converter(Converter):
    '''
        Class for converting H2OAutoML trained models into :
        
        1. leaderboard dataframe with all tested models and their evaluation scores calculated based on the task type (binary or multiclass)
        2. model - predictions dictionary containing all models and their prediction vectors (np.ndarray)
        3. model -proba_predictions dictionary containing all models and their proba predictions (as pd.DataFrame)
        4. model - list disctionary containing lists of features sorted by their feature importace for each model
    '''
    
    MULTICLASS_METRICS_DICT={ 
        'accuracy' : accuracy_score,
        'balanced_accuracy' : balanced_accuracy_score,
        'precision_macro': lambda y_true, y_pred : precision_score(y_true, y_pred, average='macro'),
        'precision_micro' : lambda y_true, y_pred : precision_score(y_true, y_pred, average='micro'),
        'precision_weighted' : lambda y_true, y_pred : precision_score(y_true, y_pred, average='weighted'),
        'recall_macro':lambda y_true, y_pred : recall_score(y_true, y_pred, average='macro'), 
        'recall_micro':lambda y_true, y_pred : recall_score(y_true, y_pred, average='micro'), 
        'recall_weighted':lambda y_true, y_pred : recall_score(y_true, y_pred, average='weighted'),
        'f1_macro': lambda y_true, y_pred : f1_score(y_true, y_pred, average='macro'),
        'f1_micro':lambda y_true, y_pred : f1_score(y_true, y_pred, average='micro'),
        'f1_weighted':lambda y_true, y_pred : f1_score(y_true, y_pred, average='weighted'),
        'roc_auc_ovo':lambda y_true, y_pred, labels : roc_auc_score(y_true, y_pred, multi_class='ovo', labels=labels),
        'roc_auc_ovo_weighted':lambda y_true, y_pred, labels : roc_auc_score(y_true, y_pred, multi_class='ovo', average='weighted',labels=labels),
        'roc_auc_ovr':lambda y_true, y_pred, labels : roc_auc_score(y_true, y_pred, multi_class='ovr',labels=labels),
        'roc_auc_ovr_micro':lambda y_true, y_pred, labels: roc_auc_score(y_true, y_pred, multi_class='ovr', average='micro',labels=labels),
        'roc_auc_ovr_weighted': lambda y_true, y_pred , labels: roc_auc_score(y_true, y_pred, multi_class='ovr', average='weighted',labels=labels)}
    
    BINARY_METRICS_DICT = {
            'accuracy' : accuracy_score,
            'balanced_accuracy' : balanced_accuracy_score,
            'roc_auc' : roc_auc_score,
            'average_precision': lambda y_true,y_pred : average_precision_score(y_true, y_pred, pos_label="1"),
            'precision': lambda y_true,y_pred : precision_score(y_true, y_pred, pos_label="1", zero_division=0), 
            'precision_macro': lambda y_true, y_pred : precision_score(y_true, y_pred, average='macro'),
            'precision_micro' : lambda y_true, y_pred : precision_score(y_true, y_pred, average='micro'),
            'precision_weighted' : lambda y_true, y_pred : precision_score(y_true, y_pred, average='weighted'),
            'recall': lambda y_true,y_pred :recall_score(y_true, y_pred,pos_label="1" ),
            'recall_macro':lambda y_true, y_pred : recall_score(y_true, y_pred, average='macro'), 
            'recall_micro':lambda y_true, y_pred : recall_score(y_true, y_pred, average='micro'), 
            'recall_weighted':lambda y_true, y_pred : recall_score(y_true, y_pred, average='weighted'),
            'f1':  lambda y_true, y_pred : f1_score(y_true, y_pred, pos_label="1"),
            'f1_macro': lambda y_true, y_pred : f1_score(y_true, y_pred, average='macro'),
            'f1_micro':lambda y_true, y_pred : f1_score(y_true, y_pred, average='micro'),
            'f1_weighted':lambda y_true, y_pred : f1_score(y_true, y_pred, average='weighted')}
    
    

    def __init__(self, models_directory : Path, test_data : h2o.H2OFrame, target_column : str, df_name:str, feature_imp_needed = True):
        '''
            Initializes the converter with a given path to a directory containing all trained H2O models and a test dataset, 
            all metrics are set based on the problem type calculated from target column.

            Args:
                models_directory : path to a directory with trained H2O models for a given dataset
                test_data : test dataset for evaluation
                target_column : name of the target column. Used to determine task type.
                df_name : name of the dataset for saving purposes
                feature_imp_needed : boolean value indicating whether the calculation of feature importances is needed
        '''

        if h2o.cluster() is None or not h2o.cluster().is_running():
            h2o.init()

        if not isinstance(models_directory, Path):
            raise TypeError(f'models_directory must be a pathlib.Path object, got {type(models_directory).__name__}')
        if not models_directory.exists():
            raise FileNotFoundError(f'models_directory path does not exist: {models_directory}')
        if not any(models_directory.iterdir()):
            raise ValueError(f'models_directory is empty: {models_directory}')

       
        if not isinstance(test_data, h2o.H2OFrame):
            raise TypeError(f'test_data must be an h2o.H2OFrame object, got {type(test_data).__name__}')
        if test_data.nrow == 0:
            raise ValueError('test_data H2OFrame is empty')

    
        if not isinstance(target_column, str):
            raise TypeError(f'target_column must be a string, got {type(target_column).__name__}')
        if target_column.strip() == "":
            raise ValueError('target_column cannot be empty or whitespace')
        if target_column not in test_data.col_names:
            raise ValueError(f'target_column "{target_column}" not found in test_data columns: {test_data.col_names}')

     
        if not isinstance(df_name, str):
            raise TypeError(f'df_name must be a string, got {type(df_name).__name__}')
        if df_name.strip() == "":
            raise ValueError('df_name cannot be empty or whitespace')

        self.models_directory = models_directory
        self.test_data = test_data
        self.target_column = target_column
        self.df_name = df_name
        self.feature_imp_needed = feature_imp_needed
        self.task_type = self.determine_task_type()

        self.loaded_models = self.load_all_models()
        self.prediction_frames_dict = self.get_prediction_frames()

        self.class_prediction_dict = self.create_predictions_dict()
        self.proba_predictions_dict = self.create_proba_predictions_dict()
        self.classes = sorted(self.test_data[self.target_column].as_data_frame().iloc[:,0].unique().astype(str))

    def determine_task_type(self)->str:
        '''
            Method to establish task type based on the given target column.

            Returns:
                str : task type 'binary' or 'multiclass'
        '''
        target_column_type = self.test_data.types[self.target_column]
        if target_column_type =='enum':
            num_classes = self.test_data[self.target_column].nlevels()[0]
            if num_classes == 2:
                return 'binary'
            elif num_classes>2:
                return 'multiclass'
            else:
                raise ValueError('Less than 2 classes detected in test dataset.')
        else:
            raise ValueError('Task types other than classification are not supported.')
        
        
    def load_all_models(self)->list:
        '''
            Method for loading all models objects saved in models_directory into a list format

            Returns:
                list : List of H2O model objects loaded from the `models_directory`.
        '''
        loaded_models=[]
        for model_file in self.models_directory.iterdir():
            if model_file.is_file():  
                model = h2o.load_model(str(model_file))
                loaded_models.append(model)
        return loaded_models
    
    def get_prediction_frames(self)->dict:
        '''
            Method for accessing every models prediction H2O result and storing results in a model - Frame

            Returns:
                dict : key - model_id , value - predictions Frame
        '''
        predictions = {}
        for model in self.loaded_models:
            predictions_df = model.predict(self.test_data)
            model_id = model.model_id
            predictions[model_id] = predictions_df
        return predictions

    
    def create_predictions_dict(self)->dict:
        '''
            Method for accessing every models prediction vector and storing results in a model - vector dictionary format

            Returns:
                dict : key - model_id , value - predictions vector (ndarray)
        '''
        class_predictions_dict ={}
        for model_id, frame in self.prediction_frames_dict.items():
            predictions_df = frame
            class_predictions = predictions_df['predict'].as_data_frame().iloc[:,0]
            class_predictions_dict[model_id] = class_predictions
        return class_predictions_dict
    
    def create_proba_predictions_dict(self)->Tuple[dict, list]:
        '''
            Method for accessing every models proba predictions  and storing results in a model - prediction matrix dictionary format

            Returns:
                dict : key - model_id , value - predictions matrix (n samples, n classes) pd.DataFrame
        '''
        proba_predictions_dict ={}
        for model_id, frame in self.prediction_frames_dict.items():
            predictions_df = frame
            proba_columns = [col for col in predictions_df.columns if col != 'predict']
            proba_df = predictions_df[proba_columns].as_data_frame()
            if self.task_type =='binary':
                proba_df.columns = [str(i) for i in range(len(proba_columns))] #0-1 column names
                classes = [str(i) for i in range(len(proba_columns))]
            else:
                classes = proba_columns
            
            proba_predictions_dict[model_id] = proba_df
          
        return proba_predictions_dict
    
    def create_feature_importance_dict(self)->dict:
        '''
            Method for obtaining feature importance (for models where it's possible) and sorting features based on their importance.

            Returns:
                dict : key - model_id, value - sorted list of features or None for models where feature importance can't be obtained
        '''
        importance_dict ={}
        for model in self.loaded_models:
            try:
                importance_df = model.varimp(use_pandas=True)
                sorted_variables = importance_df.sort_values('scaled_importance', ascending=False)['variable'].tolist()
                importance_dict[model.model_id] = sorted_variables
            except (AttributeError, NotImplementedError):
                print(f'Model {model.model_id} does not have .varimp(). None inserted.')
                importance_dict[model.model_id] = None
        return importance_dict
    
    def extract_target_column(self)->pd.DataFrame:
        test_data_df = self.test_data.as_data_frame()
        y_true = test_data_df[[self.target_column]]
        return y_true

    
    def calculate_multiclass_metrics(self) -> pd.DataFrame:
        '''
            Method for calculating all evaluation metrics for multiclass task type for each model. 

            Returns:
                pd.DataFrame : DataFrame with models as rows and columns as their evaluation metrics
        '''
        
        y_true_raw = self.test_data[self.target_column].as_data_frame().iloc[:,0].to_numpy()

        encoder = LabelEncoder()
        encoder.fit(self.classes)
        y_true_encoded = encoder.transform(y_true_raw)

        rows=[]
        for model_id in self.class_prediction_dict.keys():
            row = {'model': model_id}
            y_pred_class = self.class_prediction_dict[model_id]
            y_pred_encoded_class = encoder.transform(y_pred_class)
            y_pred_proba = self.proba_predictions_dict[model_id].to_numpy()

            for metric_name, metric_func in self.MULTICLASS_METRICS_DICT.items():
                try:
                    #roc auc base on probabilities 
                    if metric_name.startswith('roc_auc'):
                        row[metric_name] = metric_func(y_true_encoded, y_pred_proba, labels = range(len(self.classes)))
                    else: #other metrics based on class predictions (encoded by LabelEncoder just in case)
                        row[metric_name] = metric_func(y_true_encoded, y_pred_encoded_class)
                except Exception as e:
                    row[metric_name] = None
                    print(f'Error with {metric_name} : {e}')
            rows.append(row)
        metrics_df = pd.DataFrame(rows)
        return metrics_df
    
    def calculate_binary_metrics(self)->pd.DataFrame:
        '''
            Method for calculating all evaluation metrics for binary classification task type for each model. 

            Returns:
                pd.DataFrame : DataFrame with models as rows and columns as their evaluation metrics
        '''
        y_true_raw = self.test_data[self.target_column].as_data_frame().iloc[:,0]
        y_true = y_true_raw.astype(str).to_numpy() # classes '0' and '1'

        rows=[]
        for model_id in self.class_prediction_dict.keys():
            row = {'model': model_id}

            y_class_pred = self.class_prediction_dict[model_id].astype(str) 
            y_pred_proba = self.proba_predictions_dict[model_id].to_numpy()

            for metric_name, metric_func in self.BINARY_METRICS_DICT.items():
                try:
                    
                    #roc auc and avg precision need positive class probability:
                    if metric_name =='roc_auc' or metric_name=='average_precision':
                        row[metric_name] = metric_func(y_true, y_pred_proba[:,1])
                    else:
                        row[metric_name] = metric_func(y_true, y_class_pred)

                except Exception as e:
                    row[metric_name] = None
                    print(f'Error with metric: {metric_name} : {e}')
            rows.append(row)
        metrics_df = pd.DataFrame(rows)
        return metrics_df
    
    def save_results(self,leaderboard: pd.DataFrame, predictions_dict :dict, proba_predictions_dict:dict, feature_importance_dict:dict, y_true: pd.DataFrame, saving_path : Path = None):
        '''
            Method used for saving .convert() results on disk.
            If saving_path is None then saving_path by default is converter_results/h2o/df_name 
        '''
        if saving_path is None:
            saving_path  = RES_SAVING_DIR/"h2o"/self.df_name
        saving_dir = Path(saving_path)
        saving_dir.mkdir(parents=True, exist_ok=True)

        leaderboard.to_csv(saving_dir/'leaderboard.csv', index=False)
        y_true.to_csv(saving_dir/'y_true.csv', index=False)

        with open(saving_dir/'predictions_dict.pkl', 'wb') as f:
            pickle.dump(predictions_dict, f)

        with open(saving_dir/'proba_predictions_dict.pkl', 'wb') as f:
            pickle.dump(proba_predictions_dict, f)
        
        if self.feature_imp_needed:
            with open(saving_dir/'feature_importance_dict.pkl', 'wb') as f:
                pickle.dump(feature_importance_dict, f)
        print(f'H2O conversion results saved to: {saving_dir.resolve()}')
    

    def convert(self, saving_path : Path = None) -> Tuple[pd.DataFrame, dict, dict, dict, pd.DataFrame]:
        '''
            Primary method used to perform all calculations. 

            Args:
                saving_path : if saving_path is None then saving_path by default is converter_results/h2o/df_name 

            Returns:
                pd.DataFrame : leaderboard obtained by calculating evaluation metrics for the given task type 
                dict : predictions dict returned by get_class_predictions_dict() method
                dict : proba_predictions dict returned by get_proba_predictions_dict() method
                dict : feature importance dict returned by get_feature_importance_dict() method
        '''
        if self.task_type == 'binary':
            leaderboard = self.calculate_binary_metrics()
        else:
            leaderboard = self.calculate_multiclass_metrics()
        if self.feature_imp_needed:
            importance_dict = self.create_feature_importance_dict()
        else:
            importance_dict = None
        y_true = self.extract_target_column()

        self.save_results(leaderboard, self.class_prediction_dict, self.proba_predictions_dict, importance_dict,y_true, saving_path)
        
        return leaderboard, self.class_prediction_dict, self.proba_predictions_dict, importance_dict, y_true
