import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from rashomon_analysis.rashomon_set import *
from rashomon_analysis.rashomon_intersection import *
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from rashomon_analysis.visualizers.rashomon_visualizer import *

plot_title_font = dict(
    color="#6B7F8A",
    family="Inter, Segoe UI, sans-serif",  
    size=16,
    style="normal",
    weight=400            
)

color_palette = ['#fcfafa', '#6C929E','#94B4C1','#205781', '#132440']
chart_colors_v2 = [
    '#DBE8EF',  
    '#C8DCEA',  
    '#B5CDD9',  
    '#9FBDCF',  
    '#89ADC4',  
    '#739DB9',  
    '#638EA8',  
    '#557D95',  
    '#476C82',  
    '#3A5B70',
    "#16476A",
    "#6C929E"
]

contrast_colors = [ "#ed801a"]
class_colors = ['#205781', '#739DB9', '#94B4C1', '#9FBDCF']

class_colors = [
    '#08306b',  
    '#08519c',  
    '#2171b5',
    '#4292c6',
    '#6baed6',
    '#9ecae1',
    '#9fbdcf',
    '#739db9',
    '#94b4c1',
    '#deebf7'  
]


class IntersectionVisualizer(Visualizer):
    '''
        Child class of the Visualizer. Used to generate plots for the Rashomon Intersection analysis.

        Arguments:
            rashomon_intersection: RashomonIntersection object to be analyzed
            y_true : true prediction vector

        Attributes:
            rashomon_set : passed RashomonIntersection object
            y_true : passed y_true object
            binary_methods : plots that can be generated for the binary classification task type
            multiclass_methods: plots that can be generated fot the multiclass classification task type
    '''

    def __init__(self, rashomon_intersection : RashomonIntersection, y_true : pd.DataFrame):
        self.rashomon_set = rashomon_intersection
        self.y_true = y_true

        self.binary_methods = ["generate_rashomon_set_table","base_model_return","weighted_method_return","base_metric_return", "number_of_classes_return", "set_size_indicator","pareto_front_plot","generate_gauge_for_metrics","plot_venn_diagram","rashomon_ratio_indicator", "pattern_ratio_indicator","lolipop_ambiguity_discrepancy","ambiguity_vs_epsilon", "discrepancy_vs_epsilon",
                                            "rashomon_ratio_vs_epsilon","pattern_rashomon_ratio_vs_epsilon", "rashomon_capacity_distribution","rashomon_capacity_distribution_by_class",
                                            "percent_agreement_barplot","vprs_widths_plot", "vpr_width_histogram", "feature_importance_table", "feature_importance_heatmap",
                                            "agreement_rates_density", "vpr_vs_base_model_plot","proba_probabilities_for_sample", "rashomon_capacity_for_sample", "cohens_kappa_heatmap", "cohens_kappa_diverging_barplot"] 
        self.multiclass_methods =  ["generate_rashomon_set_table","base_model_return","weighted_method_return","base_metric_return", "number_of_classes_return","set_size_indicator","pareto_front_plot", "generate_gauge_for_metrics","plot_venn_diagram","rashomon_ratio_indicator", "pattern_ratio_indicator","lolipop_ambiguity_discrepancy","ambiguity_vs_epsilon", "discrepancy_vs_epsilon",
                                            "rashomon_ratio_vs_epsilon","pattern_rashomon_ratio_vs_epsilon", "rashomon_capacity_distribution","rashomon_capacity_distribution_by_class",
                                            "percent_agreement_barplot", "feature_importance_table", "feature_importance_heatmap",
                                            "agreement_rates_density","proba_probabilities_for_sample", "rashomon_capacity_for_sample", "cohens_kappa_heatmap", "cohens_kappa_diverging_barplot"]
        
    #override 
    def base_metric_return(self)->Tuple[go.Figure, str]:
        '''Overrides the base_metric_return method from Visualiser by returning both evaluation metrics from the RashomonIntersection object'''
        return go.Figure(), self.rashomon_set.metrics
    
    def weighted_method_return(self)->Tuple[go.Figure, str]:
        '''Returns the name of the selected weighted_sum_method from the RashomonIntersection and an empty plot'''
        return go.Figure(), self.rashomon_set.weighted_sum_method
    
    #override
    def set_size_indicator(self)->Tuple[go.Figure, str]:
        '''Overrides the set_size_indicator method from Visualiser by returning the gauge plot with the size of the RashomonIntersection'''
        rashomon_size = len(self.rashomon_set.rashomon_set)
        all_models_num = len(self.rashomon_set.leaderboard)
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = rashomon_size,
            number = {'font': {'size': 40, 'color': '#6B7F8A'}},
            title =dict(text = 'Number of models in the Rashomon Intersection',
                        font = plot_title_font),
            gauge = {
                'axis': {'range': [0, all_models_num], 'dtick': 5, 'tickfont': {'color': '#6B7F8A'}},
                'bar': {'color': chart_colors_v2[6]},
                'steps': [
                    {'range': [0, all_models_num], 'color': "#ebebeb"},
                ],
            }
        ))

        return fig, "The gauge plot represents how many models from the leaderboard were included in the Rashomon Intersection for the given parameters."
    

    #override
    def ambiguity_vs_epsilon(self)-> Tuple[go.Figure, str]:
        '''
            Method for creating a plot representing possible ambiguity values for different epsilon paramaters and it's description.
            
            Returns:
                Tuple[go.Figure, str]
                - plot
                - plot description
        '''
        epsilons = np.linspace(0, 1, 100)
        valid_epsilons = [eps for eps in epsilons if len(self.rashomon_set.get_rashomon_set(eps))>1]

        def compute_ambiguity(epsilon):
            rs = RashomonIntersection(self.rashomon_set.leaderboard, self.rashomon_set.predictions_dict, self.rashomon_set.proba_predictions_dict, self.rashomon_set.feature_importance_dict, self.rashomon_set.metrics, epsilon, self.rashomon_set.custom_weights, self.rashomon_set.weighted_sum_method)
            if rs.task_type=='binary':
                return rs.binary_ambiguity()
            elif rs.task_type=='multiclass':
                return rs.multiclass_ambiguity()
            else:
                raise ValueError("Unknown task type for the Rashomon Set")
            
        ambiguity_vals = [compute_ambiguity(eps) for eps in valid_epsilons]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x = valid_epsilons, 
            y = ambiguity_vals, 
            mode='markers+lines',
            marker = dict(color=chart_colors_v2[11], size=2),
            line=dict(color=chart_colors_v2[11], width=2),
            text=[f'Epsilon: {x:.2f}<br>Ambiguity: {y:.2f}' for x, y in zip(valid_epsilons, ambiguity_vals)],
            hoverinfo='text',
            showlegend=False
        ))

        if self.rashomon_set.task_type=='binary':
            real_ambiguity = self.rashomon_set.binary_ambiguity()
        elif self.rashomon_set.task_type=='multiclass':
            real_ambiguity = self.rashomon_set.multiclass_ambiguity()

        fig.add_trace(go.Scatter(
            x=[self.rashomon_set.epsilon],
            y=[real_ambiguity],
            mode='markers',
            marker=dict(color=contrast_colors[0], size=5),
            text = [f'Epsilon: {self.rashomon_set.epsilon:.2f} <br> Ambiguity : {real_ambiguity:.2f}'],
            hoverinfo="text",
            name = "Ambiguity for the given Rashomon Set"
        ))
        step = max(1, len(valid_epsilons)//10)
        tickvals = [round(e, 2) for e in valid_epsilons[::step]]

        tickfont_combined = {**plot_axis_font, "size": 9}
        fig.update_layout(
            title = dict(text = 'Ambiguity vs Epsilon values',
                        font = plot_title_font,
                        x=0.5, 
                        xanchor='center'),
            height=400, 
            width = 600,
            xaxis = dict(title=dict(
                            text="Epsilon",
                            font=plot_axis_font),
                         showgrid=False, 
                         tickmode='array', 
                         tickvals = tickvals, 
                         tickangle=45, 
                         tickfont=tickfont_combined),
            yaxis=dict(title=dict(
                            text="Ambiguity",
                            font=plot_axis_font),
                       range = [0,1.05], 
                       showgrid=False, 
                       tickfont=tickfont_combined),
            margin= dict(l=70, r = 40, t = 60, b = 60),
            legend=dict(
                font=dict(size=9),
                x=1,             
                y=0,             
                xanchor='right',
                yanchor='bottom',
                orientation='v',
                bgcolor="rgba(0,0,0,0)"
            ))
        
        descr= """
            The plot shows how Ambiguity changes with epsilon values. The highlighted point is the Ambiguity calculated for the given Rashomon Set. 
        """

        return fig, descr
    

    #override
    def discrepancy_vs_epsilon(self)-> Tuple[go.Figure, str]:
        '''
            Method for creating a plot representing possible discrepancy values for different epsilon paramaters. 
            
            Returns:
                Tuple[go.Figure, str]
                - plot
                - plot description
        '''

        epsilons = np.linspace(0, 1, 100)
        valid_epsilons = [eps for eps in epsilons if len(self.rashomon_set.get_rashomon_set(eps))>1]

        def compute_discrepancy(epsilon):
            rs =RashomonIntersection(self.rashomon_set.leaderboard, self.rashomon_set.predictions_dict, self.rashomon_set.proba_predictions_dict, self.rashomon_set.feature_importance_dict, self.rashomon_set.metrics, epsilon, self.rashomon_set.custom_weights, self.rashomon_set.weighted_sum_method)
            if rs.task_type=='binary':
                return rs.binary_discrepancy()
            elif rs.task_type=='multiclass':
                return rs.multiclass_discrepancy()
            else:
                raise ValueError("Unknown task type for the Rashomon Set")
            
        discrepancy_vals = [compute_discrepancy(eps) for eps in valid_epsilons]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x = valid_epsilons, 
            y = discrepancy_vals, 
            mode='markers+lines',
            marker = dict(color=chart_colors_v2[11], size=2),
            line=dict(color=chart_colors_v2[11], width=2),
            text=[f'Epsilon: {x:.2f}<br>Discrepancy: {y:.2f}' for x, y in zip(valid_epsilons, discrepancy_vals)],
            hoverinfo='text',
            showlegend=False
        ))

        if self.rashomon_set.task_type=='binary':
            real_dicrepancy = self.rashomon_set.binary_discrepancy()
        elif self.rashomon_set.task_type=='multiclass':
            real_dicrepancy = self.rashomon_set.multiclass_discrepancy()

        fig.add_trace(go.Scatter(
            x=[self.rashomon_set.epsilon],
            y=[real_dicrepancy],
            mode='markers',
            marker=dict(color=contrast_colors[0], size=5),
            text = [f'Epsilon: {self.rashomon_set.epsilon:.2f} <br> Discrepancy : {real_dicrepancy:.2f}'],
            hoverinfo="text",
            name = "Discrepancy for the given Rashomon Set"
        ))
        step = max(1, len(valid_epsilons)//10)
        tickvals = [round(e, 2) for e in valid_epsilons[::step]]

        tickfont_combined = {**plot_axis_font, "size": 9}
        fig.update_layout(
            title = dict(text = 'Discrepancy vs Epsilon values',
                        font = plot_title_font,
                        x=0.5, 
                        xanchor='center'),
            height=400, 
            width = 600,
            xaxis = dict(title=dict(
                            text="Epsilon",
                            font=plot_axis_font),
                         showgrid=False, 
                         tickmode='array', 
                         tickvals = tickvals, 
                         tickangle=45, 
                         tickfont=tickfont_combined),
            yaxis=dict(title=dict(
                            text="Discrepancy",
                            font=plot_axis_font),
                       range = [0,1.05], 
                       showgrid=False, 
                       tickfont=tickfont_combined),
            margin= dict(l=70, r = 40, t = 60, b = 60),
            #legend in the bottom right corner
            legend=dict(
                font=dict(size=9),
                x=1,             
                y=0,             
                xanchor='right',
                yanchor='bottom',
                orientation='v',
                bgcolor="rgba(0,0,0,0)"
            ))
        
        descr= """
            The plot shows how Discrepancy changes with epsilon values. The highlighted point is the Discrepancy calculated for the given Rashomon Set. 
        """

        return fig, descr
    
    #override
    def proba_ambiguity_vs_epsilon(self, delta : float)-> Tuple[go.Figure, str]:
        '''
            Method for creating a plot representing possible Probabilistic Ambiguity values for different epsilon paramaters and it's description.
            
            Returns:
                Tuple[go.Figure, str]
                - plot
                - plot description
        '''
        epsilons = np.linspace(0, 1, 100)
        valid_epsilons = [eps for eps in epsilons if len(self.rashomon_set.get_rashomon_set(eps))>1]

        def compute_proba_ambiguity(epsilon, delta):
            rs =RashomonIntersection(self.rashomon_set.leaderboard, self.rashomon_set.predictions_dict, self.rashomon_set.proba_predictions_dict, self.rashomon_set.feature_importance_dict, self.rashomon_set.metrics, epsilon, self.rashomon_set.custom_weights, self.rashomon_set.weighted_sum_method)
            if rs.task_type=='binary':
                return rs.probabilistic_abiguity(delta)
            else:
                raise ValueError("Probabilistic Ambiguity cannot be applied to multiclass classification task.")
            
        ambiguity_vals = [compute_proba_ambiguity(eps, delta) for eps in valid_epsilons]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x = valid_epsilons, 
            y = ambiguity_vals, 
            mode='markers+lines',
            marker = dict(color=chart_colors_v2[11], size=2),
            line=dict(color=chart_colors_v2[11], width=2),
            text=[f'Epsilon: {x:.2f}<br>Probabilistic Ambiguity: {y:.2f}' for x, y in zip(valid_epsilons, ambiguity_vals)],
            hoverinfo='text',
            showlegend=False
        ))

        if self.rashomon_set.task_type=='binary':
            real_ambiguity = self.rashomon_set.probabilistic_abiguity(delta)
        else:
            raise ValueError("Probabilistic Ambiguity cannot be applied to multiclass classification task.")
            

        fig.add_trace(go.Scatter(
            x=[self.rashomon_set.epsilon],
            y=[real_ambiguity],
            mode='markers',
            marker=dict(color=contrast_colors[0], size=5),
            text = [f'Epsilon: {self.rashomon_set.epsilon:.2f} <br> Probabilistic Ambiguity : {real_ambiguity:.2f}'],
            hoverinfo="text",
            name = "Probabilistic Ambiguity for the given Rashomon Set"
        ))
        step = max(1, len(valid_epsilons)//10)  
        tickvals = [round(e, 2) for e in valid_epsilons[::step]]

        tickfont_combined = {**plot_axis_font, "size": 9}
        fig.update_layout(
            title = dict(text = f'Probabilistic Ambiguity (delta = {delta}) vs Epsilon values',
                        font = plot_title_font,
                        x=0.5, 
                        xanchor='center'),
            height=400, 
            width = 600,
            xaxis = dict(title=dict(
                            text="Epsilon",
                            font=plot_axis_font),
                         showgrid=False, 
                         tickmode='array', 
                         tickvals = tickvals, 
                         tickangle=45, 
                         tickfont=tickfont_combined),
            yaxis=dict(title=dict(
                            text="Probabilistic Ambiguity",
                            font=plot_axis_font),
                       range = [0,1.05], 
                       showgrid=False, 
                       tickfont=tickfont_combined),
            margin= dict(l=70, r = 40, t = 60, b = 60),
            legend=dict(
                font=dict(size=9),
                x=1,             
                y=0,             
                xanchor='right',
                yanchor='bottom',
                orientation='v',
                bgcolor="rgba(0,0,0,0)"
            ))
        
        descr= """
            The plot shows how Probabilistic Ambiguity changes with epsilon values. The highlighted point is the Probabilistic Ambiguity calculated for the given Rashomon Set. 
        """

        return fig, descr
    
    #override
    def proba_discrepancy_vs_epsilon(self, delta : float)-> Tuple[go.Figure, str]:
        '''
            Method for creating a plot representing possible Probabilistic Discrepancy values for different epsilon paramaters. 
            
            Returns:
                Tuple[go.Figure, str]
                - plot
                - plot description
        '''
        epsilons = np.linspace(0, 1, 100)
        valid_epsilons = [eps for eps in epsilons if len(self.rashomon_set.get_rashomon_set(eps))>1]

        def compute_proba_discrepancy(epsilon, delta):
            rs =RashomonIntersection(self.rashomon_set.leaderboard, self.rashomon_set.predictions_dict, self.rashomon_set.proba_predictions_dict, self.rashomon_set.feature_importance_dict, self.rashomon_set.metrics, epsilon, self.rashomon_set.custom_weights, self.rashomon_set.weighted_sum_method)
            if rs.task_type=='binary':
                return rs.probabilistic_discrepancy(delta)
            else:
                raise ValueError("Probabilistic Discrepancy cannot be applied to multiclass classification task.")
            
        discrepancy_vals = [compute_proba_discrepancy(eps, delta) for eps in valid_epsilons]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x = valid_epsilons, 
            y = discrepancy_vals, 
            mode='markers+lines',
            marker = dict(color=chart_colors_v2[11], size=2),
            line=dict(color=chart_colors_v2[11], width=2),
            text=[f'Epsilon: {x:.2f}<br>Probabilistic Discrepancy: {y:.2f}' for x, y in zip(valid_epsilons, discrepancy_vals)],
            hoverinfo='text',
            showlegend=False
        ))

        if self.rashomon_set.task_type=='binary':
            real_dicrepancy = self.rashomon_set.probabilistic_discrepancy(delta)
        else:
            raise ValueError("Probabilistic Discrepancy cannot be applied to multiclass classification task.")

        fig.add_trace(go.Scatter(
            x=[self.rashomon_set.epsilon],
            y=[real_dicrepancy],
            mode='markers',
            marker=dict(color=contrast_colors[0], size=5),
            text = [f'Epsilon: {self.rashomon_set.epsilon:.2f} <br>Probabilistic Discrepancy : {real_dicrepancy:.2f}'],
            hoverinfo="text",
            name = "Probabilistic Discrepancy for the given Rashomon Set"
        ))
        step = max(1, len(valid_epsilons)//10)  
        tickvals = [round(e, 2) for e in valid_epsilons[::step]]

        tickfont_combined = {**plot_axis_font, "size": 9}
        fig.update_layout(
            title = dict(text = f'Probabilistic Discrepancy (delta = {delta}) vs Epsilon values',
                        font = plot_title_font,
                        x=0.5, 
                        xanchor='center'),
            height=400, 
            width = 600,
            xaxis = dict(title=dict(
                            text="Epsilon",
                            font=plot_axis_font),
                         showgrid=False, 
                         tickmode='array', 
                         tickvals = tickvals, 
                         tickangle=45, 
                         tickfont=tickfont_combined),
            yaxis=dict(title=dict(
                            text="Probabilistic Discrepancy",
                            font=plot_axis_font),
                       range = [0,1.05], 
                       showgrid=False, 
                       tickfont=tickfont_combined),
            margin= dict(l=70, r = 40, t = 60, b = 60),
            #legend in the bottom right corner
            legend=dict(
                font=dict(size=9),
                x=1,             
                y=0,             
                xanchor='right',
                yanchor='bottom',
                orientation='v',
                bgcolor="rgba(0,0,0,0)"
            ))
        
        descr= """
            The plot shows how Probabilistic Discrepancy changes with epsilon values. The highlighted point is the Probabilistic Discrepancy calculated for the given Rashomon Set. 
        """
        return fig, descr
    
    #override
    def rashomon_ratio_vs_epsilon(self) -> Tuple[go.Figure, str]:
        '''
            Method for creating a plot representing possible Rashomon Ratio values for different epsilon paramaters. 
            
            Returns:
                Tuple[go.Figure, str]
                - plot
                - plot description
        '''
        epsilons = np.linspace(0, 1, 100)
        valid_epsilon = [eps for eps in epsilons if len(self.rashomon_set.get_rashomon_set(eps))>1]

        def compute_rashomon_ratio(epsilon):
            rs = RashomonIntersection(self.rashomon_set.leaderboard, self.rashomon_set.predictions_dict, self.rashomon_set.proba_predictions_dict, self.rashomon_set.feature_importance_dict, self.rashomon_set.metrics, epsilon, self.rashomon_set.custom_weights, self.rashomon_set.weighted_sum_method)
            rashomon_ratio = rs.rashomon_ratio()
            return rashomon_ratio
        
        rashomon_ratio_vals = [compute_rashomon_ratio(epsilon=eps) for eps in valid_epsilon]
        real_rashomon_ratio = self.rashomon_set.rashomon_ratio()

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x = valid_epsilon, 
            y = rashomon_ratio_vals, 
            mode='markers+lines',
            marker = dict(color=chart_colors_v2[11], size=2),
            line=dict(color=chart_colors_v2[11], width=2),
            text=[f'Epsilon: {x:.2f}<br>Rashomon Ratio: {y:.2f}' for x, y in zip(valid_epsilon, rashomon_ratio_vals)],
            hoverinfo='text',
            showlegend=False
        ))

        fig.add_trace(go.Scatter(
            x=[self.rashomon_set.epsilon],
            y=[real_rashomon_ratio],
            mode='markers',
            marker=dict(color=contrast_colors[0], size=5),
            text = [f'Epsilon: {self.rashomon_set.epsilon:.2f} <br> Rashomon Ratio : {real_rashomon_ratio:.2f}'],
            hoverinfo="text",
            name = "Rashomon Ratio for the given Rashomon Set."
        ))

        step = max(1, len(valid_epsilon)//10)
        tickvals = [round(e, 2) for e in valid_epsilon[::step]]

        tickfont_combined = {**plot_axis_font, "size": 9}
        fig.update_layout(
            title = dict(text = 'Rashomon Ratio vs Epsilon values',
                        font = plot_title_font,
                        x=0.5, 
                        xanchor='center'),
            height=400, 
            width = 600,
            xaxis = dict(title=dict(
                            text="Epsilon",
                            font=plot_axis_font),
                         showgrid=False, 
                         tickmode='array', 
                         tickvals = tickvals, 
                         tickangle=45, 
                         tickfont=tickfont_combined),
            yaxis=dict(title=dict(
                            text="Rashomon Ratio",
                            font=plot_axis_font),
                       range = [0,1.05], 
                       showgrid=False, 
                       tickfont=tickfont_combined),
            margin= dict(l=70, r = 40, t = 60, b = 60),
            #legend in the bottom right corner
            legend=dict(
                font=dict(size=9),
                x=1,             
                y=0,             
                xanchor='right',
                yanchor='bottom',
                orientation='v'
            ))


        descr= """
                The plot shows how Rashomon Ratio changes with epsilon values. The highlighted point is the Rashomon Ratio calculated for the given Rashomon Set. 
            """
        
        return fig, descr
    

    #override
    def pattern_rashomon_ratio_vs_epsilon(self) -> Tuple[go.Figure, str]:
        '''
            Method for creating a plot representing possible Pattern Rashomon Ratio values for different epsilon paramaters. 
            Returns:
                go.Figure plot 
                plot description : str
        '''
        epsilons = np.linspace(0, 1, 100)
        valid_epsilon = [eps for eps in epsilons if len(self.rashomon_set.get_rashomon_set(eps))>1]

        def compute_pattern_rashomon_ratio(epsilon):
            rs = RashomonIntersection(self.rashomon_set.leaderboard, self.rashomon_set.predictions_dict, self.rashomon_set.proba_predictions_dict, self.rashomon_set.feature_importance_dict, self.rashomon_set.metrics, epsilon, self.rashomon_set.custom_weights, self.rashomon_set.weighted_sum_method)
            return rs.pattern_rashomon_ratio()
        
        pattern_rashomon_ratio_vals = [compute_pattern_rashomon_ratio(epsilon=eps) for eps in valid_epsilon]
        real_pattern_rashomon_ratio = self.rashomon_set.pattern_rashomon_ratio()

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x = valid_epsilon, 
            y = pattern_rashomon_ratio_vals, 
            mode='markers+lines',
            marker = dict(color=chart_colors_v2[11], size=2),
            line=dict(color=chart_colors_v2[11], width=2),
            text=[f'Epsilon: {x:.2f}<br>Pattern Rashomon Ratio: {y:.2f}' for x, y in zip(valid_epsilon, pattern_rashomon_ratio_vals)],
            hoverinfo='text',
            showlegend=False
        ))

        fig.add_trace(go.Scatter(
            x=[self.rashomon_set.epsilon],
            y=[real_pattern_rashomon_ratio],
            mode='markers',
            marker=dict(color=contrast_colors[0], size=5),
            text = [f'Epsilon: {self.rashomon_set.epsilon:.2f} <br> Pattern Rashomon Ratio : {real_pattern_rashomon_ratio:.2f}'],
            hoverinfo="text",
            name = "Pattern Rashomon Ratio for the given Rashomon Set."
        ))

        step = max(1, len(valid_epsilon)//10)
        tickvals = [round(e, 2) for e in valid_epsilon[::step]]

        tickfont_combined = {**plot_axis_font, "size": 9}
        fig.update_layout(
            title = dict(text = 'Pattern Rashomon Ratio vs Epsilon values',
                        font = plot_title_font,
                        x=0.5, 
                        xanchor='center'),
            height=400, 
            width = 600,
            xaxis = dict(title=dict(
                            text="Epsilon",
                            font=plot_axis_font),
                         showgrid=False, 
                         tickmode='array', 
                         tickvals = tickvals, 
                         tickangle=45, 
                         tickfont=tickfont_combined),
            yaxis=dict(title=dict(
                            text="Pattern Rashomon Ratio",
                            font=plot_axis_font),
                       range = [0,1.05], 
                       showgrid=False, 
                       tickfont=tickfont_combined),
            margin= dict(l=70, r = 40, t = 60, b = 60),
            legend=dict(
                font=dict(size=9),
                x=1,             
                y=0,             
                xanchor='right',
                yanchor='bottom',
                orientation='v'
            ))

        descr= """
                The plot shows how Pattern Rashomon Ratio changes with epsilon values. The highlighted point is the Rashomon Ratio calculated for the given Rashomon Set. 
            """
        
        return fig, descr
    
    #override
    def generate_rashomon_set_table(self)-> Tuple[pd.DataFrame, str]:
        '''
            Method for generating the table with Rashomon Intersection models and their base metrics values, as well as a brief text overview of the Rashomon Intersection properties.
            
            Returns:
                Tuple[go.Figure, str]
                - plot
                - plot description
        '''
        leaderboard= self.rashomon_set.leaderboard
        rashomon_set = self.rashomon_set.rashomon_set
        base_model_name = self.rashomon_set.base_model

        filtered_leaderboard = leaderboard.loc[leaderboard['model'].isin(rashomon_set), ['model']+ self.rashomon_set.metrics].reset_index(drop=True).round({metric : 3 for metric in self.rashomon_set.metrics})
        base_row = filtered_leaderboard[filtered_leaderboard['model'] == base_model_name]
        other_rows = filtered_leaderboard[filtered_leaderboard['model'] != base_model_name]
        filtered_leaderboard = pd.concat([base_row, other_rows], ignore_index=True)
        
        filtered_leaderboard.insert(0, "Nr", range(1, len(filtered_leaderboard)+1))
        styled_df = filtered_leaderboard.copy().astype(str)
        
        mask = styled_df["model"] == base_model_name
        styled_df.loc[mask] = styled_df.loc[mask].apply(
            lambda col: col.map(lambda x: f"<b>{x}</b>")
        )

        fig = go.Figure(data = [go.Table(
            columnwidth = [30,200,100],
            header = dict(
                values=list(filtered_leaderboard.columns),
                font=dict(family="Inter, sans-serif", color='darkgray', size=13),
                fill_color='white',
                align='left'
            ),
            cells = dict(values = [styled_df[c] for c in styled_df.columns],
                         align = 'left', fill_color='white', font=dict(family="Inter, sans-serif",color='darkgray', size=12))
        )])

        le, names = self.rashomon_set.find_same_score_as_base()
        if le == 1:
            descr =f"""
                The table shows all models that are included in the Rashomon Intersection for the metrics  : {self.rashomon_set.metrics[0]}, {self.rashomon_set.metrics[1]} and epsilon value : {self.rashomon_set.epsilon:.3f}. The values of the base metrics are rounded to three decimal points. 
                <br>The intersection consists of <strong>{len(self.rashomon_set.rashomon_set)} models </strong>  with <strong>{self.rashomon_set.base_model} </strong>as the base model.
                <br>There is <strong>{le} model</strong>, which achieved the same value of the metrics weighted sum as the base model - {names[0]}
                """
        elif le == 0:
            descr =f"""
                The table shows all models that are included in the Rashomon Intersection for the metrics : {self.rashomon_set.metrics[0]}, {self.rashomon_set.metrics[1]} and epsilon value : {self.rashomon_set.epsilon:.3f}. The values of the base metrics are rounded to three decimal points. 
                <br>The intersection consists of <strong>{len(self.rashomon_set.rashomon_set)} models </strong>  with <strong>{self.rashomon_set.base_model} </strong>as the base model.
                <br>There are <strong>no models</strong>, which achieved the same value of the metrics weighted sum as the base model.
                """
        else:
            descr =f"""
                The table shows all models that are included in the Rashomon Intersection for the metrics : {self.rashomon_set.metrics[0]}, {self.rashomon_set.metrics[1]} and epsilon value : {self.rashomon_set.epsilon:.3f}. The values of the base metrics are rounded to three decimal points. 
                <br>The set consists of <strong>{len(self.rashomon_set.rashomon_set)} models </strong>  with <strong>{self.rashomon_set.base_model} </strong>as the base model.
                <br>There are <strong>{le} models</strong>, which achieved the same value of the metrics weighted sum as the base model - {', '.join(f"{x}" for x in names)}
                """

        return fig, descr
    
    def generate_gauge_for_metrics(self)-> Tuple[go.Figure, str]:
        '''
            Method for generating gauge plots that visualize the proportion of models from each metric-specific Rashomon set that are included in the Rashomon Intersection.

            Returns:
                    Tuple[go.Figure, str]
                    - plot
                    - plot description
        '''

        intersection_metrics = self.rashomon_set.metrics
        intersection_models = self.rashomon_set.rashomon_set
        rashomon_models_metric1 = self.rashomon_set.get_rashomon_set_for_metric(intersection_metrics[0])
        rashomon_models_metric2 = self.rashomon_set.get_rashomon_set_for_metric(intersection_metrics[1])

        rashomon_size_metric1, rashomon_size_metric2 = len(rashomon_models_metric1), len(rashomon_models_metric2)
        models_in_intersection_metric1 = len(set(rashomon_models_metric1) & set(intersection_models))
        models_in_intersection_metric2 = len(set(rashomon_models_metric2) & set(intersection_models))


        fig = make_subplots(
            rows=1, cols=2,
            specs=[[{"type": "indicator"}, {"type": "indicator"}]]
        )

        fig.add_trace(go.Indicator(
            mode='number+gauge',
            value=models_in_intersection_metric1,
            title={"text": f"{intersection_metrics[0]}", "font": plot_title_font},
            number={'font': {'size': 30, 'color': '#6B7F8A'}},
            gauge={
                "axis": {"range": [0, rashomon_size_metric1]},
                "bar": {"color": "#6C929E"},
                "shape": "angular"
            }
        ), row=1, col=1)

        fig.add_trace(go.Indicator(
            mode='number+gauge',
            value=models_in_intersection_metric2,
            title={"text": f"{intersection_metrics[1]}", "font" : plot_title_font},
            number={'font': {'size': 30, 'color': '#6B7F8A'}},
            gauge={
                "axis": {"range": [0, rashomon_size_metric2]},
                "bar": {"color": "#6C929E"},
                "shape": "angular"}
        ), row=1, col=2)
        

        fig.update_layout(
            autosize=True,
            margin=dict(l=50, r=50, t=0, b=0)
        )

        descr = f'''Gauge plots showing how many models from each metric-specific Rashomon set 
        ({intersection_metrics[0]} and {intersection_metrics[1]}) were included in the final Rashomon Intersection.
        The left gauge shows {models_in_intersection_metric1} out of {rashomon_size_metric1} models from {intersection_metrics[0]} Rashomon set,
        and the right gauge shows {models_in_intersection_metric2} out of {rashomon_size_metric2} models from {intersection_metrics[1]} Rashomon set.
        '''

        return fig, descr


    def plot_venn_diagram(self)-> Tuple[go.Figure, str]:
        '''
            Method for visualizing rashomon sets for both metrics as well as the intersection using the Venn diagram. 

            Returns:
                Tuple[go.Figure, str]
                - plot
                - plot description
        '''

        #obtaining sets for both metrics and the intersection
        metrics = self.rashomon_set.metrics
        metric1_set = self.rashomon_set.get_rashomon_set_for_metric(metrics[0])
        metric2_set = self.rashomon_set.get_rashomon_set_for_metric(metrics[1])
        metric1_set = set(metric1_set)
        metric2_set = set(metric2_set)
        intersection = self.rashomon_set.rashomon_set
        set_A = metric1_set - metric2_set
        set_B = metric2_set - metric1_set
        set_AB = set(intersection)
        set_A_str = [str(item) for item in set_A]
        set_B_str = [str(item) for item in set_B]
        set_AB_str = [str(item) for item in set_AB]
        
        circle_radius = 2
        circle_A = {'x': -1, 'y': 0, 'r': 2, 'color': 'rgba(108, 146, 158, 0.3)' }

        circle_B = {'x': 1, 'y': 0, 'r': 2, 'color': 'rgba(85, 129, 177, 0.3)'}
        
        fig = go.Figure()
    
        for circle in [circle_A, circle_B]:
            fig.add_shape(
                type="circle",
                xref="x", yref="y",
                x0=circle['x']-circle['r'], y0=circle['y']-circle['r'],
                x1=circle['x']+circle['r'], y1=circle['y']+circle['r'],
                line=dict(color=circle['color'].replace('0.3', '1'), width=2),
                fillcolor=circle['color']
            )
        
        fig.add_trace(go.Scatter(
            x=[circle_A['x']], y=[circle_A['y'] + circle_radius + 0.3],
            mode="text", text=[f"<b>{metrics[0]}</b>"],
            textposition="middle center",
            textfont=dict(size=14, color='rgba(108, 146, 158, 1)'),
            showlegend=False
        ))
        
        fig.add_trace(go.Scatter(
            x=[circle_B['x']], y=[circle_B['y'] + circle_radius + 0.3],
            mode="text", text=[f"<b>{metrics[1]}</b>"],
            textposition="middle center",
            textfont=dict(size=14, color= 'rgba(85, 129, 177, 1)'),
            showlegend=False
        ))
        
        def add_text_list(x_center, y_center, items, position="left", max_display=15):
            if not items:
                return
            
            if len(self.rashomon_set.leaderboard)>20:
                font_size = 7.5
            else:
                font_size=12
                
            display_items = items[:max_display]
            text = '<br>'.join(display_items)
            if len(items) > max_display:
                text += f'<br>... +{len(items)-max_display} more'
            
            
            if position == "left":
                x_pos = x_center - circle_radius * 0.38
            elif position == "right":
                x_pos = x_center + circle_radius * 0.38 
            else:  # "center"
                x_pos = x_center
                
            fig.add_trace(go.Scatter(
                x=[x_pos], y=[y_center],
                mode="text",
                text=[text],
                textposition="middle center",
                textfont=dict(size=font_size, color='black'),
                showlegend=False
            ))
        
        add_text_list(circle_A['x'], circle_A['y'], set_A_str, position="left")    
        add_text_list(circle_B['x'], circle_B['y'], set_B_str, position="right")   
        add_text_list(0, 0, set_AB_str, position="center")                         
        
        x_range = [-2.5, 2.5]
        y_range = [-2, 2.5]
        
        fig.update_layout(
            xaxis=dict(visible=False, range=x_range),
            yaxis=dict(visible=False, range=y_range),
            plot_bgcolor='white',
            showlegend=False,
            margin=dict(l=0, r=0, b=5, t=40),
            autosize=True,
        )
        
        fig.add_annotation(
            x=0, y=-2.2,
            text=f"{metrics[0]}: {len(set_A)} | {metrics[1]}: {len(set_B)} | Intersection: {len(set_AB)}",
            showarrow=False,
            font=dict(size=12, color='black')
        )

        descr = "The Venn diagram represents models that are included in the separate Rashomon Sets for the given parameters as well as in the Rashomon Intersection."

        return fig, descr
    

    def pareto_front_plot(self)->Tuple[go.Figure, str]:
        '''
            Method for visualizing the Pareto Front created from all models available in the leaderboard as an additional analysis to the RashomonIntersection.
            
            Returns:
                Tuple[go.Figure, str]
                - plot
                - plot description
        '''

        def pareto_front(df, x_col, y_col):
            #data = df.sort_values(by=[x_col, y_col], ascending=[False, False]).reset_index(drop=True)
            pareto_indices =[]
            

            for i in df.index.values: #point that we check
                isDominant = True
                xi = df.loc[i, x_col]
                yi = df.loc[i, y_col]

                for j in df.index.values: #all other points to check dominance
                    if i==j:
                        continue
                    xj = df.loc[j, x_col]
                    yj = df.loc[j, y_col]
                    condition1 = (xj>=xi) and (yj>=yi) #xj is not worse in any metric
                    condition2 = (xj>xi) or (yj>yi) # j is better in at least one metric
                    if condition1 and condition2:
                        isDominant = False #there is a better point j 
                        break
                if isDominant:
                    pareto_indices.append(i)
            return df.loc[pareto_indices]
        

        whole_leaderboard = self.rashomon_set.leaderboard
        
        metric1 = self.rashomon_set.metrics[0]
        metric2 = self.rashomon_set.metrics[1]
        
        agg = whole_leaderboard.groupby([metric1, metric2]).agg(
            count=('model','size'),
            models=('model', lambda x: ', '.join(x))
        ).reset_index()

        front = pareto_front(agg, metric1, metric2)
        
        agg['color'] = chart_colors_v2[6]
        agg.loc[agg.set_index([metric1, metric2]).index.isin(front.set_index([metric1, metric2]).index), 'color'] = contrast_colors[0]
        agg['hover_text'] = agg.apply(lambda row: 
                              f"Number of models: {row['count']}<br>" +
                              "<br>".join([f"- {m}" for m in row['models'].split(', ')] ) +
                              f"<br>{metric1}: {row[metric1]}<br>{metric2}: {row[metric2]}", axis=1)

        normal_points = agg[agg['color'] ==chart_colors_v2[6] ]
        pareto_points = agg[agg['color'] ==contrast_colors[0] ]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x = normal_points[metric1],
            y = normal_points[metric2],
            mode = 'markers',
            marker=dict(
                size=normal_points['count'] , 
                color=chart_colors_v2[6],
                sizemode = "area",
                sizeref = 20 * max(agg['count']) / (40 ** 2),
                sizemin=3
            ),
            text=normal_points['hover_text'],
            hoverinfo='text',
            name = 'Other models'

                ))
        
        fig.add_trace(go.Scatter(
            x = pareto_points[metric1],
            y = pareto_points[metric2],
            mode = 'markers',
            marker=dict(
                size=pareto_points['count'],  
                color=contrast_colors[0] ,
                sizemode = "area",
                sizeref = 20 * max(agg['count']) / (40 ** 2),
                sizemin=3
            ),
            text=pareto_points['hover_text'],
            hoverinfo='text',
            name = 'Pareto Front'

                ))
        
        
        tickfont_combined = {**plot_axis_font, "size": 9}
        fig.update_layout(
            title = dict(text = 'All models from the leaderboard',
                        font = plot_title_font),
            xaxis = dict(title=dict(
                            text=f"{metric1}",
                            font=plot_axis_font),
                         tickfont=tickfont_combined),
            yaxis=dict(title=dict(
                            text=f"{metric2}",
                            font=plot_axis_font),
                       tickfont=tickfont_combined,
                       gridcolor = "#D3D3D3"),
            legend=dict(
                font=plot_axis_font,
                itemsizing='constant'
            )
        )

        

        pareto_leaderboard = pareto_front(whole_leaderboard, metric1, metric2)
        pareto_models = pareto_leaderboard['model'].tolist()

        return fig, f"The plot illustrates all models present in the <strong>leaderboard</strong> and their scores for both evaluation metrics. The highlighted points belong to the Pareto Front, meaning that for each of these models, there is no other model that simultaneously achieves better scores in all evaluation metrics. At least one metric is superior compared to other models.<br> Models in the Pareto Front: <br>  {', '.join(pareto_models)}"