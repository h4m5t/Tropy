from dataclasses import dataclass


@dataclass
class Host:
    ip: str
    main_port: int = None
    sub_port: int = None