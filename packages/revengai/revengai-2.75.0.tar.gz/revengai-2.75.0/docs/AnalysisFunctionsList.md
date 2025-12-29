# AnalysisFunctionsList

API response schema for paginated functions list

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**functions** | [**List[FunctionListItem]**](FunctionListItem.md) | The functions associated with the analysis | 

## Example

```python
from revengai.models.analysis_functions_list import AnalysisFunctionsList

# TODO update the JSON string below
json = "{}"
# create an instance of AnalysisFunctionsList from a JSON string
analysis_functions_list_instance = AnalysisFunctionsList.from_json(json)
# print the JSON string representation of the object
print(AnalysisFunctionsList.to_json())

# convert the object into a dict
analysis_functions_list_dict = analysis_functions_list_instance.to_dict()
# create an instance of AnalysisFunctionsList from a dict
analysis_functions_list_from_dict = AnalysisFunctionsList.from_dict(analysis_functions_list_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


