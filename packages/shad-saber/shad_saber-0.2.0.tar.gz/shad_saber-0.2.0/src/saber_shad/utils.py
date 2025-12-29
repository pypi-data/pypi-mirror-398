def print_user_info(info: dict):
    print("----- User Info -----")
    print(f"First Name: {info['first_name']}")
    print(f"Username:   {info['username']}")
    print(f"User Guid:  {info['user_guid']}")
    print(f"Phone:      {info['phone']}")
    print("---------------------")

def show_shad_verification(code: str|None):
    print("===== Shad Verification =====")
    if code:
        print(f"code shad: {code}")
    else:
        print("No verification code has been sent to the specified phone number.")
    print("=============================")