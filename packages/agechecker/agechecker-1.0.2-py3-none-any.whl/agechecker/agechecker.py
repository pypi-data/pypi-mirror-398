from datetime import datetime

def agecheck(year_of_birth): # age checking function. main part that scripts use.
    current_year = datetime.now().year
    age = current_year - year_of_birth
    if age < 13:
        title = "Minor"
    elif age < 18:
        title = "Teenager"
    else:
        title = "Adult"
    return age, title

def error(msg): # error handling function
    print("And Error Has Occurred!")
    print(f"Error Message: {msg}")
    raise SystemExit(1)

def main(): # main script.
    current_year = datetime.now().year
    print("What Is Your Year Of Birth?")
    
    try:
        year_of_birth = int(input())
        if year_of_birth < 1900 or year_of_birth < 0: # unrealistic year of birth fixes
            error("Please Enter A Real Year Of Birth!")
    except ValueError:
        error("Please Enter A Number Instead Of Letters!")
    
    if year_of_birth > current_year:
        error("Year Of Birth Cannot Be In The Future!")
    age, title = agecheck(int(year_of_birth))
    print(f"The User Is {age} Years Old, Which Makes Them An {title}.")

if __name__ == "__main__":
    main()
