# AutoUnstripRequest


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**min_similarity** | **float** | Minimum similarity expected for a match as a percentage, default is 90 | [optional] [default to 90.0]
**apply** | **bool** | Whether to apply the matched function names to the target binary, default is False | [optional] [default to False]
**confidence_threshold** | **float** | Confidence threshold for applying function names as a percentage, default is 90 | [optional] [default to 90.0]
**min_group_size** | **int** | Minimum number of matching functions required to consider for a match, default is 10 | [optional] [default to 10]
**status_only** | **bool** | If set to true, only returns the status of the auto-unstrip operation without the actual results | [optional] [default to False]
**no_cache** | **bool** | If set to true, forces the system to bypass any cached results and perform a fresh computation | [optional] [default to False]
**use_canonical_names** | **bool** | Whether to use canonical function names during matching for auto-unstrip, default is False | [optional] [default to False]

## Example

```python
from revengai.models.auto_unstrip_request import AutoUnstripRequest

# TODO update the JSON string below
json = "{}"
# create an instance of AutoUnstripRequest from a JSON string
auto_unstrip_request_instance = AutoUnstripRequest.from_json(json)
# print the JSON string representation of the object
print(AutoUnstripRequest.to_json())

# convert the object into a dict
auto_unstrip_request_dict = auto_unstrip_request_instance.to_dict()
# create an instance of AutoUnstripRequest from a dict
auto_unstrip_request_from_dict = AutoUnstripRequest.from_dict(auto_unstrip_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


