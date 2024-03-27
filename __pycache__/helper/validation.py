import re
import binary_search
import db_operations

 
def check_school_email_validity(school_email):  
    """
    validates school_email against regular expression  
    RETURNS: bool  
    """  

    try:  
        check = re.search(r"^(?!-)[a-z][a-z-]{1,29}(?<!-)\.[a-z][a-z-]{1,29}(?<!-)\@cns-school\.org$", school_email) 
        check.string  
        return True  
    except AttributeError:  
        return False  

def check_password_validity(password):  
    """  
    validates password against regular expression  
    RETURNS: bool  
    """  

    try:  
        check = re.search(r"^(?=.*?[a-z])(?=.*?[A-Z])(?=.*?[0-9])(?=.*?[#?!@$ %^&*-]).{8,12}$", password)  
        check.string
        return True
    except AttributeError:
        return False 

def check_user_exists(given_school_email, given_password):  
    """ 
    checks if a user exists when making login attempt  
    RETURNS: bool  
    """ 

    sorted_data = db_operations.get_details()  
    target_tuple = (given_school_email, given_password)  
    exists = binary_search(sorted_data, target_tuple)  

    if exists:  
        return True  
    else: 
        return False 
