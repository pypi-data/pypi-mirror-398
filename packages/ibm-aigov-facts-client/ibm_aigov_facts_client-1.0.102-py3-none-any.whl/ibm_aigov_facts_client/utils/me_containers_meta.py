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
    def __init__(self, model_platform=None,asset_placeholder=None, space_type=None,deployment_details=None,openscale_monitored=None,expected_container=None,notes=None):
        self.ml_platform = model_platform
        self.asset_placeholder= asset_placeholder
        self.space_type = space_type
        self.deployment_details = deployment_details
        self.openscale_monitored = openscale_monitored
        self.expected_container = expected_container
        self.notes = notes


class SupportBase:
    def __init__(self, props_definitions):
        self._props_definitions = props_definitions

    def get(self,asset_platform:str,container_name:str):
        data=list(filter(lambda x: (x.ml_platform==asset_platform and x.expected_container==container_name.upper()), self._props_definitions))
        #return sorted(list(map(lambda x: x, filter(lambda x: (x.ml_platform==asset_platform and x.expected_container==container_name.upper()), self._props_definitions))))
        return [i.__dict__ for i in data ]

    def show(self):
        print(self._generate_table())

    def _generate_doc_table(self):
        return self._generate_table('Model Asset Platform', 'Asset Placeholder','Space Type', 'Deployment info available','Openscale monitored', 'Expected container','Notes', format='grid')


    def _generate_doc(self, resource_name):
        return """

To view container definitions , use:

    >>> client.AssetsContainersDefinitions.show()

To see only specific container definitions , use:

    >>> client.AssetsContainersDefinitions.get(asset_platform='WML',container_name='OPERATE')

Set of {}.


{}

""".format(resource_name, SupportBase(self._props_definitions)._generate_doc_table())


    def _generate_table(self, platform_label='ML_PLATFORM', asset_placeholder_label='ASSET_PLACEHOLDER',space_type_label='SPACE_TYPE',
                        deployment_details_label='DEPLOYMENT_INFO_AVAILABLE',openscale_monitored_label='OPENSCALE_MONITORED',expected_container_label='EXPECTED_CONTAINER',
                        notes_label='NOTES', format='simple'):

        header = [platform_label,asset_placeholder_label, space_type_label,
                  deployment_details_label,openscale_monitored_label,expected_container_label,notes_label]

        # show_post_training = any(
        #     prop.post_training_metrics != '' for prop in self._props_definitions)
        
        # if show_post_training:
        #         row.append(prop.post_training_metrics)

        table_content = []

        for prop in self._props_definitions:
            row = [prop.ml_platform, prop.asset_placeholder if prop.space_type and prop.space_type!='' else 'Project', prop.space_type if prop.space_type else '', u'Y' if prop.deployment_details else u'N', u'Y' if prop.openscale_monitored else u'N', prop.expected_container, prop.notes if prop.notes else u'']

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


class AssetsContainersDefinitions(SupportBase):

    _props_definitions = [
        Prop('WML',False, False, False, False,
             'DEVELOP','The asset in project considered as in development'),
        Prop('WML','Space', 'development', False, False,
             'TEST','Spaces that are not tagged as AIGovernance:Pre-production or AIGovernance:Production are considered as Test environment'),
        Prop('WML', 'Space', 'pre-production', False, False,
             'VALIDATE','Space is tagged as AIGovernance:Pre-production'),
        Prop('WML', 'Space','pre-production', False, True,
             'VALIDATE','Space tagged as pre-production in Watson OpenScale and deployment is monitored as pre-production'),
        Prop('WML', 'Space', 'production', False, False,
             'OPERATE','Space is tagged as AIGovernance:Production'),
        Prop('WML', 'Space', 'production', False, True,
             'OPERATE','Space is tagged as production in Watson OpenScale and deployment is monitored as production'),

        Prop('External','Platform asset catalog', 'development', False, False,
             'DEVELOP','The model does not have any deployments and classified as in a Development environment'),
        
        Prop('External','Platform asset catalog', 'development', True, False,
             'TEST','The asset has deployment info under model stub and is not monitored in Watson OpenScale thus classified as in a Test environment'),
        
        Prop('External', 'Platform asset catalog', 'pre-production', False, True,
             'VALIDATE','The asset deployment is tagged as Pre-production in Watson OpenScale and considered as in pre-production environment'),


        Prop('External', 'Platform asset catalog','production', False, True,
             'OPERATE','The asset deployment is tagged as Production in Watson OpenScale and considered as in production environment')

    ]

    __doc__ = SupportBase(
        _props_definitions)._generate_doc('containers classification definitions')

    def __init__(self):
        SupportBase.__init__(self, self._props_definitions)