# coding: utf-8

# Copyright 2020,2021 IBM All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from tabulate import tabulate


class Prop:
    def __init__(self, name=None, framework_name=None, autolog=None,manual_log=None, version=None, trigger_methods=None, training_metrics=None, post_training_metrics=None, parameters=None, tags=None, artifacts=None, search_estimator=None):
        self.name = name
        self.framework_name = framework_name
        self.autolog = autolog
        self.manual_log = manual_log
        self.version = version
        self.trigger_methods = trigger_methods
        self.training_metrics = training_metrics
        self.post_training_metrics = post_training_metrics
        self.parameters = parameters
        self.tags = tags
        self.artifacts = artifacts
        self.search_estimator = search_estimator


class SupportBase:
    def __init__(self, props_definitions):
        self._props_definitions = props_definitions

    def get(self):
        return sorted(list(map(lambda x: x.framework_name, filter(lambda x: (x.autolog or x.manual_log), self._props_definitions))))

    def show(self):
        print(self._generate_table())

    def _generate_doc_table(self):
        return self._generate_table('Name', 'Framework Name', 'Autolog','Manual Log', 'Version','Trigger Methods', 'Metrics', 'Parameters', 'Tags', 'Artifacts', 'Search Estimators', format='grid')

    def _generate_doc_framework_table(self):
        return self._generate_framwork_table('Framework Name', 'Trigger Methods', 'Training Metrics', 'Parameters', 'Tags', 'Artifacts', 'Post Training Metrics', 'Search Estimators', format='grid')

    def _generate_doc(self, resource_name):
        return """

To view supported frameworks , use:

    >>> client.FrameworkSupportNames.show()

To see only supported framework names , use:

    >>> client.FrameworkSupportNames.get()

Set of Supported Frameworks for {}. Manual log is not version dependent.

Available Options:

{}

""".format(resource_name, SupportBase(self._props_definitions)._generate_doc_table())

    def _generate_doc_framework(self, resource_name, limit):
        if limit:
            return """


Current autolog support scope for {}.

Available Options:

{}

{}

""".format(resource_name, SupportBase(self._props_definitions)._generate_doc_framework_table(), limit)
        else:
            return """


Current autolog support scope for {}.

Available Options:

{}

""".format(resource_name, SupportBase(self._props_definitions)._generate_doc_framework_table())

    def _generate_table(self, name_label='NAME', framework_label='FRAMEWORK_NAME',
                        autolog_label='AUTOLOG',manual_log_label='MANUAL_LOG',version_label='VERSION',
                        trigger_methods_label='TRIGGER_METHODS', metrics_label='LOGGING_METRICS', parameter_label='LOGGING_PARAMETERS', tag_label='LOGGING_TAGS', artifact_label='LOGGING_ARTIFACTS', search_estimator_label='SEARCH_ESTIMATORS', format='simple'):

        header = [name_label, framework_label,
                  autolog_label,manual_log_label,version_label]

        table_content = []

        for prop in self._props_definitions:
            row = [prop.name, prop.framework_name, u'Y' if prop.autolog else u'N', u'Y' if prop.manual_log else u'N', prop.version]

            # if show_defaults:
            #     row.append(values_format.format(meta_prop.default_value)
            #                if meta_prop.default_value != '' else '')

            # if show_examples:
            #     row.append(values_format.format(meta_prop.example_value)
            #                if meta_prop.example_value != '' else '')

            # if show_schema:
            #     row.append(values_format.format(meta_prop.schema)
            #                if meta_prop.schema != '' else '')

            table_content.append(row)

        table = tabulate(
            [header] + table_content,
            tablefmt=format
        )
        return table

    def _generate_framwork_table(self, framework_label='FRAMEWORK_NAME',
                                 trigger_methods_label='TRIGGER_METHODS', training_metrics_label='LOGGING_TRAINING_METRICS',
                                 parameter_label='PARAMETERS', tag_label='TAGS', artifact_label='ARTIFACTS', post_training_metrics_label='LOGGING_POST_TRAINING_METRICS', search_estimator_label='SEARCH_ESTIMATORS', format='grid'):

        show_post_training = any(
            prop.post_training_metrics != '' for prop in self._props_definitions)

        show_search_estimator = any(
            prop.search_estimator != '' for prop in self._props_definitions)

        show_tags = any(
            prop.tags != '' for prop in self._props_definitions)

        header = [framework_label,
                  trigger_methods_label, training_metrics_label, parameter_label]

        if show_tags:
            header.append(tag_label)

        if show_post_training:
            header.append(post_training_metrics_label)

        if show_search_estimator:
            header.append(search_estimator_label)

        framework_table_content = []

        for prop in self._props_definitions:
            row = [prop.framework_name, prop.trigger_methods,
                   prop.training_metrics, prop.parameters]

            if show_tags:
                row.append(prop.tags)

            if show_post_training:
                row.append(prop.post_training_metrics)

            if show_search_estimator:
                row.append(prop.search_estimator)
            # if show_defaults:
            #     row.append(values_format.format(meta_prop.default_value)
            #                if meta_prop.default_value != '' else '')

            # if show_examples:
            #     row.append(values_format.format(meta_prop.example_value)
            #                if meta_prop.example_value != '' else '')

            # if show_schema:
            #     row.append(values_format.format(meta_prop.schema)
            #                if meta_prop.schema != '' else '')

            framework_table_content.append(row)

        table = tabulate(
            [header] + framework_table_content,
            tablefmt=format
        )
        return table


