import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import MaxNLocator
import seaborn as sns
import warnings

from .rashomon_set import *

class RashomonIntersection(RashomonSet):
    '''
        Class for calculating Rashomon set intersection for multiple Rashomon sets based on different metrics.
        Inherits from RashomonSet class.
    '''

    def __init__(self, leaderboard : pd.DataFrame, predictions : dict, proba_predictions : dict, feature_importances : dict,  metrics : list, epsilon: float,  custom_weights : list =None, weighted_sum_method : str = 'entropy'):
        '''
            Initializes RashomonSetIntersection with two Rashomon sets.

            Args:
                leaderboard : dataframe with all trained model names and their test scores (returned by Converter)
                predictions : dictionary with model + prediction vector (returned by Converter)
                proba_predictions : dictonary with model + proba predictions vector (returned by Converter)
                feature_importances : dictionary with model + sorted feature names by their feature importance (returned by Converter)
                metrics : list of metrics to be used in the intersection calculation
                epsilon : epsilon value informing how the test scores can differ in order for models to be included in rashomon set 
                custom_weights : if weighted_sum is 'custom_weights' then user must specify weights in 2-element list.
                weighted_sum_method : Specifies the weighted sum method for selecting the base model. Options are:
                    - None or 'entropy' (default): Uses entropy-based method to select the base model.
                    - 'critic': Uses critic-based method to select the base model.
                    - 'custom_weights' : Uses the user specified weights to select the base model.
                
        '''

        #metrics validation
        if not isinstance(metrics, list):
            raise TypeError(f"'metrics' must be a list, got {type(metrics).__name__} instead.")
        if len(metrics)!=2:
            raise ValueError('This class calculates intersection for 2 given metrics. Please pass on a list of metrics with the correct length.')
        if metrics[0] not in self.METRICS:
            raise ValueError(f"Metric '{metrics[0]}' is not supported. Supported metrics are: {self.METRICS}")
        if metrics[1] not in self.METRICS:
            raise ValueError(f"Metric '{metrics[1]}' is not supported. Supported metrics are: {self.METRICS}")
        if metrics[0] == metrics[1]:
            raise ValueError('Metrics should be different.')
        
        #leaderboard validation -> not empty, pd.DataFrame type, must contain columns 'model' and metrics, metrics columns cannot contain NaN values
        if not isinstance(leaderboard, pd.DataFrame):
            raise(TypeError(f'leaderboard must be a pandas DataFrame, got {type(leaderboard)} instead.'))
        if leaderboard.empty:
            raise(ValueError('leaderboard is empty, cannot create RashomonSet object.'))
        if 'model' not in leaderboard.columns:
            raise(ValueError("leaderboard DataFrame must contain 'model' column with model names."))
        if metrics[0] not in leaderboard.columns:
            raise ValueError(f"leaderboard DataFrame must contain {metrics[0]} column.")
        if metrics[1] not in leaderboard.columns:
            raise ValueError(f"leaderboard DataFrame must contain {metrics[1]} column.")
        if leaderboard[metrics[0]].isna().any():
            raise ValueError(f"leaderboard DataFrame must contain valid metric values in {metrics[0]} column, not NaN.")
        if leaderboard[metrics[1]].isna().any():
            raise ValueError(f"leaderboard DataFrame must contain valid metric values in {metrics[1]} column, not NaN.")
        
        #predictions validation -> not empty dictionary with keys being model names, and values being predictions
        if not isinstance(predictions, dict):
            raise(TypeError(f'predictions must be a dictionary, got {type(predictions).__name__} instead.'))
        #predictions dictionary cannot be empty
        if not predictions:
            raise(ValueError('predictions dictionary is empty, cannot create RashomonSetIntersection object.'))
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
            raise(ValueError('proba_predictions dictionary is empty, cannot create RashomonSetIntersection object.'))
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
                raise(ValueError('feature_importances dictionary is empty, cannot create RashomonSetIntersection object.'))
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
                
        self.metrics = metrics
        self.custom_weights = custom_weights #user paramter value saved 
        self.weighted_sum_method = weighted_sum_method #user paramter value saved 
        self.leaderboard = leaderboard
        self.predictions_dict = predictions
        self.proba_predictions_dict = proba_predictions
        self.feature_importance_dict = feature_importances

        self.base_metric = None #not defined in Rashomon Intersection
        self.worst_score = None #not defined in Rashomon Intersection
        self.best_score = None #not defined in Rashomon Intersection

        if not isinstance(epsilon, float):
            raise(TypeError('epsilon must be a float value.'))
        if epsilon<0:
            raise(ValueError('epsilon must be non-negative float value.'))
        self.epsilon = epsilon

        self.all_rashomon_sets = {metric: self.get_rashomon_set_for_metric(metric) for metric in metrics}
        self.rashomon_set = self.find_rashomon_intersection()
        if len(self.rashomon_set)<=1:
            raise ValueError(f'For given base metrics : {self.metrics} and epsilon value = {self.epsilon}, the Rashomon Intersection consists of {len(self.rashomon_set)} models. Please provide valid epsilon and base metrics.')
        
        self.rashomon_predictions, self.rashomon_proba_predictions = self.get_rashomon_predictions()
        if feature_importances is not None:
            self.rashomon_feature_importance = self.get_rashomon_feature_importances()
        else:
            self.rashomon_feature_importance = None
        self.number_of_classes = self.determine_number_of_classes()
        self.task_type = self.determine_task_type()

        #base_model based on weighted sum method, by default entropy method
        if weighted_sum_method=='entropy':
            if custom_weights is not None:
                raise ValueError(f"For 'entropy' weighted_sum_method, 'custom_weights' must be None. Received: {custom_weights}")
            self.base_model = self.find_base_model_entropy_based()
            self.weights = self.find_weights_entropy_based()
        elif weighted_sum_method =='critic':
            if custom_weights is not None:
                raise ValueError(f"For 'critic' weighted_sum_method, 'custom_weights' must be None. Received: {custom_weights}")
            self.base_model = self.find_base_model_critic_based()
            self.weights = self.find_weights_critic_method()
        elif weighted_sum_method=='custom_weights':
            if custom_weights is None:
                raise ValueError("Custom weights method requires 'custom_weights' argument, got None.")
            if not isinstance(custom_weights, list):
                raise TypeError(f"'custom_weights' must be list, got {type(custom_weights).__name__}.")
            if len(custom_weights) != 2:
                raise ValueError(f"'custom_weights' must have exactly 2 elements, got {len(custom_weights)}.")
            if not np.isclose(sum(custom_weights), 1.0, atol=1e-4):
                raise ValueError(f"The sum of 'custom_weights' must be 1.0, got {sum(custom_weights)}.")
            self.base_model = self.find_base_model(custom_weights[0], custom_weights[1])
            self.weights = pd.Series(custom_weights)
        else:
            raise ValueError(f'Unknown weighted sum method :  {weighted_sum_method}. Try custom_weights, entropy or critic')
        

    def get_rashomon_set_for_metric(self, metric: str, epsilon : float = None) -> list:
        '''
            Method for getting Rashomon Set for a given metric.

            Args:
                metric : metric for which Rashomon Set is to be calculated

            Returns:
                list : List of models that are in Rashomon Set for the given metric
        '''

        if metric not in self.METRICS:
            raise ValueError(f"Metric '{metric}' is not supported. Supported metrics are: {self.METRICS}")
        if epsilon is None:
            epsilon = self.epsilon
       
        if self.METRICS_GREATER_IS_BETTER.get(metric):
            best_metric_value = self.leaderboard[metric].max()
            rashomon_models = self.leaderboard[self.leaderboard[metric] >= best_metric_value - epsilon]
        else:
            best_metric_value = self.leaderboard[metric].min()
            rashomon_models = self.leaderboard[self.leaderboard[metric] <= best_metric_value + epsilon]

        rashomon_models_names = rashomon_models['model']

        return rashomon_models_names
    

    def find_rashomon_intersection(self, epsilon :float = None) -> list:
        '''
            Method for calculating intersection of Rashomon Sets based on the models from Rashomon Sets chosen for each test metric.

            Returns:
                list : List of model names that are in intersection of Rashomon Sets
        '''
        if epsilon is None:
            epsilon = self.epsilon

        rashomon_sets = [self.get_rashomon_set_for_metric(metric, epsilon) for metric in self.metrics]
        if not rashomon_sets:
            return []
        else:
            return list(set.intersection(*map(set, rashomon_sets)))
        

    def get_rashomon_set(self, epsilon : float = None) -> list:
        '''
            Method for finding all models that are included in the Rashomon Intersection. 

            Returns:
                list : List of model names that are in the Rashomon Intersection
        '''

        if epsilon is None:
            epsilon = self.epsilon

        rashomon_intersection = self.find_rashomon_intersection(epsilon)
        return rashomon_intersection
        
    def get_rashomon_predictions(self)-> Tuple[Dict,Dict]:
        '''
            Override method to use intersection models, not single metric models.
        '''

        rashomon_predictions = {model: self.predictions_dict[model] for model in self.rashomon_set}
        rashomon_proba_predictions = {model: self.proba_predictions_dict[model] for model in self.rashomon_set}
        return rashomon_predictions, rashomon_proba_predictions
    
    def get_rashomon_feature_importances(self):
        '''
            Override method to use intersection models, not single metric models.
        '''
        rashomon_importances = {model : self.feature_importance_dict[model] for model in self.rashomon_set}
        return rashomon_importances
        
    
    def find_base_model(self, weight1, weight2) -> str:
        '''
            Method for finding base_model based on user passed weight values. 

            Returns:
                str : Model name that maximizes the sum : weight1*metrics[0] + weight2*metrics[1].
                      If many models have the same sum value, base model is the first one in the leaderboard.
        '''

        if not np.isclose(weight1+weight2, 1, atol=1e-6) or weight1<0 or weight2<0:
            raise ValueError('Passed weights should be >= 0 and sum to 1')
        
        rashomon_leaderboard_subset = self.leaderboard[self.leaderboard['model'].isin(self.rashomon_set)].copy()
        rashomon_leaderboard_subset['weighted_sum'] = weight1 * rashomon_leaderboard_subset[self.metrics[0]] + weight2* rashomon_leaderboard_subset[self.metrics[1]]
        best_row = rashomon_leaderboard_subset.loc[rashomon_leaderboard_subset['weighted_sum'].idxmax()]
        best_model = best_row['model']
        return best_model
    
    def find_worst_model(self) -> str:
        '''
            Method for finding worst_model based on user passed weight values. 

            Returns:
                str : Model name that minimizes the sum : weight1*metrics[0] + weight2*metrics[1].
                      If many models have the same sum value, base model is the first one in the leaderboard.
        '''
        weight1 = self.weights.iloc[0]
        weight2 = self.weights.iloc[1]

        if not np.isclose(weight1+weight2, 1, atol=1e-6) or weight1<0 or weight2<0:
            raise ValueError('Passed weights should be >= 0 and sum to 1')
        
        rashomon_leaderboard_subset = self.leaderboard[self.leaderboard['model'].isin(self.rashomon_set)].copy()
        rashomon_leaderboard_subset['weighted_sum'] = weight1 * rashomon_leaderboard_subset[self.metrics[0]] + weight2* rashomon_leaderboard_subset[self.metrics[1]]
        worst_row = rashomon_leaderboard_subset.loc[rashomon_leaderboard_subset['weighted_sum'].idxmin()]
        worst_model = worst_row['model']
        return worst_model
    
    def find_same_score_as_base(self) -> Tuple[int, list]:
        '''
            Method for finding how many models from the leaderboard have the same value weighted sum of two passed metrics.

            Returns:
                Tuple[int, list]:
                - Number of models (excluding base_model)
                - List of model names (excluding base_model)
        '''
        weight1 = self.weights.iloc[0]
        weight2 = self.weights.iloc[1]

        if not np.isclose(weight1 + weight2, 1, atol=1e-6):
            raise ValueError("Weights must sum to 1.")

        leaderboard_subset = self.leaderboard[self.leaderboard['model'].isin(self.rashomon_set)].copy()
        leaderboard_subset['weighted_score'] = (weight1 * leaderboard_subset[self.metrics[0]] + weight2 * leaderboard_subset[self.metrics[1]])
        base_model_score = leaderboard_subset.loc[leaderboard_subset['model'] == self.base_model, 'weighted_score'].values[0]

        same_score_rows = leaderboard_subset[leaderboard_subset['weighted_score'] == base_model_score]
        same_score_rows = same_score_rows[same_score_rows['model'] != self.base_model]
        same_scores_count = same_score_rows.shape[0]
        same_scores_models = same_score_rows['model'].tolist()
        
        return same_scores_count, same_scores_models

    
    def find_weights_entropy_based(self) -> pd.Series:
        '''
            Method for finding weights based on the entropy method.

            Returns:
                pd.Series : weights with index as metric names and values as weights.
        '''

        leaderboard_subset = self.leaderboard[['model'] + self.metrics]
        leaderboard_subset = leaderboard_subset[leaderboard_subset['model'].isin(self.rashomon_set)] #only models from rashomon set (intersection)

        #step1: scaling 
        leaderboard_subset[self.metrics] = leaderboard_subset[self.metrics].apply(lambda x: x / x.sum())
        #step 2: calculating entropy for each column as -h * sum(rij *ln(rij)) where h = 1/ln(numer_of_models) and rij is a scaled cell value
        h = -1 / np.log(len(leaderboard_subset))
        leaderboard_subset[self.metrics] = leaderboard_subset[self.metrics].apply(lambda x: x * np.log(x + 1e-9)) # rij * ln(rij) 
        entropy_values = leaderboard_subset[self.metrics].sum() * h 

        # step 3: calculate weights for each column as wj = (1-ej)/sum(1-ej)
        denominator = (1-entropy_values).sum()
        weights = (1-entropy_values)/denominator
        if not np.isclose(weights.sum(), 1.0, atol=1e-6):
            raise ValueError(f'Weights do not add up to 1!: {weights}')
        
        return weights
    
    def find_base_model_entropy_based(self) -> str:
        '''
            Method for finding base_model based on entropy method.

            Returns:
                str : Model name that maximizes the sum : weight1*metrics[0] + weight2*metrics[1].
                      If many models have the same sum value, base model is the first one in the leaderboard.
        '''

        weights_series = self.find_weights_entropy_based()
        weights = weights_series.loc[self.metrics]
        best_model = self.find_base_model(weights.iloc[0], weights.iloc[1])

        return best_model
    
    def find_weights_critic_method(self) -> pd.Series:
        '''
            Method for finding weights based on the CRITIC method.
            Falls back to entropy method if CRITIC fails for any reason.

            Returns:
                str : weights with index as metric names and values as weights.
        '''

        try:
            leaderboard_subset = self.leaderboard[['model'] + self.metrics]
            leaderboard_subset = leaderboard_subset[leaderboard_subset['model'].isin(self.rashomon_set)] #only models from rashomon set (intersection)

            if len(leaderboard_subset) < 2:
                raise ValueError(f"Insufficient number of models ({len(leaderboard_subset)}) in Rashomon set. At least 2 models are required.")

            #step1: min-max normalization -> all metrics are in [0,1] range
            leaderboard_subset[self.metrics] = leaderboard_subset[self.metrics].apply(
                lambda x: (x - x.min()) / (x.max() - x.min()) if x.max() > x.min() else 0)
            
            #if all values in both columns are the same, correlation matrix cannot be calculated (there is no variation) therefore CRITIC metric cannot be applied 
            if (leaderboard_subset[self.metrics].nunique() == 1).any():
                raise ValueError(f"One or more metrics have identical values across all models: {leaderboard_subset[self.metrics].nunique()}.")
            else:
                #step 2: computing pearson correlation matrix for all metrics
                correlation_matrix = leaderboard_subset[self.metrics].corr(method='pearson')
                if correlation_matrix.isna().any().any():
                    raise ValueError("Correlation matrix contains NaN values, likely due to zero or near-zero variation in metrics.")
                
                #step 3: computing standard deviation for each metric
                standard_deviations = leaderboard_subset[self.metrics].std(ddof=0)
                if (standard_deviations == 0).any():
                    raise ValueError(f"One or more metrics have zero standard deviation: {standard_deviations}.")
                
                #step 4: calculating weights as cj = sj * sum(1 - correlation_matrix_ij) where sj is standard deviation for metric j and correlation_matrix_ij is correlation between metric j and other metrics
                c_values = standard_deviations * (1-correlation_matrix).sum(axis=1)
                weights = c_values / c_values.sum()

                if not np.isclose(weights.sum(), 1.0, atol=1e-6):
                    raise ValueError(f'Weights do not add up to 1!: {weights}')
        
            return weights
        except Exception as e:
            warnings.warn(f"CRITIC method not applicable to this task: {e}. Falling back to default: entropy method.")
            return self.find_weights_entropy_based()

    
    def find_base_model_critic_based(self) -> str:
        '''
            Method for finding base_model based on CRITIC method.

            Returns:
                str : Model name that maximizes the sum : weight1*metrics[0] + weight2*metrics[1].
                      If many models have the same sum value, base model is the first one in the leaderboard.
        '''

        weights_series = self.find_weights_critic_method()
        weights = weights_series.loc[self.metrics]
        best_model = self.find_base_model(weights.iloc[0], weights.iloc[1])

        return best_model
    

    def get_rashomon_metrics(self, delta: float = 0.1) -> Dict[str, float]:
        '''
            Method for getting all Rashomon Intersection metrics in a dictionary format.

            Args:
                delta : threshold for probabilistic ambiguity and discrepancy

            Returns:
                Dict[str, float] : Dictionary with Rashomon Intersection metrics where keys are metric names.
        '''
        capacity_values = [self.rashomon_capacity(i) for i in range(self.determine_number_of_samples())]

        metrics = {
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
            Method for printing all calculated metrics for Rashomon Intersection.
        '''
        
        metrics = self.get_rashomon_metrics(delta=delta)

        print(f"\n=== Rashomon Intersection Set Summary ===\n")
        print(f"Selected metrics: {self.metrics[0]}, {self.metrics[1]}")
        print(f"Determined task type is: {metrics['Task Type']}")
        print(f"Number of classes: {metrics['Number of classes']}")
        print(f"Computed weights: {self.weights.iloc[0]}, {self.weights.iloc[1]}")
        print(f"The size of Rashomon set for given epsilon is: {metrics['Rashomon Set Size']}.")

        print(f'Base model for given metrics ({self.metrics[0]}, {self.metrics[1]}) is {self.base_model}.')
        #number of models with the same score as the base model
        print(f'There were {self.find_same_score_as_base()[0]} other models found with the same weighted sum of metrics as base model. These models are: {self.find_same_score_as_base()[1]}')

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
        print("Agreement percents for all models in the Rashomon Intersection: \n")
        for key, value in metrics['Percent agreement dict'].items():
            print(f"{key} : {value:.2f}\n")

        # Rashomon Capacity
        print(f"Mean Rashomon Capacity: {metrics['Mean Rashomon Capacity']:.2f}")
        print(f"Min Rashomon Capacity: {metrics['Min Rashomon Capacity']:.2f}")
        print(f"Max Rashomon Capacity: {metrics['Max Rashomon Capacity']:.2f}")
        print(f"Std Rashomon Capacity: {metrics['Std Rashomon Capacity']:.2f}")
    