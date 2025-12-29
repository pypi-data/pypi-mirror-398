# SinglePDBEntryModel


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**guid** | **str** |  | 
**age** | **int** |  | 
**path** | **str** |  | 

## Example

```python
from revengai.models.single_pdb_entry_model import SinglePDBEntryModel

# TODO update the JSON string below
json = "{}"
# create an instance of SinglePDBEntryModel from a JSON string
single_pdb_entry_model_instance = SinglePDBEntryModel.from_json(json)
# print the JSON string representation of the object
print(SinglePDBEntryModel.to_json())

# convert the object into a dict
single_pdb_entry_model_dict = single_pdb_entry_model_instance.to_dict()
# create an instance of SinglePDBEntryModel from a dict
single_pdb_entry_model_from_dict = SinglePDBEntryModel.from_dict(single_pdb_entry_model_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


