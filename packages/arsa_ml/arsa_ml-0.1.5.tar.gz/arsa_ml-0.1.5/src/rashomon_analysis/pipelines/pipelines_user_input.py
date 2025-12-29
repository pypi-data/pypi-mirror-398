from datetime import datetime
import pandas as pd
import h2o
from h2o.frame import H2OFrame
import random
import inspect 
import os
import sys
import importlib.resources as pkg_resources
import subprocess
import time
import psutil
from pathlib import Path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from rashomon_analysis.rashomon_set import *
from rashomon_analysis.rashomon_intersection import *
from rashomon_analysis.visualizers.rashomon_visualizer import *
from rashomon_analysis.visualizers.intersection_visualizer import *
from app.rashomon_binary_app import *
from rashomon_analysis.converters import *
from rashomon_analysis.pipelines.builder_abstract import *
import pickle
import warnings
warnings.filterwarnings("ignore")
import logging
BLUE_BOLD = "\033[1;34m"
RESET = "\033[0m"

logging.basicConfig(
    level=logging.INFO,
    format=f"{BLUE_BOLD}%(message)s{RESET}"
)

PROJECT_ROOT = Path(__file__).resolve().parents[3] #pipelines -> rahsomon_analysis ->src -> root
# RASHOMON_BINARY_APP_PATH = PROJECT_ROOT/"src"/"app"/"rashomon_binary_app.py"
# RASHOMON_MULTICLASS_APP_PATH = PROJECT_ROOT/"src"/"app"/"rashomon_multiclass_app.py"
# INTERSECTION_BINARY_APP_PATH = PROJECT_ROOT/"src"/"app"/"intersection_binary_app.py"
# INTERSECTION_MULTICLASS_APP_PATH = PROJECT_ROOT/"src"/"app"/"intersection_multiclass_app.py"

INTERSECTION_BINARY_APP_PATH = Path(pkg_resources.files("app") / "intersection_binary_app.py")
INTERSECTION_MULTICLASS_APP_PATH = Path(pkg_resources.files("app") / "intersection_multiclass_app.py")
RASHOMON_BINARY_APP_PATH = Path(pkg_resources.files("app") / "rashomon_binary_app.py")
RASHOMON_MULTICLASS_APP_PATH = Path(pkg_resources.files("app") / "rashomon_multiclass_app.py")


PIPELINES_DIR = Path(__file__).resolve().parent
TMP_DIR = PIPELINES_DIR / "tmp"
TMP_DIR.mkdir(exist_ok=True)  



