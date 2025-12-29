# byond.topic

A python module for sending packets to BYOND servers, for calling
`/world/Topic()` and receiving a response. In the same vein as
[BYOND.TopicSender](https://github.com/Cyberboss/BYOND.TopicSender),
but in python!

## Installation

Open the directory, and `pip install .`!

## Exports
### `send(address, port, query)`

Sends a Topic() packet to the specified server, and (ideally) returns
the response from the server.
* `address`: The address (IP, or DNS) of the target DreamDaemon
  instance to send the Topic() packet to.
* `port`: Port that the DreamDaemon instance is serving the world on
* `query`: Query string to be sent. This is an urlencoded series of
  keys (and, where required, values.)
  (...Yeah. it really is just an url query string.)

Returns: A tuple containing the response-type, and the response from
the server.

If the response-type is `TOPIC_RESPONSE_STRING`, the response will be
a dict of key-value pairs, parsed out from the URL query-format string
returned from the server.

The actual data returned from the server depends on the codebase that
the server is running, and the query that was sent.

If the response-type is `TOPIC_RESPONSE_FLOAT`, the response will be a
floating point numeric value.

(`send` automatically opens a socket, transmits the packet, receives
the reply, and then closes the socket again.)

### `queryStatus(address, port)`

Sends a Topic() packet to the specified server, querying the `?status`
endpoint. This returns a string of JSON, or `None` for an invalid
response.

### `queryPlayerCount(address, port)`

Sends a Topic() packet to the specified server, querying the
`?playing` endpoint. This should return the number of
currently-connected players, or `None` for an invalid response.

### Constants

* `TOPIC_PACKET_ID`: The signature that identifies a Topic() packet.
* `TOPIC_RESPONSE_STRING`: Response-type: string
* `TOPIC_RESPONSE_FLOAT`: Response-type: float/numeric
* `MALF_PACKET_ID`: Packet-id that identifies that the server is
  unhappy with the request you just sent.

## Examples

### Requesting World Status

```python

import byond.topic as Topic

responseType, responseData = Topic.send("localhost", 26200, '?status')
if(responseType == Topic.TOPIC_RESPONSE_STRING):
    print(f"We're currently playing a {responseData['mode'][0]} round on {responseData['map_name'][0]}, with {responseData['players'][0]} players!")
```

(The values available in your status response data depend on the
codebase you're querying. Try it and see, first!)
