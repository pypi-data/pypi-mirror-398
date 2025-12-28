from diagrams import Diagram
from diagrams.aws.compute import EC2
from diagrams.aws.database import RDS
from diagrams.aws.network import ELB
from diagrams.programming.language import Python

if __name__ == "__main__":
    with Diagram("Web Service", filename="./data/test", show=True):
        ELB("lb") >> EC2("web") >> RDS("userdb") >> Python("xxx")
