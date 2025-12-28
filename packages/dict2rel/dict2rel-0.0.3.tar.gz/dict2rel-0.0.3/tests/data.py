DOCSTRING_EXAMPLE_1 = {
    "project": "Alpha-Prime",
    "version": "1.0.3",
    "config": {
        "modules": [
            {
                "id": "A1",
                "status": "active",
                "settings": {
                    "security": {
                        "encryption_level": 5,
                        "algorithms": ["AES-256", "SHA-512"],
                    }
                },
            },
            {
                "id": "B2",
                "status": "passive",
                "settings": {
                    "security": {
                        "encryption_level": 0,
                        "algorithms": ["AES-256"],
                    }
                },
            },
        ]
    },
}

EXAMPLE_SMALL = {
    "name": {"first": "John", "last": "Smith", "suffixes": ["MD", "JD"]},
    "phones": [
        {
            "country": "USA",
            "number": "1234567890",
        },
        {"country": "ESP", "number": "987654321"},
    ],
    "matrix": [[1, 2], [3, 4]],
}
