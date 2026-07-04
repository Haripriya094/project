def user_login(input_data):
    """
    user logic
    Args:
    input_data:
        email:
        password:

    returns:
    """


    final_json={"status":"failed","message":"failed to login"}
    email = input_data['email']
    user_name=(email.split('@')[0]).replace('.',' ')
    user_id=self.user_collection.find_one({"user_id":user_id})['_id']
    if user_id:
        status=
    user_id=
    print(user_name)

input_data = {
    "email": "Haripriya1610546@gmail.com",
    "password": "Hari@123"
}
print(user_login(input_data))

