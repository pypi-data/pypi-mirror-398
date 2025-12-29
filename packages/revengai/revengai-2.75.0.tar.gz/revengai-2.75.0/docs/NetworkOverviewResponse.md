# NetworkOverviewResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**dns** | [**List[NetworkOverviewDns]**](NetworkOverviewDns.md) |  | 
**metadata** | [**List[NetworkOverviewMetadata]**](NetworkOverviewMetadata.md) |  | 

## Example

```python
from revengai.models.network_overview_response import NetworkOverviewResponse

# TODO update the JSON string below
json = "{}"
# create an instance of NetworkOverviewResponse from a JSON string
network_overview_response_instance = NetworkOverviewResponse.from_json(json)
# print the JSON string representation of the object
print(NetworkOverviewResponse.to_json())

# convert the object into a dict
network_overview_response_dict = network_overview_response_instance.to_dict()
# create an instance of NetworkOverviewResponse from a dict
network_overview_response_from_dict = NetworkOverviewResponse.from_dict(network_overview_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


