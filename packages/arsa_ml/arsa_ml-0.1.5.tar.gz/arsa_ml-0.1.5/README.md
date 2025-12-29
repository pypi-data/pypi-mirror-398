# ARSA_ML - Automated Rashomon Set Analysis package 
### Weclome to the official ARSA_ML package site.
<div align="center">
  <img src="docs/logo.jpg" alt="Welcome to the official ARSA_ML package site" width="300">
</div>



## Overview 
ARSA_ML is a Python library for detailed analysis of the Rashomon Sets - the collections of models that perform nearly equally well on a given dataset. It provides tools to create various objects, analyse the related properties and metrics, as well as visualize the results. The package is compatible with two AutoML frameworks - AutoGluon and H2O. Additionally, you may analyze your own set of models if you present their results in a requsted format (See : [documentation](https://katarzynarogalska.github.io/ARSA-Automated-Rashomon-Set-Analysis/)).

## Installation 
Install the package with PyPI:
```bash 
pip install arsa_ml
```

## Example usage 
```Python 
from rashomon_analysis.pipelines.builder_abstract import *
from rashomon_analysis.pipelines.pipelines_user_input import * 

#create pipeline from H2O saved models
builder = BuildRashomonH2O(models_directory=example_models_path, 
                           test_data = test_h2o, 
                           target_column=target_column, 
                           df_name = 'heart', 
                           base_metric='accuracy', 
                           feature_imp_needed=True)

#preview Rashomon Set properties
builder.preview_rashomon()

#set epsilon value
builder.set_epsilon(0.03)

#launch pipeline
rashomon_set, visualizer = builder.build()

#close dashboard 
builder.dashboard_close()
```

## Documentation
For detailed package dokumentation visit [documentation page](https://katarzynarogalska.github.io/ARSA-Automated-Rashomon-Set-Analysis/) 

## Authors
* [Katarzyna Rogalska](https://github.com/katarzynarogalska) (repository owner)
* [Zuzanna Sieńko](https://github.com/sienkozuzanna) 