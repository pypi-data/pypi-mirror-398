from asyncio.streams import FlowControlMixin
from typing import List

from flows.flows_meta import Flow
from flows.leads_generator_flow.flow.lead_flow import address_based_lead_flow
from google_drive.authenticator import get_google_services

if __name__ == '__main__':

    addresses: List[str] = [
        '108 Ambleside Dr, Pittsburgh, PA 15237',
    ]

    print('Authenticating...')
    get_google_services()
    print('Authenticated successfully.')

    for address in addresses:
        print(f'Working on address: {address}')
        address_based_lead_flow(address=address, flow=Flow.GENERATE_LEADS)
