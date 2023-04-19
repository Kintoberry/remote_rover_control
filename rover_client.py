import rpyc

if __name__ == "__main__":
    rover_conn = rpyc.connect("localhost", 20000)
    sum = rover_conn.root.add(3, 5)
    print("sum: ", sum)