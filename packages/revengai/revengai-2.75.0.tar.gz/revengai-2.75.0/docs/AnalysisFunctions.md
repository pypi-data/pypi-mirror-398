# AnalysisFunctions


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**functions** | [**List[AppApiRestV2FunctionsTypesFunction]**](AppApiRestV2FunctionsTypesFunction.md) | The functions associated with the analysis | 

## Example

```python
from revengai.models.analysis_functions import AnalysisFunctions

# TODO update the JSON string below
json = "{}"
# create an instance of AnalysisFunctions from a JSON string
analysis_functions_instance = AnalysisFunctions.from_json(json)
# print the JSON string representation of the object
print(AnalysisFunctions.to_json())

# convert the object into a dict
analysis_functions_dict = analysis_functions_instance.to_dict()
# create an instance of AnalysisFunctions from a dict
analysis_functions_from_dict = AnalysisFunctions.from_dict(analysis_functions_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


