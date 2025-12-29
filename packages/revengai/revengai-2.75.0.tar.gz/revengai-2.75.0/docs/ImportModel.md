# ImportModel


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**number_of_imports** | **int** |  | 
**imports** | **List[Dict[str, Dict[str, int]]]** |  | 

## Example

```python
from revengai.models.import_model import ImportModel

# TODO update the JSON string below
json = "{}"
# create an instance of ImportModel from a JSON string
import_model_instance = ImportModel.from_json(json)
# print the JSON string representation of the object
print(ImportModel.to_json())

# convert the object into a dict
import_model_dict = import_model_instance.to_dict()
# create an instance of ImportModel from a dict
import_model_from_dict = ImportModel.from_dict(import_model_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


