from cgi import test
from typing import Dict, Any, Optional


def test_param(        send_persistent: Optional[bool] = True,
        send_live: Optional[bool] = False):
    print("send_persistent", send_persistent, "send_live", send_live)
    if(send_live==False):
        send_persistent = True
    
    print("after - send_persistent", send_persistent, "send_live", send_live)
    
    
def main():
    test_param()
    print("\n")
    test_param(send_persistent=True, send_live=True)
    print("\n")
    test_param(send_live=True)
    print("\n")
    test_param(send_persistent=True)
    print("\n")
    test_param(send_persistent=False, send_live=False)
    
    
if __name__ == "__main__":
    main()
    
    