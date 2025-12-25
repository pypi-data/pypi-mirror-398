from app import RunAutosmoteAPI

if __name__ == "__main__":
    RunAutosmoteAPI(__name__).run(host="0.0.0.0", port=8080, debug=False)