class FrameworkSupportOptions(SupportBase):
    _props_definitions = [
        Prop('scikit', 'sklearn', True, True,
             '0.22.1 <= scikit-learn <= 1.1.2'),
        Prop('Tensorflow', 'tensorflow', True,True,
             '2.3.0 <= tensorflow <= 2.9.1'),
        Prop('Keras', 'keras', True, True,
             '2.3.0 <= keras <= 2.9.0'),
        Prop('PySpark', 'pyspark', True, True,
             '3.0.0 <= pyspark <= 3.4.0'),
        Prop('Xgboost', 'xgboost', True, True,
             '1.1.1 <= xgboost <= 1.6.1'),
        Prop('LightGBM', 'lightgbm', True, True,
             '2.3.1 <= lightgbm <= 3.3.2'),
        Prop('PyTorch', 'pytorch', True, True,
             '1.0.5 <= pytorch-lightning <= 1.7.1'),
        Prop('Pycaret', 'pycaret', True, False,
             '')
        # Prop('StatModels', 'statsmodels', False, False,
        #      '0.11.1 <= statsmodels <= 0.12.2'),
        # Prop('Gluon', 'gluon', False, False,
        #      '1.5.1 <= mxnet <= 1.8.0'),

    ]

    __doc__ = SupportBase(
        _props_definitions)._generate_doc('Auto logging')

    def __init__(self):
        SupportBase.__init__(self, self._props_definitions)


class FrameworkSupportSklearn(SupportBase):
    _props_definitions_scikit = [
        Prop(framework_name='sklearn', trigger_methods='- estimator.fit()\n- estimator.fit_predict()\n- estimator.fit_transform()', training_metrics=' Classifier:\n \n- precision score \n- recall score \n- f1 score \n- accuracy score\n \nIf the classifier has method `predict_proba`\n \n- log loss \n- roc auc score\n \nRegression:\n \n- mean squared error \n- root mean squared error \n- mean absolute error \n- r2 score', parameters='estimator.get_params(deep=True)',
             tags=' - estimator class name(e.g. “LinearRegression”) \n- fully qualified estimator class name(e.g. “sklearn.linear_model._base.LinearRegression”)', post_training_metrics=' Scikit-learn metric APIs:\n \n- model.score \n- metric APIs defined in the sklearn.metrics module\n \nNote:\n  \n- metric key format is: `{metric_name}[-{call_index}]_{dataset_name}` \n- if `sklearn.metrics`: `metric_name` is the metric function name \n- if `model.score`, then `metric_name` is `{model_class_name}_score`\n\nIf multiple calls are made to the same scikit-learn metric API\n \neach subsequent call adds a “call_index” (starting from 2) to the metric key', search_estimator='Meta estimator:\n \n- Pipeline, \n- GridSearchCV , \n- RandomizedSearchCV \n \nIt logs child runs with metrics for each set of \n\nexplored parameters, as well as parameters \n\nfor the best model and the best parameters (if available)')
    ]

    limit = ''
    __doc__ = SupportBase(
        _props_definitions_scikit)._generate_doc_framework('Scikit learn', limit)

    def __init__(self):
        SupportBase.__init__(self, self._props_definitions_scikit)


class FrameworkSupportSpark(SupportBase):
    _props_definitions_spark = [
        Prop(framework_name='pyspark', trigger_methods='estimator.fit(), except for\n\nestimators (featurizers) under `pyspark.ml.feature`', training_metrics='Not Supported', parameters='`estimator.params`\n\nIf a param value is also an `Estimator`\n\nthen params in the the wrapped estimator will also be logged, the nested\n\nparam key will be `{estimator_uid}.{param_name}`',
             tags=' - estimator class name(e.g. “LinearRegression”) \n- fully qualified estimator class name(e.g. “pyspark.ml.regression.LinearRegression”)', post_training_metrics='pyspark ML evaluators used under `Evaluator.evaluate`\n  \n- metric key format is: `{metric_name}[-{call_index}]_{dataset_name}` \n- Metric name: `Evaluator.getMetricName()` \n\nIf multiple calls are made to the same pyspark ML evaluator metric API\n \neach subsequent call adds a “call_index” (starting from 2) to the metric key', search_estimator='Meta estimator:\n \n- Pipeline, \n- CrossValidator, \n- TrainValidationSplit, \n- OneVsRest\n \nIt logs child runs with metrics for each set of \n\nexplored parameters, as well as parameters \n\nfor the best model and the best parameters (if available)'),
    ]
    limit = ''
    __doc__ = SupportBase(
        _props_definitions_spark)._generate_doc_framework('Spark', limit)

    def __init__(self):
        SupportBase.__init__(self, self._props_definitions_spark)


