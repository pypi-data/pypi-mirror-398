import pandas as pd
import time
import os
import sys
import inspect 
import random
import subprocess
import psutil
from pathlib import Path
import importlib.resources as pkg_resources
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from rashomon_analysis.rashomon_set import *
from rashomon_analysis.rashomon_intersection import *
from rashomon_analysis.visualizers.rashomon_visualizer import *
from rashomon_analysis.visualizers.intersection_visualizer import *
from app.rashomon_binary_app import *
from rashomon_analysis.pipelines.builder_abstract import *
import pickle
import warnings
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

class BuildRashomonFromConverted(Builder):

    def __init__(self, converter_results_path: Path, base_metric : str, delta : float = 0.1):
        '''
            Initializes the Pipeline from converted results in order to create the Rashomon Set and it's visualizations.
            Args:
            converter_results_path : path to a folder where all objects returned by Converter.convert() are stored. 
            Should contain files such as : leaderboard.csv, predictions_dict.pkl, proba_predictions_dict.pkl, y_true.csv and feature_importance_dict.pkl (optional)

            base_metric : evaluation metric to be used while creating the Rashomon Set

            delta : delta parameter for probabilistic ambiguity and discrepancy (used only for binary task type). If not specified the default value of 0.1 will be used

        '''

        logging.info("Initializing Rashomon Builder...")
        self.METRICS = ['accuracy', 'balanced_accuracy', 'f1', 'f1_macro', 'f1_micro', 'f1_weighted',
            'roc_auc', 'roc_auc_ovo', 'roc_auc_ovo_macro', 'roc_auc_ovo_weighted', 'roc_auc_ovr', 
            'roc_auc_ovr_macro', 'roc_auc_ovr_micro', 'roc_auc_ovr_weighted', 'average_precision', 
            'precision', 'precision_macro', 'precision_micro', 'precision_weighted', 'recall', 
            'recall_macro', 'recall_micro', 'recall_weighted']
        
        logging.info("Arguments validation...")
        if not os.path.isdir(converter_results_path):
            raise ValueError(f"Folder path : {converter_results_path} does not exist. Provide a valid path")
        
        mandatory_files = ["leaderboard.csv", "predictions_dict.pkl", "proba_predictions_dict.pkl", "y_true.csv"]
        if not all((converter_results_path/file).is_file() for file in mandatory_files):
            raise ValueError(f"There re missing files in the provided directory. Make sure all files are present : {mandatory_files}")
        
        leaderboard = pd.read_csv( converter_results_path / "leaderboard.csv")
        y_true = pd.read_csv(converter_results_path/ "y_true.csv")
        with open(converter_results_path/ "predictions_dict.pkl", "rb") as f:
            predictions_dict = pickle.load(f)
        with open(converter_results_path / "proba_predictions_dict.pkl", "rb") as f:
            proba_predictions_dict = pickle.load(f)

        if (converter_results_path/"feature_importance_dict.pkl").is_file():
            with open(converter_results_path / "feature_importance_dict.pkl", "rb") as f:
                feature_importance_dict = pickle.load(f)
        else:
            feature_importance_dict = None


        logging.info("Arguments validated, assigning attributes...")
        self.leaderboard = leaderboard
        self.predictions = predictions_dict
        self.proba_predictions = proba_predictions_dict
        self.feature_importances = feature_importance_dict
        self.y_true = y_true
        self.base_metric = base_metric
        self.delta = delta
        self.epsilon=None

        logging.info("Rashomon Builder Initialized.")


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
    
    def set_epsilon(self, epsilon:float):
        '''
            Method for setting the value of Epsilon parameter to be used while creating the Rashomon Set object. 
            Is a necessary step before the build() method. 
        '''
        if epsilon>=0:
            self.epsilon = epsilon
        else:
            raise ValueError("Epsilon parameter cannot be less than 0. Please provide a valid epsilon value.")
    
    def build(self, launch_dashboard : bool = True):
        '''
            Primary method for creating  the Rashomon Set, Visualier and launching a final dashboard.
            Parameters: 
                launch_dashboard : boolean value indicating whether to launch the Streamlit dashboard automatically after building the Rashomon Set. Default = True
            Returns :
                RashomonSet : created Rashomon Set object
                Visualizer : Visualizer object created based on the Rashomon Set. 
        '''
        logging.info("Building Pipeline...")
        logging.info('Validating epsilon parameter...')
        if self.epsilon is None:
            raise ValueError("Please set the epsilon value using the set_epsilon() method. For help call rashomon_preview() method.")
        
        logging.info('Creating Rashomon Set and Visualizer...')
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

                    #if the method needs parameters (random sample index - if new methods have other parameters need to provide them here !):
                    if len(params)>0:
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



        
#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------

