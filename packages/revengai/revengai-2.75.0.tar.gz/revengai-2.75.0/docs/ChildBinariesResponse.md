# ChildBinariesResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**children** | [**List[RelativeBinaryResponse]**](RelativeBinaryResponse.md) | List of child binaries associated with the parent binary | 
**parent** | [**RelativeBinaryResponse**](RelativeBinaryResponse.md) |  | [optional] 

## Example

```python
from revengai.models.child_binaries_response import ChildBinariesResponse

# TODO update the JSON string below
json = "{}"
# create an instance of ChildBinariesResponse from a JSON string
child_binaries_response_instance = ChildBinariesResponse.from_json(json)
# print the JSON string representation of the object
print(ChildBinariesResponse.to_json())

# convert the object into a dict
child_binaries_response_dict = child_binaries_response_instance.to_dict()
# create an instance of ChildBinariesResponse from a dict
child_binaries_response_from_dict = ChildBinariesResponse.from_dict(child_binaries_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


