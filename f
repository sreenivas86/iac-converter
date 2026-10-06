iac-converter/
├── pyproject.toml
├── README.md
├── src/
│   └── iac_converter/
│       ├── __init__.py
│       │
│       ├── api/
│       │   ├── __init__.py
│       │   └── app.py
│       │
│       ├── compiler/
│       │   ├── __init__.py
│       │   ├── yaml_to_ir.py
│       │   └── terraform_to_ir.py
│       │
│       ├── generator/
│       │   ├── __init__.py
│       │   ├── terraform.py
│       │   └── yaml.py
│       │
│       ├── parser/
│       │   ├── __init__.py
│       │   ├── yaml_parser.py
│       │   └── terraform_parser.py
│       │
│       ├── ir/
│       │   ├── __init__.py
│       │   ├── model.py
│       │   ├── resource.py
│       │   ├── provider.py
│       │   ├── variable.py
│       │   ├── output.py
│       │   ├── data_source.py
│       │   ├── expression.py
│       │   └── reference.py
│       │
│       ├── project/
│       │   ├── __init__.py
│       │   ├── project.py
│       │   └── archive.py
│       │
│       └── schema/
│           ├── __init__.py
│           └── provider_schema.py
│
├── tests/
│   ├── unit/
│   │   └── ir/
│   └── integration/
│
├── examples/
│   └── aws/
│
└── .gitignore
-------------------------------------------------------------------------------------------------

✅ M1 — Single-file conversion
   YAML ↔ IR ↔ Terraform

   

        ↓

✅ M2 — Project conversion
   Directory/ZIP ↔ ProjectIR
        ↓
🔨M2.2- load a real directory into Project.

        ↓

🔨 M3 — Robust Terraform expressions
   Traversals
   var.foo
   data.aws_x.y
   module.foo.bar
   indexing
   functions
   conditionals
   for expressions

        ↓

🔨 M4 — Provider schema integration
   terraform providers schema

        ↓

🔨 M5 — Conversion API
   FastAPI
   POST /convert
   ZIP upload/download

        ↓

🔨 M6 — Project storage
   projects
   source format
   generated format
   metadata

        ↓

🔨 M7 — Terraform execution
   init
   plan
   apply
   destroy
   terraform.tfstate






   --------------------------------

   Terraform files
      ↓
  load_project()
      ↓
    Project
      ↓
parse_terraform_project()
      ↓
   ProjectIR
      ↓
generate_terraform_project()
      ↓
    Project
      ↓
  save_project()
      ↓
Terraform files


--------------------------------------------- 06-10-2026




✅ Basic resources
✅ Providers
✅ Variables
✅ Outputs
✅ Expressions
✅ References
✅ Project directories
✅ ZIP projects
✅ Terraform → YAML round trip
✅ YAML → Terraform round trip
⬇
NEXT
Data sources + locals
⬇
depends_on
⬇
count / for_each
⬇
provider aliases
⬇
lifecycle
⬇
nested blocks
⬇
complex expressions
⬇
dynamic blocks
⬇
Provider schemas
⬇
API
⬇
Terraform validate / plan / apply