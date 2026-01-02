## About

This is an addon for [qToggleServer](https://github.com/qtoggle/qtoggleserver).

It allows sending values from qToggleServer to [ThingSpeak](https://thingspeak.com/).


## Install

Install using pip:

    pip install qtoggleserver-thingspeak


## Usage

You'll need to register your account on [ThingSpeak](https://thingspeak.com/), if you haven't done it already. After
creating a new channel, you'll find a *write API key*; copy it and use it in the configuration below.


##### `qtoggleserver.conf:`
``` ini
...
event_handlers = [
    ...
    {
        driver = "qtoggleserver.thingspeak.ThingSpeakEventHandler"
        api_key = "FJ3U5TL443012EF7"
        fields = {
            "first_port_id" = 1     # association between port id and ThingSpeak field number
            "second_port_id" = 2
        }
        min_period = 5              # don't specify both min_period and period!
        period = 10
        ...
    }
    ...
]
...
```

The `fields` option associates a port to one of the 8 available ThinkSpeak channel fields. The channel is indirectly
identified by the API key, so there's no direct reference to its id in the configuration. Make sure you're using double
quotes around port ids in `fields` mapping; ports containing dots in their id will break the configuration otherwise.

The optional `min_period` field, if specified, will gather samples from given ports during a period of specified
seconds. The following value change event will simply push gathered samples, together, to ThingSpeak. Only values
that have changed during this time window will be pushed.

The optional `period` field, if specified, indicates a fixed sampling period, in seconds. Given ports will be sampled
with regular cadence. The last port value at the moment of sampling will be sent to ThingSpeak.

You must specify one and only one of `min_period` and `period`, depending on the desired behavior.  

For advanced event filtering, see
[Filter Event Handlers](https://github.com/qtoggle/qtoggleserver/wiki/Filter-Event-Handlers).
