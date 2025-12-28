from importlib import resources

chemistry_dict = {
    "auto": {
        "pattern": ""  # auto detect
    },
    "mobiu_5p-1": {
        "pattern": "U8C9L4C9L4C9",
    },
    "mobiu_3p-1": {
        "pattern": "C9L4C9L4C9U8",
        "bc": ["bc1.txt", "bc2.txt", "bc3.txt"],
    },
    "mobiu-1": {
        "pattern": "C9C9C9U8",  # converted
        "bc": ["bc1.txt", "bc2.txt", "bc3.txt"],
    },
    "mobiu_5p-2": {
        "pattern": "U12C9L6C9L6C9L18",
    },
    "mobiu_3p-2": {
        "pattern": "L18C9L6C9L6C9U12",
    },
    "mobiu-2": {
        "pattern": "C9C9C9U12",  # converted
        "bc": ["bc1.txt", "bc2.txt", "bc3.txt"],
        "linker": ["linker1.txt", "linker2.txt", "linker3.txt"],
    },
}

chemistry_dir = str(resources.files("celescope.data.chemistry"))
