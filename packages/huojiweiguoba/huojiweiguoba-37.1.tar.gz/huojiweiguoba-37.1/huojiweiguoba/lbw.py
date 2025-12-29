def print_name(name):
    print(name)
import pyotp
totp = pyotp.TOTP("MOCLJXVN4OSLUUPI3TC6CY237UDIFSAN")
print(totp.now())