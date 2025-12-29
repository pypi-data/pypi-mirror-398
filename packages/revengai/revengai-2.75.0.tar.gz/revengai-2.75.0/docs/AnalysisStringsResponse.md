# AnalysisStringsResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**strings** | [**List[StringFunctions]**](StringFunctions.md) | The strings associated with the analysis | 
**total_strings** | **int** | The total number of strings associated with this analysis | 

## Example

```python
from revengai.models.analysis_strings_response import AnalysisStringsResponse

# TODO update the JSON string below
json = "{}"
# create an instance of AnalysisStringsResponse from a JSON string
analysis_strings_response_instance = AnalysisStringsResponse.from_json(json)
# print the JSON string representation of the object
print(AnalysisStringsResponse.to_json())

# convert the object into a dict
analysis_strings_response_dict = analysis_strings_response_instance.to_dict()
# create an instance of AnalysisStringsResponse from a dict
analysis_strings_response_from_dict = AnalysisStringsResponse.from_dict(analysis_strings_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


