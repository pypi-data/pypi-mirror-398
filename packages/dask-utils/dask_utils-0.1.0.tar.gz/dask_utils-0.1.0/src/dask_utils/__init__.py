"""
Package containing core dask-utils  functionalities.
"""

from dask_utils import config
from dask_utils.client import DaskClient as Client

resource_location_params = [
    'client'
]
""" sections of Dask utils configuration parameters """

resource_not_exist = []

for section in resource_location_params:

    if not config.get_config().has_section(section):
        resource_not_exist.extend(section)
if resource_not_exist:
    import warnings

    warning_message = '''
        The {0} section from DASK_UTILS_ROOT_CONFIG does not exist
        To get the default behavior, please add a section to client.cfg:
    
          [section]
            option1=value1
            option2=value2
            ....
    
        Define this section into client.cfg config file and restart application.
    '''.format([s for s in resource_not_exist])
    warnings.warn(warning_message, )


