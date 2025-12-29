# ReAnalysisForm

Form Model for receiving the analysis request

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**tags** | **List[str]** | Tags associated with the analysis | [optional] [default to []]
**command_line_args** | **str** | Command line arguments for dynamic execution | [optional] [default to '']
**priority** | **int** | Priority of the analysis | [optional] [default to 0]
**essential** | **bool** | Only runs essential parts of the analysis, skips tags/sbom/cves etc. | [optional] [default to True]
**model_name** | **str** |  | [optional] 
**no_cache** | **bool** | When enabled, skips using cached data within the processing. | [optional] [default to False]

## Example

```python
from revengai.models.re_analysis_form import ReAnalysisForm

# TODO update the JSON string below
json = "{}"
# create an instance of ReAnalysisForm from a JSON string
re_analysis_form_instance = ReAnalysisForm.from_json(json)
# print the JSON string representation of the object
print(ReAnalysisForm.to_json())

# convert the object into a dict
re_analysis_form_dict = re_analysis_form_instance.to_dict()
# create an instance of ReAnalysisForm from a dict
re_analysis_form_from_dict = ReAnalysisForm.from_dict(re_analysis_form_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


