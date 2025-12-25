# Geneva - Multimodal Data Platform

`Geneva` is a petabyte-scale multimodal feature engineering and data management platform.

## Development

See [Development](./DEVELOPMENT.md) for details


## Configuration

Geneva supports specifying configuration in a few difference ways, the resolution order is:

1. overrides from `override_config`
2. enviornment variables
3. pyproject.toml -- recursively search up in dir structure
4. config files in ./.config -- ordered alphabetically
5. defaults from `default_config`

config file is any file ending in `.(json|yaml|yml|toml)`

All configs are expected to be some nested KV string value.

e.g.

```toml
[nested_config]
config.value = "42"
```
is equivalent to `export NESTED_CONFIG.CONFIG.VALUE = 42`

for a list of possible config params, please consult [TODO...](.)
