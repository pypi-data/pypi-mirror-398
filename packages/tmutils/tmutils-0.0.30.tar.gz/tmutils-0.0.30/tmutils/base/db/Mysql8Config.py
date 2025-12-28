from dataclasses import dataclass

@dataclass
class Mysql8Config:
    host: str
    user: str
    password: str
    database: str
    port: int = 3306
    charset: str = "utf8mb4"