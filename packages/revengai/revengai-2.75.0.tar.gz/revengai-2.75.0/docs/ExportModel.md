# ExportModel


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**number_of_exports** | **int** |  | 
**exports** | **List[Dict[str, int]]** |  | 

## Example

```python
from revengai.models.export_model import ExportModel

# TODO update the JSON string below
json = "{}"
# create an instance of ExportModel from a JSON string
export_model_instance = ExportModel.from_json(json)
# print the JSON string representation of the object
print(ExportModel.to_json())

# convert the object into a dict
export_model_dict = export_model_instance.to_dict()
# create an instance of ExportModel from a dict
export_model_from_dict = ExportModel.from_dict(export_model_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


