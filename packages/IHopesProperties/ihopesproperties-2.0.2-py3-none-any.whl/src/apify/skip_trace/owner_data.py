from typing import List

from attr import dataclass


@dataclass
class PhoneNumber:
    number: str
    type: str
    last_reported_date: str


@dataclass
class Relative:
    name: str
    age: str


@dataclass
class PropertyOwnerInfo:
    first_name: str
    last_name: str
    person_link: str
    age: str
    lives_in_address: str
    phone_numbers: List[PhoneNumber]
    email: str
    relatives: List[Relative]


def transform_skip_trace_results_to_property_owner_info(skip_trace_results: dict) -> PropertyOwnerInfo:
    # Collect phone numbers
    phone_numbers: List[PhoneNumber] = []
    for i in range(1, 4):
        number = skip_trace_results.get(f"Phone-{i}", "").strip()
        if not number:
            continue
        phone_type = skip_trace_results.get(f"Phone-{i} Type", "").strip()
        last_reported = skip_trace_results.get(f"Phone-{i} Last Reported", "").strip()
        phone_numbers.append(
            PhoneNumber(
                number=number,
                type=phone_type,
                last_reported_date=last_reported
            )
        )

    # Collect first available email
    email = ""
    for i in range(1, 10):
        val = skip_trace_results.get(f"Email-{i}", "").strip()
        if val:
            email = val
            break

    # Collect relatives
    relatives: List[Relative] = []
    relatives_data: List[dict] = skip_trace_results.get("Relatives", [])
    for relative in relatives_data:
        name = relative.get("Name", "").strip()
        age = relative.get("Age", "").strip()
        if name:
            relatives.append(Relative(name=name, age=age))

    return PropertyOwnerInfo(
        first_name=skip_trace_results.get("First Name", "").strip(),
        last_name=skip_trace_results.get("Last Name", "").strip(),
        person_link=skip_trace_results.get("Person Link", "").strip(),
        age=skip_trace_results.get("Age", "").strip(),
        lives_in_address=f'{skip_trace_results.get("Street Address", "").strip()}, '
                         f'{skip_trace_results.get("Lives in", "").strip()}',
        phone_numbers=phone_numbers,
        email=email,
        relatives=relatives,
    )