class BuildRashomonH2O(Builder):
    '''
        Pipeline for creating and exploring the Rashomon Set from user-provided models from H2O framework. 
    '''

    def __init__(self, models_directory: Path, test_data : h2o.H2OFrame, target_column : str, df_name : str, 
                 base_metric : str, delta : float = 0.1, feature_imp_needed = True,  converter_results_directory : Path = None):
        '''
            Initializes the Pipeline user's input (models traines with H2O framework) to the creation of the Rashomon Set and it's visualizations.

            Args:
                models_directory : path to a folder where all models saved from H2O output are stored.
                test_data : test dataset for evaluation
                target_column : name of the target column. Used to determine task type.
                df_name : name of the dataset for saving converter output purposes.
                base_metric : evaluation metric to be used while creating the Rashomon Set
                delta : delta parameter for probabilistic ambiguity and discrepancy (used only for binary task type). If not specified the default value of 0.1 will be used.
                feature_imp_needed : boolean value indicating whether the calculation of feature importances is needed.
                converter_results_directory : Path to directory where converter outputs will be stored.
                                              If None -> creates 'converter_results/<df_name>_<timestamp>' next to models_directory.
        '''

        #All __init__ parameter validation is done in other modules, so it’s not necessary to duplicate it here.
        logging.info("Converting H2O models to Rashomon Analysis format...")
        if converter_results_directory is None:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            converter_results_directory = models_directory.parent/'converter_results'/f"{df_name}_{timestamp}"
        logging.info(f"Converter results will be stored in: {converter_results_directory}")
        logging.info("Please wait...")
        logging.info("This process may take several minutes depending on the number of models and dataset size.")
        logging.info("If you wish to speed up the process, consider setting feature_imp_needed=False.")
        h2o_converter = H2O_Converter(models_directory, test_data, target_column, df_name, feature_imp_needed)
        self.leaderboard, self.predictions, self.proba_predictions, self.feature_importances, self.y_true = h2o_converter.convert(saving_path = converter_results_directory)
        self.base_metric = base_metric
        self.delta = delta
        self.epsilon = None
        logging.info("Conversion completed.")
        logging.info("You can preview the Rashomon Set size plot using preview_rashomon() method to determine epsilon parameter value.")

    
    def preview_rashomon(self):
        '''
            Method illustrating the leaderboard and the plot with all possible epsilon values and the Rashomon Set sizes to help choose the right epsilon argument.
        '''

        print("\033[1;34mThe Visualizer received a leaderboard displayed below.\033[0m")
        print("\033[1;34mCheck if this is the desired leaderboard for analysis, else change the given Path parameter\033[0m")
        print(self.leaderboard)
        print("\033[1;34mThe plot illustrating the Rashomon Set size for different epsilon values will be displayed....\033[0m")

        self.visualize_rashomon_set_volume()


    def visualize_rashomon_set_volume(self):
        '''
            Method for visualising Rashomon set size depending on epsilon.
        '''

        epsilons = np.linspace(0, 1, 100)
        tmp_rashomon_set = RashomonSet(self.leaderboard, self.predictions, self.proba_predictions, self.feature_importances, self.base_metric, 10.0)
        valid_epsilons = [eps for eps in epsilons if len(tmp_rashomon_set.get_rashomon_set(eps))>1]

        def compute_size(epsilon):
            rs = RashomonSet(self.leaderboard, self.predictions, self.proba_predictions, self.feature_importances, self.base_metric, epsilon)
            return len(rs.rashomon_set)
            
        rashomon_sizes= [compute_size(eps) for eps in valid_epsilons]
        # jump epsilons
        diff = np.diff(rashomon_sizes)
        jump_indices = np.where(diff > 0)[0] + 1

        plt.figure(figsize=(8,5))
        plt.scatter(valid_epsilons, rashomon_sizes, s=20, color = '#6d9c5d')
        plt.gca().yaxis.set_major_locator(MaxNLocator(integer=True))

        for idx in jump_indices:
            jump_epsilon = valid_epsilons[idx]
            plt.axvline(x=jump_epsilon, color='#eea951', linestyle='--', alpha=0.8)
            plt.text(jump_epsilon, plt.ylim()[0] - 0.2, f"{jump_epsilon:.3f}",
             rotation=90, color='#eea951', fontsize=9, ha='center', va='top')

        if len(jump_indices) > 0:
            plt.axvline(x=valid_epsilons[jump_indices[0]], color='#eea951', linestyle='--', alpha=0.5,
                        label='Change in Rashomon set size')
        plt.legend(fontsize=10)
        plt.xlabel('Epsilon value', labelpad=19)
        plt.ylabel('Number of models in Rashomon set')
        plt.title('Rashomon set sizes', pad=10)
        plt.tight_layout()
        plt.show()


    def set_epsilon(self, epsilon: float):
        '''
            Sets the epsilon threshold for the Rashomon Set.
            Epsilon value must be set before calling build() method.
        '''

        if epsilon>=0:
            self.epsilon = epsilon
        else:
            raise ValueError("Epsilon parameter cannot be less than 0. Please provide a valid epsilon value.")


    def build(self, launch_dashboard: bool = True):
        '''
            Builds the Rashomon Set pipeline from H2O models.
            Creates Rashomon Set object and Visualizer object from user's input and launches a Streamlit dashboard in a subprocess for interactive visualization.

            Parameters: 
                launch_dashboard : boolean value indicating whether to launch the Streamlit dashboard after building the Rashomon Set and Visualizer. Default is True.
            
            Returns:
                    RashomonSet : Rashomon Set class object computed during pipeline
                    RashomonVisualizer : Visualizer class object created for computed Rashomon Set
        '''

        logging.info("Building Rashomon Set and Visualizer...")
        logging.info('Validating epsilon parameter...')
        if self.epsilon is None:
            raise ValueError("Please set the epsilon value using the set_epsilon() method. For help call rashomon_preview() method.")
        logging.info(f"Epsilon parameter set to {self.epsilon}.")

        rashomon_set = RashomonSet(self.leaderboard, self.predictions, self.proba_predictions, self.feature_importances, self.base_metric, self.epsilon)
        visualizer = Visualizer(rashomon_set, self.y_true)

        if launch_dashboard:
            plots ={}
            descriptions ={}

            if rashomon_set.task_type == "binary":
                method_names = visualizer.binary_methods
                ambiguity_discrepancy_proba_plot, ambiguity_discrepancy_proba_descr = visualizer.lolipop_ambiguity_discrepancy_proba_version(self.delta)
                plots["lolipop_ambiguity_discrepancy_proba_version"], descriptions["lolipop_ambiguity_discrepancy_proba_version"] = ambiguity_discrepancy_proba_plot, ambiguity_discrepancy_proba_descr
                proba_ambiguity_plot, proba_ambiguity_descr = visualizer.proba_ambiguity_vs_epsilon(self.delta)
                plots["proba_ambiguity_vs_epsilon"], descriptions["proba_ambiguity_vs_epsilon"] = proba_ambiguity_plot, proba_ambiguity_descr
                proba_discrepancy_plot, proba_discrepancy_descr = visualizer.proba_discrepancy_vs_epsilon(self.delta)
                plots["proba_discrepancy_vs_epsilon"], descriptions["proba_discrepancy_vs_epsilon"] = proba_discrepancy_plot, proba_discrepancy_descr

            elif rashomon_set.task_type =="multiclass":
                method_names = visualizer.multiclass_methods

            random_idx = random.choice(self.y_true.index.tolist()) #choose random sample for analysis
            for method in method_names:
                func = getattr(visualizer, method)
                sig = inspect.signature(func)
                params = sig.parameters

                #if the method needs parameters (random sample index):
                if len(params)>0:
                    # random index 
                    if "sample_index" in params:
                        plot, descr = func(sample_index=random_idx)
                    else: 
                        raise ValueError(f"Method {method} needs unsupported parameters")
                else: plot, descr = func()
                plots[method] = plot
                descriptions[method] = descr
            
            logging.info("Rashomon Set and Visualizer built successfully.")
            temp_file = TMP_DIR / "temp_plots.pkl"
            with open(temp_file, "wb") as f:
                pickle.dump((plots, descriptions), f)

            logging.info('Closing all previous Streamlit processes...')
            self.dashboard_close() # close all processes before starting a new one
            logging.info('Launching Streamlit dashboard...')
            if rashomon_set.task_type =="binary":           
                proc = subprocess.Popen([
                    sys.executable, "-m", "streamlit", "run", str(RASHOMON_BINARY_APP_PATH), "--", str(temp_file)
                ])
            elif rashomon_set.task_type=="multiclass":
                proc = subprocess.Popen([
                    sys.executable, "-m", "streamlit", "run", str(RASHOMON_MULTICLASS_APP_PATH), "--", str(temp_file)
                ])

            logging.info(f"Streamlit dashboard launched (PID={proc.pid})")
            logging.info("You can continue working with your code - to close Streamlit process call dashboard_close() method.")
        else: 
            logging.info("Rashomon Set and Visualizer built successfully. Dashboard launch skipped as per user request.")

        return rashomon_set, visualizer
    
    def dashboard_close(self):
        '''
            Method for stopping all Streamlit processes and closing the dashboard.
        '''

        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmd = " ".join(proc.info['cmdline'] or [])
                if 'streamlit' in cmd:
                    print(f"🛑 Killing Streamlit (PID={proc.info['pid']})")
                    psutil.Process(proc.info['pid']).terminate()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    

