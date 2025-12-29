# ProcessTree


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**success** | **bool** |  | 
**data** | [**List[Process]**](Process.md) |  | 

## Example

```python
from revengai.models.process_tree import ProcessTree

# TODO update the JSON string below
json = "{}"
# create an instance of ProcessTree from a JSON string
process_tree_instance = ProcessTree.from_json(json)
# print the JSON string representation of the object
print(ProcessTree.to_json())

# convert the object into a dict
process_tree_dict = process_tree_instance.to_dict()
# create an instance of ProcessTree from a dict
process_tree_from_dict = ProcessTree.from_dict(process_tree_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


