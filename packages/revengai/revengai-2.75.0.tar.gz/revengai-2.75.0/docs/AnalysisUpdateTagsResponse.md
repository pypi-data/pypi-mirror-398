# AnalysisUpdateTagsResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**tags** | [**List[TagResponse]**](TagResponse.md) | The analysis tags after updating | 

## Example

```python
from revengai.models.analysis_update_tags_response import AnalysisUpdateTagsResponse

# TODO update the JSON string below
json = "{}"
# create an instance of AnalysisUpdateTagsResponse from a JSON string
analysis_update_tags_response_instance = AnalysisUpdateTagsResponse.from_json(json)
# print the JSON string representation of the object
print(AnalysisUpdateTagsResponse.to_json())

# convert the object into a dict
analysis_update_tags_response_dict = analysis_update_tags_response_instance.to_dict()
# create an instance of AnalysisUpdateTagsResponse from a dict
analysis_update_tags_response_from_dict = AnalysisUpdateTagsResponse.from_dict(analysis_update_tags_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


