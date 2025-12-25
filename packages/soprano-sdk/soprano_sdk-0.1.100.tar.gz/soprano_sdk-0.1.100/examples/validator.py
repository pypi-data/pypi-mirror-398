def validate_age(age, **kwargs):
    if age < 10 or  age > 50:
        return False
    return True

def validate_output(res):

    print(res)

    return True

def print_date_range(state):
    print(state)

def validate_name(name: str, **kwargs) :
    print(f"Validating name: {name}")
    if len(name) < 3:
        return False, "Name must be at least 3 characters long, Please enter a valid name."
    return True, ""

def test_age(state):
    return {"age": 23, "valid": True}

def validate_indian_state(state: str, **kwargs) :
    print(f"Validating Indian state: {state}")
    indian_states = {
        "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
        "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand"}
    return state in indian_states


def validate_mobile_number(number: str) :
    print(f"Validating mobile number: {number}")
    if len(number) != 10 or not number.isdigit():
        return False
    return True