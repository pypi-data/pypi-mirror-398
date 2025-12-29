# TTPS


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**success** | **bool** |  | 
**data** | [**TTPSData**](TTPSData.md) |  | 

## Example

```python
from revengai.models.ttps import TTPS

# TODO update the JSON string below
json = "{}"
# create an instance of TTPS from a JSON string
ttps_instance = TTPS.from_json(json)
# print the JSON string representation of the object
print(TTPS.to_json())

# convert the object into a dict
ttps_dict = ttps_instance.to_dict()
# create an instance of TTPS from a dict
ttps_from_dict = TTPS.from_dict(ttps_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


