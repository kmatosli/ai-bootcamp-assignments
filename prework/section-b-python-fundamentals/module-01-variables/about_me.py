# about_me.py
# Student profile for AI Bootcamp — Prework Section B, Module 01
# Demonstrates: variables, f-strings, string multiplication, comments

# --- Personal information stored in descriptively named variables ---
first_name = "Kathy"
last_name = "Matos"
age = 53
city = "Chicago"
state = "Illinois"
previous_career = "Investment Research / Portfolio Analytics"
why_learning_to_code = "I'm building Premia, an AI-powered analyst workbench for asset managers."
fun_fact = "I once explained a 30-year equity dataset to a regulator using only a whiteboard and three colours of marker."

# --- String multiplication: build the divider once, reuse it ---
divider = "=" * 44

# --- Print the formatted profile using f-strings ---
print(divider)
print(f"{'Student Profile':^44}")
print(divider)
print(f"{'Name:':<20}{first_name} {last_name}")
print(f"{'Age:':<20}{age}")
print(f"{'City:':<20}{city}, {state}")
print(f"{'Previous Career:':<20}{previous_career}")
print(f"\n{'Why I am learning to code:'}")
print(f'  "{why_learning_to_code}"')
print(f"\n{'Fun fact:'}")
print(f"  {fun_fact}")
print(divider)
