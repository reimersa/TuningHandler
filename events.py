event_subscriptions = {} #key -> event type, value->subscriber

def subscribe( event_type: str, fn): 
    if not event_type in event_subscriptions:
        event_subscriptions[event_type] = []
    subscribers[event_type].append( fn )

def post_event( event_type: str, data):
    if not event_type in event_subscriptions:
        return
    for fn in event_subscriptions[event_type]:
        fn(data)


