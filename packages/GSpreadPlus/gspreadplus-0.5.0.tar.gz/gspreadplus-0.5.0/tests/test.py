from GSpreadPlus import Spreadclient

client = Spreadclient('test-creds.json')

client.connect_document('12xxjpiwr2bLbD4kdN3TV3aaYEJKQAtbErMR3MGLeO3E')
client.connect_sheet('Profiles', block_width=8)

# data = client.get_rows_by_func(lambda r:'GEM' in r[client.get_header_index('Relations')])
data = client.get_block_by_id('1002')
# client.refresh_sheet()
print(data)