class BuildRashomonIntersectionH2O(Builder):
    '''
        Pipeline for creating and exploring the Rashomon Set Intersection from user-provided models from H2O framework. 
    '''

    def __init__(self, models_directory: Path, test_data : h2o.H2OFrame, target_column : str, df_name : str, 
                 metrics : list, custom_weights : list = None, weighted_sum_method : str = 'entropy', delta : float = 0.1, 
                 feature_imp_needed = True,  converter_results_directory : Path = None):
        '''
            Initializes the Pipeline user's input (models traines with H2O framework) to the creation of the Rashomon Set Intersection and it's visualizations.

            Args:
                models_directory : path to a folder where all models saved from H2O output are stored.
                test_data : test dataset for evaluation
                target_column : name of the target column. Used to determine task type.
                df_name : name of the dataset for saving converter output purposes.
                metrics : list of metrics to be used in the intersection calculation
                custom_weights : if weighted_sum is 'custom_weights' then user must specify weights in 2-element list.
                weighted_sum_method : Specifies the method or weights for selecting the base model. Options are:
                    - None or 'entropy' (default): Uses entropy-based method to select the base model.
                    - 'critic': Uses critic-based method to select the base model.
                    - 'custom_weights': Selects the base model using a weights provided by user.
                    the base model as a weighted combination of the two metrics.
                delta : delta parameter for probabilistic ambiguity and discrepancy (used only for binary task type). If not specified the default value of 0.1 will be used.
                feature_imp_needed : boolean value indicating whether the calculation of feature importances is needed.
                converter_results_directory : Path to directory where converter outputs will be stored.
                                              If None -> creates 'converter_results/<df_name>_<timestamp>' next to models_directory.
            
        '''

        #All __init__ parameter validation is done in other modules, so it’s not necessary to duplicate it here.
        logging.info("Converting H2O models to Rashomon Intersection Analysis format...")
        if converter_results_directory is None:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            converter_results_directory = models_directory.parent/'converter_results'/f"{df_name}_{timestamp}"
        logging.info(f"Converter results will be stored in: {converter_results_directory}")
        logging.info("Please wait...")
        logging.info("This process may take several minutes depending on the number of models and dataset size.")
        logging.info("If you wish to speed up the process, consider setting feature_imp_needed=False.")
        h2o_converter = H2O_Converter(models_directory, test_data, target_column, df_name, feature_imp_needed)
        self.leaderboard, self.predictions, self.proba_predictions, self.feature_importances, self.y_true = h2o_converter.convert(saving_path = converter_results_directory)
        self.metrics = metrics
        self.custom_weights = custom_weights
        self.weighted_sum_method = weighted_sum_method
        self.delta = delta
        self.epsilon = None
        logging.info("Conversion completed.")
        logging.info("You can preview the Rashomon Intersection Set size plot using preview_rashomon() method to determine epsilon parameter value.")

    
    def preview_rashomon(self):
        '''
            Method illustrating the leaderboard and the plot with all possible epsilon values and the Rashomon Intersection sizes to help choose the right epsilon argument.
        '''

        print("\033[1;34mThe Visualizer received a leaderboard displayed below.\033[0m")
        print("\033[1;34mCheck if this is the desired leaderboard for analysis, else change the given Path parameter\033[0m")
        print(self.leaderboard)
        print("\033[1;34mThe plot illustrating the Rashomon Set size for different epsilon values will be displayed....\033[0m")

        self.visualize_rashomon_set_volume()


    def visualize_rashomon_set_volume(self):
        '''
            Method for visualising Rashomon Set size depending on epsilon
        '''

        epsilons = np.linspace(0, 1, 100)
        tmp_rashomon_int = RashomonIntersection(leaderboard=self.leaderboard, predictions=self.predictions, proba_predictions=self.proba_predictions, 
                                               feature_importances=self.feature_importances, metrics=self.metrics, epsilon=10.0, 
                                               custom_weights=self.custom_weights, weighted_sum_method=self.weighted_sum_method)
        valid_epsilons = [eps for eps in epsilons if len(tmp_rashomon_int.get_rashomon_set(eps))>1]

        def compute_size(epsilon):
            rs = RashomonIntersection(leaderboard=self.leaderboard, predictions=self.predictions, proba_predictions=self.proba_predictions, 
                                               feature_importances=self.feature_importances, metrics=self.metrics, epsilon=epsilon, 
                                               custom_weights=self.custom_weights, weighted_sum_method=self.weighted_sum_method)
            return len(rs.rashomon_set)
            
        rashomon_sizes= [compute_size(eps) for eps in valid_epsilons]
        # jump epsilons
        diff = np.diff(rashomon_sizes)
        jump_indices = np.where(diff > 0)[0] + 1

        plt.figure(figsize=(8,5))
        plt.scatter(valid_epsilons, rashomon_sizes, s=20, color = '#6d9c5d')
        plt.gca().yaxis.set_major_locator(MaxNLocator(integer=True))

        for idx in jump_indices:
            jump_epsilon = valid_epsilons[idx]
            plt.axvline(x=jump_epsilon, color='#eea951', linestyle='--', alpha=0.8)
            plt.text(jump_epsilon, plt.ylim()[0] - 0.2, f"{jump_epsilon:.3f}",
             rotation=90, color='#eea951', fontsize=9, ha='center', va='top')

        if len(jump_indices) > 0:
            plt.axvline(x=valid_epsilons[jump_indices[0]], color='#eea951', linestyle='--', alpha=0.5,
                        label='Change in Rashomon set size')
        plt.legend(fontsize=10)
        plt.xlabel('Epsilon value', labelpad=19)
        plt.ylabel('Number of models in Rashomon set')
        plt.title('Rashomon set sizes', pad=10)
        plt.tight_layout()
        plt.show()


    def set_epsilon(self, epsilon: float):
        '''
            Sets the epsilon threshold for the Rashomon Intersection.
            Epsilon value must be set before calling build() method.
        '''

        if epsilon>=0:
            self.epsilon = epsilon
        else:
            raise ValueError("Epsilon parameter cannot be less than 0. Please provide a valid epsilon value.")


    def build(self, launch_dashboard: bool = True):
        '''
            Builds the Rashomon Intersection pipeline from H2O models.
            Creates Rashomon Intersection object and Intersection Visualizer object from user's input and launches a Streamlit dashboard in a subprocess for interactive visualization.

            Parameters:
                launch_dashboard : boolean value indicating whether to launch the Streamlit dashboard after building the Rashomon Intersection and Visualizer. Default is True.
                
            Returns:
                    RashomonSetIntersection : Rashomon Set Intersection class object computed during pipeline
                    IntersectionVisualizer : Visualizer class object created for computed Rashomon Set Intersection
        '''

        logging.info("Building Rashomon Intersection and Visualizer...")
        logging.info('Validating epsilon parameter...')
        if self.epsilon is None:
            raise ValueError("Please set the epsilon value using the set_epsilon() method. For help call rashomon_preview() method.")
        logging.info(f"Epsilon parameter set to {self.epsilon}.")
        
        rashomon_set = RashomonIntersection(leaderboard=self.leaderboard, predictions=self.predictions, proba_predictions=self.proba_predictions, 
                                               feature_importances=self.feature_importances, metrics=self.metrics, epsilon=self.epsilon, 
                                               custom_weights=self.custom_weights, weighted_sum_method=self.weighted_sum_method)
        visualizer = IntersectionVisualizer(rashomon_set, self.y_true)
        
        if launch_dashboard:
            plots ={}
            descriptions ={}

            if rashomon_set.task_type == "binary":
                method_names = visualizer.binary_methods
                ambiguity_discrepancy_proba_plot, ambiguity_discrepancy_proba_descr = visualizer.lolipop_ambiguity_discrepancy_proba_version(self.delta)
                plots["lolipop_ambiguity_discrepancy_proba_version"], descriptions["lolipop_ambiguity_discrepancy_proba_version"] = ambiguity_discrepancy_proba_plot, ambiguity_discrepancy_proba_descr
                proba_ambiguity_plot, proba_ambiguity_descr = visualizer.proba_ambiguity_vs_epsilon(self.delta)
                plots["proba_ambiguity_vs_epsilon"], descriptions["proba_ambiguity_vs_epsilon"] = proba_ambiguity_plot, proba_ambiguity_descr
                proba_discrepancy_plot, proba_discrepancy_descr = visualizer.proba_discrepancy_vs_epsilon(self.delta)
                plots["proba_discrepancy_vs_epsilon"], descriptions["proba_discrepancy_vs_epsilon"] = proba_discrepancy_plot, proba_discrepancy_descr

            elif rashomon_set.task_type =="multiclass":
                method_names = visualizer.multiclass_methods

            random_idx = random.choice(self.y_true.index.tolist()) #choose random sample for analysis
            for method in method_names:
                func = getattr(visualizer, method)
                sig = inspect.signature(func)
                params = sig.parameters

                #if the method needs parameters (random sample index):
                if len(params)>0:
                    # random index 
                    if "sample_index" in params:
                        plot, descr = func(sample_index=random_idx)
                    else: 
                        raise ValueError(f"Method {method} needs unsupported parameters")
                else: plot, descr = func()
                plots[method] = plot
                descriptions[method] = descr
            
            logging.info("Rashomon Intersection Set and Visualizer built successfully.")
            temp_file = TMP_DIR / "temp_plots.pkl"
            with open(temp_file, "wb") as f:
                pickle.dump((plots, descriptions), f)

            logging.info('Closing all previous Streamlit processes...')
            self.dashboard_close() # close all processes before starting a new one
            logging.info('Launching Streamlit dashboard...')

            if rashomon_set.task_type =="binary":           
                proc = subprocess.Popen([
                    sys.executable, "-m", "streamlit", "run", str(INTERSECTION_BINARY_APP_PATH), "--", str(temp_file)
                ])
            elif rashomon_set.task_type=="multiclass":
                proc = subprocess.Popen([
                    sys.executable, "-m", "streamlit", "run", str(INTERSECTION_MULTICLASS_APP_PATH), "--", str(temp_file)
                ])

            logging.info(f"Streamlit dashboard launched (PID={proc.pid})")
            logging.info("You can continue working with your code - to close Streamlit process call dashboard_close() method.")
        else:
            logging.info("Rashomon Intersection and Visualizer built successfully. Dashboard launch skipped as per user request.")

        return rashomon_set, visualizer
    
    def dashboard_close(self):
        '''
            Method for stopping all Streamlit processes and closing the dashboard.
        '''
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmd = " ".join(proc.info['cmdline'] or [])
                if 'streamlit' in cmd:
                    print(f"🛑 Killing Streamlit (PID={proc.info['pid']})")
                    psutil.Process(proc.info['pid']).terminate()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    

