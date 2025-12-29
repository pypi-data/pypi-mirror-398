# TTPSData


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**score** | **int** |  | 
**ttps** | [**List[TTPSElement]**](TTPSElement.md) |  | 

## Example

```python
from revengai.models.ttps_data import TTPSData

# TODO update the JSON string below
json = "{}"
# create an instance of TTPSData from a JSON string
ttps_data_instance = TTPSData.from_json(json)
# print the JSON string representation of the object
print(TTPSData.to_json())

# convert the object into a dict
ttps_data_dict = ttps_data_instance.to_dict()
# create an instance of TTPSData from a dict
ttps_data_from_dict = TTPSData.from_dict(ttps_data_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


