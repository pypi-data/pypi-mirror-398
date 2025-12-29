# ProcessRegistry


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**success** | **bool** |  | 
**data** | **Dict[str, List[Registry]]** |  | 

## Example

```python
from revengai.models.process_registry import ProcessRegistry

# TODO update the JSON string below
json = "{}"
# create an instance of ProcessRegistry from a JSON string
process_registry_instance = ProcessRegistry.from_json(json)
# print the JSON string representation of the object
print(ProcessRegistry.to_json())

# convert the object into a dict
process_registry_dict = process_registry_instance.to_dict()
# create an instance of ProcessRegistry from a dict
process_registry_from_dict = ProcessRegistry.from_dict(process_registry_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


