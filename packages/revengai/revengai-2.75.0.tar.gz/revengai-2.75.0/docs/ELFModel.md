# ELFModel


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**file_type** | **str** |  | 
**architecture** | **str** |  | 
**endianness** | **str** |  | 
**entry_point** | **int** |  | 
**entry_point_bytes** | **str** |  | 
**import_hash** | **str** |  | 
**export_hash** | **str** |  | 
**build_id** | **str** |  | 
**security** | [**ELFSecurity**](ELFSecurity.md) |  | 
**sections** | [**List[ELFSection]**](ELFSection.md) |  | 
**segments** | [**List[ELFSegment]**](ELFSegment.md) |  | 
**symbols** | [**List[ELFSymbol]**](ELFSymbol.md) |  | 
**dynamic_symbols** | [**List[ELFSymbol]**](ELFSymbol.md) |  | 
**relocations** | [**List[ELFRelocation]**](ELFRelocation.md) |  | 
**imports** | [**ELFImportModel**](ELFImportModel.md) |  | 
**exported_functions** | **List[str]** |  | 
**dynamic_entries** | [**List[ElfDynamicEntry]**](ElfDynamicEntry.md) |  | 
**notes** | **List[Dict[str, object]]** |  | 
**debug_info** | **Dict[str, object]** |  | 
**version_info** | **Dict[str, object]** |  | 

## Example

```python
from revengai.models.elf_model import ELFModel

# TODO update the JSON string below
json = "{}"
# create an instance of ELFModel from a JSON string
elf_model_instance = ELFModel.from_json(json)
# print the JSON string representation of the object
print(ELFModel.to_json())

# convert the object into a dict
elf_model_dict = elf_model_instance.to_dict()
# create an instance of ELFModel from a dict
elf_model_from_dict = ELFModel.from_dict(elf_model_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


