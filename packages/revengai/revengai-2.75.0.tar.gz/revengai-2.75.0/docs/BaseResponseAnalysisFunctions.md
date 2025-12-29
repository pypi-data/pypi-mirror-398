# BaseResponseAnalysisFunctions


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**status** | **bool** | Response status on whether the request succeeded | [optional] [default to True]
**data** | [**AnalysisFunctions**](AnalysisFunctions.md) |  | [optional] 
**message** | **str** |  | [optional] 
**errors** | [**List[ErrorModel]**](ErrorModel.md) |  | [optional] 
**meta** | [**MetaModel**](MetaModel.md) | Metadata | [optional] 

## Example

```python
from revengai.models.base_response_analysis_functions import BaseResponseAnalysisFunctions

# TODO update the JSON string below
json = "{}"
# create an instance of BaseResponseAnalysisFunctions from a JSON string
base_response_analysis_functions_instance = BaseResponseAnalysisFunctions.from_json(json)
# print the JSON string representation of the object
print(BaseResponseAnalysisFunctions.to_json())

# convert the object into a dict
base_response_analysis_functions_dict = base_response_analysis_functions_instance.to_dict()
# create an instance of BaseResponseAnalysisFunctions from a dict
base_response_analysis_functions_from_dict = BaseResponseAnalysisFunctions.from_dict(base_response_analysis_functions_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