class FrameworkSupportKeras(SupportBase):
    _props_definitions_keras = [
        Prop(framework_name='keras', trigger_methods='estimator.fit()', training_metrics='- Training loss, \n- Validation loss, \n- User specified metrics,\n \nMetricss related EarlyStopping callbacks:\n \n- stopped_epoch, \n- restored_epoch, \n- restore_best_weight, \n- last_epoch etc.  ',
             parameters='- fit() or fit_generator() params, \n- Optimizer name, \n- Learning rate, \n- Epsilon, \n \nParams related to EarlyStopping:\n \n- min-delta, \n- patience, \n- baseline, \n- restore_best_weights etc.', tags='', post_training_metrics='', search_estimator=''),
    ]
    limit = ''
    __doc__ = SupportBase(
        _props_definitions_keras)._generate_doc_framework('Keras', limit)

    def __init__(self):
        SupportBase.__init__(self, self._props_definitions_keras)


class FrameworkSupportTensorflow(SupportBase):
    _props_definitions_tf = [
        Prop(framework_name='tensorflow', trigger_methods='estimator.fit()', training_metrics='- Training loss, \n- Validation loss, \n- User specified metrics,\n \nMetricss related EarlyStopping callbacks:\n \n- stopped_epoch, \n- restored_epoch, \n- restore_best_weight, \n- last_epoch etc.\n \nTensorBoard metrics:\n \n- average_loss, \n- loss \n \nTensorflow Core:\n \n- tf.summary.scalar calls  ',
             parameters='- fit() or fit_generator() params, \n- Optimizer name, \n- Learning rate, \n- Epsilon, \n \nParams related to EarlyStopping:\n \n- min-delta, \n- patience, \n- baseline, \n- restore_best_weights etc.\n \nTensorboard params:\n \n- steps, \n- max_steps', tags='', post_training_metrics='', search_estimator=''),
    ]
    limit = ''
    __doc__ = SupportBase(
        _props_definitions_tf)._generate_doc_framework('Tensorflow', limit)

    def __init__(self):
        SupportBase.__init__(self, self._props_definitions_tf)


class FrameworkSupportXGB(SupportBase):
    _props_definitions_xgb = [
        Prop(framework_name='xgboost', trigger_methods='- xgboost.train(), \n- scikit-learn APIs.`fit()`', training_metrics='- Metrics at each iteration (if `evals` specified), \n- Metrics at best iteration (if `early_stopping_rounds` specified)',
             parameters='- params specified in `xgboost.train` or `fit()`', tags='', post_training_metrics='', search_estimator=''),
    ]
    limit = ''
    __doc__ = SupportBase(
        _props_definitions_xgb)._generate_doc_framework('XGBoost', limit)

    def __init__(self):
        SupportBase.__init__(self, self._props_definitions_xgb)


class FrameworkSupportLGBM(SupportBase):
    _props_definitions_lgbm = [
        Prop(framework_name='lightgbm', trigger_methods='lightgbm.train()', training_metrics='- Metrics at each iteration (if `evals` specified), \n- Metrics at best iteration (if `early_stopping_rounds` specified)',
             parameters='- params specified in `lightgbm.train`', tags='', post_training_metrics='', search_estimator=''),
    ]
    limit = ''
    __doc__ = SupportBase(
        _props_definitions_lgbm)._generate_doc_framework('LightGBM', limit)

    def __init__(self):
        SupportBase.__init__(self, self._props_definitions_lgbm)


class FrameworkSupportPyTorch(SupportBase):
    _props_definitions_pt = [
        Prop(framework_name='pytorch', trigger_methods='pytorch_lightning.Trainer()\n \n  i.e., models that subclass pytorch_lightning.LightningModule', training_metrics='- Training loss, \n- Validation loss, \n- average_test_accuracy, \n- user defined metrics, \n \nMetricss related EarlyStopping callbacks:\n \n- stopped_epoch, \n- restored_epoch, \n- restore_best_weight, \n- last_epoch etc.',
             parameters='- fit() parameters, \n- optimizer name, \n- learning rate, \n- epsilon, \n \nParams related to EarlyStopping:\n \n- min-delta, \n- patience, \n- baseline, \n- restore_best_weights etc.', tags='', post_training_metrics='', search_estimator=''),
    ]
    limit = ''
    __doc__ = SupportBase(
        _props_definitions_pt)._generate_doc_framework('PyTorch', limit)

    def __init__(self):
        SupportBase.__init__(self, self._props_definitions_pt)
