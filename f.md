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

-----------next target ----------
So the next milestone would be:

M3 — Advanced Terraform blocks

Provisioner connection
Dynamic blocks
Nested blocks
More expression preservation
Stronger round-trip tests

I'd do connection blocks next, one feature at a time just like we've been doing.

M3.2-- terraform nested blocks
Our current IR handles:

resources
attributes
count
for_each
depends_on
lifecycle
provisioners
provisioner connections
providers
variables
data sources
outputs
locals
expressions
references
But it doesn't yet have a first-class representation for arbitrary nested blocks.
------------------
M1.4 — Expression and reference semantics

Test and preserve:

aws_s3_bucket.example
aws_s3_bucket.example.id
data.aws_ami.example.id
var.bucket_name
local.bucket_prefix
each.value
self.public_ip
file("...")
${var.foo} interpolation
complex expressions such as conditional expressions and indexing
----------------------








----------- tasks ---------------27-10-26
1

Expression round-tripping
Next step
Test nested collections containing references, function calls, and conditional expressions in both conversion directions. Verify that expressions don't accidentally become quoted strings or lose their structure.



2

Tuple and collection semantics

Terraform uses square-bracket syntax for tuple/list constructors, and YAML has no native tuple type. Decide how to preserve or represent tuple-versus-list distinctions, potentially using type information or an explicit serialization convention.



3

Full IR coverage

Audit how resources, data sources, providers, variables, outputs, locals, lifecycle rules, provisioners, dependencies, and metadata are represented and preserved across both formats.



4

Provider and resource coverage

S3 is our initial AWS provider/resource focus. Expand and verify support for additional AWS resources, data sources, and provider-specific attributes as required by the project.



5

Validation and error handling

Improve handling of malformed YAML, unsupported Terraform expressions, invalid collection structures, and conversion errors with useful messages.




6

End-to-end verification

Test complete YAML → IR → Terraform and Terraform → IR → YAML conversions on realistic infrastructure examples, including comparisons of semantic equivalence and, where possible, Terraform validation.



7

Production readiness

Review the CLI/API, documentation, supported-feature matrix, fixtures, packaging, and continuous integration.


------------------------- 