# PEModel


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**type** | **str** |  | 
**timestamps** | [**TimestampModel**](TimestampModel.md) |  | 
**architecture** | **str** |  | 
**checksum** | **int** |  | 
**image_base** | **int** |  | 
**security** | [**SecurityModel**](SecurityModel.md) |  | 
**version_info** | **Dict[str, object]** |  | 
**debug_info** | [**PDBDebugModel**](PDBDebugModel.md) |  | 
**number_of_resources** | **int** |  | 
**entry_point** | [**EntrypointModel**](EntrypointModel.md) |  | 
**signature** | [**CodeSignatureModel**](CodeSignatureModel.md) |  | 
**dotnet** | **bool** |  | 
**debug_stripped** | **bool** |  | 
**import_hash** | **str** |  | 
**export_hash** | **str** |  | 
**rich_header_hash** | **str** |  | 
**sections** | [**SectionModel**](SectionModel.md) |  | 
**imports** | [**ImportModel**](ImportModel.md) |  | 
**exports** | [**ExportModel**](ExportModel.md) |  | 
**icon_data** | [**IconModel**](IconModel.md) |  | 

## Example

```python
from revengai.models.pe_model import PEModel

# TODO update the JSON string below
json = "{}"
# create an instance of PEModel from a JSON string
pe_model_instance = PEModel.from_json(json)
# print the JSON string representation of the object
print(PEModel.to_json())

# convert the object into a dict
pe_model_dict = pe_model_instance.to_dict()
# create an instance of PEModel from a dict
pe_model_from_dict = PEModel.from_dict(pe_model_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


