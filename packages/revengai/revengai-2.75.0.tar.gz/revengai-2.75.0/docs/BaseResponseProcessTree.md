# BaseResponseProcessTree


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**status** | **bool** | Response status on whether the request succeeded | [optional] [default to True]
**data** | [**ProcessTree**](ProcessTree.md) |  | [optional] 
**message** | **str** |  | [optional] 
**errors** | [**List[ErrorModel]**](ErrorModel.md) |  | [optional] 
**meta** | [**MetaModel**](MetaModel.md) | Metadata | [optional] 

## Example

```python
from revengai.models.base_response_process_tree import BaseResponseProcessTree

# TODO update the JSON string below
json = "{}"
# create an instance of BaseResponseProcessTree from a JSON string
base_response_process_tree_instance = BaseResponseProcessTree.from_json(json)
# print the JSON string representation of the object
print(BaseResponseProcessTree.to_json())

# convert the object into a dict
base_response_process_tree_dict = base_response_process_tree_instance.to_dict()
# create an instance of BaseResponseProcessTree from a dict
base_response_process_tree_from_dict = BaseResponseProcessTree.from_dict(base_response_process_tree_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


