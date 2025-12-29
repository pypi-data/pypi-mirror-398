import streamlit as st
import pickle
import sys
import streamlit as st
import pickle
import sys
from pathlib import Path
import re
import streamlit.components.v1 as components
import plotly.graph_objects as go
BASE_DIR = Path(__file__).parent
CSS_PATH = BASE_DIR / "assets" / "style.css"

plot_backgroud_color = "white"
plot_font = dict(color='#989898', size=12)
plot_title_font = dict(
    color="#6B7F8A",
    family="Inter, Segoe UI, sans-serif",  
    size=16,
    style="normal",
    weight=300            
)



#Rashomon Set dashboard for binary task type

def run_app_from_file(plots_file):
    with open(plots_file, "rb") as f:
        plots, descriptions = pickle.load(f)
    
    st.set_page_config(page_title="Rashomon Dashboard", layout="wide")

    with open(CSS_PATH) as f:
        css = f.read()
    
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

    x0, x1, y0, y1 = 0, 1, 0, 1
    r = 0.02
    path = f'M{x0+r},{y0} ' \
       f'L{x1-r},{y0} Q{x1},{y0} {x1},{y0+r} ' \
       f'L{x1},{y1-r} Q{x1},{y1} {x1-r},{y1} ' \
       f'L{x0+r},{y1} Q{x0},{y1} {x0},{y1-r} ' \
       f'L{x0},{y0+r} Q{x0},{y0} {x0+r},{y0} Z'
    
    x0v, x1v, y0v, y1v = 0, 1, -0.02, 1.05
    path_violin = f'M{x0v+r},{y0v} ' \
       f'L{x1v-r},{y0v} Q{x1v},{y0v} {x1v},{y0v+r} ' \
       f'L{x1v},{y1v-r} Q{x1},{y1v} {x1v-r},{y1v} ' \
       f'L{x0v+r},{y1v} Q{x0v},{y1v} {x0v},{y1v-r} ' \
       f'L{x0v},{y0v+r} Q{x0v},{y0v} {x0v+r},{y0v} Z'

    title_container = st.container()
    title_container.markdown('<div class="dashboard-title">Rashomon Intersection Analysis</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    #TABLES ------------------------------------------------------------------------------------------------------
    with st.container():
        rashomon_set_col, pareto_col = st.columns(2)
        
        with rashomon_set_col:
            
            rashomon_table = plots["generate_rashomon_set_table"]
            rashomon_table.update_layout(
                shapes=[
                    dict(
                        type="path",
                        path=path,
                        xref="paper", yref="paper",
                        line=dict(color="#6C929E", width=1),
                        fillcolor="rgba(0,0,0,0)"
                    ),
                    ],
                xaxis=dict(showgrid=False, zeroline=False),
                yaxis=dict(showgrid=False, zeroline=False),
                paper_bgcolor=plot_backgroud_color,
                plot_bgcolor=plot_backgroud_color,
                width=450,
                height=350
            )
            rashomon_table.update_layout(

                margin=dict(t=10, l=10, r=10, b=0)
            )
            st.markdown('<div class = "section_title"> Models present in the Rashomon Intersection</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="section_description">This section presents all models icluded in the Rashomon Intersection. Firstly, two separate Rashomon Sets for base metrics : {descriptions["base_metric_return"][0]} and {descriptions["base_metric_return"][1]} were obtained. Only models present in both sets were included in the Rashomon Intersection illustrated by the table below.  </div>', unsafe_allow_html=True)

            with st.container(key = "basics"):
                st.markdown(
                        f"""
                        <div style="font-size:15px; margin-bottom:10px;">
                            <span style="color: #426c85;font-family: 'Inter', sans-serif; font-weight: 500; letter-spacing: 0.2px; ">Base model : </span>
                            <span style="color:#989898; font-family: 'Inter', sans-serif;"> {descriptions["base_model_return"]}</span>
                        </div>
                        """,
                        unsafe_allow_html=True
                )
                st.markdown(
                        f"""
                        <div style="font-size:15px; margin-bottom:10px;">
                             <span style="color: #426c85;font-family: 'Inter', sans-serif; font-weight: 500; letter-spacing: 0.2px;">Base metrics : </span>
                            <span style="color:#989898; font-family: 'Inter', sans-serif;"> {descriptions["base_metric_return"][0]},  {descriptions["base_metric_return"][1]} </span>
                        </div>
                        """,
                        unsafe_allow_html=True
                )
                st.markdown(
                        f"""
                        <div style="font-size:15px; margin-bottom:10px;">
                            <span style="color: #426c85;font-family: 'Inter', sans-serif; font-weight: 500; letter-spacing: 0.2px;">Weighted sum method : </span>
                            <span style="color:#989898; font-family: 'Inter', sans-serif;"> {descriptions["weighted_method_return"]}</span>
                        </div>
                        """,
                        unsafe_allow_html=True
                )
            with st.container(key = "table_container", height="stretch"):
                st.plotly_chart(rashomon_table, width='stretch')
                st.markdown(f'<div class="plots_descr rashomon-table-descr">{descriptions["generate_rashomon_set_table"]}</div>', unsafe_allow_html=True)
        
        
        with pareto_col:
            pareto_plot, pareto_descr = plots['pareto_front_plot'], descriptions['pareto_front_plot']

            pareto_plot.update_layout(
                shapes=[
                    dict(
                        type="path",
                        path=path,
                        xref="paper", yref="paper",
                        line=dict(color="#6C929E", width=1),
                        fillcolor="rgba(0,0,0,0)"
                    )
                ],
                paper_bgcolor=plot_backgroud_color,
                plot_bgcolor=plot_backgroud_color,
                width=450,
                height=450,
                font=plot_font,
                legend=dict(
                font=plot_font
            )
            )
            pareto_plot.update_layout(
                title={
                    'text': "Pareto Front",
                    'y':0.97,
                    'x':0.05,
                    'xanchor': 'left',
                    'yanchor': 'top',
                    'font': plot_title_font
                },
                margin=dict(t=40, l=3, r=3, b=25)
            )

            st.markdown('<div class = "section_title">Pareto Front with all models</div>', unsafe_allow_html=True)
            st.markdown('<div class = "section_description"> The plot below presents all models from the leaderboard with highlighted models included in the Pareto front obtained for both metrics. Note that models in the Pareto Front do not have to match models present in the Rashomon Intersection, as the selection procedure for the Intersection was different.</div>', unsafe_allow_html=True)
            with st.container(key = "pareto", height="stretch"):
                st.plotly_chart(pareto_plot, width='stretch')
                st.markdown(f'<div class="plots_descr">{pareto_descr}</div>', unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class = "section_title">Rashomon Intersection analysis</div>', unsafe_allow_html=True)
        st.markdown('<div class = "section_description">In the following sections the analysis is focused on the Rashomon Intersection, not the models in the Pareto Front.</div>', unsafe_allow_html=True)

    with st.container():
        gauge_col, venn_col = st.columns([40,60])

        with gauge_col:
            st.markdown('<div class = "section_title">Rashomon Intersection size</div>', unsafe_allow_html=True)
            gauge_size, gauge_size_descr = plots["set_size_indicator"], descriptions["set_size_indicator"]

            gauge_size.update_layout(
                height=270,
                width=350,
                paper_bgcolor=plot_backgroud_color,
                plot_bgcolor=plot_backgroud_color,
                margin=dict(t=50, l=80, r=80, b=10),
                font=plot_font,
            )
            
            gauge_rashomons, gauge_rashomons_descr = plots["generate_gauge_for_metrics"], descriptions["generate_gauge_for_metrics"]

            gauge_rashomons.update_layout(
                height=220,
                paper_bgcolor=plot_backgroud_color,
                plot_bgcolor=plot_backgroud_color,
                font=plot_font,
            )

            with st.container(key = "gauge"):
                st.markdown(f'<div class = "section_description">The following chart illustrates the fraction of models from the leaderboard that are included in the Rashomon Intersection.</div>', unsafe_allow_html=True)
                st.plotly_chart(gauge_size)
                st.markdown(f'<div class = "section_description">Additionally, the numbers of models from separate Rashomon Sets included in the Intesection are represented by the plots below.</div>', unsafe_allow_html=True)
                st.plotly_chart(gauge_rashomons)

        
        with venn_col:
            st.markdown('<div class = "section_title">Venn diagram </div>', unsafe_allow_html=True)
            venn_plot, venn_descr = plots['plot_venn_diagram'], descriptions['plot_venn_diagram']
            venn_plot.update_layout(
                paper_bgcolor=plot_backgroud_color,
                plot_bgcolor=plot_backgroud_color,
                font=plot_font,
                height = 400
            )

            with st.container(key = "venn", height='stretch'):
                st.markdown(f'<div class = "venn_description">{venn_descr}</div>', unsafe_allow_html=True)
                st.plotly_chart(venn_plot)

    # -------------------------------------- SAME AS RASHOMON SET -----------------------------------------------------------------

    with st.container():
        st.markdown(
            '<div class="section_title">Rashomon Ratio and Pattern Ratio metrics</div>',
            unsafe_allow_html=True
        )
        rashomon_ratio_col,pattern_ratio_col = st.columns(2)

        with pattern_ratio_col:              
            # # PATTERN RATIO INDICATOR
            pattern_indicator, pattern_indicator_descr = plots['pattern_ratio_indicator'], descriptions['pattern_ratio_indicator']
            pattern_indicator.update_layout(
                shapes=[
                    dict(
                        type="path",
                        path=path,
                        xref="paper", yref="paper",
                        line=dict(color="#6C929E", width=1),
                        fillcolor="rgba(0,0,0,0)"
                    )
                ],
                paper_bgcolor=plot_backgroud_color,
                plot_bgcolor=plot_backgroud_color,
                width=75,
                height=75,
                font=plot_font,
            )
            pattern_indicator.update_layout(
                title={
                    'text': "Pattern Rashomon Ratio",
                    'y':0.97,
                    'x':0.05,
                    'xanchor': 'left',
                    'yanchor': 'top',
                    'font': plot_title_font
                },
                margin=dict(t=30, l=10, r=10, b=25)
            )
    
            with st.container(key = "pattern_white_container", height="stretch"):
                    st.plotly_chart(pattern_indicator, width='stretch')
                    st.markdown(
                        f'<div class="plots_descr">{pattern_indicator_descr}</div>',
                        unsafe_allow_html=True
                    )
    

        with rashomon_ratio_col:
        # RASHOMON RATIO 
            ratio_indicatior, ratio_indicator_descr = plots['rashomon_ratio_indicator'], descriptions['rashomon_ratio_indicator']
            ratio_indicatior.update_layout(
                shapes=[
                    dict(
                        type="path",
                        path=path,
                        xref="paper", yref="paper",
                        line=dict(color="#6C929E", width=1),
                        fillcolor="rgba(0,0,0,0)"
                    )
                ],
                paper_bgcolor=plot_backgroud_color,
                plot_bgcolor=plot_backgroud_color,
                font=plot_font,
            )
            ratio_indicatior.update_layout(
                title={
                    'text': "Rashomon Ratio",
                    'y':0.97,
                    'x':0.02,
                    'xanchor': 'left',
                    'yanchor': 'top',
                    'font': plot_title_font
                },
                width=75,
                height=75,
                margin=dict(t=30, l=10, r=10, b=25)
            )

            with st.container(key = "ratio_white_container", height="stretch"):
                    st.plotly_chart(ratio_indicatior, width='stretch')
                    st.markdown(
                        f'<div class="plots_descr">{ratio_indicator_descr}</div>',
                        unsafe_allow_html=True
                    )
           
        
        

# RATIOS VS EPSILONS
    with st.container():
        col1, col2 = st.columns(2)
        with col1:
             # # RASHOMON RATIO VS EPSILON
            ratio_vs_eps_plot, ratio_vs_eps_descr = plots['rashomon_ratio_vs_epsilon'], descriptions['rashomon_ratio_vs_epsilon']
            ratio_vs_eps_plot.update_layout(
                shapes=[
                    dict(
                        type="path",
                        path=path,
                        xref="paper", yref="paper",
                        line=dict(color="#6C929E", width=1),
                        fillcolor="rgba(0,0,0,0)"
                    )
                ],
                paper_bgcolor= plot_backgroud_color,
                plot_bgcolor=plot_backgroud_color,
                width=75,
                height=300,
                font=plot_font,
                xaxis=dict(title_font=dict(color="#989898"), tickfont=dict(color="#989898")),
                yaxis=dict(title_font=dict(color="#989898"), tickfont=dict(color="#989898")),
                legend=dict(font=dict(color="#989898", size=10)),
                title={
                    'text': "Rashomon Ratio vs Epsilon values",
                    'y':0.97,
                    'x':0.02,
                    'xanchor': 'left',
                    'yanchor': 'top',
                    'font': plot_title_font
                },
                margin=dict(t=50, l=10, r=10, b=0)
            )
            


            with st.container(key = "ratio_epsilon_white_container", height="stretch"):
                    st.plotly_chart(ratio_vs_eps_plot, width='stretch')
                    st.markdown(
                        f'<div class="plots_descr">{ratio_vs_eps_descr}</div>',
                        unsafe_allow_html=True
                    )
        with col2:
            # PATTERN VS EPSILON
            pattern_vs_eps_plot, pattern_vs_eps_descr = plots['pattern_rashomon_ratio_vs_epsilon'], descriptions['pattern_rashomon_ratio_vs_epsilon']
            pattern_vs_eps_plot.update_layout(
                shapes=[
                    dict(
                        type="path",
                        path=path,
                        xref="paper", yref="paper",
                        line=dict(color="#6C929E", width=1),
                        fillcolor="rgba(0,0,0,0)"
                    )
                ],
                paper_bgcolor=plot_backgroud_color,
                plot_bgcolor=plot_backgroud_color,
                width=75,
                height=300,
                font=plot_font,
                xaxis=dict(title_font=dict(color="#989898"), tickfont=dict(color="#989898")),
                yaxis=dict(title_font=dict(color="#989898"), tickfont=dict(color="#989898")),
                legend=dict(font=dict(color="#989898", size=10)),
                title={
                    'text': "Pattern Ratio vs Epsilon values",
                    'y':0.97,
                    'x':0.02,
                    'xanchor': 'left',
                    'yanchor': 'top',
                    'font': plot_title_font
                },
                margin=dict(t=50, l=10, r=10, b=0)
            )

            with st.container(key = "pattern_epsilon_white_container", height="stretch"):
                    st.plotly_chart(pattern_vs_eps_plot, width='stretch')
                    st.markdown(
                        f'<div class="plots_descr">{pattern_vs_eps_descr}</div>',
                        unsafe_allow_html=True
                    )


    #AMBIGUITY AND DISCREPANCY -------------------------------------------------------------------------------------------------------
    #with st.container(key="amb_discr"):

    with st.container():
        st.markdown(
            '<div class="section_title">Ambiguity and Discrepancy metrics</div>',
            unsafe_allow_html=True
        )
        descr= """Ambiguity can be interpreted as the proportion of observations that would receive a different prediction if we were to choose another model from the Rashomon Set, while
        Discrepancy is the maximum proportion of individuals whose predictions would change if we choose a different competing model from the Rashomon Set."""
        st.markdown(
            f'<div class="section_description">{descr}</div>',
            unsafe_allow_html=True
        )
        st.markdown(
            """
            <style>
            [data-baseweb="checkbox"] [data-testid="stWidgetLabel"] p {
                /* Styles for the label text */
                color: #8B9DA8;
                font-family: 'Inter', sans-serif; 
                font-size: 16px; 
                font-weight: 300 !important;
                letter-spacing: 0.1px;
                line-height: 1.5; 

            }
            </style>
            """,
            unsafe_allow_html=True

        )

        use_probability = st.checkbox("Show probabilistic version", value=False)
        
        if use_probability:
            st.markdown( f'<div class="section_description">While calculating probabilistic ambiguity and discrepancy, the difference between risk probabilities is considered meaningful if it is greater then or equal to delta.</div>',
            unsafe_allow_html=True)

        lolipop_col, amb_col, discr_col = st.columns([1.1,1.5,1.5])
        with st.container():
            with lolipop_col:
                
                if use_probability:
                    amb_discr_plot, amb_discr_descr = plots["lolipop_ambiguity_discrepancy_proba_version"], descriptions["lolipop_ambiguity_discrepancy_proba_version"]
                else:
                    amb_discr_plot, amb_discr_descr = plots['lolipop_ambiguity_discrepancy'], descriptions['lolipop_ambiguity_discrepancy']

                amb_discr_plot.update_layout(
                    paper_bgcolor= plot_backgroud_color,
                    plot_bgcolor=plot_backgroud_color,
                    height=250,
                    font=plot_font,
                    xaxis=dict(title_font=dict(color="#989898"), tickfont=dict(color="#989898")),
                    yaxis=dict(title_font=dict(color="#989898"), tickfont=dict(color="#989898")),
                    legend=dict(font=dict(color="#989898", size=10)),
                    title={
                    'text': "Ambiguity and Discrepancy values",
                    'y':0.97,
                    'x':0.02,
                    'xanchor': 'left',
                    'yanchor': 'top',
                    'font': plot_title_font
                    },
                )
                with st.container(key = "lolipop_container"):
                    st.plotly_chart(amb_discr_plot)
                    st.markdown(
                        f'<div class ="plots_descr">{amb_discr_descr}</div>',
                        unsafe_allow_html=True
                    )

            with amb_col:
                if use_probability:
                    amb_vs_eps_plot, amb_vs_eps_descr = plots["proba_ambiguity_vs_epsilon"], descriptions["proba_ambiguity_vs_epsilon"]
                else:
                    amb_vs_eps_plot, amb_vs_eps_descr = plots['ambiguity_vs_epsilon'], descriptions['ambiguity_vs_epsilon']
                amb_vs_eps_plot.update_layout(
                shapes=[
                    dict(
                        type="path",
                        path=path,
                        xref="paper", yref="paper",
                        line=dict(color="#6C929E", width=1),
                        fillcolor="rgba(0,0,0,0)"
                    )
                ],
                paper_bgcolor=plot_backgroud_color,
                plot_bgcolor=plot_backgroud_color,
                height=250,
                font=plot_font,
                xaxis=dict(title_font=dict(color="#989898"), tickfont=dict(color="#989898")),
                yaxis=dict(title_font=dict(color="#989898"), tickfont=dict(color="#989898")),
                legend=dict(font=dict(color="#989898", size=10)),
                title={
                    'text': "Ambiguity vs Epsilon values",
                    'y':0.97,
                    'x':0.02,
                    'xanchor': 'left',
                    'yanchor': 'top',
                    'font': plot_title_font
                },
                margin=dict(t=30, l=5, r=5, b=5)
                )

                with st.container(key="ambig_epsilon_container", height="stretch"):
                    st.plotly_chart(amb_vs_eps_plot, width='stretch')
                    st.markdown(
                        f'<div class="plots_descr">{amb_vs_eps_descr}</div>',
                        unsafe_allow_html=True
                    )

            with discr_col:
                if use_probability:
                    discr_vs_eps_plot, discr_vs_eps_descr = plots["proba_discrepancy_vs_epsilon"], descriptions["proba_discrepancy_vs_epsilon"]
                else:
                    discr_vs_eps_plot, discr_vs_eps_descr = plots['discrepancy_vs_epsilon'], descriptions['discrepancy_vs_epsilon']
                discr_vs_eps_plot.update_layout(
                shapes=[
                    dict(
                        type="path",
                        path=path,
                        xref="paper", yref="paper",
                        line=dict(color="#6C929E", width=1),
                        fillcolor="rgba(0,0,0,0)"
                    )
                ],
                paper_bgcolor=plot_backgroud_color,
                plot_bgcolor=plot_backgroud_color,
                height=250,
                font=plot_font,
                xaxis=dict(title_font=dict(color="#989898"), tickfont=dict(color="#989898")),
                yaxis=dict(title_font=dict(color="#989898"), tickfont=dict(color="#989898")),
                legend=dict(font=dict(color="#989898", size=10)),
                title={
                    'text': "Discrepancy vs Epsilon values",
                    'y':0.97,
                    'x':0.02,
                    'xanchor': 'left',
                    'yanchor': 'top',
                    'font': plot_title_font
                },
                margin=dict(t=30, l=5, r=5, b=5)
                )

                with st.container(key = "discr_epsilon_container", height="stretch"):
                    st.plotly_chart(discr_vs_eps_plot, width='stretch')
                    st.markdown(
                        f'<div class="plots_descr">{discr_vs_eps_descr}</div>',
                        unsafe_allow_html=True
                    )

    #RASHOMON CAPACITY AND PER SAMPLE -------------------------------------------------------------------------------------------------------
    with st.container():
        left, right = st.columns([45,55], vertical_alignment="top")
        with right:
            st.markdown('<div class = "section_title">Single sample analysis</div>', unsafe_allow_html=True)
            descr= f"""
            This section presents a detailed analysis of a randomly selected sample from the dataset.
            <br>
            If you wish to explore a specific sample, try experimenting with the methods (rashomon_capacity_for_sample and proba_probabilities_for_sample) available in the Visualizer class instance.
            </br>
            """
            st.markdown(
                    f'<div class ="section_description">{descr}</div>',
                    unsafe_allow_html=True
                )
            
        with left:
            st.markdown(
                '<div class="section_title">Rashomon Capacity metric</div>',
                unsafe_allow_html=True
            )
            no_classes = descriptions["number_of_classes_return"]
            descr= f"""Rashomon Capacity is a predictive multiplicity metric that measures the diversity of model predictions for each sample.
            <br> 
            <strong>Values are between [1, {no_classes}]</strong>, where 1 indicates do predictive multiplicty present, and {no_classes} represents the highest possible diversity among model predictions.
            </br>
            """
            st.markdown(
                f'<div class="section_description">{descr}</div>',
                unsafe_allow_html=True
            )
    with st.container():
        
        rashomon_capacity_col, per_sample_col = st.columns([45,55], vertical_alignment="top")

        with rashomon_capacity_col:
            with st.container():
                capacity_hist, capacity_hist_descr = plots['rashomon_capacity_distribution'], descriptions['rashomon_capacity_distribution']
                capacity_hist.update_layout(
                    shapes=[
                    dict(
                        type="path",
                        path=path,
                        xref="paper", yref="paper",
                        line=dict(color="#6C929E", width=1),
                        fillcolor="rgba(0,0,0,0)"
                    )
                ],
                paper_bgcolor=plot_backgroud_color,
                plot_bgcolor=plot_backgroud_color,
                height=230,
                font=plot_font,
                xaxis=dict(title_font=dict(color="#989898"), tickfont=dict(color="#989898")),
                yaxis=dict(title_font=dict(color="#989898"), tickfont=dict(color="#989898")),
                legend=dict(font=dict(color="#989898", size=10)),
                title={
                    'text': "Rashomon Capacity distribution",
                    'y':0.97,
                    'x':0.02,
                    'xanchor': 'left',
                    'yanchor': 'top',
                    'font': plot_title_font
                },
                margin=dict(t=40, l=5, r=10, b=5)
                )

                capacity_boxplot, capacity_boxplot_descr = plots['rashomon_capacity_distribution_by_class'], descriptions['rashomon_capacity_distribution_by_class']
                capacity_boxplot.update_layout(
                    shapes=[
                    dict(
                        type="path",
                        path=path,
                        xref="paper", yref="paper",
                        line=dict(color="#6C929E", width=1),
                        fillcolor="rgba(0,0,0,0)"
                    )
                    ],
                    paper_bgcolor = plot_backgroud_color,
                    plot_bgcolor=plot_backgroud_color,
                    height=230,
                    font=plot_font,
                    xaxis=dict(title_font=dict(color="#989898"), tickfont=dict(color="#989898")),
                    yaxis=dict(title_font=dict(color="#989898"), tickfont=dict(color="#989898")),
                    legend=dict(font=dict(color="#989898", size=10)),
                    title={
                        'text': "Rashomon Capacity distribution by class",
                        'y':0.97,
                        'x':0.02,
                        'xanchor': 'left',
                        'yanchor': 'top',
                        'font': plot_title_font
                    },
                    margin=dict(t=40, l=5, r=10, b=5)
                    )

                #histogram container for plot and description
              
                with st.container(key='capacity-hist'):
                    st.plotly_chart(capacity_hist, width='stretch')
                    st.markdown(
                        f'<div class="plots_descr">{capacity_hist_descr}</div>',
                        unsafe_allow_html=True
                    )

                #boxplot container for plot and description
                with st.container(key='capacity-boxplot', height="stretch"):
                    st.plotly_chart(capacity_boxplot, width='stretch')
                    st.markdown(
                        f'<div class="plots_descr">{capacity_boxplot_descr}</div>',
                        unsafe_allow_html=True
                    )
                    

        with per_sample_col:
                
            proba_probabilities_plot, proba_probabilities_descr = plots['proba_probabilities_for_sample'], descriptions['proba_probabilities_for_sample']

            proba_probabilities_plot.update_layout(
            shapes=[
                dict(
                    type="path",
                    path=path,
                    xref="paper", yref="paper",
                    line=dict(color="#6C929E", width=1),
                    fillcolor="rgba(0,0,0,0)"
                )
            ],
            paper_bgcolor=plot_backgroud_color,
            plot_bgcolor=plot_backgroud_color,
            height=400,
            font=plot_font,
            xaxis=dict(title_font=dict(color="#989898"), tickfont=dict(color="#989898", size=10)),
            yaxis=dict(title_font=dict(color="#989898"), tickfont=dict(color="#989898", size=10)),
            legend=dict(font=dict(color="#989898", size=10)),
            title={
                'text': "Predicted probabilities for sample across all models in the Rashomon Set",
                'y':0.97,
                'x':0.02,
                'xanchor': 'left',
                'yanchor': 'top',
                'font': plot_title_font
            },
            margin=dict(t=30, l=5, r=5, b=5)
            )

            capacity_per_sample, capacity_per_sample_descr = plots['rashomon_capacity_for_sample'], descriptions['rashomon_capacity_for_sample']

            capacity_per_sample.update_layout(
            shapes=[
                dict(
                    type="path",
                    path=path,
                    xref="paper", yref="paper",
                    line=dict(color="#6C929E", width=1),
                    fillcolor="rgba(0,0,0,0)"
                )
            ],
            paper_bgcolor=plot_backgroud_color,
            plot_bgcolor=plot_backgroud_color,
            height=100,
            font=plot_font,
            xaxis=dict(title_font=dict(color="#989898"), tickfont=dict(color="#989898")),
            yaxis=dict(title_font=dict(color="#989898"), tickfont=dict(color="#989898")),
            legend=dict(font=dict(color="#989898", size=10)),
            title={
                'text': "Rashomon Capacity value for sample",
                'y':0.97,
                'x':0.02,
                'xanchor': 'left',
                'yanchor': 'top',
                'font': plot_title_font
            },
            margin=dict(t=60, l=5, r=5, b=10)
            )

            
           
            #proba probabilities container for plot and description
            with st.container(key='per_sample', height="stretch"):
                st.plotly_chart(proba_probabilities_plot, width='stretch')
                st.markdown(
                    f'<div class="plots_descr">{proba_probabilities_descr}</div>',
                    unsafe_allow_html=True
                )

            #rashomon capacity for sample container for plot and description
                with st.container(key="capacity_per_sample_padding"):
                    st.plotly_chart(capacity_per_sample, width='stretch')
                    st.markdown(
                        f'<div class="plots_descr">{capacity_per_sample_descr}</div>',
                        unsafe_allow_html=True
                    )


    #PERCENT AGREEMENT AND FEATURE IMPORTANCE -------------------------------------------------------------------------------------------------------

    with st.container():
        
        percent_agreement_bar_plot, percent_agreement_bar_descr = plots['percent_agreement_barplot'], descriptions['percent_agreement_barplot']
        percent_agreement_bar_plot.update_layout(
            paper_bgcolor=plot_backgroud_color,
            plot_bgcolor=plot_backgroud_color,
            height=350,
            font=plot_font,
            xaxis=dict(title_font=dict(color="#989898"), tickfont=dict(color="#989898")),
            yaxis=dict(title_font=dict(color="#989898"), tickfont=dict(color="#989898")),
            legend=dict(font=dict(color="#989898", size=10)),
            title={
                'text': "Percent Agreement Rates distribution",
                'y':0.97,
                'x':0.02,
                'xanchor': 'left',
                'yanchor': 'top',
                'font': plot_title_font
            },
            margin=dict(t=40, l=5, r=10, b=5)
            )
        
        cohens_kappa_barplot, cohens_kappa_barplot_descr = plots['cohens_kappa_diverging_barplot'], descriptions['cohens_kappa_diverging_barplot']
        cohens_kappa_barplot.update_layout(
            paper_bgcolor=plot_backgroud_color,
            plot_bgcolor=plot_backgroud_color,
            height=350,
            font=plot_font,
            xaxis=dict(title_font=dict(color="#989898"), tickfont=dict(color="#989898")),
            yaxis=dict(title_font=dict(color="#989898"), tickfont=dict(color="#989898")),
            legend=dict(font=dict(color="#989898", size=10)),
            title={
                'text': "Cohen's Kappa distribution",
                'y':0.97,
                'x':0.02,
                'xanchor': 'left',
                'yanchor': 'top',
                'font': plot_title_font
            },
            margin=dict(t=40, l=5, r=10, b=5)
            )

        
        agreement_rates_violin_plot, agreement_rates_violin_descr = plots['agreement_rates_density'], descriptions['agreement_rates_density']
        agreement_rates_violin_plot.update_yaxes(range=[-0.005,1.005], tickvals=[0, 0.2, 0.4, 0.6, 0.8, 1], showgrid=True)
        agreement_rates_violin_plot.update_layout(
            shapes=[
            dict(
                type="path",
                path=path_violin,
                xref="paper", yref="paper",
                line=dict(color="#6C929E", width=1),
                fillcolor="rgba(0,0,0,0)"
            )
            ],
            paper_bgcolor=plot_backgroud_color,
            plot_bgcolor=plot_backgroud_color,
            height=390,
            font=plot_font,
            xaxis=dict(title_font=dict(color="#989898"), tickfont=dict(color="#989898")),
            yaxis=dict(title_font=dict(color="#989898"), tickfont=dict(color="#989898"), showgrid=True),
            legend=dict(font=dict(color="#989898", size=10)),
            title={
                'text': "Agreement Rates distribution",
                'y':0.97,
                'x':0.02,
                'xanchor': 'left',
                'yanchor': 'top',
                'font': plot_title_font
            },
            margin=dict(t=50, l=5, r=10, b=5)
            )
        
        fi_table, fi_table_descr = plots['feature_importance_table'], descriptions['feature_importance_table']
        fi_heatmap, fi_heatmap_descr = plots['feature_importance_heatmap'], descriptions['feature_importance_heatmap']

        fi_table.update_traces(columnwidth=[1,2,2])
        fi_table.update_layout(
            shapes=[
                dict(
                    type="path",
                    path=path,
                    xref="paper", yref="paper",
                    line=dict(color="#6C929E", width=1),
                    fillcolor="rgba(0,0,0,0)"
                ),
                ],
            xaxis=dict(showgrid=False, zeroline=False),
            yaxis=dict(showgrid=False, zeroline=False),
            paper_bgcolor= plot_backgroud_color,
            plot_bgcolor=plot_backgroud_color,
            height=139
        )
        fi_table.update_layout(
            title={
                'text': "Top 3 Feature Importance in Rashomon Set",
                'y':0.97,
                'x':0.05,
                'xanchor': 'left',
                'yanchor': 'top',
                'font': plot_title_font
            },
            margin=dict(t=40, l=10, r=10, b=10)
        )

        heatmap_is_empty = (len(fi_heatmap.data) == 0 or fi_heatmap.data[0].z is None or len(fi_heatmap.data[0].z) == 0)
        if not heatmap_is_empty:
            fillcolor = 'rgba(108,146,158,0.2)'
        else:
            fillcolor = 'rgba(0,0,0,0)'
                
        fi_heatmap.update_layout(
            shapes=[
                dict(
                    type="path",
                    path=path,
                    xref="paper", yref="paper",
                    line=dict(color="#6C929E", width=1),
                    fillcolor="rgba(0,0,0,0)"
                ),
                dict(
                    type="rect",
                    xref="paper", yref="paper",
                    x0=0, y0=0, x1=1, y1=1,
                    fillcolor=fillcolor,
                    line=dict(width=0),
                    layer="below"   #background below the heatmap to show borders between cells
                )
            ],
            paper_bgcolor= plot_backgroud_color,
            plot_bgcolor=plot_backgroud_color,
            height=570,
            font=plot_font,
            xaxis=dict(title_font=dict(color="#989898"), tickfont=dict(color="#989898", size=8)),
            yaxis=dict(title_font=dict(color="#989898"), tickfont=dict(color="#989898", size=8)),
            legend=dict(font=dict(color="#989898", size=10)),
            title={
                'text': "Feature Importance Rank",
                'y':0.97,
                'x':0.02,
                'xanchor': 'left',
                'yanchor': 'top',
                'font': plot_title_font
            },
            margin=dict(t=40, l=0, r=5, b=5),
            )

        percent_agreement_col, feature_importance_col = st.columns([45, 55], vertical_alignment='top')
        agreement_rates_col, fi_heatmap_col = st.columns([45, 55], vertical_alignment='bottom')

        with st.container():
            with percent_agreement_col:

                st.markdown('<div class = "section_title">Models agreement metrics</div>', unsafe_allow_html=True)
                descr = '''
                    This section shows how models in the Rashomon Set agree with the base model using Percent Agreement or Cohen’s Kappa metrics.
                    '''
                st.markdown(f'<div class="section_description no_padding">{descr}</div>', unsafe_allow_html=True)

                metric_option = st.radio(
                    "Select metric:",
                    ["Percent Agreement", "Cohen's Kappa"],
                    horizontal=True,
                    label_visibility="collapsed"
                )

                if metric_option=="Percent Agreement":
                    st.markdown('<div class = "section_title">Percent Agreement</div>', unsafe_allow_html=True)
                    descr = '''
                        Percent Agreement is defined as the proportion of observations for which each model from the Rashomon Set predicted the same class as the base model.
                        '''
                    st.markdown(f'<div class="section_description less_padding">{descr}</div>', unsafe_allow_html=True)
                    with st.container(key = "percent_agreement"):
                        st.plotly_chart(percent_agreement_bar_plot, width='stretch')
                        st.markdown(f'<div class="plots_descr">{percent_agreement_bar_descr}</div>', unsafe_allow_html=True)

                elif metric_option=="Cohen's Kappa":
                    st.markdown('<div class = "section_title">Cohens Kappa</div>', unsafe_allow_html=True)
                    descr = '''
                        Cohen's Kappa measures how much each model agrees with the base model beyond chance.
                        Values range from -1 (complete disagreement) to 1 (perfect agreement), with 0 meaning chance-level agreement.
                        '''
                    st.markdown(f'<div class="section_description less_padding">{descr}</div>', unsafe_allow_html=True)
                    with st.container(key = "cohens_kappa_barplot"):
                        st.plotly_chart(cohens_kappa_barplot, width='stretch')
                        st.markdown(f'<div class="plots_descr">{cohens_kappa_barplot_descr}</div>', unsafe_allow_html=True)

            with feature_importance_col:
                st.markdown('<div class = "section_title">Feature Importance</div>', unsafe_allow_html=True)
                descr = '''
                This section provides an overview of the most important features identified across the models included in the Rashomon Set, highlighting which features contribute most to the predictions of each model.
                <br>
                <em>Note that this section presents information for models with feature importnace data available. 
                If feature importance was not selected or was unavailable for certain models, no information is displayed.</em><br>
                '''
                st.markdown(f'<div class="section_description less_padding">{descr}</div>', unsafe_allow_html=True)
                with st.container(key='fi_table'):
                    st.plotly_chart(fi_table, width='stretch')
                    fi_table_description_update = fi_table_descr + " <br>If the base model does not provide feature importance values, a ‘–’ will be displayed to indicate that this information is unavailable."
                    st.markdown(f'<div class = "plots_descr">{fi_table_description_update}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="section_description heatmap-descr">{fi_heatmap_descr}</div>', unsafe_allow_html=True)

        with st.container():
            with agreement_rates_col:
                st.markdown('<div class ="section_title">Agreement Rates</div>', unsafe_allow_html=True)
                descr = '''
                For each observation, the Agreement Rate quantifies the proportion of models that produce the same class prediction as the base model.
                '''
                st.markdown(
                        f'<div class="section_description">{descr}</div>',
                        unsafe_allow_html=True
                    )

                #violin container for plot and description
                with st.container(key='agreement_rates_violin'):
                    st.plotly_chart(agreement_rates_violin_plot, width='stretch')
                    st.markdown(
                        f'<div class="plots_descr">{agreement_rates_violin_descr}</div>',
                        unsafe_allow_html=True
                    )
            with fi_heatmap_col:
                #feature importance heatmap
                with st.container(key = 'fi_heatmap', height="stretch"):
                    st.plotly_chart(fi_heatmap, width='stretch')

                    
    #VPRS -------------------------------------------------------------------------------------------------------
    with st.container():
        with st.container():
            st.markdown('<div class = "section_title">Viable Prediction Range</div>', unsafe_allow_html=True)

            vprs_hist_plot, vprs_hist_descr = plots['vpr_width_histogram'], descriptions['vpr_width_histogram']
            vprs_by_class_plot, vprs_by_class_descr = plots['vprs_widths_plot'], descriptions['vprs_widths_plot']

            plot_description, vpr_definition = vprs_by_class_descr.split('.', 1)
            plot_description = plot_description + '.' 
            vpr_definition = vpr_definition.strip()

            descr= f"""
            {vpr_definition}
            """
            st.markdown(
                    f'<div class = "section_description">{descr}</div>',
                    unsafe_allow_html=True
                )

            vprs_hist_plot.update_layout(
                shapes=[
                    dict(
                        type="path",
                        path=path,
                        xref="paper", yref="paper",
                        line=dict(color="#6C929E", width=1),
                        fillcolor="rgba(0,0,0,0)"
                    ),
                    ],
                paper_bgcolor=plot_backgroud_color,
                plot_bgcolor=plot_backgroud_color,
                height=250,
                font=plot_font,
                xaxis=dict(title_font=dict(color="#989898"), tickfont=dict(color="#989898")),
                yaxis=dict(title_font=dict(color="#989898"), tickfont=dict(color="#989898")),
                legend=dict(font=dict(color="#989898", size=10)),
                title={
                    'text': "Viable Prediction Range Widths",
                    'y':0.97,
                    'x':0.02,
                    'xanchor': 'left',
                    'yanchor': 'top',
                    'font': plot_title_font
                },
                margin=dict(t=30, l=5, r=5, b=5)
                )

            vprs_by_class_plot, vprs_by_class_descr = plots['vprs_widths_plot'], descriptions['vprs_widths_plot']

            vprs_by_class_plot.update_layout(
            shapes=[
                dict(
                    type="path",
                    path=path,
                    xref="paper", yref="paper",
                    line=dict(color="#6C929E", width=1),
                    fillcolor="rgba(0,0,0,0)"
                )
            ],
            paper_bgcolor=plot_backgroud_color,
            plot_bgcolor=plot_backgroud_color,
            height=270,
            font=plot_font,
            xaxis=dict(title_font=dict(color="#989898"), tickfont=dict(color="#989898")),
            yaxis=dict(title_font=dict(color="#989898"), tickfont=dict(color="#989898")),
            legend=dict(font=dict(color="#989898", size=10)),
            title={
                'text': "Viable Prediction Range Widths by class",
                'y':0.97,
                'x':0.02,
                'xanchor': 'left',
                'yanchor': 'top',
                'font': plot_title_font
            },
            margin=dict(t=30, l=5, r=5, b=5)
            )
            vprs_by_class_plot.update_xaxes(
                showticklabels=False,  # usuwa numery/tick labels
                showgrid=False,        # usuwa linie siatki dla osi X, jeśli chcesz
                zeroline=False         # usuwa linię 0, jeśli jest
            )

            vprs_vs_base_model_plot, vprs_vs_base_model_plot_descr = plots['vpr_vs_base_model_plot'], descriptions['vpr_vs_base_model_plot']
            vprs_vs_base_model_plot.update_yaxes(range=[-0.005,1.005], tickvals=[0, 0.2, 0.4, 0.6, 0.8, 1], showgrid=True)
            vprs_vs_base_model_plot.update_layout(
            shapes=[
                dict(
                    type="path",
                    path=path_violin,
                    xref="paper", yref="paper",
                    line=dict(color="#6C929E", width=1),
                    fillcolor="rgba(0,0,0,0)"
                )
            ],
            paper_bgcolor=plot_backgroud_color,
            plot_bgcolor=plot_backgroud_color,
            height=350,
            font=plot_font,
            xaxis=dict(title_font=dict(color="#989898"), tickfont=dict(color="#989898")),
            yaxis=dict(title_font=dict(color="#989898"), tickfont=dict(color="#989898"), showgrid=True),
            showlegend=False,
            title={
                'text': "Viable Prediction Range Widths by class",
                'y':0.97,
                'x':0.02,
                'xanchor': 'left',
                'yanchor': 'top',
                'font': plot_title_font
            },
            margin=dict(t=40, l=5, r=5, b=5)
            )

            hist_col, by_class_col = st.columns([1, 1])
            with hist_col:
                #vpr widths hist container for plot and description
                with st.container(key='vprs_hist', height="stretch"):
                    st.plotly_chart(vprs_hist_plot, width='stretch')
                    st.markdown(
                        f'<div class="plots_descr">{vprs_hist_descr}</div>',
                        unsafe_allow_html=True
                    )
            
            with by_class_col:
                #vpr widths by class container for plot and description
                with st.container(key='vprs_by_class', height="stretch"):
                    st.plotly_chart(vprs_by_class_plot, width='stretch')
                    st.markdown(
                        f'<div class="plots_descr">{plot_description}</div>',
                        unsafe_allow_html=True
                    )
            
            with st.container(key='vprs_vs_base_model', height="stretch"):
                chart_col, descr_col = st.columns([3, 1])
                with chart_col:
                    st.plotly_chart(vprs_vs_base_model_plot, width='stretch')
                with descr_col:
                    st.markdown('<br>', unsafe_allow_html=True)
                    st.markdown(f'<div class="plots_descr">{vprs_vs_base_model_plot_descr}</div>', unsafe_allow_html=True)
                
            
                    
            


if __name__ == "__main__":
    plots_file = sys.argv[1]   
    run_app_from_file(plots_file)