class BuildIntersectionFromConverted(Builder):

    def __init__(self, converter_results_path: Path, metrics : list,  custom_weights : list =None, weighted_sum_method : str = 'entropy', delta : float = 0.1):
        '''
            Initializes the Pipeline from converted results to the creation of the Rashomon Set and it's visualizations.
            Args:
            converter_results_path : path to a folder where all objects returned by Converter.convert() are stored. 
            Should contain files such as : leaderboard.csv, predictions_dict.pkl, proba_predictions_dict.pkl, y_true.csv and feature_importance_dict.pkl (optional)

            metrics : evaluation metrics to be used while creating the Rashomon Intersection

            custom_weights : list of weights for custom_weights weighted sum method. Default = None 

            weighted_sum_method: weighted sum method to be used while creating the Intersection. Default = entropy

            delta : delta parameter for probabilistic ambiguity and discrepancy (used only for binary task type). If not specified the default value of 0.1 will be used.
        '''
        logging.info("Initializing Rashomon Intersection Builder...")
        self.METRICS = ['accuracy', 'balanced_accuracy', 'f1', 'f1_macro', 'f1_micro', 'f1_weighted',
            'roc_auc', 'roc_auc_ovo', 'roc_auc_ovo_macro', 'roc_auc_ovo_weighted', 'roc_auc_ovr', 
            'roc_auc_ovr_macro', 'roc_auc_ovr_micro', 'roc_auc_ovr_weighted', 'average_precision', 
            'precision', 'precision_macro', 'precision_micro', 'precision_weighted', 'recall', 
            'recall_macro', 'recall_micro', 'recall_weighted']

        logging.info("Arguments validation...")
        if not os.path.isdir(converter_results_path):
            raise ValueError(f"Folder path : {converter_results_path} does not exist. Provide a valid path")
        
        mandatory_files = ["leaderboard.csv", "predictions_dict.pkl", "proba_predictions_dict.pkl", "y_true.csv"]
        if not all((converter_results_path/file).is_file() for file in mandatory_files):
            raise ValueError(f"There re missing files in the provided directory. Make sure all files are present : {mandatory_files}")
        
        leaderboard = pd.read_csv( converter_results_path / "leaderboard.csv")
        y_true = pd.read_csv(converter_results_path/ "y_true.csv")
        with open(converter_results_path/ "predictions_dict.pkl", "rb") as f:
            predictions_dict = pickle.load(f)
        with open(converter_results_path / "proba_predictions_dict.pkl", "rb") as f:
            proba_predictions_dict = pickle.load(f)

        if (converter_results_path/"feature_importance_dict.pkl").is_file():
            with open(converter_results_path / "feature_importance_dict.pkl", "rb") as f:
                feature_importance_dict = pickle.load(f)
        else:
            feature_importance_dict = None

        if not delta:
            raise ValueError("Delta parameter cannot be None")
        if not isinstance(delta, float):
            raise TypeError("Delta parameter must be float")
        if delta > 1 or delta <0:
            raise ValueError("Delta parameter must be from [0-1]")
        
        logging.info("Assigning attributes...")

        #if all assertions are correct 
        self.leaderboard = leaderboard
        self.predictions = predictions_dict
        self.proba_predictions = proba_predictions_dict
        self.feature_importances = feature_importance_dict
        self.y_true = y_true
        self.metrics = metrics
        self.custom_weights = custom_weights
        self.weighted_sum_method = weighted_sum_method
        self.delta = delta
        self.epsilon=None
        logging.info("Rashomon Intersection Builder initialized.")


    def preview_rashomon(self):
        '''
            Method illustrating the leaderboard and the plot with all possible epsilon values and the Rashomon Intersection sizes to help choose the right epsilon argument.
        '''
        print("\033[1;34mThe Visualizer received a leaderboard displayed below.\033[0m")
        print("\033[1;34mCheck if this is the desired leaderboard for analysis, else change the given Path parameter\033[0m")
        print(self.leaderboard)
        print("\033[1;34mThe plot illustrating the Rashomon Intersection size for different epsilon values will be displayed....\033[0m")

        self.visualize_rashomon_set_volume()

    def visualize_rashomon_set_volume(self):
        '''
            Method for visualising Rashomon Intersection size depending on epsilon
        '''
        epsilons = np.linspace(0, 1, 100)
        tmp_rashomon_int = RashomonIntersection(self.leaderboard, self.predictions, self.proba_predictions, self.feature_importances, self.metrics, 10.0, self.custom_weights, self.weighted_sum_method)
        valid_epsilons = [eps for eps in epsilons if len(tmp_rashomon_int.get_rashomon_set(eps))>1]

        def compute_size(epsilon):
            rs = RashomonIntersection(self.leaderboard, self.predictions, self.proba_predictions, self.feature_importances, self.metrics, epsilon, self.custom_weights, self.weighted_sum_method)
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
    
    def set_epsilon(self, epsilon:float):
        '''
            Method for setting the value of Epsilon parameter to be used while creating the Rashomon Intersection object. 
            Is a necessary step before the build() method. 
        '''

        if epsilon>=0:
            self.epsilon = epsilon
        else:
            raise ValueError("Epsilon parameter cannot be less than 0. Please provide a valid epsilon value.")
    
    def build(self, launch_dashboard : bool = True):
        '''
            Primary method for creating  the Rashomon Intersection, IntersectionVisualier and launching a final dashboard.
            Parameters: 
                launch_dashboard : boolean value indicating whether to launch the Streamlit dashboard automatically after building the Rashomon Intersection. Default = True
            Returns :
                RashomonIntersection : created Rashomon Intersection object
                IntersectionVisualizer : IntersectionVisualizer object created based on the Rashomon Intersection. 
        '''
        logging.info("Building Pipeline...")
        logging.info('Validating epsilon parameter...')
        if self.epsilon is None:
            raise ValueError("Please set the epsilon value using the set_epsilon() method. For help call rashomon_preview() method.")
        logging.info('Creating Rashomon Intersection and Visualizer...')
        rashomon_int = RashomonIntersection(self.leaderboard, self.predictions, self.proba_predictions, self.feature_importances, self.metrics, self.epsilon, self.custom_weights, self.weighted_sum_method)
        visualizer = IntersectionVisualizer(rashomon_int, self.y_true)
        
        if launch_dashboard:
            plots ={}
            descriptions ={}

            if rashomon_int.task_type == "binary":
                method_names = visualizer.binary_methods
                ambiguity_discrepancy_proba_plot, ambiguity_discrepancy_proba_descr = visualizer.lolipop_ambiguity_discrepancy_proba_version(self.delta)
                plots["lolipop_ambiguity_discrepancy_proba_version"], descriptions["lolipop_ambiguity_discrepancy_proba_version"] = ambiguity_discrepancy_proba_plot, ambiguity_discrepancy_proba_descr
                proba_ambiguity_plot, proba_ambiguity_descr = visualizer.proba_ambiguity_vs_epsilon(self.delta)
                plots["proba_ambiguity_vs_epsilon"], descriptions["proba_ambiguity_vs_epsilon"] = proba_ambiguity_plot, proba_ambiguity_descr
                proba_discrepancy_plot, proba_discrepancy_descr = visualizer.proba_discrepancy_vs_epsilon(self.delta)
                plots["proba_discrepancy_vs_epsilon"], descriptions["proba_discrepancy_vs_epsilon"] = proba_discrepancy_plot, proba_discrepancy_descr


            elif rashomon_int.task_type =="multiclass":
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
            logging.info("Rashomon Intersection and Visualizer built successfully.")
            temp_file = TMP_DIR / "temp_plots2.pkl"
            with open(temp_file, "wb") as f:
                pickle.dump((plots, descriptions), f)

            logging.info("Closing all previous Streamlit processes...")
            self.dashboard_close()
            logging.info("Launching Streamlit dashboard...")
            if rashomon_int.task_type =="binary":           
                proc = subprocess.Popen([
                    sys.executable, "-m", "streamlit", "run", str(INTERSECTION_BINARY_APP_PATH), "--", str(temp_file)
                ])
            elif rashomon_int.task_type=="multiclass":
                proc = subprocess.Popen([
                    sys.executable, "-m", "streamlit", "run", str(INTERSECTION_MULTICLASS_APP_PATH), "--", str(temp_file)
                ])

            logging.info(f"Streamlit dashboard launched (PID={proc.pid})")
            logging.info(f"You can continue working with your code - to close Streamlit process call dashboard_close() method.")
        else: 
            logging.info("Rashomon Intersection and Visualizer built successfully. Dashboard launch skipped as per user request.")

        return rashomon_int, visualizer

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

