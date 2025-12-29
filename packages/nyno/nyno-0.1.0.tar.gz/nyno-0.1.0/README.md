# nyno (Python driver)
Python client for Nyno (https://nyno.dev) server.

## Installation
```bash
uv add nyno # or: pip install nyno
```

## Usage
```
from nyno import NynoClient

def main():
    client = NynoClient(
        credentials="change_me",
        host="127.0.0.1",
        port=9024,
    )
    print("workflow test", client.run_workflow('/test'))
    print("Client created:", client)

if __name__ == "__main__":
    main()
```



# Build package
```
uv run python -m build
```

# Upload
```
uv run python -m twine upload dist/*          
```

