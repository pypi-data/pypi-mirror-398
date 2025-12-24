# delta-trace-db

(en)Japanese ver
is [here](https://github.com/MasahideMori-SimpleAppli/delta_trace_db_py/blob/main/README_JA.md).  
(ja)
この解説の日本語版は[ここ](https://github.com/MasahideMori-SimpleAppli/delta_trace_db_py/blob/main/README_JA.md)
にあります。

## Overview

**DeltaTraceDB is a lightweight and high-performance in-memory NoSQL database 
that stores and searches class structures as-is.**  
Although it is NoSQL, it also supports full-text search across nested child objects.

Queries in DeltaTraceDB are also represented as classes.  
By serializing and storing these query objects, you can not only restore the database to any past state,  
but also keep operation metadata such as **who / when / what / why / from**.  
This allows you to build rich and highly detailed operation logs suitable for security audits and usage analysis.

## Features

- **Store and search classes directly** (your model classes define the DB structure)
- High-speed search performance even with ~100,000 records
- Queries are classes, making it easy to preserve operation logs
- There is a Dart version for the front end.  
  → https://pub.dev/packages/delta_trace_db
- GUI editor for DB content is under available.   
  → https://github.com/MasahideMori-SimpleAppli/delta_trace_studio

## Basic Operations

For detailed usage, including how to write queries, see the documentation:

📘 [Online Documentation](https://masahidemori-simpleappli.github.io/delta_trace_db_docs/)

## Quickstart

Here's a simple example of server-side code:  
[ServerSide Example](https://github.com/MasahideMori-SimpleAppli/delta_trace_db_py_server_example)  

And here's a simple example:

```python
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Any
from file_state_manager import CloneableFile
from delta_trace_db import DeltaTraceDatabase, QueryBuilder


@dataclass
class User(CloneableFile):
    id: int
    name: str
    age: int
    created_at: datetime
    updated_at: datetime
    nested_obj: dict

    @classmethod
    def from_dict(cls, src: Dict[str, Any]) -> "User":
        return User(
            id=src["id"],
            name=src["name"],
            age=src["age"],
            created_at=datetime.fromisoformat(src["createdAt"]).astimezone(timezone.utc),
            updated_at=datetime.fromisoformat(src["updatedAt"]).astimezone(timezone.utc),
            nested_obj=dict(src["nestedObj"]),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "age": self.age,
            "createdAt": self.created_at.astimezone(timezone.utc).isoformat(),
            "updatedAt": self.updated_at.astimezone(timezone.utc).isoformat(),
            "nestedObj": dict(self.nested_obj),
        }

    def clone(self) -> "User":
        return User.from_dict(self.to_dict())


def main():
    db = DeltaTraceDatabase()
    now = datetime.now(timezone.utc)

    users = [
        User(
            id=-1,
            name="Taro",
            age=30,
            created_at=now,
            updated_at=now,
            nested_obj={"a": "a"},
        ),
        User(
            id=-1,
            name="Jiro",
            age=25,
            created_at=now,
            updated_at=now,
            nested_obj={"a": "b"},
        ),
    ]

    # If you want the return value to be reflected immediately on the front end,
    # set return_data = True to get data that properly reflects the serial key.
    query = (
        QueryBuilder.add(
            target="users",
            add_data=users,
            serial_key="id",
            return_data=True,
        )
        .build()
    )

    # In the Python version, no type specification is required (duck typing)
    r = db.execute_query(query)

    # If you want to check the return value, you can easily do so by using toDict, which serializes it.
    print(r.to_dict())

    # You can easily convert from the Result object back to the original class.
    # The value of r.result is deserialized using the function specified by convert.
    results = r.convert(User.from_dict)


if __name__ == "__main__":
    main()
```

## DB structure

In DeltaTraceDB, each collection corresponds to a **list of class instances**.  
Since the data structure directly mirrors your class definitions,  
it becomes easy to keep consistency between the frontend and backend while  
focusing solely on retrieving the class objects you need.

```
📦 Database (DeltaTraceDB)
├── 🗂️ CollectionA (key: "collection_a")
│   ├── 📄 Item (ClassA)
│   │   ├── id: int
│   │   ├── name: String
│   │   └── timestamp: String
│   └── ...
├── 🗂️ CollectionB (key: "collection_b")
│   ├── 📄 Item (ClassB)
│   │   ├── uid: String
│   │   └── data: Map<String, dynamic>
└── ...
```

## Performance

DeltaTraceDB is fast due to its in-memory design.
Although it has no dedicated optimization mechanisms at the moment,
its performance is roughly equivalent to a simple for loop over the data.
Around 100,000 records can typically be handled without issues.

You can run performance tests using:
```text
tests/test_speed.py
```

Below is an example result from a Ryzen 3600 machine:

```text
tests/test_speed.py speed test for 100000 records
start add
end add: 339 ms
start getAll (with object convert)
end getAll: 659 ms
returnsLength: 100000
start save (with json string convert)
end save: 467 ms
start load (with json string convert)
end load: 558 ms
start search (with object convert)
end search: 866 ms
returnsLength: 100000
start search paging, half limit pre search (with object convert)
end search paging: 425 ms
returnsLength: 50000
start searchOne, the last index object search (with object convert)
end searchOne: 38 ms
returnsLength: 1
start update at half index and last index object
end update: 90 ms
start updateOne of half index object
end updateOne: 16 ms
start conformToTemplate
end conformToTemplate: 82 ms
start delete half object (with object convert)
end delete: 621 ms
returnsLength: 50000
start deleteOne for last object (with object convert)
end deleteOne: 22 ms
returnsLength: 1
start add with serialKey
end add with serialKey: 98 ms
addedCount:100000
```

## Future plans

Although further optimization is possible, performance improvements have lower priority.  
The focus will instead be on improving usability and developing surrounding tools.

## Notes

This package is designed for single-threaded environments.  
When using parallel processing without shared memory, additional mechanisms such as message passing are required.

## Support

There is no official support, but bugs are likely to be fixed actively.  
Please open an issue on GitHub if you find any problems.

## About version control

The C part will be changed at the time of version upgrade.  
However, versions less than 1.0.0 may change the file structure regardless of the following rules.

- Changes such as adding variables, structure change that cause problems when reading previous
  files.
    - C.X.X
- Adding methods, etc.
    - X.C.X
- Minor changes and bug fixes.
    - X.X.C

## License

This software is released under the Apache-2.0 License, see LICENSE file.

Copyright 2025 Masahide Mori

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

## Trademarks

- “Dart” and “Flutter” are trademarks of Google LLC.  
  *This package is not developed or endorsed by Google LLC.*

- “Python” is a trademark of the Python Software Foundation.  
  *This package is not affiliated with the Python Software Foundation.*

- GitHub and the GitHub logo are trademarks of GitHub, Inc.  
  *This package is not affiliated with GitHub, Inc.*
