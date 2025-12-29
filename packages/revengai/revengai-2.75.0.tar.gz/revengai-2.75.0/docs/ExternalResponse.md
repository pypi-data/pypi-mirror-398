# ExternalResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**sha_256_hash** | **str** |  | 
**data** | **Dict[str, object]** |  | 
**last_updated** | **datetime** |  | 

## Example

```python
from revengai.models.external_response import ExternalResponse

# TODO update the JSON string below
json = "{}"
# create an instance of ExternalResponse from a JSON string
external_response_instance = ExternalResponse.from_json(json)
# print the JSON string representation of the object
print(ExternalResponse.to_json())

# convert the object into a dict
external_response_dict = external_response_instance.to_dict()
# create an instance of ExternalResponse from a dict
external_response_from_dict = ExternalResponse.from_dict(external_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


