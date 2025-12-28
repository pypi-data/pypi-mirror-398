STARTING = {
    "status": "Starting",
    "details": None,
    "engines": [],
    "engine_lbs": [],
}

RUNNING = {
    "status": "Running",
    "details": None,
    "engines": [
        {
            "ip": "10.1.14.13",
            "name": "engine-7fdd65cd78-9wl2s",
            "status": "Running",
            "reason": None,
            "pipeline_statuses": {"pipelines": []},
            "model_statuses": {
                "models": [
                    {
                        "class": "ccfraud",
                        "name": "3feda548-0e4c-4b36-ad5c-43175ff6924b",
                        "status": "Running",
                    }
                ]
            },
        }
    ],
    "engine_lbs": [
        {
            "ip": "10.1.14.12",
            "name": "engine-lb-577b4b9787-r8f84",
            "status": "Running",
            "reason": None,
        }
    ],
}

ERROR = {
    "status": "Error",
    "details": None,
    "engines": [
        {
            "ip": None,
            "name": "engine-694fd68967-hxvkv",
            "status": "Pending",
            "reason": ["0/1 nodes are available: 1 Insufficient cpu."],
            "pipeline_statuses": None,
            "model_statuses": None,
        }
    ],
    "engine_lbs": [
        {
            "ip": "10.1.14.28",
            "name": "engine-lb-577b4b9787-v52kw",
            "status": "Running",
            "reason": None,
        }
    ],
}

DEPLOYED = {
    "status": "Deployed",
    "details": None,
    "engines": [
        {
            "ip": "10.1.14.173",
            "name": "engine-5857fc75c6-7mr2g",
            "status": "Pending",
            "reason": None,
            "pipeline_statuses": None,
            "model_statuses": None,
        }
    ],
    "engine_lbs": [
        {
            "ip": "10.1.14.172",
            "name": "engine-lb-577b4b9787-pgv9q",
            "status": "Running",
            "reason": None,
        }
    ],
}