class BuildRashomonAutogluon(Builder):
    '''
        Pipeline for creating and exploring the Rashomon Set from user-provided models from AutoGluon framework. 
    '''
    
    def __init__(self, predictor : TabularPredictor, test_data : TabularDataset, df_name : str, base_metric : str,
                delta : float = 0.1, feature_imp_needed = True,  converter_results_directory : Path = None):
        '''
            Initializes the Pipeline user's input (models traines with AutoGluon framework) to the creation of the Rashomon Set and it's visualizations.

            Args:
                predictor : trained Autogluon predictor object
                test_data : test dataset for evaluation
                df_name : name of the dataset for saving converter output purposes.
                base_metric : evaluation metric to be used while creating the Rashomon Set
                delta : delta parameter for probabilistic ambiguity and discrepancy (used only for binary task type). If not specified the default value of 0.1 will be used.
                feature_imp_needed : boolean value indicating whether the calculation of feature importances is needed.
                converter_results_directory : Path to directory where converter outputs will be stored.
                                              If None -> creates 'converter_results/<df_name>_<timestamp>' in the current directory.
        '''

        #All __init__ parameter validation is done in other modules, so it’s not necessary to duplicate it here.
        logging.info("Converting AutoGluon models to Rashomon Analysis format...")
        if converter_results_directory is None:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            converter_results_directory = Path.cwd()/'converter_results'/f"{df_name}_{timestamp}"
        logging.info(f"Converter results will be stored in: {converter_results_directory}")
        logging.info("Please wait...")
        logging.info("This process may take several minutes depending on the number of models and dataset size.")
        autogluon_converter = PredictorConverter(predictor=predictor, test_data=test_data, df_name=df_name, feature_imp_needed=feature_imp_needed)
        self.leaderboard, self.predictions, self.proba_predictions, self.feature_importances, self.y_true = autogluon_converter.convert(saving_path = converter_results_directory)
        self.base_metric = base_metric
        self.delta = delta
        self.epsilon = None
        logging.info("Conversion completed.")
        logging.info("You can preview the Rashomon Set size plot using preview_rashomon() method to determine epsilon parameter value.")


    
    def preview_rashomon(self):
        '''
            Method illustrating the leaderboard and the plot with all possible epsilon values and the Rashomon Set sizes to help choose the right epsilon argument.
        '''

        print("\033[1;34mThe Visualizer received a leaderboard displayed below.\033[0m")
        print("\033[1;34mCheck if this is the desired leaderboard for analysis, else change the given Path parameter\033[0m")
        print(self.leaderboard)
        print("\033[1;34mThe plot illustrating the Rashomon Set size for different epsilon values will be displayed....\033[0m")

        self.visualize_rashomon_set_volume()


    def visualize_rashomon_set_volume(self):
        '''
            Method for visualising Rashomon set size depending on epsilon
        '''

        epsilons = np.linspace(0, 1, 100)
        tmp_rashomon_set = RashomonSet(self.leaderboard, self.predictions, self.proba_predictions, self.feature_importances, self.base_metric, 10.0)
        valid_epsilons = [eps for eps in epsilons if len(tmp_rashomon_set.get_rashomon_set(eps))>1]

        def compute_size(epsilon):
            rs = RashomonSet(self.leaderboard, self.predictions, self.proba_predictions, self.feature_importances, self.base_metric, epsilon)
            return len(rs.rashomon_set)
            
        rashomon_sizes= [compute_size(eps) for eps in valid_epsilons]
        # jump epsilons
        diff = np.diff(rashomon_sizes)
        jump_indices = np.where(diff > 0)[0] + 1

        plt.figure(figsize=(8,5))
        plt.scatter(valid_epsilons, rashomon_sizes, s=20, color = '#6d9c5d')
        plt.gca().yaxis.set_major_locator(MaxNLocator(integer=True))

        for idx in jump_indices:
            jump_epsilon = valid_epsilons[idx]
            plt.axvline(x=jump_epsilon, color='#eea951', linestyle='--', alpha=0.8)
            plt.text(jump_epsilon, plt.ylim()[0] - 0.2, f"{jump_epsilon:.3f}",
             rotation=90, color='#eea951', fontsize=9, ha='center', va='top')

        if len(jump_indices) > 0:
            plt.axvline(x=valid_epsilons[jump_indices[0]], color='#eea951', linestyle='--', alpha=0.5,
                        label='Change in Rashomon set size')
        plt.legend(fontsize=10)
        plt.xlabel('Epsilon value', labelpad=19)
        plt.ylabel('Number of models in Rashomon set')
        plt.title('Rashomon set sizes', pad=10)
        plt.tight_layout()
        plt.show()


    def set_epsilon(self, epsilon: float):
        '''
            Sets the epsilon threshold for the Rashomon Set.
            Epsilon value must be set before calling build() method.
        '''

        if epsilon>=0:
            self.epsilon = epsilon
        else:
            raise ValueError("Epsilon parameter cannot be less than 0. Please provide a valid epsilon value.")


    def build(self, launch_dashboard: bool = True):
        '''
            Builds the Rashomon Set pipeline from AutoGluon input.
            Creates Rashomon Set object and Visualizer object from user's input and launches a Streamlit dashboard in a subprocess for interactive visualization.

            Parameters:
                launch_dashboard : boolean value indicating whether to launch the Streamlit dashboard after building the Rashomon Set and Visualizer. Default is True.
                
            Returns:
                    RashomonSet : Rashomon Set class object computed during pipeline
                    RashomonVisualizer : Visualizer class object created for computed Rashomon Set
        '''

        logging.info("Building Rashomon Set and Visualizer...")
        logging.info('Validating epsilon parameter...')
        if self.epsilon is None:
            raise ValueError("Please set the epsilon value using the set_epsilon() method. For help call rashomon_preview() method.")
        logging.info(f"Epsilon parameter set to {self.epsilon}.")
        
        rashomon_set = RashomonSet(self.leaderboard, self.predictions, self.proba_predictions, self.feature_importances, self.base_metric, self.epsilon)
        visualizer = Visualizer(rashomon_set, self.y_true)
        
        if launch_dashboard:
            plots ={}
            descriptions ={}

            if rashomon_set.task_type == "binary":
                method_names = visualizer.binary_methods
                ambiguity_discrepancy_proba_plot, ambiguity_discrepancy_proba_descr = visualizer.lolipop_ambiguity_discrepancy_proba_version(self.delta)
                plots["lolipop_ambiguity_discrepancy_proba_version"], descriptions["lolipop_ambiguity_discrepancy_proba_version"] = ambiguity_discrepancy_proba_plot, ambiguity_discrepancy_proba_descr
                proba_ambiguity_plot, proba_ambiguity_descr = visualizer.proba_ambiguity_vs_epsilon(self.delta)
                plots["proba_ambiguity_vs_epsilon"], descriptions["proba_ambiguity_vs_epsilon"] = proba_ambiguity_plot, proba_ambiguity_descr
                proba_discrepancy_plot, proba_discrepancy_descr = visualizer.proba_discrepancy_vs_epsilon(self.delta)
                plots["proba_discrepancy_vs_epsilon"], descriptions["proba_discrepancy_vs_epsilon"] = proba_discrepancy_plot, proba_discrepancy_descr

            elif rashomon_set.task_type =="multiclass":
                method_names = visualizer.multiclass_methods

            random_idx = random.choice(self.y_true.index.tolist()) #choose random sample for analysis
            for method in method_names:
                    func = getattr(visualizer, method)
                    sig = inspect.signature(func)
                    params = sig.parameters

                    #if the method needs parameters (random sample index):
                    if len(params)>0:
                        # random index 
                        if "sample_index" in params:
                            plot, descr = func(sample_index=random_idx)
                        else: 
                            raise ValueError(f"Method {method} needs unsupported parameters")
                    else: plot, descr = func()
                    plots[method] = plot
                    descriptions[method] = descr
            
            logging.info("Rashomon Set and Visualizer built successfully.")
            temp_file = TMP_DIR / "temp_plots.pkl"
            with open(temp_file, "wb") as f:
                pickle.dump((plots, descriptions), f)

            logging.info('Closing all previous Streamlit processes...')
            self.dashboard_close() # close all processes before starting a new one
            logging.info('Launching Streamlit dashboard...')

            if rashomon_set.task_type =="binary":           
                proc = subprocess.Popen([
                    sys.executable, "-m", "streamlit", "run", str(RASHOMON_BINARY_APP_PATH), "--", str(temp_file)
                ])
            elif rashomon_set.task_type=="multiclass":
                proc = subprocess.Popen([
                    sys.executable, "-m", "streamlit", "run", str(RASHOMON_MULTICLASS_APP_PATH), "--", str(temp_file)
                ])

            logging.info(f"Streamlit dashboard launched (PID={proc.pid})")
            logging.info("You can continue working with your code - to close Streamlit process call dashboard_close() method.")
        
        else:
            logging.info("Rashomon Set and Visualizer built successfully. Dashboard launch skipped as per user request.")

        return rashomon_set, visualizer

    def dashboard_close(self):
        '''
            Method for stopping all Streamlit processes and closing the dashboard.
        '''
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmd = " ".join(proc.info['cmdline'] or [])
                if 'streamlit' in cmd:
                    print(f"🛑 Killing Streamlit (PID={proc.info['pid']})")
                    psutil.Process(proc.info['pid']).terminate()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    
