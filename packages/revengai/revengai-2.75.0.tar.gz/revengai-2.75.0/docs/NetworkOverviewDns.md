# NetworkOverviewDns


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**host** | **str** |  | 
**type** | **str** |  | 
**answers** | [**List[NetworkOverviewDnsAnswer]**](NetworkOverviewDnsAnswer.md) |  | 

## Example

```python
from revengai.models.network_overview_dns import NetworkOverviewDns

# TODO update the JSON string below
json = "{}"
# create an instance of NetworkOverviewDns from a JSON string
network_overview_dns_instance = NetworkOverviewDns.from_json(json)
# print the JSON string representation of the object
print(NetworkOverviewDns.to_json())

# convert the object into a dict
network_overview_dns_dict = network_overview_dns_instance.to_dict()
# create an instance of NetworkOverviewDns from a dict
network_overview_dns_from_dict = NetworkOverviewDns.from_dict(network_overview_dns_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


