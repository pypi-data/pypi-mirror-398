# AiUnstripRequest


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**apply** | **bool** | Whether to apply the suggested function names to the target functions, default is False | [optional] [default to False]

## Example

```python
from revengai.models.ai_unstrip_request import AiUnstripRequest

# TODO update the JSON string below
json = "{}"
# create an instance of AiUnstripRequest from a JSON string
ai_unstrip_request_instance = AiUnstripRequest.from_json(json)
# print the JSON string representation of the object
print(AiUnstripRequest.to_json())

# convert the object into a dict
ai_unstrip_request_dict = ai_unstrip_request_instance.to_dict()
# create an instance of AiUnstripRequest from a dict
ai_unstrip_request_from_dict = AiUnstripRequest.from_dict(ai_unstrip_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


