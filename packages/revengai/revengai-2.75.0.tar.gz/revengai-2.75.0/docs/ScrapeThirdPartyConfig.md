# ScrapeThirdPartyConfig


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**enabled** | **bool** |  | [optional] [default to False]

## Example

```python
from revengai.models.scrape_third_party_config import ScrapeThirdPartyConfig

# TODO update the JSON string below
json = "{}"
# create an instance of ScrapeThirdPartyConfig from a JSON string
scrape_third_party_config_instance = ScrapeThirdPartyConfig.from_json(json)
# print the JSON string representation of the object
print(ScrapeThirdPartyConfig.to_json())

# convert the object into a dict
scrape_third_party_config_dict = scrape_third_party_config_instance.to_dict()
# create an instance of ScrapeThirdPartyConfig from a dict
scrape_third_party_config_from_dict = ScrapeThirdPartyConfig.from_dict(scrape_third_party_config_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


