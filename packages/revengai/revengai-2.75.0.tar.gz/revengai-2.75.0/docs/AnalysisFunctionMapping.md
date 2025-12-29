# AnalysisFunctionMapping


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**function_maps** | [**FunctionMapping**](FunctionMapping.md) | A map of function ids to function addresses for the analysis, and it&#39;s inverse. | 

## Example

```python
from revengai.models.analysis_function_mapping import AnalysisFunctionMapping

# TODO update the JSON string below
json = "{}"
# create an instance of AnalysisFunctionMapping from a JSON string
analysis_function_mapping_instance = AnalysisFunctionMapping.from_json(json)
# print the JSON string representation of the object
print(AnalysisFunctionMapping.to_json())

# convert the object into a dict
analysis_function_mapping_dict = analysis_function_mapping_instance.to_dict()
# create an instance of AnalysisFunctionMapping from a dict
analysis_function_mapping_from_dict = AnalysisFunctionMapping.from_dict(analysis_function_mapping_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


