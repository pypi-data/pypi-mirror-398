# ELFImportModel


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**number_of_imports** | **int** |  | 
**imports** | **List[str]** |  | 

## Example

```python
from revengai.models.elf_import_model import ELFImportModel

# TODO update the JSON string below
json = "{}"
# create an instance of ELFImportModel from a JSON string
elf_import_model_instance = ELFImportModel.from_json(json)
# print the JSON string representation of the object
print(ELFImportModel.to_json())

# convert the object into a dict
elf_import_model_dict = elf_import_model_instance.to_dict()
# create an instance of ELFImportModel from a dict
elf_import_model_from_dict = ELFImportModel.from_dict(elf_import_model_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


