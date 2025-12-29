# ELFSymbol


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**name** | **str** |  | 
**value** | **int** |  | 
**size** | **int** |  | 
**type** | **str** |  | 
**binding** | **str** |  | 
**visibility** | **str** |  | 
**section_index** | **int** |  | 

## Example

```python
from revengai.models.elf_symbol import ELFSymbol

# TODO update the JSON string below
json = "{}"
# create an instance of ELFSymbol from a JSON string
elf_symbol_instance = ELFSymbol.from_json(json)
# print the JSON string representation of the object
print(ELFSymbol.to_json())

# convert the object into a dict
elf_symbol_dict = elf_symbol_instance.to_dict()
# create an instance of ELFSymbol from a dict
elf_symbol_from_dict = ELFSymbol.from_dict(elf_symbol_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


