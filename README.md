## Run dev server
`python index.py`

## Install
`pip install -e .`

## Testing

`python setup.py test`

From root
`coverage run --source piperci_gman -m py.test`
`coverage report -m`
OR
`pytest tests`


## Notes About API
Dates: timestamp is an iso8601 formatted date
