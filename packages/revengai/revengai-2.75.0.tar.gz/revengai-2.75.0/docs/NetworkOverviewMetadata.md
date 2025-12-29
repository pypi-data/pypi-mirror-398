# NetworkOverviewMetadata


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**host** | **str** |  | 
**country_code** | **str** |  | 
**asn** | **str** |  | 
**type** | **str** |  | 

## Example

```python
from revengai.models.network_overview_metadata import NetworkOverviewMetadata

# TODO update the JSON string below
json = "{}"
# create an instance of NetworkOverviewMetadata from a JSON string
network_overview_metadata_instance = NetworkOverviewMetadata.from_json(json)
# print the JSON string representation of the object
print(NetworkOverviewMetadata.to_json())

# convert the object into a dict
network_overview_metadata_dict = network_overview_metadata_instance.to_dict()
# create an instance of NetworkOverviewMetadata from a dict
network_overview_metadata_from_dict = NetworkOverviewMetadata.from_dict(network_overview_metadata_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


