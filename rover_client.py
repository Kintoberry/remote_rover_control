import rpyc

if __name__ == "__main__":
    rover_conn = rpyc.connect("localhost", 20000)
    result = rover_conn.root.initiate_rover()
    print("result: ", result)