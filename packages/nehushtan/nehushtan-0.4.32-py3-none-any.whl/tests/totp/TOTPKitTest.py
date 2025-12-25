import time

from nehushtan.helper.authenticate.TOTPKit import TOTPKit

if __name__ == '__main__':

    # shared_secret=b'BASE32SECRET2345AB=='

    # shared_secret = TOTPKit.generate_shared_secret_with_base32()
    # print(shared_secret)
    # print(shared_secret.decode())

    shared_secret = b'67YJGPVA63LAHZKYPJKT'
    print(shared_secret.lower())

    k = TOTPKit(shared_secret)

    last_p = ''
    last_count = 0
    for i in range(60):
        x = k.generate_current_TOTP_tuple()

        t = x[0]
        formatted_time = x[1]
        p = x[3]

        if last_p == p:
            last_count += 1
        else:
            print(f"last p {last_p} for {last_count} times")
            last_p = p
            last_count = 1

        print(f'applied on {x[0]}, available in [{x[1]}, {x[2]}): {x[3]}')

        time.sleep(1)

    print("end")