class BuildRashomonIntersectionAutogluon(Builder):
    '''
        Pipeline for creating and exploring the Rashomon Set Intersection from user-provided models from Autogluon framework. 
    '''

    def __init__(self, predictor : TabularPredictor, test_data : TabularDataset, df_name : str, metrics : list, 
                 custom_weights : list = None, weighted_sum_method : str = 'entropy', delta : float = 0.1, 
                 feature_imp_needed = True,  converter_results_directory : Path = None):
        '''
            Initializes the Pipeline user's input (models traines with AutoGluon framework) to the creation of the Rashomon Set Intersection and it's visualizations.

            Args:
                predictor : trained Autogluon predictor object
                test_data : test dataset for evaluation
                df_name : name of the dataset for saving converter output purposes.
                metrics : list of metrics to be used in the intersection calculation
                custom_weights : if weighted_sum is 'custom_weights' then user must specify weights in 2-element list.
                weighted_sum_method : Specifies the method or weights for selecting the base model. Options are:
                    - None or 'entropy' (default): Uses entropy-based method to select the base model.
                    - 'critic': Uses critic-based method to select the base model.
                    - 'custom_weights': Selects the base model using a weights provided by user.
                    the base model as a weighted combination of the two metrics.
                delta : delta parameter for probabilistic ambiguity and discrepancy (used only for binary task type). If not specified the default value of 0.1 will be used.
                feature_imp_needed : boolean value indicating whether the calculation of feature importances is needed.
                converter_results_directory : Path to directory where converter outputs will be stored.
                                              If None -> creates 'converter_results/<df_name>_<timestamp>' in the current directory.
            
        '''

        #All __init__ parameter validation is done in other modules, so it’s not necessary to duplicate it here.
        logging.info("Converting AutoGluon models to Rashomon Intersection Analysis format...")
        if converter_results_directory is None:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            converter_results_directory = Path.cwd()/'converter_results'/f"{df_name}_{timestamp}"
        logging.info(f"Converter results will be stored in: {converter_results_directory}")
        logging.info("Please wait...")
        logging.info("This process may take several minutes depending on the number of models and dataset size.")
        logging.info("If you wish to speed up the process, consider setting feature_imp_needed=False.") 
        autogluon_converter = PredictorConverter(predictor=predictor, test_data=test_data, df_name=df_name, feature_imp_needed=feature_imp_needed)
        self.leaderboard, self.predictions, self.proba_predictions, self.feature_importances, self.y_true = autogluon_converter.convert(saving_path = converter_results_directory)
        self.metrics = metrics
        self.custom_weights = custom_weights
        self.weighted_sum_method = weighted_sum_method
        self.delta = delta
        self.epsilon = None
        logging.info("Conversion completed.")
        logging.info("You can preview the Rashomon Intersection Set size plot using preview_rashomon() method to determine epsilon parameter value.")

    
    def preview_rashomon(self):
        '''
            Method illustrating the leaderboard and the plot with all possible epsilon values and the Rashomon Intersection sizes to help choose the right epsilon argument.
        '''

        print("\033[1;34mThe Visualizer received a leaderboard displayed below.\033[0m")
        print("\033[1;34mCheck if this is the desired leaderboard for analysis, else change the given Path parameter\033[0m")
        print(self.leaderboard)
        print("\033[1;34mThe plot illustrating the Rashomon Set size for different epsilon values will be displayed....\033[0m")

        self.visualize_rashomon_set_volume()


    def visualize_rashomon_set_volume(self):
        '''
            Method for visualising Rashomon set size depending on epsilon
        '''

        epsilons = np.linspace(0, 1, 100)
        tmp_rashomon_int = RashomonIntersection(leaderboard=self.leaderboard, predictions=self.predictions, proba_predictions=self.proba_predictions, 
                                               feature_importances=self.feature_importances, metrics=self.metrics, epsilon=10.0, 
                                               custom_weights=self.custom_weights, weighted_sum_method=self.weighted_sum_method)
        valid_epsilons = [eps for eps in epsilons if len(tmp_rashomon_int.get_rashomon_set(eps))>1]

        def compute_size(epsilon):
            rs = RashomonIntersection(leaderboard=self.leaderboard, predictions=self.predictions, proba_predictions=self.proba_predictions, 
                                               feature_importances=self.feature_importances, metrics=self.metrics, epsilon=epsilon, 
                                               custom_weights=self.custom_weights, weighted_sum_method=self.weighted_sum_method)
            return len(rs.rashomon_set)
            
        rashomon_sizes= [compute_size(eps) for eps in valid_epsilons]
        # jump epsilons
        diff = np.diff(rashomon_sizes)
        jump_indices = np.where(diff > 0)[0] + 1

        plt.figure(figsize=(8,5))
        plt.scatter(valid_epsilons, rashomon_sizes, s=20, color = '#6d9c5d')
        plt.gca().yaxis.set_major_locator(MaxNLocator(integer=True))

        for idx in jump_indices:
            jump_epsilon = valid_epsilons[idx]
            plt.axvline(x=jump_epsilon, color='#eea951', linestyle='--', alpha=0.8)
            plt.text(jump_epsilon, plt.ylim()[0] - 0.2, f"{jump_epsilon:.3f}",
             rotation=90, color='#eea951', fontsize=9, ha='center', va='top')

        if len(jump_indices) > 0:
            plt.axvline(x=valid_epsilons[jump_indices[0]], color='#eea951', linestyle='--', alpha=0.5,
                        label='Change in Rashomon set size')
        plt.legend(fontsize=10)
        plt.xlabel('Epsilon value', labelpad=19)
        plt.ylabel('Number of models in Rashomon set')
        plt.title('Rashomon set sizes', pad=10)
        plt.tight_layout()
        plt.show()


    def set_epsilon(self, epsilon: float):
        '''
            Sets the epsilon threshold for the Rashomon Intersection.
            Epsilon value must be set before calling build() method.
        '''

        if epsilon>=0:
            self.epsilon = epsilon
        else:
            raise ValueError("Epsilon parameter cannot be less than 0. Please provide a valid epsilon value.")


    def build(self, launch_dashboard : bool = True):
        '''
            Builds the Rashomon Intersection pipeline from AutoGluon input.
            Creates Rashomon Intersection object and Intersection Visualizer object from user's input and launches a Streamlit dashboard in a subprocess for interactive visualization.

            Parameters:
                launch_dashboard : boolean value indicating whether to launch the Streamlit dashboard after building the Rashomon
                    
            Returns:
                    RashomonSetIntersection : Rashomon Set Intersection class object computed during pipeline
                    IntersectionVisualizer : Visualizer class object created for computed Rashomon Set Intersection
        '''

        logging.info("Building Rashomon Intersection and Visualizer...")
        logging.info('Validating epsilon parameter...')
        if self.epsilon is None:
            raise ValueError("Please set the epsilon value using the set_epsilon() method. For help call rashomon_preview() method.")
        logging.info(f"Epsilon parameter set to {self.epsilon}.")
        
        rashomon_set = RashomonIntersection(leaderboard=self.leaderboard, predictions=self.predictions, proba_predictions=self.proba_predictions, 
                                               feature_importances=self.feature_importances, metrics=self.metrics, epsilon=self.epsilon, 
                                               custom_weights=self.custom_weights, weighted_sum_method=self.weighted_sum_method)
        visualizer = IntersectionVisualizer(rashomon_set, self.y_true)

        if launch_dashboard:
            plots ={}
            descriptions ={}

            if rashomon_set.task_type == "binary":
                method_names = visualizer.binary_methods
                ambiguity_discrepancy_proba_plot, ambiguity_discrepancy_proba_descr = visualizer.lolipop_ambiguity_discrepancy_proba_version(self.delta)
                plots["lolipop_ambiguity_discrepancy_proba_version"], descriptions["lolipop_ambiguity_discrepancy_proba_version"] = ambiguity_discrepancy_proba_plot, ambiguity_discrepancy_proba_descr
                proba_ambiguity_plot, proba_ambiguity_descr = visualizer.proba_ambiguity_vs_epsilon(self.delta)
                plots["proba_ambiguity_vs_epsilon"], descriptions["proba_ambiguity_vs_epsilon"] = proba_ambiguity_plot, proba_ambiguity_descr
                proba_discrepancy_plot, proba_discrepancy_descr = visualizer.proba_discrepancy_vs_epsilon(self.delta)
                plots["proba_discrepancy_vs_epsilon"], descriptions["proba_discrepancy_vs_epsilon"] = proba_discrepancy_plot, proba_discrepancy_descr

            elif rashomon_set.task_type =="multiclass":
                method_names = visualizer.multiclass_methods

            random_idx = random.choice(self.y_true.index.tolist()) #choose random sample for analysis
            for method in method_names:
                    func = getattr(visualizer, method)
                    sig = inspect.signature(func)
                    params = sig.parameters

                    #if the method needs parameters (random sample index):
                    if len(params)>0:
                        # random index 
                        if "sample_index" in params:
                            plot, descr = func(sample_index=random_idx)
                        else: 
                            raise ValueError(f"Method {method} needs unsupported parameters")
                    else: plot, descr = func()
                    plots[method] = plot
                    descriptions[method] = descr
            
            logging.info("Rashomon Intersection Set and Visualizer built successfully.")
            temp_file = TMP_DIR / "temp_plots.pkl"
            with open(temp_file, "wb") as f:
                pickle.dump((plots, descriptions), f)

            logging.info('Closing all previous Streamlit processes...')
            self.dashboard_close()
            logging.info('Launching Streamlit dashboard...')

            if rashomon_set.task_type =="binary":           
                proc = subprocess.Popen([
                    sys.executable, "-m", "streamlit", "run", str(INTERSECTION_BINARY_APP_PATH), "--", str(temp_file)
                ])
            elif rashomon_set.task_type=="multiclass":
                proc = subprocess.Popen([
                    sys.executable, "-m", "streamlit", "run", str(INTERSECTION_MULTICLASS_APP_PATH), "--", str(temp_file)
                ])

            logging.info(f"Streamlit dashboard launched (PID={proc.pid})")
            logging.info("You can continue working with your code - to close Streamlit process call dashboard_close() method.")
        else:
            logging.info("Rashomon Set and Visualizer built successfully. Dashboard launch skipped as per user request.")

        return rashomon_set, visualizer

    def dashboard_close(self):
        '''
            Method for stopping all Streamlit processes and closing the dashboard.
        '''
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmd = " ".join(proc.info['cmdline'] or [])
                if 'streamlit' in cmd:
                    print(f"🛑 Killing Streamlit (PID={proc.info['pid']})")
                    psutil.Process(proc.info['pid']).terminate()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

