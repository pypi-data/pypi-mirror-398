import pywhatkit as kit

TWENTY_TO_FORTHY_GROUP_ID: str = 'CMdxIFPaTzq0bOFU8BxaJj'

#kit.sendwhatmsg_instantly("+972545336285", "Hello!")

def notify_completion(new_leads_count: int) -> None:
    kit.sendwhatmsg_to_group_instantly(
        group_id=TWENTY_TO_FORTHY_GROUP_ID,
        message=f'[Leads Flow System Bot] I have just generated {new_leads_count} new leads for you!'
    )
    print(f'Whatsapp message sent to group {TWENTY_TO_FORTHY_GROUP_ID} with the new leads count')

notify_completion(80)