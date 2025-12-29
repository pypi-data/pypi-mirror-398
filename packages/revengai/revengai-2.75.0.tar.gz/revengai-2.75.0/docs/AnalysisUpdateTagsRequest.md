# AnalysisUpdateTagsRequest


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**tags** | **List[str]** |  | 

## Example

```python
from revengai.models.analysis_update_tags_request import AnalysisUpdateTagsRequest

# TODO update the JSON string below
json = "{}"
# create an instance of AnalysisUpdateTagsRequest from a JSON string
analysis_update_tags_request_instance = AnalysisUpdateTagsRequest.from_json(json)
# print the JSON string representation of the object
print(AnalysisUpdateTagsRequest.to_json())

# convert the object into a dict
analysis_update_tags_request_dict = analysis_update_tags_request_instance.to_dict()
# create an instance of AnalysisUpdateTagsRequest from a dict
analysis_update_tags_request_from_dict = AnalysisUpdateTagsRequest.from_dict(analysis_update_tags_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


