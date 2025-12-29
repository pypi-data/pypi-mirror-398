import streamlit as st
import sys
import pickle
import os
import plotly.io as pio
from pathlib import Path
import streamlit.components.v1 as components
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from rashomon_analysis.visualizers.rashomon_visualizer import *
from rashomon_analysis import *
BASE_DIR = Path(__file__).resolve().parent.parent
assets_dir = BASE_DIR / "style"

def load_converterd_results(df_name, framework_name):
    leaderboard = pd.read_csv( BASE_DIR.parent / "converter_results" / framework_name/ df_name / "leaderboard.csv")
    y_true = pd.read_csv( BASE_DIR.parent / "converter_results" / framework_name/ df_name / "y_true.csv")
    with open(BASE_DIR.parent / "converter_results" / framework_name / df_name / "predictions_dict.pkl", "rb") as f:
        predictions_dict = pickle.load(f)

    with open(BASE_DIR.parent / "converter_results" / framework_name / df_name / "proba_predictions_dict.pkl", "rb") as f:
        proba_predictions_dict = pickle.load(f)

    with open(BASE_DIR.parent / "converter_results" / framework_name / df_name / "feature_importance_dict.pkl", "rb") as f:
        feature_importance_dict = pickle.load(f)

    return leaderboard, predictions_dict, proba_predictions_dict, feature_importance_dict, y_true


def main():
    print(str(assets_dir))
    l, p_d, proba_d, f_d, y = load_converterd_results('compas', 'h2o')
    rashomon = RashomonSet(l, p_d, proba_d, f_d, 'accuracy', 0.1)
    rashomon.summarize_rashomon()
    

    # visualizer = Visualizer(rashomon, y)
    # fig, descr = visualizer.vpr_vs_base_model_plot()
    # st.plotly_chart(fig, use_container_width=True)
    # st.markdown(descr)

    # ratios, ratios_descr = visualizer.pattern_ratio_indicator()
    # st.plotly_chart(ratios)
    # st.markdown(ratios_descr, unsafe_allow_html=True)

    # ratios, ratios_descr = visualizer.rashomon_ratio_indicator()
    # st.plotly_chart(ratios)
    # st.markdown(ratios_descr, unsafe_allow_html=True)

    # table_rashomon, table_descr = visualizer.generate_rashomon_set_table()
    # st.dataframe(table_rashomon)
    # st.markdown(table_descr, unsafe_allow_html=True)

    #capacity_by_class, capacity_by_class_descr = visualizer.rashomon_capacity_distribution_by_class()
    #st.plotly_chart(capacity_by_class)
    #st.markdown(capacity_by_class_descr, unsafe_allow_html=True)

    #capacity_by_class, capacity_by_class_descr = visualizer.rashomon_capacity_distribution()
    #t.plotly_chart(capacity_by_class)
    #st.markdown(capacity_by_class_descr, unsafe_allow_html=True)

    #capacity_by_class, capacity_by_class_descr = visualizer.rashomon_capacity_distribution_by_class()
    #st.plotly_chart(capacity_by_class)
    #t.markdown(capacity_by_class_descr, unsafe_allow_html=True)

    #table_rashomon, table_descr = visualizer.feature_importance_table()
    #st.plotly_chart(table_rashomon)
    #st.markdown(table_descr, unsafe_allow_html=True)

    #fi_heatmap, fi_heatmap_descr = visualizer.feature_importance_heatmap()
    #st.plotly_chart(fi_heatmap)
    #st.markdown(fi_heatmap_descr, unsafe_allow_html=True)
    
    # test działania wykresów w połączniu z html css
   
    # '''
    # html_fig = pio.to_html(fig, full_html=False, config={'responsive': True})

    # with open(assets_dir / "layout.html") as f:
    #     layout_html = f.read()

    # layout_html = layout_html.replace("{{FIGURE}}", html_fig)
    # components.html(layout_html, height = 800, scrolling=False)
    # '''


if __name__ == "__main__":
    main()