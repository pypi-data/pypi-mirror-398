import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from rashomon_analysis.rashomon_set import *
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

plot_title_font = dict(
    color="#6B7F8A",
    family="Inter, Segoe UI, sans-serif",  
    size=16,
    style="normal",
    weight=400            
)

plot_axis_font = dict(
    color="#6B7F8A",
    family="Inter, Segoe UI, sans-serif"
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


class Visualizer:
    '''
        Class for generating plots and statistics using the Rashomon Set metrics.

        Arguments:
            rashomon_set : Rashomon Set object to be analyzed.
            y_true : target column from the test dataset.

        Attributes:
            rashomon_set : passed Rashomon Set object
            y_true : passed y_true object
            binary_methods : plots which can be generated for binary classification task type
            multiclass_methods : plots which can be generated for multiclass classification task type
            
    '''

    def __init__(self, rashomon_set : RashomonSet, y_true : pd.DataFrame):

        self.rashomon_set = rashomon_set
        self.y_true = y_true

        self.binary_methods = ["base_model_return","base_model_score_return","base_metric_return", "number_of_classes_return", "set_size_indicator","generate_rashomon_set_table", "rashomon_ratio_indicator", "pattern_ratio_indicator","lolipop_ambiguity_discrepancy","ambiguity_vs_epsilon", 
                               "discrepancy_vs_epsilon", "rashomon_ratio_vs_epsilon",
                               "pattern_rashomon_ratio_vs_epsilon", "rashomon_capacity_distribution","rashomon_capacity_distribution_by_class",
                                "percent_agreement_barplot","vprs_widths_plot", "vpr_width_histogram", "feature_importance_table", "feature_importance_heatmap",
                                "agreement_rates_density", "vpr_vs_base_model_plot","proba_probabilities_for_sample","rashomon_capacity_for_sample", "cohens_kappa_heatmap", "cohens_kappa_diverging_barplot"] 
        self.multiclass_methods=  ["base_model_return","base_model_score_return","base_metric_return", "number_of_classes_return", "set_size_indicator","generate_rashomon_set_table",  "rashomon_ratio_indicator", "pattern_ratio_indicator","lolipop_ambiguity_discrepancy","ambiguity_vs_epsilon", "discrepancy_vs_epsilon",
                                            "rashomon_ratio_vs_epsilon","pattern_rashomon_ratio_vs_epsilon", "rashomon_capacity_distribution","rashomon_capacity_distribution_by_class",
                                            "percent_agreement_barplot", "feature_importance_table", "feature_importance_heatmap",
                                            "agreement_rates_density","proba_probabilities_for_sample", "rashomon_capacity_for_sample", "cohens_kappa_heatmap", "cohens_kappa_diverging_barplot"]
    
    def base_model_return(self)->Tuple[go.Figure, str]:
        '''Returns the base model's name and an empty plot'''
        return go.Figure(), self.rashomon_set.base_model
    
    def base_model_score_return(self)-> Tuple[go.Figure, str]: 
        '''Returns the base model's score and an empty plot'''
        return go.Figure(), self.rashomon_set.best_score
    
    def base_metric_return(self)->Tuple[go.Figure, str]:
        '''Returns the base evaluation metric and an empty plot'''
        return go.Figure(), self.rashomon_set.base_metric
    
    def number_of_classes_return(self)->Tuple[go.Figure, str]:
        '''Returns the number of classes and an empty plot'''
        return go.Figure(), str(self.rashomon_set.determine_number_of_classes())
    
    def set_size_indicator(self)->Tuple[go.Figure, str]:
        '''
            Creates the gauge plot illustrating the number of models in the Rashomon Set vs all available models.

            Returns:
                Tuple[go.Figure, str]
                - plot
                - plot description
        '''
        rashomon_size = len(self.rashomon_set.rashomon_set)
        all_models_num = len(self.rashomon_set.leaderboard)
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = rashomon_size,
            number = {'font': {'size': 40, 'color': '#6B7F8A'}},
            title =dict(text = 'Number of models in the Rashomon Set',
                        font = plot_title_font),
            gauge = {
                'axis': {'range': [0, all_models_num], 'dtick': 5, 'tickfont': {'color': '#6B7F8A'}},
                'bar': {'color': chart_colors_v2[6]},
                'steps': [
                    {'range': [0, all_models_num], 'color': "#ebebeb"},
                ],
            }
        ))
        
        return fig, "The gauge plot represents how many models from the leaderboard were included in the Rashomon Set for the given parameters."

    
    def rashomon_ratio_indicator(self) -> Tuple[go.Figure, str]:
        '''
            Creates the Rashomon Ratio indicator plot and it's description.

            Returns:
                Tuple[go.Figure, str]
                - plot
                - plot description
        '''
        rashomon_ratio = self.rashomon_set.rashomon_ratio()
        
        fig = go.Figure(go.Indicator(
            mode="number+gauge",
            value=rashomon_ratio,
            gauge={"shape": "bullet", "axis": {"range": [0, 1]}, "bar": {"color": chart_colors_v2[4]}}

        ))

        fig.update_layout(
            title=dict(
                text="Rashomon Ratio",
                font=plot_title_font),
            xaxis=dict(
                tickfont=plot_axis_font,
                automargin=True,
            ),
            yaxis=dict(
                tickfont=plot_axis_font,
                automargin=True,
            )
        )
        
        descr = f'''
        <strong>Rashomon Ratio</strong> shows what portion of all models are included in the Rashomon Set. 
        Currently, {round(rashomon_ratio*100, 3)}% of the AutoML models are part of the Rashomon Set.
        '''
        
        return fig, descr


    def pattern_ratio_indicator(self) -> Tuple[go.Figure, str]:
        '''
            Creates the Rashomon Pattern Ratio indicator plot and it's description.

            Returns:
                Tuple[go.Figure, str]
                - plot
                - plot description
        '''
        rashomon_pattern_ratio = self.rashomon_set.pattern_rashomon_ratio()
        
        fig = go.Figure(go.Indicator(
            mode="number+gauge",
            value=rashomon_pattern_ratio,
            gauge={"shape": "bullet", "axis": {"range": [0, 1]}, "bar": {"color": chart_colors_v2[4]}}
        ))
        
        fig.update_layout(
            title=dict(
                text="Pattern Rashomon Ratio",
                font=plot_title_font),
            xaxis=dict(
                tickfont=plot_axis_font,
                automargin=True,
            ),
            yaxis=dict(
                tickfont=plot_axis_font,
                automargin=True,
            )
        )
        
        descr = f'''
        <strong>Pattern Rashomon Ratio</strong> represents the fraction of unique prediction patterns that appear in the Rashomon Set. 
        That is, {round(rashomon_pattern_ratio*100, 3)}% of all observed prediction patterns are covered by models within the Rashomon Set.
        '''
        return fig, descr
    

    def lolipop_ambiguity_discrepancy(self)-> Tuple[go.Figure, str]:
        '''
            Method for creating a lolipop plot illustrating the values of ambiguity and discrepancy calculated for the Rashomon Set. 

            Returns:
                Tuple[go.Figure, str]
                - plot
                - plot description
        '''
        metrics = ['Ambiguity', 'Discrepancy']

        if self.rashomon_set.task_type =='binary':
            values = [self.rashomon_set.binary_ambiguity(), self.rashomon_set.binary_discrepancy()]
        elif self.rashomon_set.task_type=='multiclass':
            values = [self.rashomon_set.multiclass_ambiguity(), self.rashomon_set.multiclass_discrepancy()]
        else:
            raise ValueError("Unknown task type in the given Rashomon Set object")
        
        shapes =[]
        for xi, metric in zip(values, metrics):
            shapes.append(
                dict(
                    type='line',
                    x0 = metric, #start point
                    x1 = metric, #end point
                    y0 = 0, #start point
                    y1 = xi, #end point
                    line =dict(color=chart_colors_v2[10], width =1)
                    )
            )
        points = go.Scatter(
            x = metrics, 
            y= values, 
            mode = "markers",
            marker = dict(size=7, color=chart_colors_v2[10]),
            hoverinfo="text",
            hovertext=[f"{metric}: {v:.2f}" for metric, v in zip(metrics, values)]
        )

        fig = go.Figure(data = [points])

        fig.update_layout(
            title =dict(text = 'Ambiguity and Discrepancy values',
                        font=plot_title_font,
                        x=0.5, 
                        xanchor='center'),
            height=300,
            width=300,
            shapes=shapes,
            xaxis = dict(title=dict(
                            text="",
                            font=plot_axis_font),
                         showgrid=False, 
                         showline = True, 
                         tickfont = plot_axis_font),
            yaxis=dict(title=dict(
                        text='Metric value',
                        font={**plot_axis_font}),
                       range = [0,1.05], 
                       tickvals = [0,1], 
                       showgrid=False, 
                       showline=True, 
                       title_standoff=10, 
                       tickfont = plot_axis_font),
            margin= dict(l=70, r = 50, t = 40, b = 40)
        )

        fig.update_yaxes(
            tickvals =[0,0.5, 1],
            ticks='outside',
            ticklen=10,
            tickcolor='black'
        )

        descr = f"The lolipop chart represents the calculated values of {self.rashomon_set.task_type} ambiguity and discrepancy for the given Rashomon Set."
        return fig, descr
    
    def lolipop_ambiguity_discrepancy_proba_version(self, delta:float)-> Tuple[go.Figure, str]:
        '''
            Method for creating a lolipop plot illustrating the values of ambiguity and discrepancy calculated for the Rashomon Set. 

            Returns:
                Tuple[go.Figure, str]
                - plot
                - plot description
        '''
        metrics = ['Proba Ambiguity', 'Proba Discrepancy']

        if delta<0 or delta>1:
            raise ValueError(f"Delta argument must be between 0 and 1, received {delta}")
        if self.rashomon_set.task_type =='binary':
            values = [self.rashomon_set.probabilistic_abiguity(delta), self.rashomon_set.probabilistic_discrepancy(delta)]
        else:
            raise ValueError('Cannot calculate probabilistic metrics for task types other than binary')
        
        shapes =[]
        for xi, metric in zip(values, metrics):
            shapes.append(
                dict(
                    type='line',
                    x0 = metric, #start point
                    x1 = metric, #end point
                    y0 = 0, #start point
                    y1 = xi, #end point
                    line =dict(color=chart_colors_v2[10], width =1)
                    )
            )
        points = go.Scatter(
            x = metrics, 
            y= values, 
            mode = "markers",
            marker = dict(size=7, color=chart_colors_v2[10]),
            hoverinfo="text",
            hovertext=[f"{metric}: {v:.2f}" for metric, v in zip(metrics, values)]
        )

        fig = go.Figure(data = [points])

        fig.update_layout(
            title =dict(text = f'Ambiguity and Discrepancy values for delta : {delta:.2f}',
                        font = plot_title_font,
                        x=0.5, 
                        xanchor='center'),
            height=300,
            width=400,
            shapes=shapes,
            xaxis = dict(title=dict(
                            text="",
                            font=plot_axis_font),
                         showgrid=False, 
                         showline = True, 
                         tickfont = plot_axis_font),
            yaxis=dict(title=dict(
                        text='Metric value',
                        font={**plot_axis_font}),
                       range = [0,1.05], 
                       tickvals = [0,1], 
                       showgrid=False, 
                       showline=True, 
                       title_standoff=10, 
                       tickfont = plot_axis_font),
            margin= dict(l=70, r = 50, t = 40, b = 40)
        )

        fig.update_yaxes(
            tickvals =[0,0.5, 1],
            ticks='outside',
            ticklen=10,
            tickcolor='black'
        )

        descr = f"""
        The lolipop chart represents the calculated values of probabilistic ambiguity and discrepancy based on the delta parameter passed as an argument. (delta = {delta})
        """
        return fig, descr
    

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
            rs = RashomonSet(self.rashomon_set.leaderboard, self.rashomon_set.predictions_dict, self.rashomon_set.proba_predictions_dict, self.rashomon_set.feature_importance_dict, self.rashomon_set.base_metric, epsilon)
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
            rs = RashomonSet(self.rashomon_set.leaderboard, self.rashomon_set.predictions_dict, self.rashomon_set.proba_predictions_dict, self.rashomon_set.feature_importance_dict, self.rashomon_set.base_metric, epsilon)
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
                y=-0.03,             
                xanchor='right',
                yanchor='bottom',
                orientation='v',
                bgcolor="rgba(0,0,0,0)"
            ))
        
        descr= """
            The plot shows how Discrepancy changes with epsilon values. The highlighted point is the Discrepancy calculated for the given Rashomon Set. 
        """

        return fig, descr
    
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
            rs = RashomonSet(self.rashomon_set.leaderboard, self.rashomon_set.predictions_dict, self.rashomon_set.proba_predictions_dict, self.rashomon_set.feature_importance_dict, self.rashomon_set.base_metric, epsilon)
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
            rs = RashomonSet(self.rashomon_set.leaderboard, self.rashomon_set.predictions_dict, self.rashomon_set.proba_predictions_dict, self.rashomon_set.feature_importance_dict, self.rashomon_set.base_metric, epsilon)
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
            rs = RashomonSet(self.rashomon_set.leaderboard, self.rashomon_set.predictions_dict, self.rashomon_set.proba_predictions_dict, self.rashomon_set.feature_importance_dict, self.rashomon_set.base_metric, epsilon)
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
                x=0.98,             
                y=0.02,             
                xanchor='right',
                yanchor='bottom',
                orientation='v'
            ))


        descr= """
                The plot shows how Rashomon Ratio changes with epsilon values. The highlighted point is the Rashomon Ratio calculated for the given Rashomon Set. 
            """
        
        return fig, descr
    
    
    def pattern_rashomon_ratio_vs_epsilon(self) -> Tuple[go.Figure, str]:
        '''
            Method for creating a plot representing possible Pattern Rashomon Ratio values for different epsilon paramaters. 
            
            Returns:
                Tuple[go.Figure, str]
                - plot
                - plot description
        '''
        epsilons = np.linspace(0, 1, 100)
        valid_epsilon = [eps for eps in epsilons if len(self.rashomon_set.get_rashomon_set(eps))>1]

        def compute_pattern_rashomon_ratio(epsilon):
            rs = RashomonSet(self.rashomon_set.leaderboard, self.rashomon_set.predictions_dict, self.rashomon_set.proba_predictions_dict, self.rashomon_set.feature_importance_dict, self.rashomon_set.base_metric, epsilon)
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
                x=0.98,             
                y=0.02,              
                xanchor='right',
                yanchor='bottom',
                orientation='v'
            ))

        descr= """
                The plot shows how Pattern Rashomon Ratio changes with epsilon values. The highlighted point is the Pattern Rashomon Ratio calculated for the given Rashomon Set. 
            """
        
        return fig, descr
    

    def proba_probabilities_for_sample(self, sample_index: int) -> Tuple[go.Figure, str]:
        '''
            Method for plotting predicted probabilities for a given sample across all models in the Rashomon Set.

            Args:
                sample_index : index of the sample for which predictions are to be plotted

            Returns:
                Tuple[go.Figure, str]
                - plot
                - plot description
        '''

        labels = self.rashomon_set.rashomon_proba_predictions[next(iter(self.rashomon_set.rashomon_proba_predictions))].columns.tolist()
        sample_predictions = {model: predictions.loc[sample_index].values for model, predictions in self.rashomon_set.rashomon_proba_predictions.items()}
        sample_predictions_df = pd.DataFrame(sample_predictions).T # no need for normalization, plotting probabilities

        sample_predictions_df.reset_index(inplace=True)
        sample_predictions_df.columns = ['Model'] + labels


        colors = class_colors
        if len(labels)<=10:
            fig = go.Figure()
            left = np.zeros(len(sample_predictions_df))
            for i, label in enumerate(labels):
                hover_text = [f"Class label {label}: Proba probability = {v:.2f}" for v in sample_predictions_df[label]] #in hover proba predictions rounded to 2 decimal places
                fig.add_trace(go.Bar(
                    y = sample_predictions_df['Model'],
                    x = sample_predictions_df[label].values,
                    name = label, 
                    orientation='h',
                    marker=dict(color=colors[i]),
                    base = left,
                    hovertext = hover_text,
                    hoverinfo = 'text'
                ))
                left += sample_predictions_df[label].values

            tickfont_combined = {**plot_axis_font, "size": 9}
            fig.update_layout(
                barmode='stack',
                autosize=True,
                title=dict(text=f'Predicted probabilities for sample {sample_index} across all models in Rashomon set',
                           font = plot_title_font),
                xaxis = dict(title=dict(
                            text="Predicted probabilities",
                            font=plot_axis_font),
                            automargin=True),
                yaxis=dict(
                    automargin=True,
                    tickfont = tickfont_combined
                ),
                legend=dict(title=dict(
                            text="Class",
                            font=plot_axis_font),
                            font = plot_axis_font)
                )
        else:
            fig = px.imshow(
                sample_predictions_df.set_index('Model')[labels],
                labels=dict(x="Class", y="Model", color="Probability"),
                aspect="auto",
                color_continuous_scale='Blues')
            fig.update_layout(
                title=dict(text=f'Predicted probabilities for sample {sample_index} across all models',
                           font = plot_title_font),
                xaxis=dict(
                    automargin=True,
                    tickfont = tickfont_combined
                ),
                yaxis=dict(
                    automargin=True,
                    tickfont = tickfont_combined
                ),
                plot_bgcolor='white'
            )
        
        descr = f'''
        Predicted probabilities for sample {sample_index} across all models present in the Rashomon Set. 
        The sizes of the segments indicate how confident each model is in predicting each class.
        '''

        return fig, descr
    
    def rashomon_capacity_for_sample(self, sample_index: int) -> Tuple[go.Figure, str]:
        '''
            Method to visualize Rashomon Capacity metric for a given sample. Metric value is presented on horizontal axis in range [1, number of classes].

            Returns:
                Tuple[go.Figure, str]
                - plot
                - plot description
        '''

        n_classes = self.rashomon_set.determine_number_of_classes()  
        capacity = self.rashomon_set.rashomon_capacity(sample_index=sample_index)

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=[1, n_classes],
            y=[0, 0],
            mode='lines',
            line=dict(color=chart_colors_v2[10], width=2),
            showlegend=False,
            hoverinfo='skip'
        ))

        fig.add_trace(go.Scatter(
            x=[1, n_classes],
            y=[0, 0],
            mode='markers',
            line=dict(color=chart_colors_v2[10], width=2),
            showlegend=False,
            hoverinfo='skip'
        ))
        fig.add_trace(go.Scatter(
            x = [capacity],
            y = [0],
            mode='markers',
            marker=dict(color=contrast_colors[0], size=8),
            name='Rashomon Capacity',
            hovertemplate=f'Rashomon Capacity = {capacity:.2f}<extra></extra>'
        ))

        margin = 0.1
        tickfont_combined = {**plot_axis_font, "size": 11}
        fig.update_layout(
            title=dict(text = f'Rashomon Capacity for sample {sample_index}',
                        font = plot_title_font),
            xaxis=dict(title=dict(
                            text="Capacity",
                            font=plot_axis_font),
                       range=[1 - margin, n_classes + margin], 
                       dtick=1,
                       tickfont = tickfont_combined),
            yaxis=dict(visible=False,
                       tickfont = tickfont_combined), 
            legend=dict(font = plot_axis_font),
            height=200,
            width=600
        )

        descr = f"""
            The plot shows Rashomon Capacity value calculated for sample {sample_index}.
        """

        return fig, descr
    
    def rashomon_capacity_distribution(self) -> Tuple[go.Figure, str]:
        '''
            Method for creating a plot representing distribution of Rashomon Capacity metric across all samples in dataset. 

            Returns:
                Tuple[go.Figure, str]
                - plot
                - plot description
        '''
        n_samples = self.rashomon_set.determine_number_of_samples()
        n_classes = self.rashomon_set.determine_number_of_classes()  
        capacity_values = [self.rashomon_set.rashomon_capacity(i) for i in range(n_samples)]

        iqr = np.percentile(capacity_values, 75) - np.percentile(capacity_values, 25)
        bin_width = 2 * iqr / (len(capacity_values) ** (1/3))
        if bin_width > 0:
            nbins = int(np.ceil((max(capacity_values) - min(capacity_values)) / bin_width))
        else:
            nbins = 10

        fig = px.histogram(
            x = capacity_values,
            title="Distribution of Rashomon Capacity",
            labels={'x': 'Rashomon Capacity', 'y': 'Count'},
            nbins = nbins,
            color_discrete_sequence=[chart_colors_v2[6]]
        )

        fig.update_traces(
         marker=dict(line=dict(color='#184B57', width=1))  
        )

        tickfont_combined = {**plot_axis_font, "size": 11}
        fig.update_layout(
            title=dict(text = 'Distribution of Rashomon Capacity',
                        font = plot_title_font),
            xaxis=dict(title=dict(
                            text="Capacity",
                            font=plot_axis_font),
                       tickfont = tickfont_combined),
            yaxis=dict(title=dict(
                            text="Count",
                            font=plot_axis_font),
                       tickfont = tickfont_combined,
                       gridcolor = "#D3D3D3"),
            height=400,
            width=600,
        )

        mean_value = round(np.mean(capacity_values),2)
        std_value = round(np.std(capacity_values),2)
        min_value = round(np.min(capacity_values),2)
        max_value = round(np.max(capacity_values),2)

        descr = f"""
            The plot shows the distribution of Rashomon Capacity values across all samples in dataset. The number of bins was determined using the Freedman-Diaconis rule.
            <br>
            <strong>Rashomon Capacity summary</strong> — Mean: {mean_value:.2f}, Std: {std_value:.2f}, Min: {min_value:.2f}, Max: {max_value:.2f}.
            </br>
        """

        return fig, descr
    

    def rashomon_capacity_distribution_by_class(self) -> Tuple[go.Figure, str]:
        '''
            Creates a plot representing distribution of Rashomon Capacity metric across all samples and grouped by true class labels.

            Returns:
                Tuple[go.Figure, str]
                - plot
                - plot description
        '''

        n_samples = self.rashomon_set.determine_number_of_samples()
        n_classes = self.rashomon_set.determine_number_of_classes()
        capacity_values = np.array([self.rashomon_set.rashomon_capacity(i) for i in range(n_samples)]).reshape(-1)
        y_true = np.array(self.y_true).reshape(-1)

        capacity_df = pd.DataFrame({
            'Capacity': capacity_values,
            'Class': y_true
        })
        fig = go.Figure()

        fig.add_trace(go.Box(
            y=capacity_df['Capacity'],
            name='All samples',
            boxpoints='all',
            marker_color='#6C929E',
            jitter=0.4, 
            marker_size=2, 
            opacity=0.8
        ))

        if self.rashomon_set.task_type=="binary":
            visibility = True
            legend = False
        else:
            visibility = 'legendonly'
            legend = True
        for sample_class in sorted(capacity_df['Class'].unique()):
            fig.add_trace(go.Box(
                y=capacity_df.loc[capacity_df['Class'] == sample_class, 'Capacity'],
                name=f'Class {sample_class}',
                boxpoints='all',
                marker_color='#16476A',
                line_color="#132440",
                fillcolor="#16476A", 
                jitter=0.4, 
                marker_size=2, 
                opacity=0.8,
                visible=visibility
            ))

        tickfont_combined = {**plot_axis_font, "size": 9}
        fig.update_layout(
            showlegend=legend,
            title=dict(text = "Rashomon Capacity Distribution by Class",
                        font = plot_title_font),
            xaxis=dict(title=dict(
                            text="True Class",
                            font=plot_axis_font),
                       tickfont = tickfont_combined),
            yaxis=dict(title=dict(
                            text="Rashomon Capacity",
                            font=plot_axis_font),
                       tickfont = tickfont_combined),
            legend=dict(font = plot_axis_font),
            width=600,
            height=400
        )

        descr = f"""
            The plot shows the distribution of Rashomon Capacity values across all samples in dataset with respect to sample true class. 
        """

        return fig, descr

    
    def percent_agreement_barplot(self)->Tuple[go.Figure, str]:
        '''
            Method for creating a barplot with percent agreement values and its description.
            
            Returns:
                Tuple[go.Figure, str]
                - plot
                - plot description
        '''
        percent_agreement_dict = self.rashomon_set.percent_agreement()
        highlight_model = self.rashomon_set.base_model
        sorted_items = sorted(
            percent_agreement_dict.items(),
            key=lambda x: (x[0] != highlight_model, -x[1])
        )
        models = [item[0] for item in sorted_items]
        short_labels = [f"Model {i}" for i in range(len(models))]
        short_labels[0] = "Base Model"
        values = [item[1] for item in sorted_items]

        count_100 = sum(1 for v in percent_agreement_dict.values() if v == 100) -1 #how many models have percent agreement = 100, without base model
        colors = ['#E3E2E1' if m == highlight_model else chart_colors_v2[8] for m in models]
        fig = go.Figure(
            data = [
                go.Bar(
                    x=short_labels,
                    y=values, 
                    marker_color=colors, 
                    text =[f"{v:.2f}" for v in values],                 
                    textposition='auto',
                    hovertext=[f'Model name : {name}, <br> Percent agreement value : {v:.2f}' for name, v in zip(models,values)],
                    hoverinfo='text'
                )
            ]
        )
        mean_without_base = (
            sum(v for m, v in percent_agreement_dict.items() if m != highlight_model)
            / (len(percent_agreement_dict) - 1)
        )

        fig.add_hline(
            y = mean_without_base,
            line_dash = "dash",
            line_color = chart_colors_v2[10],
            annotation=dict(
                text=f"Mean: {mean_without_base:.2f}",
                font=dict(color=chart_colors_v2[10], size=10),    
                showarrow=False,
                align="right"
            ),
           
        )

        fig.update_xaxes(tickangle=45)

        tickfont_combined = {**plot_axis_font, "size": 9}
        fig.update_layout(
            title=dict(text ="Percent agreements for models in the Rashomon Set",
                        font = plot_title_font),

            xaxis=dict(title=dict(
                            text="Model",
                            font=plot_axis_font),
                       tickfont = tickfont_combined),
            yaxis=dict(title=dict(
                            text="Percent Agreement",
                            font=plot_axis_font),
                       tickfont = tickfont_combined,
                       gridcolor = "#D3D3D3")
        )

        if count_100==1:
            descr = f'''
                This plot shows the percentage agreement between the base model and all models included in the Rashomon Set. 
                In this scenario, there is {count_100} model , which achieved 100% agreement with the base model - meaning it produced identical class predictions for each observation in the test data.
        '''
        else:
            descr = f'''
                    This plot shows the percentage agreement between the base model and all models included in the Rashomon Set. 
                    In this scenario, there are {count_100} models , which achieved 100% agreement with the base model - meaning they produced identical class predictions for each observation in the test data.
            '''
        return fig, descr
    
    def cohens_kappa_diverging_barplot(self) -> Tuple[go.Figure, str]:
        '''
            Method for generating diverging barplot for Cohen's Kappa metric for all models in the Rashomon Set.

            Returns:
                Tuple[go.Figure, str]
                - plot
                - plot description
        '''

        cohens_kappa_dict = self.rashomon_set.cohens_kappa()
        highlight_model = self.rashomon_set.base_model
        full_agreement_count = sum(1 for m, v in cohens_kappa_dict.items() if m != highlight_model and v == 1)

        sorted_items = sorted(
            cohens_kappa_dict.items(),
            key=lambda x: (x[0] != highlight_model, -x[1])
        )

        models = [item[0] for item in sorted_items]
        values = [item[1] for item in sorted_items]
        short_labels = [
            "Base Model" if m == self.rashomon_set.base_model else f"Model {i}" 
            for i, m in enumerate(models)
        ]

        colors = []
        for m, v in zip(models, values):
            if m == highlight_model:
                colors.append('#E3E2E1')
            elif v >= 0:
                colors.append('#205781')
            else:
                colors.append('#94B4C1')

        fig = go.Figure(
            data=[
                go.Bar(
                    x=values,
                    y=short_labels,
                    marker_color=colors,
                    text=[f"{v:.2f}" for v in values],
                    textposition='auto',
                    orientation='h',
                    hovertext=[f'Model: {name}, <br>Cohen\'s Kappa: {v:.5f}' for name, v in zip(models, values)],
                    hoverinfo='text'
                )
            ]
        )

        fig.add_vline(x=0, line_dash="dash", line_color="#888", opacity=0.7)
        fig.add_vline(x=-1, line_color="#888", opacity=0.5)
        fig.add_vline(x=-0.5, line_color="#888", opacity=0.5)
        fig.add_vline(x=0.5, line_color="#888", opacity=0.5)
        fig.add_vline(x=1, line_color="#888", opacity=0.5)

        tickfont_combined = {**plot_axis_font, "size": 10}
        fig.update_layout(
            title=dict(
                text="Cohen's Kappa relative to base model",
                font=plot_title_font),
            xaxis=dict(
                title=dict(
                    text="Cohen's Kappa",
                    font={**plot_axis_font, "size": 12}
                ),
                tickfont=tickfont_combined,
                automargin=True,
                gridcolor="#D3D3D3",
                range=[-1,1]),
            yaxis=dict(
                tickfont=tickfont_combined,
                automargin=True,
                autorange="reversed")
        )
        fig.update_yaxes(
            tickmode="array",
            tickvals = short_labels,
            ticktext = short_labels,
            tickfont = {**plot_axis_font, "size":8},
            autorange = "reversed"
        )

        if full_agreement_count==1:
            descr = f"""
            This plot shows Cohen's Kappa metric calculated for each model relative to base model in Rashomon Set: {self.rashomon_set.base_model}.
            There is {full_agreement_count} model with perfect agreement with the base model.
            """
        
        if full_agreement_count>1:
            descr = f"""
            This plot shows Cohen's Kappa metric calculated for each model relative to base model in Rashomon Set: {self.rashomon_set.base_model}.
            There are {full_agreement_count} models with perfect agreement with the base model.
            """
        
        if full_agreement_count==0:
            descr = f"""
            This plot shows Cohen's Kappa metric calculated for each model relative to base model in Rashomon Set: {self.rashomon_set.base_model}.
            There are no models with perfect agreement with the base model.
            """

        return fig, descr
    
    def cohens_kappa_heatmap(self) -> Tuple[go.Figure, str]:
        '''
            Method for generating heatmap with Cohen's Kappa metric for every pair of models in the Rashomon Set.

            Returns:
                Tuple[go.Figure, str]
                - plot
                - plot description
        '''

        kappa_matrix = self.rashomon_set.cohens_kappa_matrix()
        models = kappa_matrix.index.tolist()
        short_labels = [
            "Base Model" if m == self.rashomon_set.base_model else f"Model {i+1}" 
            for i, m in enumerate(models)
        ]

        fig = px.imshow(kappa_matrix,
                        text_auto=".2f",
                        color_continuous_scale="teal",
                        zmin=-1, zmax=1,
                        aspect="auto",
                        )
        
        tickfont_combined = {**plot_axis_font, "size": 10}
        fig.update_layout(
            title =dict(text = "Cohen's Kappa between all models pairs",
                        font = plot_title_font),
            xaxis=dict(tickfont=tickfont_combined,
                       automargin=True,
                       tickvals=list(range(len(models))),
                        ticktext=short_labels,),
            yaxis = dict(gridcolor="#D3D3D3",
                         tickfont=tickfont_combined,
                         automargin=True,
                         tickvals=list(range(len(models))),
                         ticktext=short_labels)
        )

        descr = f"""This heatmap shows Cohen’s Kappa scores for all model pairs in the Rashomon Set, 
        illustrating how similar or diverse their predictions are. 
        High values indicate redundant behavior, while low values highlight complementary models."""

        return fig, descr
       
    
    def generate_rashomon_set_table(self)-> Tuple[pd.DataFrame, str]:
        '''
            Method for generating the table with Rashomon Set models and their base metric value, as well as a brief text overview of the Rashomon Set properties.

            Returns:
                Tuple[go.Figure, str]
                - plot
                - plot description
        '''
        leaderboard= self.rashomon_set.leaderboard
        rashomon_set = self.rashomon_set.rashomon_set

        filtered_leaderboard = leaderboard.loc[leaderboard['model'].isin(rashomon_set), ['model', self.rashomon_set.base_metric]].sort_values(
            by = self.rashomon_set.base_metric,
            ascending=False
        ).reset_index(drop=True).round({self.rashomon_set.base_metric:3})
        filtered_leaderboard.insert(0, "Nr", range(1, len(filtered_leaderboard)+1))

        base_model_score_rounded = filtered_leaderboard.loc[filtered_leaderboard['model'] == self.rashomon_set.base_model, self.rashomon_set.base_metric].iloc[0]
        #number of models with the same rounded score
        
        same_score_models = filtered_leaderboard.loc[
            (filtered_leaderboard[self.rashomon_set.base_metric] == base_model_score_rounded) &
            (filtered_leaderboard['model'] != self.rashomon_set.base_model),
            'model'
        ].tolist()
        same_score_count = len(same_score_models)

        styled_df = filtered_leaderboard.copy().astype(str)
        styled_df.iloc[0] = styled_df.iloc[0].apply(lambda x: f"<b>{x}</b>")

        fig = go.Figure(data = [go.Table(
            columnwidth = [28,200,70],
            header = dict(
                values=list(filtered_leaderboard.columns),
                font=dict(family="Inter, sans-serif", color='darkgray', size=13),
                fill_color='white',
                align='left'
            ),
            cells = dict(values = [styled_df[c] for c in styled_df.columns],
                         align = 'left', fill_color='white', font=dict(family="Inter, sans-serif",color='darkgray', size=12))
        )])

        
        if same_score_count == 1:
            descr =f"""
                The table shows all models that are included in the Rashomon Set for the base metric: {self.rashomon_set.base_metric} and epsilon value: {self.rashomon_set.epsilon:.2f}. The values of the {self.rashomon_set.base_metric} metric are rounded to three decimal points. 
                The set consists of <strong>{len(self.rashomon_set.rashomon_set)} models </strong>  with <strong>{self.rashomon_set.base_model} </strong>as the base model with the value of {self.rashomon_set.base_metric} equal to approximately {filtered_leaderboard.loc[filtered_leaderboard['model']==self.rashomon_set.base_model, self.rashomon_set.base_metric].values[0]:.3f}
                There is <strong>1 model</strong>, which achieved the same score as the base model (rounded to 3 decimal places) - {same_score_models[0]}
                """
        elif same_score_count == 0:
            descr =f"""
                The table shows all models that are included in the Rashomon Set for the base metric: {self.rashomon_set.base_metric} and epsilon value: {self.rashomon_set.epsilon:.2f}. The values of the {self.rashomon_set.base_metric} are rounded to three decimal points. 
                The set consists of <strong>{len(self.rashomon_set.rashomon_set)} models </strong>  with <strong>{self.rashomon_set.base_model} </strong>as the base model with the value of {self.rashomon_set.base_metric} equal to approximately {filtered_leaderboard.loc[filtered_leaderboard['model']==self.rashomon_set.base_model, self.rashomon_set.base_metric].values[0]:.3f}
                There are <strong>no models</strong>, which achieved the same score as the base model (rounded to 3 decimal places).
                """
        else:
            descr =f"""
                The table shows all models that are included in the Rashomon Set for the base metric: {self.rashomon_set.base_metric} and epsilon value: {self.rashomon_set.epsilon:.2f}. The values of the {self.rashomon_set.base_metric} are rounded to three decimal points. 
                The set consists of <strong>{len(self.rashomon_set.rashomon_set)} models </strong>  with <strong>{self.rashomon_set.base_model} </strong>as the base model with the value of {self.rashomon_set.base_metric} equal to approximately {filtered_leaderboard.loc[filtered_leaderboard['model']==self.rashomon_set.base_model, self.rashomon_set.base_metric].values[0]:.3f}
                There are <strong>{same_score_count} models</strong>, which achieved the same score as the base model (rounded to 3 decimal places) - {', '.join(f"{x}" for x in same_score_models)}
                """

        return fig, descr
    
    
    def vprs_widths_plot(self) -> Tuple[go.Figure, str]:
        '''
            This method creates the boxplot for VPRs width values for all observation divided by their real class label.
            
            Returns:
                Tuple[go.Figure, str]
                - plot
                - plot description
        '''
        if self.rashomon_set.task_type != 'binary':
            raise ValueError("VPR plot cannot be created for task types other than binary")
        
        vprs = self.rashomon_set.viable_prediction_range()
        widths = [b-a for a,b in vprs]

        df_tmp = pd.DataFrame({
            'width': widths,
            'y_true_label' : self.y_true.iloc[:,0]
        })
        df_class_0 = df_tmp[df_tmp['y_true_label'] == 0]
        df_class_1 = df_tmp[df_tmp['y_true_label'] == 1]

        fig = go.Figure()

        fig.add_trace(go.Box(
            y= df_class_0['width'],
            name='0',
            line_color=chart_colors_v2[7],
            fillcolor=chart_colors_v2[6],
            boxpoints='all',
            jitter=0.3,
            marker = dict(
                color='gray',
                size=3,
                opacity=0.6
            ),
            hovertemplate=(
                "VPR width: %{y:.3f}<br>"
                "True Label: 0<br>"
                "<extra></extra>"
            ),
            hoveron='boxes+points'
        ))

        fig.add_trace(go.Box(
            y= df_class_1['width'],
            name='1',
            line_color=chart_colors_v2[7],
            fillcolor=chart_colors_v2[3],
            boxpoints='all',
            jitter=0.3,
            marker = dict(
                color='gray',
                size=3,
                opacity=0.6
            ),
            hovertemplate=(
                "VPR width: %{y:.3f}<br>"
                "True Label: 1<br>"
                "<extra></extra>"
            ),
            hoveron='boxes+points'
        ))

        tickfont_combined = {**plot_axis_font, "size": 10}
        fig.update_layout(
            title=dict(
                text="Widths of Viable Prediction Ranges grouped by true labels",
                font=plot_title_font),
            xaxis=dict(
                title=dict(
                    text="True label",
                    font=plot_axis_font,
                ),
                tickfont=tickfont_combined,
                automargin=True),
            yaxis=dict(
                title=dict(
                    text="VPRs widths",
                    font=plot_axis_font,
                ),
                tickfont=tickfont_combined,
                automargin=True,)
        )

        descr=f"""
            This plot shows the distribution of Viable Prediction Range (VPR) widths, grouped by true class labels. 
            The VPR of an observation represents the minimum and maximum risk probabilities predicted for that sample by all models in the Rashomon Set. 
            A wide Viable Prediction Range indicates high uncertainty in the predictions for that observation. """
        

        return fig, descr
    
    def vpr_width_histogram(self)-> Tuple[go.Figure, str]:
        '''
            Method for visuzalizing Viable Prediction Ranges widths on the histogram plot

            Returns:
                Tuple[go.Figure, str]
                - plot
                - plot description
        '''
        if self.rashomon_set.task_type != 'binary':
            raise ValueError("Cannot plot VPRs for task type other than binary")
        
        vprs = self.rashomon_set.viable_prediction_range()
        widths = [b - a for a, b in vprs]

        if len(widths) == 0:
            raise ValueError("No VPR widths available to plot.")
        
        if (max(widths) == min(widths)):
            nbins=1
        else:
        #number of bins based on IQR (Freedman - Diaconis)
            iqr = np.percentile(widths, 75) - np.percentile(widths, 25)
            if iqr ==0:
                nbins = min(10, len(widths))
            else:
                bin_width = 2 * iqr / (len(widths) ** (1/3))
                if bin_width<=0 or np.isnan(bin_width):
                    nbins = min(10, len(widths))
                else:
                    nbins = int(np.ceil((max(widths) - min(widths)) / bin_width))
                    nbins = max(nbins, 1)

        df = pd.DataFrame({
            'width': widths
        })

        fig = px.histogram(
           df, x = 'width',
            nbins=nbins,
            color_discrete_sequence=['#6C929E']
        )

        fig.update_traces(
         marker=dict(line=dict(color='#184B57', width=1))  
        )

        tickfont_combined = {**plot_axis_font, "size": 10}
        fig.update_layout(
            title=dict(
                text="Histogram of VPRs widths",
                font=plot_title_font),
            xaxis=dict(
                title=dict(
                    text="VPR Width",
                    font=plot_axis_font,
                ),
                tickfont=tickfont_combined,
                automargin=True),
            yaxis=dict(
                title=dict(
                    text="Count",
                    font=plot_axis_font,
                ),
                tickfont=tickfont_combined,
                automargin=True) 
        )

        descr = f"""
            This histogram shows the distribution of Viable Prediction Range (VPR) widths for all observations in the test dataset. The number of bins was determined using the Freedman-Diaconis rule.
        """

        return fig, descr
    
    def feature_importance_table(self) -> Tuple[go.Figure, str]:
        '''
            Method for generating a table comparing the top 3 most important features in the base model with features that most frequently appeared at the 1st, 2nd,
            and 3rd positions across all models in the Rashomon Set.
            
            Returns:
                Tuple[go.Figure, str]
                - plot
                - plot description
        '''

        if self.rashomon_set.rashomon_feature_importance is None:
            return go.Figure(), 'Visualization is not available since there are no feature importance present in the Rashomon Set.'
        
        bm = self.rashomon_set.base_model
        fi = self.rashomon_set.rashomon_feature_importance
        fi_bm = fi.get(bm, [])
        fi_bm_top3 = fi_bm[:3] if fi_bm else ["-", "-", "-"] #top 3 most important features for base model or '-' if base model has no feature importance

        position_counts = {1: {}, 2: {}, 3: {}}
        for feature_list in fi.values():
            if not feature_list:
                continue
            for i in range(3):
                if len(feature_list) > i:
                    position_counts[i+1][feature_list[i]] = position_counts[i+1].get(feature_list[i], 0) + 1

        most_common = [max(position_counts[i], key=position_counts[i].get) if position_counts[i] else None for i in range(1, 4)]

        table_data = [
            ["Rank", "Base Model Top 3", "Most Frequent in Rashomon Set"],
            ["1", fi_bm_top3[0] if len(fi_bm_top3) > 0 else "-", most_common[0] or "-"],
            ["2", fi_bm_top3[1] if len(fi_bm_top3) > 1 else "-", most_common[1] or "-"],
            ["3", fi_bm_top3[2] if len(fi_bm_top3) > 2 else "-", most_common[2] or "-"],
        ]

        fig = go.Figure(data=[go.Table(
            header=dict(values=table_data[0],
                        fill_color=color_palette[4],
                        align='center'),
            cells=dict(values=list(zip(*table_data[1:])),
                    fill_color=color_palette[2],
                    align='center'))
        ])

        descr = f'''
        This table compares the top 3 most important features of the base model - {bm}, with the features that appear most frequently in the Rashomon Set at positions 1, 2, and 3.
        '''

        return fig, descr
    

    def feature_importance_heatmap(self) -> Tuple[go.Figure, str]:
        '''
            Method used to create a heatmap showing the top 3 features for each model in the Rashomon Set.
                - X-axis: feature names.
                - Y-axis: models with feature importance.
                - Cells are colored according to feature rank:
                    - No color: feature not in the top 3 for the model.
                    - The most important feature for model (rank 1) - dark blue
                    - Second most important feature for model (rank 2) - medium blue
                    - Third most important feature for model (rank 3) - light blue
            
            Returns:
                Tuple[go.Figure, str]
                - plot
                - plot description
        '''

        descr = '''
            This plot shows a heatmap of the top 3 features for each model in the Rashomon Set.<br>
            Rank = 1 - it is the most important feature selected by model (dark blue). <br>
            Rank = 2 - it is the second most important feature selected by model (medium blue). <br>
            Rank = 3 - it is third the most important feature selected by model (light blue). <br>
            Rank > 3 - feature is not in the top 3 most important features for the model (no color). <br>
            <em>Please note that if the entire row is empty (white), that means feature importance was not available for this particular model.</em>
        ''' 

        if self.rashomon_set.rashomon_feature_importance is None:
            return go.Figure(),  descr + 'Visualization is not available since there are no feature importance present in the Rashomon Set.<br>'
        

        fi = self.rashomon_set.rashomon_feature_importance
        models = list(fi.keys())

        all_features = set()
        for features in fi.values():
            if features is not None:
                all_features.update(features[:3])
        all_features = sorted(all_features)

        data = pd.DataFrame(4, index=all_features, columns=models, dtype=object) #rank 4 means feature not in top 3 (no color)
        for model, features in fi.items():
            if features is not None:
                for rank, feature in enumerate(features[:3], start=1):
                    data.loc[feature, model] = rank

        dark_blue = color_palette[4]
        medium_blue = color_palette[3]
        light_blue = color_palette[2]
        white = color_palette[0]
        colorscale = [
            [0.0, dark_blue],    # 1 - dark blue
            [0.25, dark_blue],
            
            [0.25, medium_blue],   # 2 - medium blue  
            [0.5, medium_blue],
            
            [0.5, light_blue],    # 3 - light blue
            [0.75, light_blue],
            
            [0.75, white],   # 4 - white
            [1.0, white]
        ]

        data_t = data.T
        hovertext = [
            [
                f"The most important feature {data_t.columns[j]} for model {data_t.index[i]}" if val == 1 else
                f"Second most important feature {data_t.columns[j]} for model {data_t.index[i]}" if val == 2 else
                f"Third most important feature {data_t.columns[j]} for model {data_t.index[i]}" if val == 3 else
                f"Feature {data_t.columns[j]} not in top 3 for model {data_t.index[i]}"
                for j, val in enumerate(row)
            ] for i, row in enumerate(data_t.values)]
        
        
        fig = go.Figure(data=go.Heatmap(
            z=data_t.values,
            x=data_t.columns,
            y=data_t.index,
            colorscale=colorscale,
            showscale=True,
            zmin=1,
            zmax=4,
            colorbar=dict(
                title="Rank", 
                title_side = 'top',
                tickmode='array',
                tickvals=[1.375, 2.125, 2.875, 3.625], 
                ticktext=['1','2','3','>3']
            ),
            text=hovertext,
            hoverinfo='text',
            xgap=1,
            ygap=1
        ))

        tickfont_combined = {**plot_axis_font, "size": 10}
        fig.update_layout(
            title=dict(
                text="Top 3 Feature Importance Across Models",
                font=plot_title_font),
            xaxis=dict(
                title=dict(
                    text="Feature Names",
                    font=plot_axis_font,
                ),
                tickfont=tickfont_combined,
                automargin=True),
            yaxis=dict(
                tickfont=tickfont_combined,
                automargin=True), 
            width=max(600, 70 * len(data_t.columns)),
            height=max(400, 30 * len(data_t.index))
        )

        fig.update_yaxes(
            tickmode='array',
            tickvals=list(range(len(data_t.index))),
            ticktext=list(data_t.index),
            tickfont=dict(size=10),
        )

        fig.update_xaxes(
            tickmode='array',
            tickvals=list(range(len(data_t.columns))),
            ticktext=list(data_t.columns),
            tickfont=dict(size=10),
        )


        return fig, descr

    
    def agreement_rates_density(self)-> Tuple[go.Figure, str]:
        '''
            This method creates the density plot of agreement rates for each observation in the dataset.
            
            Returns:
                Tuple[go.Figure, str]
                - plot
                - plot description
        '''
        y_true = self.y_true.iloc[:,0]
        agreement_rates = self.rashomon_set.agreement_rate()

        df = pd.DataFrame({
            'y_true': y_true,
            'rates': agreement_rates
        })
        
        fig = px.violin(data_frame=df, y='rates', points=False)
        fig.update_traces( fillcolor=chart_colors_v2[4], line=dict(color=chart_colors_v2[6]), marker=dict(color='gray', size=3, opacity=0.6))

        tickfont_combined = {**plot_axis_font, "size": 10}
        fig.update_layout(
            title=dict(
                text="Agreement rate distribution",
                font=plot_title_font),
            yaxis=dict(
                title=dict(
                    text="Agreement rates",
                    font=plot_axis_font,
                ),
                tickfont=tickfont_combined,
                automargin=True,
                gridcolor="#D3D3D3"),
            xaxis=dict(
                tickfont=tickfont_combined,
                automargin=True), 
        )
        

        descr=""" This violin plot shows the distribution of agreement rates for all observations in the test dataset.
        An agreement rate of 1 indicates that all models in the Rashomon Set made the same prediction as the base model for a given observation,
        while an agreement rate of 0 means that none of the models agreed with the base model’s prediction."""

        return fig, descr
    
    def vpr_vs_base_model_plot(self)-> Tuple[go.Figure, str]:
        '''
            Creates the violin plot illustrating differences between base model's predictions and VPRs.
            
            Returns:
                Tuple[go.Figure, str]
                - plot
                - plot description
        '''
        if self.rashomon_set.task_type != 'binary':
            raise ValueError("Cannot plot VPRs for task type other than binary")

        vprs = self.rashomon_set.viable_prediction_range()
        min_ranges, max_ranges = zip(*vprs)
        min_ranges = list(min_ranges)
        max_ranges = list(max_ranges)
        h0_risk_preds = self.rashomon_set.proba_predictions_dict[self.rashomon_set.base_model].iloc[:,1]
        y_true_vals = self.y_true.iloc[:,0]

        df_tmp = pd.DataFrame({
            'y_true' : y_true_vals,
            'risk_pred': h0_risk_preds,
            'min_range': min_ranges,
            'max_range' : max_ranges
            })
        df_tmp['diff'] = df_tmp.apply(
            lambda row: row['risk_pred'] - row['min_range'] if row['y_true'] == 0
                        else row['max_range'] - row['risk_pred'],
            axis=1
        )
        
        fig = px.violin(
            df_tmp,
            x='y_true',      
            y='diff',        
            points='all',   
            color='y_true',  
            box=True         
        ) 
        fig.update_traces( fillcolor=chart_colors_v2[6], line=dict(color=chart_colors_v2[8]), marker=dict(color='gray', size=3, opacity=0.6))

        tickfont_combined = {**plot_axis_font, "size": 10}
        fig.update_layout(
            title=dict(
                text="Agreement rate distribution",
                font=plot_title_font),
            yaxis=dict(
                title=dict(
                    text="Agreement rates",
                    font=plot_axis_font,
                ),
                tickfont=tickfont_combined,
                automargin=True,
                gridcolor="#D3D3D3"),
            xaxis=dict(
                tickfont=tickfont_combined,
                automargin=True), 
        )
        fig.update_layout(
            title=dict(
                text='Differences between base model risk prediction and VPRs ends',
                font=plot_title_font),
            yaxis=dict(
                title=dict(
                    text="Differences",
                    font=plot_axis_font,
                ),
                tickfont=tickfont_combined,
                automargin=True),
            xaxis=dict(
                title=dict(
                    text="True class label",
                    font=plot_axis_font,
                ),
                tickfont=tickfont_combined,
                automargin=True),
            legend = dict(
                title=dict(
                    text="True class label",
                    font=plot_axis_font,
                )
            )

        )
        fig.update_yaxes(range=[0,1])
        descr = """This violin plot shows how the base model's risk predictions compare to the range of predictions produced by all models in the Rashomon set. 
        For each observation, the Viable Prediction Range (VPR) is defined as  [min risk prediction, max risk prediction] across all models from the Rashomon Set.
        This plot allows you to see where the base model's prediction falls within this range for each observation. 
        For positive class the difference is calculated as the max risk prediction - base model's risk prediction, while for the negative class it's the base model's risk prediction - min risk prediction. 
        """
        
        return fig, descr
