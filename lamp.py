from asyncio import current_task
import json
import sys
import tornado.gen
from tornado.ioloop import IOLoop
from wotpy.protocols.http.server import HTTPServer
from wotpy.wot.servient import Servient
import asyncio

CATALOGUE_PORT = 9100
HTTP_PORT = 9101

TD = {
    'title': 'Smart-Lamp',
    'id': 'it:unibo:filippo:benvenuti3:wot-lamp',
    'description': '''A smart lamp which can be turned on and off.''',
    '@context': [
        'https://www.w3.org/2019/wot/td/v1',
    ],
    'properties': {
        'state': {
            'type': 'string',
            'observable': True
        }
    },
    'actions': {
        'on': {
            'description': '''Turn on the lamp, if already on nothing happens.'''
        },
        'off': {
            'description': '''Turn off the lamp, if already off nothing happens.'''
        }
    },
    'events': {
        'stateChanged': {
            'description': '''Lamp just got toggle.''',
            'data': {
                'type': 'string'
            },
        },
    },
}

@tornado.gen.coroutine
def main():

    # Http service.
    http_server = HTTPServer(port=HTTP_PORT)
    
    # Servient.
    servient = Servient(catalogue_port=CATALOGUE_PORT)
    servient.add_server(http_server) # Adding http functionalities.

    # Start servient.
    wot = yield servient.start()

    # Creating thing from TD.
    exposed_thing = wot.produce(json.dumps(TD))

    # Initialize thing property.
    exposed_thing.properties['state'].write('off')

    # Observe state value changing.
    exposed_thing.properties['state'].subscribe(
        on_next=lambda data: exposed_thing.emit_event('stateChanged', f'Value changed for state: {data}'), # What to do when value change.
        on_completed= print('Subscribed for an observable property: state'), # What to do when subscribed.
        on_error=lambda error: print(f'Error trying to observe state: {error}') # What to do in case of error.
    )

    # Handlers for actions.

    # Handle for on.
    async def on_action_handler(params):
        # In this case there are no params.
        # params = params['input'] if params['input'] else {}

        # Change state only if needed.
        current_state = await exposed_thing.read_property('state')
        if current_state == 'off':
            exposed_thing.properties['state'].write('on')
            return {'result': True, 'message': 'Lamp turned on.'}
        return {'result': False, 'message': 'Lamp was already on.'}
    # Register handle for action on.
    exposed_thing.set_action_handler('on', on_action_handler)

    # Handle for off.
    async def off_action_handler(params):
        # In this case there are no params.
        # params = params['input'] if params['input'] else {}

        # Change state only if needed.
        current_state = await exposed_thing.read_property('state')
        if current_state == 'on':
            exposed_thing.properties['state'].write('off')
            return {'result': True, 'message': 'Lamp turned off.'}
        return {'result': False, 'message': 'Lamp was already off.'}
    # Register handle for action off.
    exposed_thing.set_action_handler('off', off_action_handler)

    # Finaly expose lamp thing.
    exposed_thing.expose()
    print(f'{TD["title"]} is ready')

if __name__ == '__main__':
    #asyncio.set_event_loop(asyncio.ProactorEventLoop())
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    IOLoop.current().add_callback(main)
    IOLoop.current().start()