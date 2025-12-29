# Structure


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**last_change** | **str** |  | [optional] 
**name** | **str** | Name of the structure | 
**size** | **int** |  | [optional] 
**members** | [**Dict[str, StructureMember]**](StructureMember.md) | Dictionary of structure members | 
**artifact_type** | **str** | Type of artifact that the structure is associated with | [optional] 

## Example

```python
from revengai.models.structure import Structure

# TODO update the JSON string below
json = "{}"
# create an instance of Structure from a JSON string
structure_instance = Structure.from_json(json)
# print the JSON string representation of the object
print(Structure.to_json())

# convert the object into a dict
structure_dict = structure_instance.to_dict()
# create an instance of Structure from a dict
structure_from_dict = Structure.from_dict(structure_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


