from pymemcache.client import base

# Connect to Memcached running on localhost and port 11211
client = base.Client(('localhost', 11211))

# Set a key-value pair
client.set('mykey', 'hello')

# Retrieve the value
value = client.get('mykey')

# Print the result
print("Value from Memcached:", value.decode())
