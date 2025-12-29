# TimestampModel


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**pe_timestamp** | **int** |  | 
**export_timestamp** | **int** |  | 
**debug_timestamp** | **int** |  | 

## Example

```python
from revengai.models.timestamp_model import TimestampModel

# TODO update the JSON string below
json = "{}"
# create an instance of TimestampModel from a JSON string
timestamp_model_instance = TimestampModel.from_json(json)
# print the JSON string representation of the object
print(TimestampModel.to_json())

# convert the object into a dict
timestamp_model_dict = timestamp_model_instance.to_dict()
# create an instance of TimestampModel from a dict
timestamp_model_from_dict = TimestampModel.from_dict(timestamp_model_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


