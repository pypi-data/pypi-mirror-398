# PDBDebugModel


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**debug_entries** | [**List[SinglePDBEntryModel]**](SinglePDBEntryModel.md) |  | 

## Example

```python
from revengai.models.pdb_debug_model import PDBDebugModel

# TODO update the JSON string below
json = "{}"
# create an instance of PDBDebugModel from a JSON string
pdb_debug_model_instance = PDBDebugModel.from_json(json)
# print the JSON string representation of the object
print(PDBDebugModel.to_json())

# convert the object into a dict
pdb_debug_model_dict = pdb_debug_model_instance.to_dict()
# create an instance of PDBDebugModel from a dict
pdb_debug_model_from_dict = PDBDebugModel.from_dict(pdb_debug_model_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


