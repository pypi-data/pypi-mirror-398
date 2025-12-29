import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import MaxNLocator
from typing import Tuple, Dict
import seaborn as sns
import warnings

class RashomonSet:
    '''
        Class representing all models that are included in the Rashomon set for a given Epsilon value and related metrics.
         

        Attributes:
            leaderboard : parameter
            predictions : parameter
            proba_predictions : parameter
            feature_importances : parameter
            base_metric : parameter
            epsilon : parameter

            base_model : name of the model with the best test score (base_meric)
            best_score : best value of base-metric achieved across all models
            worst_score : worst value of base-metric achieved across all models
            rashomon_set : list of model names that are included in the Rashomon set for given epsilon
            rashomon_predictions : subset of predictions only for models in Rashomon Set
            rashomon_proba_predictions : subset of proba_predictions only for models in Rashomon Set
            number of classes : calculated number of classes 
            task type : determined task type (binary or multiclass)
    '''

    #possible metrics for classification from autogluon.tabular
    #documentation: https://github.com/autogluon/autogluon/blob/master/tabular/src/autogluon/tabular/predictor/predictor.py
    #https://scikit-learn.org/stable/api/sklearn.metrics.html

    METRICS = ['accuracy', 'balanced_accuracy', 'f1', 'f1_macro', 'f1_micro', 'f1_weighted',
            'roc_auc', 'roc_auc_ovo', 'roc_auc_ovo_macro', 'roc_auc_ovo_weighted', 'roc_auc_ovr', 
            'roc_auc_ovr_macro', 'roc_auc_ovr_micro', 'roc_auc_ovr_weighted', 'average_precision', 
            'precision', 'precision_macro', 'precision_micro', 'precision_weighted', 'recall', 
            'recall_macro', 'recall_micro', 'recall_weighted']
    
    METRICS_GREATER_IS_BETTER = {
        'accuracy': True,
        'balanced_accuracy': True,
        'f1': True,
        'f1_macro': True,
        'f1_micro': True,
        'f1_weighted': True,
        'roc_auc': True,
        'roc_auc_ovo': True,
        'roc_auc_ovo_macro': True,
        'roc_auc_ovo_weighted': True,
        'roc_auc_ovr': True,
        'roc_auc_ovr_macro': True,
        'roc_auc_ovr_micro': True,
        'roc_auc_ovr_weighted': True,
        'average_precision': True,
        'precision': True,
        'precision_macro': True,
        'precision_micro': True,
        'precision_weighted': True,
        'recall': True,
        'recall_macro': True,
        'recall_micro': True,
        'recall_weighted': True,
    }

    def __init__(self, leaderboard : pd.DataFrame, 
                 predictions : dict, proba_predictions : dict, feature_importances : dict, base_metric:str, epsilon:float):
        '''
            Initializes RashomonSet with given parameters and calulates basic metrics. 

            Args:
                leaderboard : dataframe with all trained model names and their test scores (returned by Converter)
                predictions : dictionary with model + prediction vector (pd.Series) (returned by Converter)
                proba_predictions : dictonary with model + proba predictions vector)pd.DataFrame) (returned by Converter)
                feature_importances : dictionary with model + sorted feature names by their feature importance (returned by Converter)
                base_metric : test metric for rashomon set analysis 
                epsilon : epsilon value informing how the test scores can differ in order for models to be included in rashomon set
        '''
        

        #leaderboard validation -> not empty pd.DataFrame, with model column and base_metric
        if not isinstance(leaderboard, pd.DataFrame):
            raise(TypeError(f'leaderboard must be a pandas DataFrame, got {type(leaderboard)} instead.'))
        if leaderboard.empty:
            raise(ValueError('leaderboard is empty, cannot create RashomonSet object.'))
        if 'model' not in leaderboard.columns:
            raise(ValueError("leaderboard DataFrame must contain 'model' column with model names."))
        
        #base metric validation
        if base_metric not in self.METRICS:
            raise ValueError(f"Base metric '{base_metric}' is not supported. Supported metrics are: {self.METRICS}. Please choose a valid base metric.")
        if base_metric not in leaderboard.columns:
            raise(ValueError(f"Base metric '{base_metric}' not found in leaderboard columns. Please ensure the leaderboard contains the specified base metric. If there is a mismatch in metric naming, please correct it so it matches metric name in METRICS list."))
        if leaderboard[base_metric].isna().any():
            raise ValueError(f"leaderboard DataFrame must contain valid metric values in {base_metric} column, not NaN.")
        
        #predictions validation
        if not isinstance(predictions, dict):
            raise(TypeError(f'predictions must be a dictionary, got {type(predictions).__name__} instead.'))
        #predictions dictionary cannot be empty
        if not predictions:
            raise(ValueError('predictions dictionary is empty, cannot create RashomonSet object.'))
        #all values in predictions dict must be pandas Series and cannot be empty
        for model, preds in predictions.items():
            if not isinstance(preds, pd.Series):
                raise TypeError(f"Predictions for model '{model}' must be a pandas Series, not {type(preds).__name__}.")
            if preds.empty:
                raise ValueError(f"Predictions for model '{model}' are empty.")
        #all keys in predictions dict must match model names in leaderboard
        missing_in_leaderboard = set(predictions.keys()) - set(leaderboard['model'])
        missing_in_predictions = set(leaderboard['model']) - set(predictions.keys())
        if missing_in_leaderboard:
            raise ValueError(f"The following models in predictions dict are not found in leaderboard: {missing_in_leaderboard}")
        if missing_in_predictions:
            raise ValueError(f"The following models in leaderboard are not found in predictions dict: {missing_in_predictions}")
        
        #proba predictions validation
        if not isinstance(proba_predictions, dict):
            raise(TypeError(f'proba_predictions must be a dictionary, got {type(proba_predictions).__name__} instead.'))
         #proba predictions dictionary cannot be empty
        if not proba_predictions:
            raise(ValueError('proba_predictions dictionary is empty, cannot create RashomonSet object.'))
        #all values in proba predictions dict must be pandas DataFrame and cannot be empty
        for model, preds in proba_predictions.items():
            if not isinstance(preds, pd.DataFrame):
                raise TypeError(f"Proba predictions for model '{model}' must be a pandas DataFrame, not {type(preds).__name__}.")
            if preds.empty:
                raise ValueError(f"Proba predictions for model '{model}' are empty.")
        
        #all keys in proba predictions dict must match model names in leaderboard
        missing_in_leaderboard_proba = set(proba_predictions.keys()) - set(leaderboard['model'])
        missing_in_proba_predictions = set(leaderboard['model']) - set(proba_predictions.keys())
        if missing_in_leaderboard_proba:
            raise ValueError(f"The following models in proba predictions dict are not found in leaderboard: {missing_in_leaderboard_proba}")
        if missing_in_proba_predictions:
            raise ValueError(f"The following models in leaderboard are not found in proba predictions dict: {missing_in_proba_predictions}")

        #feature importances validation
        if feature_importances is not None:
            if not isinstance(feature_importances, dict):
                raise(TypeError(f'feature_importances must be a dictionary, got {type(feature_importances).__name__} instead.'))
            #feature importances dictionary cannot be empty
            if not feature_importances:
                raise(ValueError('feature_importances dictionary is empty, cannot create RashomonSet object.'))
            #some models do not produce feature importances, so we warn the user insted of raising an error
            #for keys in feature importances dict that are not in leaderboard, we warn that these models will be ignored
            missing_in_leaderboard_fi = set(feature_importances.keys()) - set(leaderboard['model'])
            missing_in_fi = set(leaderboard['model']) - set(feature_importances.keys())
            if missing_in_leaderboard_fi:
                warnings.warn(
                    f"The following models in feature_importances dict are not found in leaderboard "
                    f"(they will be ignored): {missing_in_leaderboard_fi}")
            if missing_in_fi:
                warnings.warn(
                    f"The following models from leaderboard are missing in feature_importances dict "
                    f"(possibly because these models do not provide feature importances): {missing_in_fi}")

        if not isinstance(epsilon, float):
            raise(TypeError('epsilon must be a float value.'))
        if epsilon<0:
            raise(ValueError('epsilon must be non-negative float value.'))

        self.leaderboard = leaderboard
        self.predictions_dict = predictions
        self.proba_predictions_dict = proba_predictions
        self.feature_importance_dict = feature_importances
        self.base_metric = base_metric
        self.epsilon = epsilon

        self.base_model = self.find_base_model()
        if self.base_metric not in self.METRICS:
            raise ValueError(f"Base metric '{self.base_metric}' is not supported. Supported metrics are: {self.METRICS}")
        if self.METRICS_GREATER_IS_BETTER.get(self.base_metric):
            self.best_score = self.leaderboard[self.base_metric].max()
            self.worst_score = self.leaderboard[self.base_metric].min()
        else:
            self.best_score = self.leaderboard[self.base_metric].min()
            self.worst_score = self.leaderboard[self.base_metric].max()

        self.rashomon_set = self.get_rashomon_set()
        if len(self.rashomon_set)<=1:
            raise ValueError(f'For a given base metric : {self.base_metric} and epsilon value = {self.epsilon}, the Rashomon Set consists of {len(self.rashomon_set)} models. Please provide valid epsilon and base metric.')
        self.rashomon_predictions, self.rashomon_proba_predictions = self.get_rashomon_predictions()
        if feature_importances is not None:
            self.rashomon_feature_importance = self.get_rashomon_feature_importances()
        else:
            self.rashomon_feature_importance = None
        self.number_of_classes = self.determine_number_of_classes()
        self.task_type = self.determine_task_type()
   

    def determine_task_type(self) -> str:
        '''
            Method for assigning task type based on predictions vector.

            Returns
                str : task type 'binary' or 'multiclass'    
        '''
        all_labels = set()
        for preds in self.predictions_dict.values():
            all_labels.update(preds)
        if len(all_labels)==2:
            return 'binary'
        elif len(all_labels)>2:
            return 'multiclass'
        else:
            raise ValueError(f"Can't determine task type. Number of unique labels is : {len(all_labels)}")
        
        
    def determine_number_of_classes(self) -> int:
        '''
            Method for determining number of classes in the task based on predictions vector.

            Returns:
                int : Number of classes
        '''
        sample_predictions = next(iter(self.rashomon_predictions.values())) #sample predictions vec
        unique_labels = set(sample_predictions)
        return len(unique_labels)
    
    
    def determine_number_of_samples(self) -> int:
        '''
            Method for determining number of samples in the task based on predictions vector.

            Returns:
                int : Number of samples
        '''
        sample_predictions = next(iter(self.rashomon_predictions.values()))
        return len(sample_predictions)
    

    def find_base_model(self) -> str:
        '''
            Method for finding the name of the model with the best score (base_metric)
            Returns:
                str : Name of the model with the best score
        '''
        if self.METRICS_GREATER_IS_BETTER.get(self.base_metric):
            best_score_row = self.leaderboard.loc[self.leaderboard[self.base_metric].idxmax()]
        else:
            best_score_row = self.leaderboard.loc[self.leaderboard[self.base_metric].idxmin()]
        name = best_score_row['model']
        return name
    
    
    def find_worst_model(self) -> str:
        '''
            Method for finding the name of the model with the worst score (base_metric)
            Returns:
                str : Name of the model with the worst score
        '''
        if self.METRICS_GREATER_IS_BETTER.get(self.base_metric):
            worst_score_row = self.leaderboard.loc[self.leaderboard[self.base_metric].idxmin()]
        else:
            worst_score_row = self.leaderboard.loc[self.leaderboard[self.base_metric].idxmax()]
        name = worst_score_row['model']
        return name
    
    
    def find_same_score_as_base(self) -> Tuple[int, list]:
        '''
            Method for finding how many models from the leaderboard have the same value of base_metric

            Returns:
                Tuple[int, list]
                - int : Number of models (excluding base_model)
                - list: List of model names (excluding base_model)
        '''
        base_model_score = self.leaderboard.loc[self.leaderboard['model'] == self.base_model, self.base_metric].values[0]
        same_score_rows = self.leaderboard[self.leaderboard[self.base_metric] == base_model_score]
        same_score_rows = same_score_rows[same_score_rows['model']!= self.base_model] #exclude base model
        same_scores_count = same_score_rows.shape[0]
        same_scores_models = same_score_rows['model'].tolist()
        return same_scores_count, same_scores_models
    
    
    def get_rashomon_set(self, epsilon : float = None) -> list:
        '''
            Method for finding all models that are included in the Rashomon Set. 
            All models that achieved base_metric value not worse that epsilon from the best model.
            
            Returns:
                list : List of model names present in the Rashomon Set.
        '''
        if epsilon is None:
            epsilon = self.epsilon
       
        best_metric_value = self.leaderboard.loc[self.leaderboard['model'] == self.base_model, self.base_metric].values[0]

        if self.METRICS_GREATER_IS_BETTER.get(self.base_metric):
            rashomon_models = self.leaderboard[self.leaderboard[self.base_metric] >= best_metric_value - epsilon]
        else:
            rashomon_models = self.leaderboard[self.leaderboard[self.base_metric] <= best_metric_value + epsilon]
        rashomon_models_names = rashomon_models['model']
        return rashomon_models_names
    
    
    def get_rashomon_predictions(self) -> Tuple[Dict, Dict]:
        '''
            Method for selecting sub - dictionary from predictions_dict that contains only models from Rashomon Set.

            Returns:
                Tuple[Dict, Dict]:
                - rashomon predictions: Dictionary where keys are model names from the Rashomon Set and values are their predictions.
                - rashomon_proba_predictions: Dictionary where keys are model names from the Rashomon Set and values are their probability predictions.

        '''
        rashomon_models = self.get_rashomon_set()
        rashomon_predictions = {model: self.predictions_dict[model] for model in rashomon_models}
        rashomon_proba_predictions = {model: self.proba_predictions_dict[model] for model in rashomon_models}
        return rashomon_predictions, rashomon_proba_predictions
    
    def get_rashomon_feature_importances(self)-> dict:
        '''
            Method for selecting sub - dictionary from feature_importance_dict that contains only models from the Rashomon Set.

            Returns:
                dict : Dictionary where keys are model names from the Rashomon Set and values are the corresponding feature importances.

        '''
        rashomon_models = self.rashomon_set
        rashomon_importances = {model : self.feature_importance_dict[model] for model in rashomon_models}
        return rashomon_importances


    def binary_ambiguity(self) -> float:
        '''
            Calculates binary ambiguity of a rashomon set by counting all observations where at least one model made a different prediction than base model H0. 

            Returns:
                float : Fraction of observations that are ambigous.  
        '''

        if self.task_type != 'binary':
            raise ValueError("binary_ambiguity method is only applicable for binary classification tasks.")

        
        h0_predictions = self.rashomon_predictions[self.base_model]
        n = len(h0_predictions)

        differences_mask = np.array([False] * n) 
        for model,predictions in self.rashomon_predictions.items():
            if model == self.base_model:
                continue #skip h0 in comparison
            comparison = predictions!= h0_predictions #returns vector of [True False False ...] with True where rows have diff predictions
            differences_mask = differences_mask | comparison.values #update mask 
        
        num_differences = differences_mask.sum()
        return num_differences/n
    
    def multiclass_ambiguity(self)->float:
        '''
            Calculates ambiguity for multiclass target by counting all observations where at least one model made a different prediction than base model h0.
            
            Returns:
                float : Fraction of observations that are ambigous.
        '''

        if self.task_type != 'multiclass':
            raise ValueError("multiclass_ambiguity method is only applicable for multiclass classification tasks.")

        
        h0_proba_predictions = self.rashomon_proba_predictions[self.base_model]
        h0_class_predictions = h0_proba_predictions.values.argmax(axis=1)
        n = len(h0_class_predictions)
        
        difference_mask = np.array([False]*n)
        for model,probas in self.rashomon_proba_predictions.items():
            if model==self.base_model:
                continue
            model_class_prediction = probas.values.argmax(axis=1) #class predicted by model h_i
            comparison = model_class_prediction != h0_class_predictions
            difference_mask = difference_mask | comparison
        num_diffrerences = difference_mask.sum()
        return num_diffrerences/n

    

    def probabilistic_abiguity(self, delta: float)-> float:
        '''
            Calculates binary ambiguity for probabilistic risk estimation by comparing the positive class (Target Class Label = 1)  probability calculated by each model against the base model. 
            If the max absolute difference is greater than delta, observation is ambigous.

            Returns:
                float : Fraction of observations that are ambigous.

        '''

        if self.task_type != 'binary':
            raise ValueError("probabilistic_abiguity method is only applicable for binary classification tasks.")
        
        if delta<0 or delta>1:
            raise ValueError('delta parameter must be in range [0,1].')

        h0_predictions = self.rashomon_proba_predictions[self.base_model].iloc[:,1].values  #only positive class prediction
        n = len(h0_predictions)

        proba_matrix =[]
        for model, predictions in self.rashomon_proba_predictions.items():
            if model==self.base_model:
                continue
            proba_matrix.append(predictions.iloc[:,1].values)
        proba_array = np.vstack(proba_matrix) #matrix row = model, columns : P(class=1) values for each observation
        h0_differences = np.abs(proba_array - h0_predictions)
        max_diff_per_observation = np.max(h0_differences, axis=0) #max difference from h0 predictions for all observations
        ambigous_count = np.sum(max_diff_per_observation>=delta)
        return ambigous_count/n
    
    
    def binary_discrepancy(self)->float:
        '''
            Calculates discrepancy for binary target task by counting how many predictions are different between base and refererence model. 
            Then choses the max sum of different predictions across all models from Rashomon Set.

            Returns:
                float : Max differences fraction.
        '''

        if self.task_type != 'binary':
            raise ValueError("binary_discrepancy method is only applicable for binary classification tasks.")
        
        h0_pred = self.rashomon_predictions[self.base_model]
        n = len(h0_pred)
        max_differences = 0
        for model,predictions in self.rashomon_predictions.items():
            if model == self.base_model:
                continue
            differences = np.sum(pred1!=pred2 for pred1, pred2 in zip(h0_pred, predictions))
            differences_frac = differences/n
            max_differences = max(max_differences, differences_frac)
        return max_differences
    
    def multiclass_discrepancy(self)->float:
        '''
            Calculates discrepancy for multiclass target task by counting how many predictions are different between base and competing models. 
            Then choses the max sum of different predictions across all models from Rashomon Set.

            Returns:
                float : Max differences fraction
        '''

        if self.task_type != 'multiclass':
            raise ValueError("multiclass_discrepancy method is only applicable for multiclass classification tasks.")

        h0_predictions = self.rashomon_proba_predictions[self.base_model].values.argmax(axis=1)
        n = len(h0_predictions)
        max_differences = 0.0
        for model, probas in self.rashomon_proba_predictions.items():
            if model == self.base_model:
                continue
            h_predictions = probas.values.argmax(axis=1)
            differences = np.sum(h0_predictions != h_predictions)
            differences_frac = differences/n
            max_differences = max(max_differences, differences_frac)
        return max_differences
    
    
    def probabilistic_discrepancy(self, delta: float) -> float:
        '''
            Calculates binary discrepancy for probabiblistic predictions that is counted for each prediction that differs from the base model by more than 'delta'. 

            Returns:
              float : The max fraction across all models.
        '''

        if self.task_type != 'binary':
            raise ValueError("probabilistic_discrepancy method is only applicable for binary classification tasks.")
        
        if delta<0 or delta>1:
            raise ValueError('delta parameter must be in range [0,1].')

        h0_risk_pred = self.rashomon_proba_predictions[self.base_model].iloc[:,1].values
        n = len(h0_risk_pred)
        max_differences = 0
        for model, predictions_proba in self.rashomon_proba_predictions.items():
            if model == self.base_model:
                continue
            risk_prediction = predictions_proba.iloc[:,1].values
            difference_mask = abs(h0_risk_pred - risk_prediction) > delta
            diff_frac = difference_mask.sum()/n
            max_differences = max(max_differences, diff_frac)
        return max_differences
    
    def viable_prediction_range(self)-> list[tuple[float,float]]:
        '''
            Calculates the Viable Predicion Range (VPR) for each sample as the [min risk estimate, max risk estimate] predicted by all models in a Rashomon Set.
            Used for binary classification tasks.

            Returns:
                list[tuple[float,float]]:
                - list of Viable Prediction Ranges of all samples in (min,max) format.
        '''

        if self.task_type != 'binary':
            raise ValueError("viable_prediction_range method is only applicable for binary classification tasks.")

        all_models_risk_estimates = [df.iloc[:,1].values for df in self.rashomon_proba_predictions.values()]
        all_probabilities_matrix = np.vstack(all_models_risk_estimates) #rows = models, columns = samples risk estimates
        vpr_min = all_probabilities_matrix.min(axis=0)
        vpr_max = all_probabilities_matrix.max(axis=0)
        vprs = list(zip(vpr_min, vpr_max))
        return vprs
    
    def agreement_rate(self)->list:
        '''
            For every observation x_i returns the percent of models from the Rashomon Set, which made the same prediction as the base model.

            Returns: 
                list : agreement rate for every observation 

        '''
        predictions_df = pd.DataFrame(self.rashomon_predictions)
        predictions_df['agreement_count'] = (predictions_df.drop(columns = [self.base_model]).values == predictions_df[self.base_model].values[:,None] ).sum(axis=1)
        predictions_df['agreement_rate'] = predictions_df['agreement_count']/ (len(self.rashomon_set)-1) #base model is not counted so that if all models agree the rate can be 100%

        return predictions_df['agreement_rate'].tolist()
    
    def percent_agreement(self)-> dict:
        '''
            For every model in the Rashomon Set returns the percent of observations where the model and the base model made the same prediction. 

            Returns:
                dict : Model name as key and percent agreement with the base model as value

        '''
        predictions_df = pd.DataFrame(self.rashomon_predictions)
        percent_agreements = {}
        for model in predictions_df.columns:
            # if model == self.base_model:
            #     continue
            agreement_percent = (predictions_df[model] == predictions_df[self.base_model]).mean() *100 
            percent_agreements[model] = agreement_percent
        
        return percent_agreements

    
    def rashomon_ratio(self) -> float:
        '''
            Calculates Rashomon ratio which is Ratio of Rashomon Set size to the total number of models in the leaderboard. 

            Returns:
                float : Fraction of models in the hypothesis space that fit the data about equally well.
        '''

        if len(self.leaderboard) == 0:
            raise ValueError("Leaderboard is empty, cannot calculate Rashomon ratio.")
        
        rashomon_ratio = len(self.rashomon_set) / len(self.leaderboard)
        return rashomon_ratio
    
    
    def get_patterns_rashomon_set(self) -> set:
        '''
            Method to retrive all unique prediction patterns from the Rashomon Set, representing the collection of predictions produced by each model in the set.

            Returns:
                set : Set of patterns present in the Rashomon Set.
        '''

        patterns = set()
        for model, predictions in self.rashomon_predictions.items():
            patterns.add(tuple(predictions.values)) #predictions.values is pandas Series, converting to tuple

        return patterns
    
    
    def get_patterns_hypothesis_set(self) -> set:
        '''
            Method to retrive all unique prediction patterns from models present in the leaderboard (our hypothesis space).

            Returns:
                set : Set of patterns present in the hypothesis space.
        '''

        patterns = set()
        for model, predictions in self.predictions_dict.items():
            patterns.add(tuple(predictions.values))

        return patterns
    
    
    def pattern_rashomon_ratio(self) -> float:
        '''
            Method for calculating Pattern Rashomon Ratio, defined as ratio of the number of unique prediction patterns in the Rashomon Set to the total number of unique predictions patterns in the hypothesis space (leaderboard).

            Returns:
                float : Pattern Rashomon Ratio
        '''

        patterns_rashomon_set = self.get_patterns_rashomon_set()
        patterns_hypothesis_set = self.get_patterns_hypothesis_set()

        if len(patterns_hypothesis_set) == 0:
            raise ValueError("Hypothesis set patterns are empty, cannot calculate Pattern Rashomon ratio.")

        pattern_rashomon_ratio = len(patterns_rashomon_set) / len(patterns_hypothesis_set)
        return pattern_rashomon_ratio
    
    
    def rashomon_capacity(self, sample_index : int) -> float:
        '''
            Method for calculating Rashomon capacity for a given sample.

            Args:
                sample_index : index of the sample for which Rashomon capacity is to be calculated

            Returns:
                float : Rashomon capacity value for the given sample.
        '''

        if sample_index < 0 or sample_index >= self.determine_number_of_samples():
            raise ValueError(f"Sample index {sample_index} is out of bounds. Must be between 0 and {self.determine_number_of_samples() - 1}.")

        transition_matrix = self.generate_transition_matrix(sample_index=sample_index)

        if transition_matrix.size == 0:
            raise ValueError(f"Transition matrix is empty for sample index {sample_index}.")
        if np.any(transition_matrix<0) or np.any(transition_matrix>1):
            raise ValueError("Transition matrix contains invalid probabilities (must be in [0,1]).")
        
        channel_capacity = self.blahut_arimoto_algorithm(transition_matrix)
        rashomon_capacity = 2**channel_capacity
        return rashomon_capacity


    def generate_transition_matrix(self, sample_index) -> np.ndarray:
        '''
            Method for generating transition matrix for a given sample.
            Transition matrix (m, c), where m corresponds to the number of models included in the set, while c denotes the number of classes associated with the prediction task.

            Args:
                sample_index : index of the sample for which transition matrix is to be calculated.

            Returns:

                np.ndarray : Transition matrix for a given sample.
        '''

        models = list(self.rashomon_proba_predictions.keys())
        class_names = self.rashomon_proba_predictions[models[0]].columns

        m, c = len(models), len(class_names)
        transition_matrix = np.zeros((m,c))
        for i, model in enumerate(models):
            proba_df = self.rashomon_proba_predictions[model]
            if sample_index not in proba_df.index:
                raise ValueError(f"Sample index {sample_index} not found in proba_predictions for model '{model}'.")
            transition_matrix[i, :] = proba_df.loc[sample_index].values
        return transition_matrix
    
    
    def blahut_arimoto_algorithm(self, transition_matrix, max_iterations = 1000, tolerance = 1e-8) -> float:
        '''
            Method for comupting channel capacity for a given sample.

                Args: 
                    transition_matrix: matrix with m rows (models from Rashomon set) and c columns (number of classes for specified task).
                                       the columns of the transition matrix represent the class probability distributions predicted by each model for every class.
                    max_iterations: maximum number of algorithm iterations.
                    tolerance: error tolerance for algorithm to stop iterations.

                Returns:
                    float : Channel capacity value for the given sample - max over p(x) I(X,Y).
        '''
        m, c = transition_matrix.shape[0], transition_matrix.shape[1]
   
        #starting with uniform p_0(x) distribution, where x is models 'alphabet'
        p_x = np.ones((m)) / m
        eps = 1e-12
      
        for i in range(max_iterations):
            #q_t(y) = sum_x p(x) * p(y|x)
            q_t = p_x @ transition_matrix  # shape: (c,)
            #D_t(x) = sum_y p(y|x) * log(p(y|x) / q_t(y))
            D_t = np.sum(transition_matrix * np.log((transition_matrix + eps)/ (q_t+eps)), axis=1)  # shape: (m,), + eps to avoid log0
            #updating input distribution: p_t(x) = e^{D_t} / sum(e^{D_t})
            p_t = np.exp(D_t)
            p_t /= np.sum(p_t)

            #checking the convergance
            #max absolute difference between iterations
            error = np.max(np.abs(p_t - p_x))
            if error<tolerance:
                p_x = p_t
                break
            p_x = p_t

        #channel capacity = sum_x p(x) * p(y|x) * log (p(y|x)/p(y)) = sum_x p(x) * D_t(x)
        channel_capacity = np.sum(p_x * D_t) / np.log(2)
        return channel_capacity
    
    def cohens_kappa(self) -> dict:
        '''
            Method for calculating Cohen's Kappa metric for every model in the Rashomon Set relative to the base model.

            Returns:
                dict : {model_name: kappa_value}
        '''

        cohens_kappa_dict = {}
        percent_agreements = self.percent_agreement()
        predictions_df = pd.DataFrame(self.rashomon_predictions)
        base_model_predictions = predictions_df[self.base_model]
        n = len(base_model_predictions)

        for model in predictions_df.columns:
            if model == self.base_model:
                cohens_kappa_dict[model] = 1.0
                continue

            p_o = percent_agreements[model] / 100
            model_predictions = predictions_df[model]

            crosstab = pd.crosstab(base_model_predictions, model_predictions)
            base_model_marginals = crosstab.sum(axis=1)/n
            model_marginals = crosstab.sum(axis=0)/n

            labels = set(base_model_marginals.index) & set(model_marginals.index)
            p_e = sum(base_model_marginals[label]*model_marginals[label] for label in labels)
    
            kappa = (p_o - p_e) / (1 - p_e) if p_e != 1 else 1.0
            cohens_kappa_dict[model] = kappa

        return cohens_kappa_dict
    
    def cohens_kappa_matrix(self) -> pd.DataFrame:
        '''
            Method for calculating the Cohen's Kappa metric for every pair of models in the Rashomon Set.

            Returns:
                pd.DataFrame : A symmetric matrix where the entry at [i, j] represents the Cohen's Kappa score between model i and model j. 
                               Diagonal entries are 1.0, representing a model compared with itself.
        '''
        predictions_df = pd.DataFrame(self.rashomon_predictions)
        models = predictions_df.columns
        kappa_matrix = pd.DataFrame(index=models, columns=models, dtype=float)
        n = len(predictions_df)

        for i, model_i in enumerate(models):
            for j in range(i, len(models)):
                model_i, model_j = models[i], models[j]

                p_o = (predictions_df[model_i] == predictions_df[model_j]).mean()
                crosstab = pd.crosstab(predictions_df[model_i], predictions_df[model_j])
                marginals_i = crosstab.sum(axis=1)/n
                marginals_j = crosstab.sum(axis=0)/n
                labels = set(marginals_i.index) & set(marginals_j.index)
                p_e = sum(marginals_i[label] * marginals_j[label] for label in labels)

                kappa = (p_o - p_e) / (1 - p_e) if p_e != 1 else 1.0
                kappa_matrix.loc[model_i, model_j], kappa_matrix.loc[model_j, model_i] = kappa, kappa

        return kappa_matrix


    def get_rashomon_metrics(self, delta: float = 0.1) -> Dict[str, float]:
        '''
            Method for getting all Rashomon metrics in a dictionary format.

            Args:
                delta : threshold for probabilistic ambiguity and discrepancy

            Returns:
                Dict[str, float] : Dictionary with Rashomon metrics where keys are metric names.
        '''

        capacity_values = [self.rashomon_capacity(i) for i in range(self.determine_number_of_samples())]

        metrics = {
            'Base Model': self.base_model,
            'Rashomon Set Size': len(self.rashomon_set),
            'Task Type': self.determine_task_type(),
            'Number of classes': self.determine_number_of_classes(),
            'Rashomon Ratio': self.rashomon_ratio(),
            'Pattern Rashomon Ratio': self.pattern_rashomon_ratio(),
            'Ambiguity': self.binary_ambiguity() if self.determine_task_type() == 'binary' else self.multiclass_ambiguity(),
            'Discrepancy': self.binary_discrepancy() if self.determine_task_type() == 'binary' else self.multiclass_discrepancy(),
            'Probabilistic Ambiguity': self.probabilistic_abiguity(delta) if self.determine_task_type() == 'binary' else None,
            'Probabilistic Discrepancy': self.probabilistic_discrepancy(delta) if self.determine_task_type() == 'binary' else None,
            'VPRs' : self.viable_prediction_range() if self.determine_task_type() =='binary' else None,
            'Agreement rates list': self.agreement_rate(),
            'Percent agreement dict': self.percent_agreement(),
            'Mean Rashomon Capacity': np.mean(capacity_values),
            'Min Rashomon Capacity': np.min(capacity_values),
            'Max Rashomon Capacity': np.max(capacity_values),
            'Std Rashomon Capacity': np.std(capacity_values)
        }
        return metrics
        

    def summarize_rashomon(self, delta: float = 0.1):
        '''
            Method for printing all calculated metrics.
        '''
    
        metrics = self.get_rashomon_metrics(delta=delta)

        print(f"\n=== Rashomon Set Summary ===\n")
        print(f"Base Metric: {self.base_metric}")
        print(f"Determined task type is: {metrics['Task Type']}")
        print(f"Number of classes: {metrics['Number of classes']}")
        print(f"The size of Rashomon set for given epsilon is: {metrics['Rashomon Set Size']}.")

        print(f'Base model for given base metric ({self.base_metric}) is {self.base_model}.')
        #number of models with the same score as the base model
        print(f'There were {self.find_same_score_as_base()[0]} other models found with the same {self.base_metric} as base model. These models are: {self.find_same_score_as_base()[1]}')

        #worst and best values of base_metric
        print(f'Best value for metric = {self.base_metric} is {self.best_score:.2f} for {self.base_model} model (base model).')
        print(f'Worst value for metric = {self.base_metric} is {self.worst_score:.2f} for {self.find_worst_model()} model.')

        #Rashomon Ratios
        print(f'Rashomon Ratio metric value is {self.rashomon_ratio():.2f}')
        print(f'Pattern Rashomon Ratio metric value is {self.pattern_rashomon_ratio():.2f}')

        if metrics['Task Type'] == 'binary':
            print(f"Binary Ambiguity: {metrics['Ambiguity']:.2f}")
            print(f"Binary Discrepancy: {metrics['Discrepancy']:.2f}")
            print(f"Probabilistic Ambiguity (delta={delta}): {metrics['Probabilistic Ambiguity']:.2f}")
            print(f"Probabilistic Discrepancy (delta={delta}): {metrics['Probabilistic Discrepancy']:.2f}")
            #print(f"Viable Prediction Range (VPRs): {metrics['VPRs']}")
        else:
            print(f"Multiclass Ambiguity: {metrics['Ambiguity']:.2f}")
            print(f"Multiclass Discrepancy: {metrics['Discrepancy']:.2f}")

        # Agreement rates
        print(f"\nMax agreement rate: {np.max(metrics['Agreement rates list'])}")
        print(f"\nMin agreement rate: {np.min(metrics['Agreement rates list'])}")
        print(f"\nStd agreement rate: {np.std(metrics['Agreement rates list'])}")
        print("\n")
        print("Agreement percents for all models in the Rashomon Set: \n")
        for key, value in metrics['Percent agreement dict'].items():
            print(f"{key} : {value:.2f}\n")

        # Rashomon Capacity
        print(f"Mean Rashomon Capacity: {metrics['Mean Rashomon Capacity']:.2f}")
        print(f"Min Rashomon Capacity: {metrics['Min Rashomon Capacity']:.2f}")
        print(f"Max Rashomon Capacity: {metrics['Max Rashomon Capacity']:.2f}")
        print(f"Std Rashomon Capacity: {metrics['Std Rashomon Capacity']:.2f}")


    def plot_predictions_probabilities(self, sample_index : int = 0):
        '''
            Method for plotting predicted probabilities for a given sample across all models in the Rashomon set.
            
            Args:
                sample_index : index of the sample for which predictions are to be plotted
        '''
 
        if sample_index < 0 or sample_index >= self.determine_number_of_samples():
            raise ValueError(f"Sample index {sample_index} is out of bounds. Must be between 0 and {self.determine_number_of_samples() - 1}.")
        
        labels = self.rashomon_proba_predictions[next(iter(self.rashomon_proba_predictions))].columns.tolist()
        colors = sns.color_palette("Set2", n_colors=len(labels))

        sample_predictions = {model: predictions.loc[sample_index].values for model, predictions in self.rashomon_proba_predictions.items()}
        sample_predictions_df = pd.DataFrame(sample_predictions).T # no need for normalization, plotting probabilities

        sample_predictions_df.reset_index(inplace=True)
        sample_predictions_df.columns = ['Model'] + labels

        plt.figure(figsize = (10,6))
        plt.grid(axis = 'y', linestyle = '--', alpha = 0.7)
        plt.grid(axis = 'x', linestyle = '--', alpha = 0.7)

        left = np.zeros(len(sample_predictions_df))
        for i, label in enumerate(labels):
            plt.barh(y = sample_predictions_df['Model'], width = sample_predictions_df[label].values, left = left, label = label, color = colors[i], alpha = 0.8)
            left += sample_predictions_df[label].values

        plt.ylabel('Models')
        plt.xlabel('Predicted probabilities')
        plt.title(f'Predicted probabilities for sample {sample_index} across all models in Rashomon set')
        plt.legend(title = 'Classes', loc = 'lower center', ncol = len(labels), bbox_to_anchor=(0.5, -0.25))
        plt.show()
